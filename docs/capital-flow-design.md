# 资金管理 — 设计备忘

> 2026-07-10 / 2026-07-11 讨论记录，待后续实现

本文档包含两个独立但相关的功能设计：

1. **现金流水** — 记录资金存入/取出/手续费，按币种管理总投入金额
2. **投资备忘** — 个人非个股绑定的投资笔记

---

## 第一部分：现金流水

### 需求

维护一个"总投入金额"（从收入中划入投资的资金），按币种分别统计，用于计算：
- **总投入金额（CNY）** = SUM(存入 + 取出 + 手续费)，按 CNY 汇率折算
- **可用现金** = 总投入金额(CNY) − 总持仓金额(CNY)
- **总资产** = 总持仓金额(CNY) + 可用现金
- **总收益率** = 总盈亏 / 总投入金额(CNY)

### 概念定义

| 概念 | 公式 | 说明 |
|------|------|------|
| **总投入金额** | `SUM(capital_flow.amount)` | 净投入，手续费也计入（消耗部分） |
| **可用现金** | 总投入金额 − 总持仓金额(CNY) | 当前未持仓的现金 |
| **总资产** | 总持仓金额(CNY) + 可用现金 | 总持仓 + 现金 |
| **总收益率** | 总盈亏 / 总投入金额 | 所有交易已实现盈亏 ÷ 总投入 |

### 设计决策

#### 分层架构（最终定稿）

```
┌────────────────────────────────────────────────────────────┐
│  前端计算层                                                │
│                                                            │
│  现金   = 总投入金额 + 历史实际总盈亏                       │
│  总资产 = 现金 + 总持仓金额                                 │
│  总收益率 = 总资产 / 总投入金额                             │
│  总仓位  = 总持仓金额 / 总资产                              │
└───────────────────────┬────────────────────────────────────┘
                        │ 读取
┌───────────────────────▼────────────────────────────────────┐
│  capital_meta 表（单行缓存）                                │
│                                                            │
│  total_invested_cny       ← capital_flow 增删时触发重算     │
│  total_historical_pnl_cny ← transaction 增删时触发重算      │
│  total_position_value_cny ← 行情刷新时触发重算              │
└──────┬──────────────┬──────────────────┬───────────────────┘
       │              │                  │
       ▼              ▼                  ▼
┌──────────┐  ┌──────────────┐  ┌─────────────┐
│capital   │  │ exchange     │  │ stock表     │
│_flow     │  │ _rates       │  ├─────────────┤
│(现金流水)│  │(汇率字典)     │  │historical   │
│          │  │              │  │_pnl(原币)   │
│type      │  │CNY=1         │  │position(股数)│
│amount    │  │HKD=0.86754   │  │price        │
│currency  │  │USD=6.8047    │  │currency     │
│note      │  │              │  │             │
└──────────┘  └──────────────┘  └─────────────┘
```

#### 各层职责明细

**① Stock 表（个股数据层）—— 维护个股维度的原币数值**

| 字段 | 维护方式 | 说明 |
|------|---------|------|
| `historical_pnl` | `_recalc_stock()` | 交易记录增删时自动重算：`-SUM(quantity × price + gas)` |
| `position` | `_recalc_stock()` | 交易记录增删时自动重算：`SUM(quantity)` |
| `price` (最新价) | 行情刷新时更新 | 调用 Provider 获取 |
| `currency` | 用户添加时设定 | CNY / HKD / USD |
| `historical_pnl_cny` | 折算后缓存 | `historical_pnl × exchange_rates.rate_to_cny` |
| `position_value_cny` | 行情刷新时重算 | `position × price × exchange_rates.rate_to_cny` |

- `historical_pnl_cny` 和 `position_value_cny` 是 **可选缓存字段**，不做死。不加也不影响功能，前端实时折算也行。

**② `exchange_rates` 表（汇率字典）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `currency` | varchar(10) PK | 币种代码 |
| `rate_to_cny` | decimal(18,6) | 1 单位本币兑 CNY，CNY=1 |
| `updated_at` | datetime | 更新时间 |

