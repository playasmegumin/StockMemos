# Agent股票交易决策系统 — 开发需求文档（Kimi Work版）

## 1. 项目概述
构建一个本地部署（LAN级）的智能投研助手。用户通过可视化Dashboard操作触发多Agent协作分析，输出结构化投资建议。不涉及实盘交易。

## 2. 目标用户
个人投资者，具备基础金融知识，需要系统性跟踪持仓和事件影响。

## 3. 核心用户故事

### US-001 持仓管理
作为用户，我希望录入我的股票持仓（代码、数量、成本价），以便系统跟踪我的盈亏情况。

### US-002 盈亏分析
作为用户，我希望每天收盘后自动看到持仓的浮动盈亏和收益率。

### US-003 个股深度分析
作为用户，我希望选中一只股票后点击"分析"，系统自动拉取数据、搜集新闻，并由AI给出买入/卖出评级。

### US-004 事件追踪
作为用户，我希望预设跟踪重大事件（如美联储利率决议），系统能跟踪事件进度并分析对个股的影响。

### US-005 多Agent辩论
作为用户，我希望看到看多和看空AI的辩论过程，以及裁判AI的最终评级。

### US-006 策略估值
作为用户，我希望自定义技术指标组合（如PE<<20且MA120上方），系统自动判定个股估值位置。

### US-007 回测验证
作为用户，我希望对某只股票应用策略进行历史回测，验证策略有效性。

### US-008 报告输出
作为用户，我希望分析结果以结构化报告展示，支持RSS订阅和邮件推送。

## 4. 系统架构（必须严格遵循）

```
┌─────────────────────────────────────┐
│         Streamlit Frontend          │
│  持仓看板 │ 分析页 │ 事件页 │ 策略页  │
├─────────────────────────────────────┤
│         FastAPI Backend             │
│  持仓API │ 分析API │ 事件API │ 策略API │
├─────────────────────────────────────┤
│         Agent Orchestrator          │
│  调度器 + 各Agent（见第6节）         │
├─────────────────────────────────────┤
│         LLM Provider Router         │
│  DeepSeek(默认) / OpenAI / Claude   │
├─────────────────────────────────────┤
│         Data & Persistence          │
│  TuShare │ AKShare │ PostgreSQL     │
└─────────────────────────────────────┘
```

## 5. 技术栈约束
- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy 2.0 + Alembic
- PostgreSQL 15 (Docker)
- Streamlit (MVP前端)
- TuShare Pro (主数据源)
- APScheduler (定时任务)

## 6. Agent角色定义（必须实现）

| Agent | 职责 | 输入 | 输出格式 |
|-------|------|------|----------|
| **DataAgent** | 从TuShare拉取行情/财务/成交量 | stock_code, data_types | JSON: {kline: [], finance: {}, volume: {}} |
| **NewsAgent** | 搜集个股相关新闻和事件 | stock_code, keywords | JSON: {articles: [{title, source, date, summary}]} |
| **EventAgent** | 分析重大事件对个股的影响 | event_info, stock_sector, history | JSON: {direction, magnitude, confidence, time_window, reasoning} |
| **BullAgent** | 看多分析 | all_data, event_impacts | JSON: {rating, target_price, reasoning, risks} |
| **BearAgent** | 看空分析 | all_data, event_impacts | JSON: {rating, downside, reasoning, supports} |
| **RefereeAgent** | 综合多空观点给出最终评级 | bull_output, bear_output, valuation | JSON: {final_rating, confidence, key_assumptions, risks} |
| **ValuationAgent** | 运行技术指标策略 | stock_code, strategy_rules | JSON: {status: overvalued/fair/undervalued, triggered_indicators} |
| **BacktestAgent** | 历史回测 | stock_code, strategy, date_range | JSON: {total_return, max_drawdown, sharpe, trades: []} |
| **ReportAgent** | 整合所有输出为可读报告 | all_agent_outputs | Markdown/JSON混合报告 |

## 7. 数据库Schema（必须严格实现）

### 7.1 portfolio（持仓）
```sql
id: UUID PRIMARY KEY
stock_code: VARCHAR(20) NOT NULL  -- 如 "000001.SZ"
stock_name: VARCHAR(100)
quantity: INT NOT NULL
cost_price: DECIMAL(10,4) NOT NULL
build_date: DATE NOT NULL
status: VARCHAR(20) DEFAULT 'holding'  -- holding/closed
created_at: TIMESTAMP DEFAULT NOW()
updated_at: TIMESTAMP DEFAULT NOW()
```

