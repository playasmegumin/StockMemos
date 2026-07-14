# 数据备份接口规范

> 定义 StockMemos 的导出/导入数据格式、文件结构、API 接口和导入规则。
> 对应 Milestone 9。
> 版本：0.1（草案）

---

## 1. 压缩包结构

```
backup_20260713.zip
├── stocks.json              # 个股列表 + 标签
├── capital_flows.json       # 现金流记录
├── transactions.json        # 交易记录
├── memos.json               # 投资备忘
└── kline/                   # K 线数据（可选）
    ├── 600519_SH.csv
    ├── 00700_HK.csv
    ├── 07515_HK.csv
    └── AAPL_US.csv
```

- 所有文件使用 **UTF-8 without BOM** 编码
- 压缩格式：**ZIP**（`.zip`）
- K 线子目录 `kline/` 可选，仅当导出时勾选「K 线数据」时存在
- 文件名命名：`{证券代码}_{交易所}.csv`，交易所使用两位大写代码（SH / SZ / HK / US）

---

## 2. JSON 文件格式

### 2.1 stocks.json

```json
{
  "version": "1",
  "exported_at": "2026-07-13T10:00:00Z",
  "stocks": [
    {
      "exchange": "SH",
      "symbol": "600519",
      "name": "贵州茅台",
      "tags": ["白酒", "权重"]
    },
    {
      "exchange": "HK",
      "symbol": "00700",
      "name": "腾讯控股",
      "tags": ["互联网"]
    }
  ]
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `version` | string | 是 | 格式版本号（当前为 `"1"`） |
| `exported_at` | string (ISO 8601) | 是 | 导出时间戳 |
| `stocks` | array | 是 | 个股列表 |
| `stocks[].exchange` | string | 是 | 交易所代码（SH/SZ/HK/US/BJ） |
| `stocks[].symbol` | string | 是 | 证券代码（纯数字或字母代码，无交易所后缀） |
| `stocks[].name` | string | 否 | 证券名称（导入时缺失则由 Provider 自动拉取） |
| `stocks[].tags` | string[] | 否 | 标签列表（按创建时间排序，第一个为主标签） |

**导入逻辑：**
- 以 `exchange + symbol` 为唯一键
- 已存在：跳过（不覆盖，不报错）
- 不存在：创建 Stock + 创建 Tag 记录

### 2.2 transactions.json

```json
{
  "version": "1",
  "exported_at": "2026-07-13T10:00:00Z",
  "transactions": [
    {
      "exchange": "SH",
      "symbol": "600519",
      "quantity": 100,
      "price": 1500.00,
      "gas": 5.00,
      "traded_at": "2026-01-15"
    }
  ]
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `version` | string | 是 | 格式版本号 |
| `exported_at` | string (ISO 8601) | 是 | 导出时间戳 |
| `transactions` | array | 是 | 交易记录列表 |
| `transactions[].exchange` | string | 是 | 交易所代码 |
| `transactions[].symbol` | string | 是 | 证券代码 |
| `transactions[].quantity` | number | 是 | 数量（正=买入，负=卖出） |
| `transactions[].price` | number | 是 | 成交价 |
| `transactions[].gas` | number | 是 | 佣金/手续费 |
| `transactions[].traded_at` | string (YYYY-MM-DD) | 是 | 交易日期 |

**导入逻辑：**
- 以 `exchange + symbol` 匹配 Stock 记录
- 匹配成功 → 创建 Transaction
- 匹配失败 → 跳过该条交易（不报错，计入 skipped 统计）
- 重复交易判断：相同 exchange + symbol + quantity + price + traded_at → 跳过

### 2.3 memos.json

```json
{
  "version": "1",
  "exported_at": "2026-07-13T10:00:00Z",
  "memos": [
    {
      "title": "茅台分析",
      "content": "## 观点\n2026年值得继续持有。",
      "stock_exchange": "SH",
      "stock_symbol": "600519",
      "created_at": "2026-07-10T08:00:00Z",
      "updated_at": "2026-07-10T08:00:00Z"
    },
    {
      "title": "投资策略",
      "content": "控制仓位在 80% 以下。",
      "stock_exchange": null,
      "stock_symbol": null,
      "created_at": "2026-07-09T12:00:00Z",
      "updated_at": "2026-07-09T12:00:00Z"
    }
  ]
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 备忘标题 |
| `content` | string | 是 | 备忘正文（Markdown） |
| `stock_exchange` | string\|null | 否 | 关联股票交易所（为 null 则为纯文本备忘） |
| `stock_symbol` | string\|null | 否 | 关联股票代码 |
| `created_at` | string (ISO 8601) | 否 | 创建时间（缺失则使用导入时间） |
| `updated_at` | string (ISO 8601) | 否 | 更新时间（缺失则同 created_at） |

**导入逻辑：**
- `stock_exchange + stock_symbol` 匹配 Stock
  - 匹配成功 → 关联到该 Stock
  - 匹配失败 → 不关联（纯文本备忘，不阻止导入）
- 按 title + created_at 判重
- 已存在则跳过

### 2.4 capital_flows.json

```json
{
  "version": "1",
  "exported_at": "2026-07-13T10:00:00Z",
  "capital_flows": [
    {
      "type": "deposit",
      "amount": 10000.00,
      "currency": "CNY",
      "note": "入金",
      "created_at": "2026-06-01T10:00:00"
    }
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | `deposit` / `withdraw` / `fee` |
| `amount` | decimal | 是 | 金额 |
| `currency` | string | 否 | 货币代码（默认 `CNY`） |
| `note` | string | 否 | 备注 |
| `created_at` | datetime | 否 | 创建时间（ISO 8601） |

**导入逻辑：**
- 无判重，直接创建新记录
- currency 字段缺失时默认为 `CNY`

---

## 3. K 线 CSV 格式

### 3.1 文件名

`{symbol}_{exchange}.csv`

示例：`600519_SH.csv`、`00700_HK.csv`、`AAPL_US.csv`

### 3.2 列定义

```
date,open,high,low,close,volume,amount
2026-01-02,1980.00,1992.00,1970.00,1985.00,32145,63767850
2026-01-03,1985.00,1994.50,1975.00,1983.50,28456,56452100
```

| 列名 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `date` | YYYY-MM-DD | 是 | 交易日 |
| `open` | decimal | 是 | 开盘价 |
| `high` | decimal | 是 | 最高价 |
| `low` | decimal | 是 | 最低价 |
| `close` | decimal | 是 | 收盘价 |
| `volume` | integer | 是 | 成交量（股数） |
| `amount` | decimal | 否 | 成交金额（货币单位，部分数据源缺失） |

### 3.3 导入逻辑

- 以 `exchange + symbol + date` 为唯一键
- 已存在：**更新覆盖**（UPSERT）
- 不存在：创建
- K 线数据不参与导入结果统计（不计数）

---

## 4. API 端点

### 4.1 POST /api/backup/export

**请求：**

```json
Content-Type: application/json

{
  "types": ["stocks", "transactions", "memos", "capital_flows", "kline"]
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `types` | string[] | 是 | 要导出的内容类型。可选值：`stocks` / `transactions` / `memos` / `capital_flows` / `kline`。至少选一项。 |

**响应：**

```
Content-Type: application/zip
Content-Disposition: attachment; filename="stockmemos_export_20260713.zip"

（二进制 ZIP 流）
```

- 后端用 `zipfile` 库在内存中构建压缩包
- 使用 `StreamingResponse` 流式返回，不写临时文件

### 4.2 POST /api/backup/import

**请求：**

```
Content-Type: multipart/form-data

file: <stockmemos_export_20260713.tar.gz>
```

**响应：**

```json
{
  "imported": {
    "stocks": 5,
    "transactions": 12,
    "memos": 3,
    "kline_files": 2
  },
  "skipped": {
    "stocks": ["SH/600519", "HK/00700"],
    "transactions": 0,
    "memos": 0
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `imported.stocks` | int | 成功导入的新股票数 |
| `imported.transactions` | int | 成功导入的新交易数 |
| `imported.memos` | int | 成功导入的新备忘数 |
| `imported.kline_files` | int | 成功导入的 K 线 CSV 文件数 |
| `skipped.stocks` | string[] | 因已存在而跳过的股票列表（"exchange/symbol" 格式） |
| `skipped.transactions` | int | 因对应 Stock 不存在而跳过的交易数 |
| `skipped.memos` | int | 因已存在而跳过的备忘数 |

---

## 5. CLI 脚本

### 5.1 位置

`backend/scripts/backup.py`

### 5.2 使用方式

```bash
# Docker 内执行
docker compose exec backend python -m scripts.backup export --types stocks,transactions --output /tmp/backup.zip

docker compose exec backend python -m scripts.backup import --file /tmp/backup.zip
```

### 5.3 命令

```
usage: backup.py export [-h] --types TYPES [--output OUTPUT]
usage: backup.py import [-h] --file FILE

options:
  -h, --help        show this help message and exit

export:
  --types TYPES     逗号分隔的导出类型: stocks,transactions,memos,capital_flows,kline
  --output OUTPUT   输出文件路径（默认: ./stockmemos_export_<date>.zip）

import:
  --file FILE       导入文件路径（.zip）
```

- 脚本复用后端 ORM 模型（`from app.models import ...`）
- 使用 `settings.database_url` 连接数据库
- 输出文件默认写到当前工作目录

---

## 6. 前端交互

### 6.1 位置

设置页（Settings.vue）新增「数据备份」模块。

### 6.2 布局

```
┌─────────────────────────────────────────────┐
│  数据备份                                      │
│                                              │
│  ☑ 个股列表（含标签）                           │
│  ☑ 现金流记录                                 │
│  ☑ 交易记录                                   │
│  ☐ 投资备忘                                   │
│  ☐ K 线数据                                   │
│                                              │
│  [ 导出 ]    [ 导入 ]                         │
│                                              │
│  （导入结果展示区域）                            │
└─────────────────────────────────────────────┘
```

### 6.3 导出流程

1. 用户勾选需要导出的内容类型
2. 点击「导出」
3. 前端调用 `POST /api/backup/export`（body: `{ types: ["stocks", "transactions"] }`）
4. 浏览器接收 `StreamingResponse` 并下载为 `.zip` 文件

### 6.4 导入流程

1. 点击「导入」
2. 系统弹出文件选择器（accept: `.zip`）
3. 上传文件 → `POST /api/backup/import`（multipart/form-data）
4. 展示导入结果面板：
   ```
   导入完成：
   ✅ 个股：5 条成功 / 2 条跳过（SH/600519, HK/00700）
   ✅ 交易：12 条成功
   ✅ 现金流：3 条成功
   ✅ 备忘：3 条成功
   ✅ K 线：2 个文件
   ```

---

## 7. 与现有数据的关系

| 数据类型 | 导出来源 | 导入目标 | 唯一键 |
|---------|---------|---------|--------|
| stocks | Stock + StockTag | Stock + StockTag | exchange + symbol |
| capital_flows | CapitalFlow | CapitalFlow | 无判重，直接创建 |
| transactions | Transaction | Transaction | exchange + symbol + quantity + price + traded_at |
| memos | InvestmentMemo | InvestmentMemo | title + created_at |
| kline | kline_daily | kline_daily | exchange + symbol + date |

**不包含的内容：**
- StockAnalyze（基本面分析，实时数据）
- Report（Agent 分析报告）
- TpSlPoint（止盈止损点，与具体持仓股关联复杂）

---

## 8. 版本兼容

| 版本 | 变更 |
|------|------|
| v1 | 初始版本。stocks / transactions / memos / kline |
| v2 | 新增 capital_flows.json |
