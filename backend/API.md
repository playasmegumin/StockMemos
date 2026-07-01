# StockMemos 后端 API 参考

> 版本: 1.0 — 供前端开发参考
> 后端运行在 `http://localhost:8080`，测试页面: `http://localhost:8080/test/`

---

## 数据模型总览

```
stock（个股概览）
│
├── transaction（交易记录, 1:N）
│
└── stock_analyze（个股分析, 1:1）
      ├── fundamentals_data（JSONB 基本面）
      ├── reports（分析报告, 1:N）
      ├── tp_sl_points（止盈止损点, 1:N）
      └── stock_tags（个股标签, 1:N）
```

---

## Stock — 个股概览

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/stocks` | POST | 创建个股 |
| `/api/stocks` | GET | 获取所有个股 |
| `/api/stocks/{id}` | GET | 获取单只个股 |
| `/api/stocks/{id}` | PUT | 更新个股基本信息 |
| `/api/stocks/{id}` | DELETE | 删除个股（级联删除交易记录） |

### 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string (UUID) | 主键 |
| `exchange` | string | 交易所: `SH` / `SZ` / `HK` / `US` |
| `symbol` | string | 股票代码: `600519` / `AAPL` |
| `name` | string | 股票名称 |
| `currency` | string | 交易货币: `CNY` / `USD` / `HKD` |
| `position` | float | 当前持仓数量（自动从交易记录累计） |
| `historical_pnl` | float | 历史盈亏（自动计算） |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

### 约束
- `(exchange, symbol)` 唯一组合

### 请求示例（POST / PUT）

```json
{
  "exchange": "SH",
  "symbol": "600519",
  "name": "贵州茅台",
  "currency": "CNY"
}
```

### 响应示例

```json
{
  "id": "uuid...",
  "exchange": "SH",
  "symbol": "600519",
  "name": "贵州茅台",
  "currency": "CNY",
  "position": 0.0,
  "historical_pnl": 0.0,
  "created_at": "2025-07-01 10:00:00",
  "updated_at": "2025-07-01 10:00:00"
}
```

---

## Transaction — 交易记录

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/transactions` | POST | 创建交易记录（自动更新 position / pnl） |
| `/api/transactions` | GET | 获取所有交易记录 |
| `/api/transactions/{id}` | GET | 获取单条交易记录 |
| `/api/transactions/{id}` | PUT | 更新交易记录（自动重新计算） |
| `/api/transactions/{id}` | DELETE | 删除交易记录（自动重新计算） |
| `/api/transactions/stock/{stock_id}` | GET | 获取某只股票的所有交易记录 |

### 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string (UUID) | 主键 |
| `stock_id` | string | FK → `stock.id` |
| `quantity` | float | **正数 = 买入, 负数 = 卖出** |
| `price` | float | 成交价格 |
| `gas` | float | 手续费 |
| `traded_at` | date | 交易日期 |
| `created_at` | datetime | 记录创建时间 |

### 自动计算逻辑

每条交易记录的**创建/更新/删除**都会触发 `stock.position` 和 `stock.historical_pnl` 重新计算：

- `position = Σ quantity`
- `historical_pnl = -Σ(quantity × price + gas)`

### 请求示例

```json
{
  "stock_id": "uuid...",
  "quantity": 100,
  "price": 10.5,
  "gas": 5.0,
  "traded_at": "2025-07-01"
}
```

```json
{
  "stock_id": "uuid...",
  "quantity": -50,
  "price": 12.0,
  "gas": 3.0,
  "traded_at": "2025-07-15"
}
```

---

## StockAnalyze — 个股分析

**1:1 关系**：每只股票只有一个分析记录，自动创建，反复更新。

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/stock-analyze/stock/{stock_id}` | GET | 获取分析（不存在则自动创建空记录） |
| `/api/stock-analyze/{id}` | PUT | 更新基本面数据（JSONB） |
| `/api/stock-analyze/{id}` | DELETE | 删除分析（级联删除所有子表记录） |

### 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string (UUID) | 主键 |
| `stock_id` | string | FK → `stock.id`，唯一 |
| `fundamentals_data` | object (JSONB) | 基本面数据，自由结构 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

### fundamentals_data 示例（自由扩展）

Agent 分析后写入，键值完全灵活：

```json
{
  "pe_ttm": 25.5,
  "pb": 6.2,
  "roe": 0.18,
  "market_cap": 2500000000000,
  "dividend_yield": 0.015,
  "profit_growth_rate": 0.12,
  "debt_ratio": 0.35
}
```

### PUT 请求示例

```json
{
  "fundamentals_data": {
    "pe_ttm": 25.5,
    "pb": 6.2,
    "roe": 0.18
  }
}
```

---

## Report — 分析报告（stock_analyze 子表）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/stock-analyze/{id}/reports` | GET | 获取报告列表（按时间倒序） |
| `/api/stock-analyze/{id}/reports` | POST | 创建报告 |
| `/api/stock-analyze/{id}/reports/{rid}` | GET | 获取单条报告 |
| `/api/stock-analyze/{id}/reports/{rid}` | PUT | 更新报告 |
| `/api/stock-analyze/{id}/reports/{rid}` | DELETE | 删除报告 |