### 7.2 trade_point（买卖点）
```sql
id: UUID PRIMARY KEY
portfolio_id: UUID FOREIGN KEY
type: VARCHAR(20)  -- add_position/reduce_position/stop_loss/take_profit
price: DECIMAL(10,4)
reason: TEXT
report_id: UUID  -- 关联分析报告
trade_date: DATE
created_at: TIMESTAMP DEFAULT NOW()
```

### 7.3 event（全局事件库）
```sql
id: UUID PRIMARY KEY
name: VARCHAR(200) NOT NULL
category: VARCHAR(50)  -- monetary_policy/geopolitical/macro_data/company_event
expected_date: DATE
status: VARCHAR(20) DEFAULT 'pending'  -- pending/occurred/materialized
source_url: TEXT
description: TEXT
created_at: TIMESTAMP DEFAULT NOW()
```

### 7.4 event_impact（事件-个股影响）
```sql
id: UUID PRIMARY KEY
event_id: UUID FOREIGN KEY
stock_code: VARCHAR(20) NOT NULL
direction: VARCHAR(20)  -- bullish/bearish/neutral
magnitude: INT  -- 1-5
confidence: DECIMAL(3,2)  -- 0.00-1.00
time_window: VARCHAR(50)  -- 如 "1-3个月"
agent_reasoning: TEXT
created_at: TIMESTAMP DEFAULT NOW()
```

### 7.5 analysis_report（分析报告）
```sql
id: UUID PRIMARY KEY
stock_code: VARCHAR(20) NOT NULL
trigger_type: VARCHAR(20)  -- manual/scheduled
final_rating: VARCHAR(20)  -- strong_buy/buy/accumulate/neutral/reduce/sell
summary: TEXT
valuation_status: VARCHAR(20)  -- overvalued/fair/undervalued
created_at: TIMESTAMP DEFAULT NOW()
```

### 7.6 agent_log（Agent思考过程）
```sql
id: UUID PRIMARY KEY
report_id: UUID FOREIGN KEY
agent_name: VARCHAR(50) NOT NULL  -- 如 "bull_agent"
agent_role: VARCHAR(50)  -- intelligence/event_analysis/bull/bear/referee/valuation/reporter
reasoning: TEXT  -- 完整思考文本
conclusion: TEXT
metadata: JSONB  -- 结构化输出
created_at: TIMESTAMP DEFAULT NOW()
```

### 7.7 strategy（策略定义）
```sql
id: UUID PRIMARY KEY
name: VARCHAR(100) NOT NULL
description: TEXT
rules: JSONB NOT NULL  -- 指标组合规则
is_active: BOOLEAN DEFAULT TRUE
created_at: TIMESTAMP DEFAULT NOW()
```

### 7.8 strategy_signal（策略信号记录）
```sql
id: UUID PRIMARY KEY
strategy_id: UUID FOREIGN KEY
stock_code: VARCHAR(20) NOT NULL
signal_date: DATE NOT NULL
signal_type: VARCHAR(20)  -- buy/sell/hold/overvalued/undervalued
raw_data: JSONB  -- 当日指标原始值
created_at: TIMESTAMP DEFAULT NOW()
```

## 8. API接口规范（必须实现）

### 8.1 持仓管理
- `POST /api/portfolio` — 录入持仓
- `GET /api/portfolio` — 获取持仓列表（含最新盈亏）
- `PUT /api/portfolio/{id}` — 更新持仓
- `DELETE /api/portfolio/{id}` — 删除持仓
- `POST /api/portfolio/{id}/trade` — 记录买卖点

### 8.2 数据分析
- `GET /api/stock/{code}/data?types=kline,finance,volume` — 拉取股票数据
- `POST /api/stock/{code}/analyze` — 触发个股分析（手动）
- `GET /api/stock/{code}/reports` — 获取历史分析报告
- `GET /api/reports/{report_id}` — 获取报告详情（含Agent日志）

### 8.3 事件管理
- `POST /api/events` — 创建跟踪事件
- `GET /api/events` — 获取事件列表
- `PUT /api/events/{id}` — 更新事件
- `POST /api/events/{id}/impact` — 评估事件对个股影响

### 8.4 策略与回测
- `POST /api/strategies` — 创建策略
- `GET /api/strategies` — 获取策略列表
- `POST /api/strategies/{id}/run` — 对个股运行策略
- `POST /api/backtest` — 执行回测（body: {stock_code, strategy_id, start_date, end_date}）

