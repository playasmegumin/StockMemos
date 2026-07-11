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

#### 存储架构

三张表联合工作：

```
┌─────────────────────┐      ┌──────────────────────────┐
│   exchange_rates    │      │     capital_flow          │
├─────────────────────┤      ├──────────────────────────┤
│  currency     PK    │←─FK──│  currency                  │
│  rate_to_cny        │      │  type (deposit/withdraw/fee)│
│  updated_at         │      │  amount (+/-)              │
└─────────────────────┘      │  note                      │
                              │  created_at                │
                              └───────┬──────────────────┘
                                       │ 增删触发重算
                                       ▼
                              ┌──────────────────────────┐
                              │     capital_meta          │ ← 单行缓存
                              ├──────────────────────────┤
                              │  total_invested_cny       │ ← SUM(流水×汇率)
                              │  total_historical_pnl_cny │ ← SUM(股盈亏×汇率)
                              │  updated_at               │
                              └──────────────────────────┘
```

**`exchange_rates` 表：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `currency` | varchar(10) PK | 币种代码：CNY / HKD / USD |
| `rate_to_cny` | decimal(18,6) | 1 单位本币兑 CNY，CNY=1 |
| `updated_at` | datetime | 最后更新时间 |

- 数据来源：容器启动时由 seed 脚本写入（与前端 `exchangeRates.ts` 同源维护）
- 后续扩展：可加 `api_source` 字段支持自动更新

**`capital_flow` 表：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID PK | 主键 |
| `type` | varchar(20) | 操作类型：`deposit`(存入) / `withdraw`(取出) / `fee`(手续费) |
| `amount` | decimal(18,4) | 金额，**正负号约定**：deposit>0, withdraw<0, fee<0 |
| `currency` | varchar(10) | 币种，FK → exchange_rates.currency，默认 CNY |
| `note` | text, nullable | 备注 |
| `created_at` | datetime | 创建时间 |

**`capital_meta` 表（单行）：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int PK, default=1 | 始终为 1，全表仅一行 |
| `total_invested_cny` | decimal(18,4) | 总投入金额(CNY)：`SUM(capital_flow.amount × rate_to_cny)` |
| `total_historical_pnl_cny` | decimal(18,4) | 历史总盈亏(CNY)：`SUM(stock.historical_pnl × rate_to_cny)` |
| `updated_at` | datetime | 最后更新时间 |

#### 自动更新机制

**触发点 1：`capital_flow` 增删**
```sql
-- 重算 total_invested_cny
UPDATE capital_meta SET
  total_invested_cny = (
    SELECT SUM(cf.amount * er.rate_to_cny)
    FROM capital_flow cf
    JOIN exchange_rates er ON cf.currency = er.currency
  ),
  updated_at = NOW()
WHERE id = 1;
```

**触发点 2：`Transaction` 增删**
```sql
-- 重算 total_historical_pnl_cny
UPDATE capital_meta SET
  total_historical_pnl_cny = (
    SELECT SUM(s.historical_pnl * er.rate_to_cny)
    FROM stock s
    JOIN exchange_rates er ON s.currency = er.currency
  ),
  updated_at = NOW()
WHERE id = 1;
```

实现方式：在后端 API 的 `create/delete capital_flow` 和 `_recalc_stock` 中追加重算调用。

#### KPI 计算公式（最终确认版）

| 指标 | 公式 | 数据来源 |
|------|------|---------|
| **总投入金额** | `capital_meta.total_invested_cny` | 缓存 |
| **历史总盈亏** | `capital_meta.total_historical_pnl_cny` | 缓存 |
| **总持仓金额** | `SUM(position × current_price × 汇率)` | 前端计算 |
| **可用现金** | 总投入金额 + 历史总盈亏 | 前端计算 |
| **总资产** | 可用现金 + 总持仓金额 | 前端计算 |
| **总收益率** | 总资产 / 总投入金额 | 前端计算 |
| **总仓位** | 总持仓金额 / 总资产 | 前端计算 |

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
+ <t-menu-item value="capital">资金流水</t-menu-item>
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