### 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string (UUID) | 主键 |
| `stock_analyze_id` | string | FK → `stock_analyze.id` |
| `generated_at` | datetime | 报告生成时间 |
| `title` | string (200) | 报告标题 |
| `content` | text | 报告正文 |
| `created_at` | datetime | 记录创建时间 |

### 请求示例

```json
{
  "generated_at": "2025-07-01T10:00:00",
  "title": "基本面分析报告",
  "content": "这是一份由 Agent 自动生成的分析报告，包含详细的财务分析和估值判断..."
}
```

---

## TpSlPoint — 止盈止损点（stock_analyze 子表）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/stock-analyze/{id}/tp-sl-points` | GET | 获取止盈止损点列表 |
| `/api/stock-analyze/{id}/tp-sl-points` | POST | 创建止盈止损点 |
| `/api/stock-analyze/{id}/tp-sl-points/{pid}` | PUT | 更新止盈止损点 |
| `/api/stock-analyze/{id}/tp-sl-points/{pid}` | DELETE | 删除止盈止损点 |

### 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string (UUID) | 主键 |
| `stock_analyze_id` | string | FK → `stock_analyze.id` |
| `price` | float | 股价 / 目标价 |
| `label` | string | 标签：`买入` / `卖出` / `目标估值` |
| `notes` | text | 备注（可选） |
| `created_at` | datetime | 记录创建时间 |

### 请求示例

```json
{
  "price": 150.0,
  "label": "卖出",
  "notes": "达到目标价，考虑分批减仓"
}
```

---

## StockTag — 个股标签（stock_analyze 子表）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/stock-analyze/{id}/stock-tags` | GET | 获取标签列表 |
| `/api/stock-analyze/{id}/stock-tags` | POST | 创建标签 |
| `/api/stock-analyze/{id}/stock-tags/{tid}` | DELETE | 删除标签 |

### 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string (UUID) | 主键 |
| `stock_analyze_id` | string | FK → `stock_analyze.id` |
| `tag` | string (50) | 自由文本标签 |
| `created_at` | datetime | 记录创建时间 |

标签为自由文本，无枚举限制。示例值：

```
"分红", "投机", "成长", "价值", "周期", "高股息", "行业龙头"
```

### 请求示例

```json
{
  "tag": "成长"
}
```

---

## 级联删除规则

| 删除操作 | 影响 |
|----------|------|
| DELETE `/api/stocks/{id}` | 级联删除该 stock 的所有 transactions |
| DELETE `/api/stock-analyze/{id}` | 级联删除所有 reports / tp_sl_points / stock_tags |

---

## 前端开发建议

### 获取个股完整信息（含分析和交易）

```javascript
// 并行请求，获取全貌
const stock = await fetch(`/api/stocks/${stockId}`).then(r => r.json());
const analyze = await fetch(`/api/stock-analyze/stock/${stockId}`).then(r => r.json());
const transactions = await fetch(`/api/transactions/stock/${stockId}`).then(r => r.json());

// analyze.id 用于后续嵌套请求
const { id: analyzeId } = analyze;
const reports = await fetch(`/api/stock-analyze/${analyzeId}/reports`).then(r => r.json());
const tpSlPoints = await fetch(`/api/stock-analyze/${analyzeId}/tp-sl-points`).then(r => r.json());
const tags = await fetch(`/api/stock-analyze/${analyzeId}/stock-tags`).then(r => r.json());
```

### 创建新股票 + 第一笔交易

```javascript
// 1. 创建股票
const stock = await fetch('/api/stocks', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({exchange:'SH', symbol:'600519', name:'贵州茅台', currency:'CNY'})
}).then(r => r.json());

// 2. 录入交易记录（自动更新 position / pnl）
await fetch('/api/transactions', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({stock_id: stock.id, quantity: 100, price: 10, gas: 5, traded_at: '2025-07-01'})
}).then(r => r.json());

// 3. 获取分析记录（自动创建）
const analyze = await fetch(`/api/stock-analyze/stock/${stock.id}`).then(r => r.json());
```

### 错误处理

API 在以下情况返回 HTTP 错误码：

| 状态码 | 含义 | 常见场景 |
|--------|------|----------|
| 201 | 创建成功 | POST 请求 |
| 204 | 删除成功 | DELETE 请求 |
| 404 | 资源不存在 | ID 错误或已被删除 |
| 409 | 冲突 | 创建重复的 `(exchange, symbol)` |