## 9. 前端页面（Streamlit MVP）

### 9.1 持仓总览页（首页）
- 表格展示所有持仓：代码、名称、数量、成本、最新价、盈亏、盈亏率
- 操作按钮：分析 / 加仓 / 减仓 / 删除
- 顶部卡片：总资产、总盈亏、今日盈亏

### 9.2 个股分析页
- 股票代码输入框 + "深度分析"按钮
- 分析进度展示（Agent执行状态）
- 结果展示：
  - 最终评级（大字体突出）
  - 多空辩论标签页（看多/看空/裁判）
  - 事件影响表格
  - 估值判定
  - 原始数据摘要

### 9.3 事件追踪页
- 事件列表（时间线视图）
- 新增事件表单
- 事件与个股关联展示

### 9.4 策略配置页
- 策略列表（启用/停用）
- 新建策略表单（指标选择器）
- 策略运行结果展示

### 9.5 回测页
- 选择股票 + 策略 + 时间区间
- 运行回测按钮
- 结果展示：收益曲线、统计指标、交易记录

## 10. 开发里程碑

### Milestone 1: 骨架与数据（第1周）
- [ ] Docker Compose环境跑通（backend + db）
- [ ] Alembic配置完成，能执行upgrade/downgrade
- [ ] 所有数据库模型创建完成
- [ ] TuShare客户端封装完成（含错误重试）
- [ ] 持仓CRUD API完成
- [ ] Streamlit首页展示持仓列表

### Milestone 2: 单Agent分析（第2周）
- [ ] LLM Router封装完成（支持DeepSeek）
- [ ] DataAgent + NewsAgent实现
- [ ] AnalystAgent（单Agent版）实现
- [ ] 报告生成与存储
- [ ] Streamlit分析页完成（可触发分析并展示报告）

### Milestone 3: 多Agent与事件（第3-4周）
- [ ] BullAgent + BearAgent + RefereeAgent实现
- [ ] 辩论过程存储与展示（多标签页）
- [ ] 事件库CRUD
- [ ] EventAgent实现
- [ ] 定时任务框架（APScheduler）配置

### Milestone 4: 策略与回测（第5周）
- [ ] ValuationAgent实现
- [ ] 策略规则引擎（JSON解析执行）
- [ ] BacktestAgent实现
- [ ] Streamlit策略页和回测页

### Milestone 5: 输出与部署（第6周）
- [ ] RSS结构化输出接口
- [ ] 邮件发送接口（SMTP配置）
- [ ] 数据库迁移兼容性测试
- [ ] 局域网部署文档
- [ ] .env模板和配置说明

## 11. 环境变量模板（.env）

```bash
# 数据库
DATABASE_URL=postgresql+psycopg2://trading:changeme@db:5432/agent_trading
DB_PASSWORD=changeme

# TuShare
TUSHARE_TOKEN=your_tushare_pro_token_here

# LLM（至少填一个）
DEEPSEEK_API_KEY=your_deepseek_key_here
DEEPSEEK_MODEL=deepseek-chat
OPENAI_API_KEY=optional
ANTHROPIC_API_KEY=optional

# 邮件（可选）
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# 应用
APP_ENV=development
APP_PORT=8080
LOG_LEVEL=INFO
```

## 12. 验收标准

### 功能验收
- [ ] 用户能录入持仓并看到实时盈亏
- [ ] 用户能点击"分析"按钮，60秒内得到一份带评级的报告
- [ ] 报告包含：评级、理由、关键指标、风险提示
- [ ] 用户能查看历史报告和Agent思考过程
- [ ] 用户能添加跟踪事件并查看对个股的影响评估
- [ ] 用户能配置策略并看到估值判定
- [ ] 用户能手动触发回测并看到结果

### 技术验收
- [ ] `docker-compose up`一键启动所有服务
- [ ] 数据库迁移能正常升级和回滚
- [ ] 所有API在`/docs`页面可测试
- [ ] 所有Agent调用有日志记录
- [ ] 代码通过`mypy`类型检查（无严重错误）
- [ ] 局域网内其他设备可通过IP访问

## 13. 关键约束提醒
1. **用户不直接输入Prompt**：所有Agent输入由Dashboard操作转化为结构化JSON
2. **思考过程必须保留**：每个Agent的完整推理存入agent_log
3. **TuShare限流处理**：所有TuShare请求必须加缓存和重试
4. **LLM输出校验**：强制JSON模式，失败重试3次
5. **数据安全**：API Key不提交Git，使用.env
