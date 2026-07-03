# Market Data 扩展 — 需求与设计方案

> 生成时间: 2026-07-03
> 生成方式: opencode grilling (14 轮结构化访谈)
> 对应文件: `backend/app/services/market_data/PLAN.md`（实施技术方案）
> 前提条件: 本文件 + PLAN.md + PROJECT.md 三者配合使用，修改需求时需同步更新三者。

---

## 1. 原始需求

为 StockMemos 增加三个市场的数据能力：

1. 拉取 A 股、港股、美股**实时股价**，用于前端动态计算资产变化
2. 拉取 A 股、港股、美股**日 K 线数据**，用于计算 MA120 等技术指标并在网页端生成 K 线图
3. 拉取 A 股、港股、美股**基本面数据**（PE/PB/ROE/市值等）

修改范围包括：数据库表单结构、后端处理函数、前端显示方法。

---

## 2. Grilling 决策过程（14 轮）

### Q1：数据源选择（最基础的决策）
- **问题**：用什么 API 覆盖 A 股 + 港股 + 美股？
- **候选**：TuShare Pro（已有 A 股） / yfinance / AKShare / Polygon / Finnhub
- **决策**：支持在 `.env` 配置文件中按交易所粒度设置：`CN=Tushare US=yfinance HK=yfinance`。
- **约束**：已有 Tushare 2000 积分 API Key。

### Q2：实时股价的"实时"定义是什么？
- **问题**：需要的实时程度（盘后日级 / 分钟级轮询 / 秒级 / 真实时）？
- **决策**：分钟级刷新可以接受。有前端页面连接时进行分钟级刷新（前端驱动），后端不存实时数据。

### Q3：A 股实时报价——TuShare 2000 积分够吗？
- **问题**：TuShare 2000 分能否满足 A 股实时 + 基本面需求？
- **发现**：TuShare 2000 分可拿日 K 和基本面，但拿不到盘中实时报价。yfinance 有延迟 15 分钟免费报价。
- **决策**：A 股日 K/基本面用 TuShare，实时价用 yfinance 兜底。港股/美股全部 yfinance。

### Q4：yfinance 是否支持获取 PE 等基本面数据？
- **问题**：yfinance 基本面覆盖度如何？
- **发现**：`Ticker.info` 提供 50+ 基本面字段（PE/PB/ROE/市值/股息率等）。美股完美覆盖，港股良好，A 股稀疏常有缺失。
- **决策**：A 股基本面用 TuShare（权威准确），港股/美股基本面用 yfinance。

### Q5：A 股数据源最终选哪个？
- **问题**：TuShare vs yfinance 各有优劣，以哪个为主？
- **决策**：不拆分实时/基本面配置，统一按交易所设置。如果数据源拿不到分钟级实时，自动降级返回最新日 K 收盘价，降级逻辑封装在 provider 内部，对外提供统一接口。

### Q6：统一数据结构怎么定？
- **问题**：不同数据源返回格式不统一，需要统一 Pydantic 模型。
- **决策**：
  - `CurrentPrice`: `{symbol, exchange, price, price_time, currency, volume, source}` — 精简 7 字段
  - `DailyKline`: `{date, open, high, low, close, volume, amount}` — 含成交额
  - `Fundamentals`: 参考 FinceptTerminal 的 InfoData，覆盖 PE/PB/ROE/market_cap/dividend/beta/week52 等
  - 降级标识（data_quality）与数据源绑定，不通过 API 透传
  - 涨跌幅等衍生值由前端实时计算，后端不返回

### Q7：实时行情字段的进一步精简
- **问题**：CurrentPrice 是否需要包含涨跌幅等衍生字段？
- **决策**：前端实时计算。接口仅返回：`symbol, exchange, price, price_time, currency, volume, source`。

### Q8：日 K 存在哪？
- **问题**：新建表还是用现有结构？
- **决策**：新建 `kline_daily` 表，`PK(stock_id FK→stock, trade_date)`，字段 `O/H/L/C/V/amount`。外键关联 stock 表，删股票时自动级联清理。天然去重，UPSERT 友好。

### Q9：基本面数据存哪？
- **问题**：新建专用表还是用现有 JSONB？
- **决策**：沿用 `stock_analyze.fundamentals_data` JSONB 字段。后台自动拉取填充，不新增表。

### Q10：后台 Provider 架构
- **问题**：单体 tushare_client.py 如何重构支持多数据源？
- **决策**：适配器模式。`BaseProvider` 抽象类 → `TuShareProvider` / `YFinanceProvider`。`ProviderRouter` 按 exchange 路由。`MarketDataService` 高层封装（缓存 + DB + Provider 编排）。

### Q11：API 端点设计
- **问题**：后端定时任务 vs 前端请求触发？
- **决策**：日 K + 基本面：前端首次打开页面时触发批量刷新。实时行情：页面加载/手动刷新时拉取一次。不做定时轮询。支持"刷新基本面"按钮。

### Q12：前端轮询频率
- **问题**：实时行情轮询间隔？
- **决策**：不做固定轮询，仅在用户刷新页面或打开页面时拉取一次。

### Q13：第一次打开页面时如何判断是否需要刷新？
- **问题**：判定条件是什么？
- **决策**：根据昨日日 K 数据是否存在来判断。有则直接显示，无则触发批量刷新。

### Q14：工作流改进
- **问题**：grilling → 存档 → 跨会话实施的流程如何优化？
- **决策**：PLAN.md 存完整方案 + PROJECT.md 更新文档 + ctx_memory 存核心决策树（跨会话自动注入）。三个层次形成完整的需求传递链。

---

## 3. 最终决策树

```
                   原始需求
         ┌──────────┼──────────┐
         │          │          │
      实时股价     日K线      基本面
    ┌────┴────┐    │    ┌──────┴──────┐
    │         │    │    │             │
  前端驱动  纯内存  持久化  TuShare(A股)
  页面加载  不落盘  kline_   yfinance
  +手动刷新         daily表  (港股/美股)
    │              │             │
    │         ┌────┴────┐       │
    │         │         │       │
  标注      首个交易日  "刷新基本面"
  数据源     自动触发   按钮手动
  +频度     批量刷新   触发
```

## 4. 分发策略

| 渠道 | 文件 | 用途 |
|------|------|------|
| 项目仓库 | `REQUIREMENTS_MARKET_DATA.md`（本文） | 需求 + 决策全过程记录，供人阅读 |
| 项目仓库 | `backend/app/services/market_data/PLAN.md` | 实施技术方案，供开发使用 |
| 项目仓库 | `PROJECT.md` | 主架构文档，同步更新了 kline_daily 表/API/.env/约束 |
| opencode 记忆 | `ctx_memory` category=PROJECT_RULES | 跨会话自动注入核心决策树（新会话无需手动指明） |

## 5. 实施顺序

| 阶段 | 内容 | 依赖 |
|------|------|------|
| 1 | 添加 yfinance 依赖 + Alembic 迁移（kline_daily 表） | 无 |
| 2 | Provider 适配器层：base + TuShare + yfinance + router + service | 阶段 1 |
| 3 | REST API 端点：/price /kline /fundamentals /refresh /refresh-fundamentals | 阶段 1 + 2 |
| 4 | 前端：持仓页"刷新基本面"按钮 + 显示行情标签 | 阶段 3 |
| 5 | MA120 等指标计算 + K 线图 | 阶段 3 |
