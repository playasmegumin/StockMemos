# Market Data 扩展设计方案

## 1. .env 配置

```ini
# 按交易所选择数据源
MARKET_DATA_SOURCE_CN=Tushare    # A股数据源: Tushare / yfinance
MARKET_DATA_SOURCE_HK=yfinance   # 港股数据源
MARKET_DATA_SOURCE_US=yfinance   # 美股数据源

# Tushare API Key（A股用）
TUSHARE_API_KEY=your_key_here
```

## 2. 新增数据库表

### kline_daily（日K线）

```sql
CREATE TABLE kline_daily (
    stock_id   VARCHAR(36)  NOT NULL REFERENCES stock(id) ON DELETE CASCADE,
    trade_date DATE         NOT NULL,
    open       NUMERIC(12,4) NOT NULL,
    high       NUMERIC(12,4) NOT NULL,
    low        NUMERIC(12,4) NOT NULL,
    close      NUMERIC(12,4) NOT NULL,
    volume     NUMERIC(20,4) NOT NULL,   -- 成交量（股数）
    amount     NUMERIC(20,4) NOT NULL,   -- 成交额（元/港币/美元）
    PRIMARY KEY (stock_id, trade_date)
);
```

### 基本面

沿用 `stock_analyze.fundamentals_data` JSONB 字段，后台自动填充。

## 3. 统一数据结构

```python
class CurrentPrice(BaseModel):
    symbol: str
    exchange: str           # SH/SZ/HK/US
    price: float
    price_time: datetime
    currency: str           # CNY/HKD/USD
    volume: float | None
    source: str             # "tushare" / "yfinance"

class DailyKline(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float

class Fundamentals(BaseModel):
    symbol: str
    exchange: str
    name: str
    sector: str | None
    industry: str | None
    market_cap: float | None
    pe_ratio: float | None
    pb_ratio: float | None
    dividend_yield: float | None
    eps: float | None
    roe: float | None
    profit_margin: float | None
    debt_to_equity: float | None
    current_ratio: float | None
    beta: float | None
    avg_volume: float | None
    week52_high: float | None
    week52_low: float | None
    source: str
    data_date: date
```

## 4. Backend 架构

```
services/market_data/
├── __init__.py
├── provider_base.py          # BaseProvider 抽象类
├── providers/
│   ├── __init__.py
│   ├── yfinance_provider.py  # HK/US 数据源
│   └── tushare_provider.py   # A 股数据源（降级支持）
├── provider_router.py        # 按 exchange 路由到对应 provider
├── market_data_service.py    # 高层业务逻辑（缓存+DB+Provider编排）
└── schemas.py                # Pydantic 数据模型
```

## 5. API 端点

```python
# 实时行情（纯内存，不落盘）
GET /api/stocks/{id}/price
  → Backend: 内存缓存未过期? → 返回
            | 否则 → provider.get_current_price()
            → 写入缓存 → 返回

# 日K（持久化）
GET /api/stocks/{id}/kline?start=&end=
  → Backend: DB 查询 → 返回 list[DailyKline]

# 基本面（持久化）
GET /api/stocks/{id}/fundamentals
  → Backend: DB 查询 → 返回 Fundamentals

# 批量刷新（前端触发）
POST /api/market/refresh
  → 遍历所有股票:
     拉日K（昨日至今最新）→ UPSERT kline_daily
     拉基本面 → UPSERT stock_analyze.fundamentals_data
POST /api/market/refresh-fundamentals
  → 仅刷新所有股票基本面
```

## 6. 刷新策略

| 场景 | 触发 | 存储 |
|------|------|------|
| 首次打开页面 | 前端检查昨日日K缺失→调 POST /refresh | PostgreSQL |
| 点击"刷新基本面"按钮 | 前端调 POST /refresh-fundamentals | PostgreSQL |
| 打开个股详情 | 前端 GET /price（实时） | 纯内存 |
| 页面刷新/重新打开 | 前端 GET /price（实时） | 纯内存 |

## 7. 数据源降级规则

```
TuShareProvider:
  get_capabilities() → {"kline", "fundamentals"}
  get_current_price() → 返回最近日K收盘价（降级）

YFinanceProvider:
  get_capabilities() → {"price", "kline", "fundamentals"}
  get_current_price() → 实时延迟报价
```

## 8. 前端显示

- 实时行情标签: `数据源: yfinance | 按需更新`
- 若降级: `数据源: TuShare | 日级更新（盘后价）`
- 涨跌幅等衍生值由前端实时计算
- 持仓概览页个股列表上方增加"刷新基本面"按钮
