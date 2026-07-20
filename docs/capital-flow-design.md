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

### 变更范围一览

#### 🔵 无需修改（已有逻辑）

| 表 | 字段 | 更新方式 | 代码位置 |
|----|------|---------|---------|
| Stock | `position` | 后端 `_recalc_stock()`: `SUM(quantity)` | `routers/transaction.py` |
| Stock | `historical_pnl` | 后端 `_recalc_stock()`: `-SUM(qty×price+gas)` | `routers/transaction.py` |
| Stock | `currency` | 创建时设定 | `routers/stock.py` |

#### 🟢 后端新增

| 表 | 字段 | 更新方式 | 代码位置 |
|----|------|---------|---------|
| `exchange_rates` | 全部 | seed 脚本，容器启动时写入 | 新增 `scripts/seed_exchange_rates.py` |
| `capital_flow` | 全部 | 后端 API（CRUD） | 新增 `routers/capital.py` |
| `capital_meta` | `total_position_value_cny` | kline_daily INSERT/UPDATE 触发自动重算 | 无需 Python 代码 |

#### 🟣 数据库层新增（PostgreSQL Trigger）

| 触发事件 | 触发器函数 | 更新表 | 更新字段 |
|---------|-----------|--------|---------|
| `capital_flow` INSERT / DELETE | `recalc_invested()` | `capital_meta` | `total_invested_cny` |
| `transaction` INSERT / DELETE / UPDATE | `recalc_pnl_position()` | `capital_meta` | `total_historical_pnl_cny` + `total_position_value_cny` |
| `kline_daily` INSERT / UPDATE | `recalc_position_value()` | `capital_meta` | `total_position_value_cny` |
| `stock` DELETE | `recalc_pnl_position()` | `capital_meta` | 同上（聚合中移除该股贡献） |

#### 🟡 前端新增

| 页面 | 变更 | 说明 |
|------|------|------|
| 持仓总览 `/` | KPI 卡片替换 | 旧：收益/股票/持仓金额/现金 → **新：总资产/总收益率/总仓位/现金** |
| 资金管理 `/capital` | 新建页面 | 4 KPI 卡片（同上）+ 现金流记录表格 |
| API 调用 | `GET /api/capital/summary` | 返回 3 个缓存值，前端算 4 个 KPI |
| 侧边栏 | 新增"资金管理" | → 路由 `/capital` |

---

### 表结构总表

#### `Stock` 表（个股数据层）

| 中文 | 字段 | 类型 | 维护方 | 说明 |
|------|------|------|--------|------|
| 持仓股数 | `position` | decimal | 🔵 | `_recalc_stock()`: `SUM(quantity)` |
| 历史总盈亏(原币) | `historical_pnl` | decimal | 🔵 | `_recalc_stock()`: `-SUM(qty×price+gas)` |
| 个股所属币种 | `currency` | varchar | 🔵 | 创建时分类器推断 |
| 最新价(原币) | 存于 `kline_daily.close` | decimal | 🔵 | 行情刷新时写入 |

#### `exchange_rates` 表（汇率字典）

| 中文 | 字段 | 类型 | 维护方 | 说明 |
|------|------|------|--------|------|
| 币种 | `currency` | varchar PK | 🟢 | 容器启动 seed |
| 兑人民币汇率 | `rate_to_cny` | decimal | 🟢 | 构建时一次写入 |
| 更新时间 | `updated_at` | datetime | 🟢 | 自动 |

#### `capital_flow` 表（现金流水）

| 中文 | 字段 | 类型 | 维护方 | 说明 |
|------|------|------|--------|------|
| 主键 | `id` | UUID PK | 🟢 | 自动生成 |
| 操作类型 | `type` | varchar(20) | 🟢 | `deposit`/`withdraw`/`fee` |
| 金额 | `amount` | decimal | 🟢 | 用户填正数，后端转符号 |
| 币种 | `currency` | varchar(10) | 🟢 | FK → exchange_rates，默认 CNY |
| 备注 | `note` | text | 🟢 | 可选 |
| 创建时间 | `created_at` | datetime | 🟢 | 自动 |

#### `capital_meta` 表（单行缓存）

| 中文 | 字段 | 类型 | 重算方法 | 维护方 | 触发时机 |
|------|------|------|---------|--------|---------|
| 主键 | `id` | int PK=1 | — | 🟢 | 首次创建 |
| 总投入金额(CNY) | `total_invested_cny` | decimal | `SUM(capital_flow.amount × rate)` | 🟣 | capital_flow INSERT/DELETE |
| 历史总盈亏(CNY) | `total_historical_pnl_cny` | decimal | `SUM(stock.historical_pnl × rate)` | 🟣 | transaction 增删 / stock DELETE |
| 总持仓金额(CNY) | `total_position_value_cny` | decimal | `SUM(stock.position × kline.close × rate)` | 🟣 | transaction 增删 / kline_daily 写入时 |
| 更新时间 | `updated_at` | datetime | 自动 | 自动 | |

#### 前端计算指标（🟡）

| 中文 | 公式 | 数据来源 | 展示位置 |
|------|------|---------|---------|
| 可用现金 | 总投入金额 + 历史总盈亏 | capital_meta | 持仓总览页 + 资金管理页 |
| 总资产 | 可用现金 + 总持仓金额 | capital_meta | 持仓总览页 + 资金管理页 |
| 总收益率 | 总资产 / 总投入金额 | capital_meta | 持仓总览页 + 资金管理页 |
| 总仓位 | 总持仓金额 / 总资产 | capital_meta | 持仓总览页 + 资金管理页 |