- 容器启动时由 seed 脚本写入（与前端 exchangeRates.ts 同源维护）

**③ `capital_flow` 表（现金流水）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID PK | |
| `type` | varchar(20) | `deposit` / `withdraw` / `fee` |
| `amount` | decimal(18,4) | deposit>0, withdraw<0, fee<0 |
| `currency` | varchar(10) | FK → exchange_rates.currency，默认 CNY |
| `note` | text, nullable | |
| `created_at` | datetime | |

**④ `capital_meta` 表（单行缓存）**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK, default=1 | 始终为 1 |
| `total_invested_cny` | decimal(18,4) | `SUM(capital_flow.amount × rate_to_cny)` |
| `total_historical_pnl_cny` | decimal(18,4) | `SUM(stock.historical_pnl × rate_to_cny)` |
| `total_position_value_cny` | decimal(18,4) | `SUM(stock.position × stock.price × rate_to_cny)` |
| `updated_at` | datetime | |

#### 缓存更新机制

采用 **PostgreSQL 数据库触发器** 自动更新，而非 Python 层面手动调用。

**触发器函数 1：`recalc_invested()`**
- 触发事件：`capital_flow` 表 INSERT / DELETE
- 动作：重算 `total_invested_cny`

**触发器函数 2：`recalc_pnl_position()`**
- 触发事件：`stock` 表 UPDATE（position 变化）/ DELETE，`transaction` 表 INSERT / DELETE
- 动作：重算 `total_historical_pnl_cny` + `total_position_value_cny`

**行情刷新**
- 由 `POST /api/market/refresh` 在 Python 层面调用：从 `kline_daily` 取最新 `close` 更新 `total_position_value_cny`。
- 刚添加的股票无 K 线时，`JOIN` 不命中，SUM 中不贡献持仓金额；触发行情刷新后自动补算。

#### 汇率表填充

`exchange_rates` 表在容器构建启动时由后端 seed 脚本写入，写死与前端 `config/exchangeRates.ts` 相同的值（CNY=1, HKD=0.86754, USD=6.8047）。两端同步手动维护。

#### 金额符号约定

用户永远在表单中填正数，后端根据 `type` 转换符号：

| 类型 | 用户填 | 数据库存 |
|------|--------|---------|
| `deposit` 存入 | ¥10,000 | `amount = 10000` |
| `withdraw` 取出 | ¥5,000 | `amount = -5000` |
| `fee` 手续费 | ¥100 | `amount = -100` |

#### API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/capital/summary` | 返回 `{ total_invested_cny, total_historical_pnl_cny, total_position_value_cny }`，前端据此算出 4 个 KPI |
| `GET` | `/api/capital/flows` | 流水记录列表（分页，按 created_at 降序） |
| `POST` | `/api/capital/flows` | 添加流水（body: `{ type, amount, currency?, note? }`） |
| `DELETE` | `/api/capital/flows/{id}` | 删除流水 |

**`GET /api/capital/summary` 返回值 → 前端计算 4 个 KPI：**

```javascript
cash = total_invested_cny + total_historical_pnl_cny           // 可用现金
total_asset = cash + total_position_value_cny                   // 总资产
return_rate = total_asset / total_invested_cny                  // 总收益率
position_ratio = total_position_value_cny / total_asset         // 总仓位
```

#### 前端页面结构

**持仓总览页（`/`）**
- 顶部 4 张 KPI 卡片：总资产 / 总收益率 / 总仓位 / 现金
- Portfolio Treemap（已有）
- 持仓列表（已有）

**资金管理页（`/capital`）**
- 顶部 4 张 KPI 卡片：总资产 / 总收益率 / 总仓位 / 现金（与持仓总览相同）
- 现金流记录表格（按时间降序）
- 添加记录对话框

#### 全套指标公式（最终定稿）

| # | 指标 | 公式 | 计算层 |
|---|------|------|--------|
| 1 | 个股历史总盈亏（原币） | `_recalc_stock()`: `-SUM(qty×price+gas)` | Stock 表 |
| 2 | 个股持仓总金额（原币） | `position × 现价` | Stock 表 / 前端 |
| 3 | **历史实际总盈亏（CNY）** | `SUM(stock.historical_pnl × rate_to_cny)` | capital_meta 缓存 |
| 4 | **总投入金额（CNY）** | `SUM(capital_flow.amount × rate_to_cny)` | capital_meta 缓存 |
| 5 | **总持仓金额（CNY）** | `SUM(stock.position × price × rate_to_cny)` | capital_meta 缓存 |
| 6 | **现金** | ③ + ④ | **前端** |
| 7 | **总资产** | ⑥ + ⑤ | **前端** |
| 8 | **总收益率** | ⑦ / ④ | **前端** |
| 9 | **总仓位** | ⑤ / ⑦ | **前端** |

> **缓存字段 optional**：`historical_pnl_cny` 和 `position_value_cny` 如果在 Stock 表中维护，capital_meta 的聚合直接 SUM 这些字段，无需 JOIN 汇率表。不加也不影响，只是每次聚合多一次 JOIN 而已。

#### 前端
| 项目 | 决策 |
|------|------|
| 入口 | 侧边栏新增「资金流水」菜单项 |
| 页面 | 独立页面 `/capital` |
| KPI 卡片（在该页面顶部） | 总资产 / 总收益率 / 总仓位 / 现金 |
| 操作列表 | 表格展示所有流水记录，按 `created_at` 降序 |
| 添加记录 | 弹出对话框：选择类型（存入/取出/手续费）、金额、币种、备注 |
| 持仓总览页 KPI 卡片 | 暂不变（"现金"卡片保持 0），后续再联 |

#### API
- `GET /api/capital/cash` — 获取现金概况（总投入金额按币种、总资产、现金）
- `GET /api/capital/flows` — 获取流水列表（分页，按 created_at 降序）
- `POST /api/capital/flows` — 添加一条记录（body: `{ type, amount, currency?, note? }`）
- `DELETE /api/capital/flows/{id}` — 删除一条记录

#### 侧边栏 & 路由

```diff
  <t-menu-item value="dashboard">持仓总览</t-menu-item>
+ <t-menu-item value="capital">资金管理</t-menu-item>
  <t-menu-item value="memos">投资备忘</t-menu-item>
```

```diff
  { path: '/',                 component: PortfolioDashboard },
  { path: '/stock/:id',        component: StockDetail },
+ { path: '/capital',          component: CapitalManage },
```

---

## 第二部分：投资备忘

### 需求

记录不绑定特定个股的个人投资笔记，例如：
- 市场观察和判断
- 交易计划
- 经验反思
- 知识整理

### 设计决策

#### 存储
| 项目 | 决策 |
|------|------|
| 存储方式 | 后端数据库 `investment_memo` 表（新表） |
| 与现有 `report` 表的区别 | `report` 绑定 Stock，`investment_memo` 完全独立 |

`investment_memo` 表结构：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID PK | 主键 |
| `title` | varchar(200), nullable | 标题（可选，不填则以 content 首行截取） |
| `content` | text | 正文，支持 Markdown |
| `type` | varchar(50), default="general" | 分类：`general` / `plan` / `review` / `idea` |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

#### 前端
| 项目 | 决策 |
|------|------|
| 入口 | 侧边栏「投资备忘」→ 独立页面 `/memos` |
| 列表样式 | 时间线逆序排列，卡片展示 |
| 编辑器 | Markdown 文本域 + 预览切换 |

#### API
- `GET /api/investment-memos` — 列表（分页，按 created_at 降序）
- `GET /api/investment-memos/{id}` — 单条
- `POST /api/investment-memos` — 创建（body: `{ title?, content, type? }`）
- `PUT /api/investment-memos/{id}` — 更新
- `DELETE /api/investment-memos/{id}` — 删除

---

## 实现顺序

建议分两次 Change 实现：

1. **第一次 Change：现金流水** — `capital_flow` 表 + migration + API + 独立页面
2. **第二次 Change：投资备忘** — `investment_memo` 表 + migration + API + 独立页面

两个功能完全独立，无依赖关系，可按需交换顺序。