#### 缓存更新机制

采用 **PostgreSQL 数据库触发器** 自动更新，而非 Python 层面手动调用。

**触发器函数 1：`recalc_invested()`**
- 触发事件：`capital_flow` 表 INSERT / DELETE
- 动作：重算 `total_invested_cny`

**触发器函数 2：`recalc_pnl_position()`**
- 触发事件：`stock` 表 DELETE，`transaction` 表 INSERT / DELETE / UPDATE
- 动作：重算 `total_historical_pnl_cny` + `total_position_value_cny`

**触发器函数 3：`recalc_position_value()`**
- 触发事件：`kline_daily` 表 INSERT / UPDATE
- 动作：重算 `total_position_value_cny`

**行情刷新**
- `POST /api/market/refresh` 写入 `kline_daily` → `recalc_position_value()` 触发器自动重算 `total_position_value_cny`
- 刚添加的股票无 K 线时，`JOIN` 不命中，SUM 中不贡献持仓金额；K 线写入后自动补算。

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

#### 历史盈亏校准（Change: `historical-pnl-adjustments`）

用户可以维护一组历史盈亏调整记录。所有记录按当前配置汇率折算后的金额之和构成账户级“历史实际总盈亏偏移值”，并入跨账户累计投资结果。系统只定义聚合算法，不限制用户记录的数据来源、业务含义或是否存在重复。

已确认的第一版约束：

- 每条记录包含原币金额、币种（CNY/HKD/USD）、备注、创建时间和更新时间，并允许新增、编辑和删除。
- `历史实际总盈亏偏移值 = SUM(历史盈亏调整记录金额 × exchange_rates.rate_to_cny)`；没有记录时为 `0`。
- `历史实际总盈亏 = 系统内历史盈亏 + 历史实际总盈亏偏移值`。
- 当前净投入大于 `0` 时，`历史总收益率 = (系统内历史盈亏 + 总持仓金额 + 历史实际总盈亏偏移值) / 当前净投入`。
- 偏移值只作用于历史实际总盈亏及历史总收益率，不影响当前现金、当前总资产、总仓位和总浮盈。
- 偏移值不分摊到个股；个股历史盈亏仍只反映 StockMemos 内已有交易。
- 表单提供 CNY/HKD/USD 币种选项；系统保存原币金额和币种，但不保存汇率快照、汇率日期或业务发生日期。
- 当前净投入小于或等于 `0` 时，历史总收益率显示“已回本”，暂不计算回本后的复杂收益率。

> **汇率口径声明**：历史盈亏调整使用设置页当前维护的兑人民币汇率动态折算，因此修改汇率会重估历史实际总盈亏和历史总收益率。该方案不保存录入时汇率，不用于审计级历史汇率还原或多币种归因。

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

> 投资备忘：**NOT YET IMPLEMENTED** — 设计完成，留待下个 change 实现

### 需求

记录不绑定特定个股的个人投资笔记，例如：
- 市场观察和判断
- 交易计划
- 经验反思
- 知识整理

也可关联已有持仓个股，方便在个股详情页统一查看。

### 表结构

`investment_memo`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID PK | 主键 |
| `title` | text | 必填 |
| `content` | text | Markdown 原文（不渲染，16px 字号阅读友好） |
| `stock_id` | UUID FK → Stock.id | 可选，关联个股（下拉选择持仓列表） |
| `created_at` | datetime | 自动 |
| `updated_at` | datetime | 自动 |

### 页面布局

**入口：** 侧边栏「投资备忘」→ 独立页面 `/memos`

**顶部：新增/编辑区**
- 标题输入框
- 关联个股下拉框（仅列出已有持仓股票，用户需先添加股票才能关联）
- 正文输入框（textarea，16px 字号）
- 保存按钮
- 编辑模式下：内容回填到此区域，保存按钮变为「更新」，不创建新条目

**下方：卡片列表（时间线，按 created_at 降序）**
- 卡片收起态：标题 + 创建时间 + 关联股票名（如有）
- 点击卡片任意区域展开：显示正文全文
- 展开后显示：编辑按钮（内容回填到顶部区）+ 删除按钮（需二次确认）

### 个股详情页联动

个股详情页标签页区域新增「投资备忘」标签页（位于止盈止损之后），过滤显示 `stock_id = 当前个股` 的备忘条目。用户在此处无法编辑，需跳转至 `/memos` 页面操作。

### 后端 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/memos` | 备忘列表（可选 `?stock_id=` 过滤） |
| GET | `/api/memos/{id}` | 单条备忘 |
| POST | `/api/memos` | 创建（body: `{ title, content, stock_id? }`） |
| PUT | `/api/memos/{id}` | 更新 |
| DELETE | `/api/memos/{id}` | 删除 |

---

## 实现顺序

建议分两次 Change 实现：

1. **第一次 Change：现金流水** — `capital_flow` 表 + migration + API + 独立页面
2. **第二次 Change：投资备忘** — `investment_memo` 表 + migration + API + 独立页面

两个功能完全独立，无依赖关系，可按需交换顺序。
