# StockMemos — 项目文档

> **文档版本**: 0.5.0  
> **文档职责**: 本文件是项目唯一的架构说明书、用户手册和开发需求文档。任何功能变更必须先修改此文档，再修改代码。  
> **文档驱动开发原则**: 后续每次迭代（Milestone / 功能模块）必须遵循「先更新本文档 → 再实现代码 → 再验证文档与代码一致」的流程。

---

## 1. 项目概述

构建一个本地部署（LAN 级）的智能投研助手。用户通过可视化 Dashboard 管理自选股、维护投资备忘录、追踪世界热点事件，并触发多 Agent 协作分析，自动更新投研笔记。系统**不涉及实盘交易**，仅提供研究与决策支持。

**核心功能模块**:
- **持仓管理**: 记录用户持仓情况，通过可视化面板展示实时盈亏（TuShare 实时行情）
- **自选股与投资备忘录**: 维护自选股列表，每只股票维护独立的投资备忘录
- **世界热点事件追踪**: 记录已发生事件节点；对未发生事件做 PolyMarket 风格预测（互斥对立结果），维护每个结果的后续影响解析
- **Agent 智能分析**: 3 类 Agent 自动更新投资备忘录 — 基本面分析、网络消息分析、交易数据分析
- **多 Agent 辩论**: 网络消息分析 Agent 通过多空辩论评估事件影响

**核心用户故事**:
- US-001: 录入股票持仓并跟踪实时盈亏
- US-002: 维护自选股列表，为每只股票建立投资备忘录
- US-003: 在投资备忘录中记录估值（目标股价）、重要事件、业务分析、趋势预测
- US-004: 追踪世界热点事件，对未发生事件做结果预测（如 PolyMarket 的互斥对赌）
- US-005: 触发 Agent 分析股票基本面，自动更新投资备忘录的估值
- US-006: 触发 Agent 分析网络消息，通过多空辩论更新备忘录中的重要事件
- US-007: 触发 Agent 分析历史交易数据，更新备忘录中的趋势预测
- US-008: 分析结果以结构化报告展示，支持 RSS 订阅和邮件推送

---

## 2. 系统架构（必须严格遵循）

```
┌─────────────────────────────────────────────────────────────┐
│              Streamlit Frontend                              │  ✅ 已实现
│  持仓看板 │ 自选股+备忘录 │ 事件时间线 │ 策略与回测 │ 设置与投递 │
├─────────────────────────────────────────────────────────────┤
│              FastAPI Backend                                 │  ✅ 已实现
│  持仓API │ 自选股API │ 备忘录API │ 事件节点API │ Agent分析API │
│  策略API │ 回测API │ 输出API(RSS/JSON/邮件)                    │
├─────────────────────────────────────────────────────────────┤
│              Agent Orchestrator                              │  ✅ 已实现
│  调度器 + 3 类核心 Agent（Fundamental/News/Technical）        │
├─────────────────────────────────────────────────────────────┤
│              LLM Provider Router                             │  ✅ 已实现
│  DeepSeek(默认) / OpenAI / Claude                            │
├─────────────────────────────────────────────────────────────┤
│              Data & Persistence                              │  ✅ 已实现
│  TuShare │ PostgreSQL │ SMTP(邮件)                            │
├─────────────────────────────────────────────────────────────┤
│              Output & Delivery                               │  ✅ 已实现
│  RSS生成 │ Markdown报告 │ JSON API │ SMTP邮件发送               │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 技术栈约束

| 层级 | 技术 | 版本 | 状态 |
|------|------|------|------|
| 后端 | Python | 3.11+ | ✅ |
| 后端 | FastAPI | 0.111.0 | ✅ |
| 后端 | Uvicorn | 0.30.0 | ✅ |
| 后端 | SQLAlchemy | 2.0.31 | ✅ |
| 后端 | Alembic | 1.13.2 | ✅ |
| 数据库 | PostgreSQL | 15 | ✅ (Docker) |
| 前端 | Streamlit | 1.37.0 | ✅ (MVP) |
| 数据 | TuShare Pro | 1.4.29 | ✅ |
| 数据 | AKShare | ⏳ | 待接入 (fallback) |
| 数据 | Web Search (Kimi Search) | ⏳ | 待接入 (Milestone 5+) |
| 任务调度 | APScheduler | ⏳ | 待配置 (Milestone 6) |
| LLM | DeepSeek | ✅ | 已接入 |
| LLM | OpenAI / Claude | ✅ | 备选（自动降级）|

**严禁更换的技术栈**:
- 不使用 LangChain / CrewAI 等重型框架（自研轻量调度器）
- 不在生产环境使用 SQLite
- 不做过度抽象（如过早引入微服务、消息队列）

---

## 4. 项目目录结构

```
StockAnalyzer/
├── docker-compose.yml          # 编排 db + backend + frontend
├── .env                        # 环境变量（不提交 Git）
├── .env.example                # 环境变量模板
├── PROJECT.md                  # 本文档（项目级唯一文档）
├── requirements.md             # 原始需求文档（只读参考）
├── system_prompt.md            # 系统提示文档（只读参考）
│
├── backend/
│   ├── Dockerfile              # Python 3.11 Slim
│   ├── requirements.txt        # 后端依赖
│   ├── alembic.ini             # Alembic 配置
│   ├── alembic/
│   │   ├── env.py              # 迁移环境（从 .env 读取 DB URL）
│   │   ├── script.py.mako      # 迁移模板
│   │   └── versions/
│   │       ├── 001_create_portfolio.py      # 创建 portfolio 表
│   │       ├── 002_add_remaining_tables.py  # 创建基础 7 张表
│   │       └── 003_add_watchlist_memo_event.py # 新增自选股/备忘录/事件节点
│   └── app/
│       ├── __init__.py
│       ├── main.py             # FastAPI 入口 + 路由注册
│       ├── config.py           # pydantic-settings 读取 .env
│       ├── database.py         # SQLAlchemy Engine + Session + Base
│       ├── models/             # ORM 模型（SQLAlchemy 2.0 Mapped）
│       │   ├── __init__.py
│       │   ├── portfolio.py    # ✅ 持仓
│       │   ├── trade_point.py  # ✅ 买卖点
│       │   ├── watchlist.py    # 🔵 自选股（新增）
│       │   ├── investment_memo.py # 🔵 投资备忘录（核心新增）
│       │   ├── memo_event.py   # 🔵 备忘录关联事件（新增）
│       │   ├── event_node.py   # 🔵 世界热点事件节点（新增）
│       │   ├── event_prediction.py # 🔵 事件预测结果（新增）
│       │   ├── analysis_report.py
│       │   ├── agent_log.py
│       │   ├── strategy.py
│       │   └── strategy_signal.py
│       ├── schemas/            # Pydantic 请求/响应模型
│       │   ├── __init__.py
│       │   ├── portfolio.py
│       │   ├── trade_point.py
│       │   ├── watchlist.py    # 🔵
│       │   ├── investment_memo.py # 🔵
│       │   ├── memo_event.py   # 🔵
│       │   ├── event_node.py   # 🔵
│       │   ├── event_prediction.py # 🔵
│       │   ├── analysis_report.py
│       │   ├── agent_log.py
│       │   ├── strategy.py
│       │   └── strategy_signal.py
│       ├── routers/            # FastAPI API 路由
│       │   ├── __init__.py
│       │   ├── health.py       # 健康检查
│       │   ├── portfolio.py    # 持仓 CRUD + Dashboard
│       │   ├── watchlist.py    # ✅ 自选股 + 备忘录
│       │   ├── event_node.py   # ✅ 事件节点 + 预测
│       │   ├── analyze.py      # ✅ Agent 分析触发
│       │   ├── strategy.py   # ✅ 策略 CRUD + 回测
│       │   └── output.py     # ✅ 输出与投递
│       ├── services/           # 业务服务层
│       │   ├── __init__.py
│       │   ├── tushare_client.py # ✅ TuShare 客户端
│       │   ├── web_search.py   # ⏳ 网络搜索封装
│       │   ├── llm_router.py   # ✅ LLM 路由
│       │   ├── strategy_engine.py # ✅ 策略规则引擎
│       │   ├── report_generator.py # ✅ 报告生成器
│       │   └── email_service.py  # ✅ 邮件发送服务
│       └── agents/             # AI Agent 实现
│           ├── __init__.py
│           ├── fundamental_agent.py   # ✅ 基本面分析
│           ├── news_agent.py        # ✅ 网络消息分析（多空辩论）
│           ├── technical_agent.py   # ✅ 交易数据分析
│           └── orchestrator.py    # ✅ Agent 结果写入备忘录
│
└── frontend/
    ├── Dockerfile              # Python 3.11 Slim + Streamlit
    ├── requirements.txt
    ├── streamlit_app.py        # 主入口 + 侧边栏导航
    └── pages/
        ├── 1_持仓总览.py        # ✅ 首页 Dashboard
        ├── 2_自选股与备忘录.py   # ✅ 核心页面：自选股列表 + 备忘录编辑
        ├── 3_事件时间线.py       # ✅ 世界热点事件追踪 + 预测
        ├── 4_策略与回测.py       # ✅ 策略与回测页
        └── 5_设置与投递.py       # ✅ RSS/邮件/报告导出
```

---

## 5. 数据库 Schema

所有表通过 Alembic 迁移管理，严禁手动改表。

### 5.1 portfolio（持仓）✅
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| stock_code | VARCHAR(20) | NOT NULL | 如 000001.SZ |
| stock_name | VARCHAR(100) | | 股票名称 |
| quantity | INT | NOT NULL | 持股数量 |
| cost_price | NUMERIC(10,4) | NOT NULL | 成本价 |
| build_date | DATE | NOT NULL | 建仓日期 |
| status | VARCHAR(20) | DEFAULT 'holding' | holding / closed |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间（自动） |

### 5.2 trade_point（买卖点）✅
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| portfolio_id | UUID | FK → portfolio.id | 关联持仓 |
| type | VARCHAR(20) | NOT NULL | add_position / reduce_position / stop_loss / take_profit |
| price | NUMERIC(10,4) | | 交易价格 |
| reason | TEXT | | 交易理由 |
| report_id | UUID | FK → analysis_report.id | 关联分析报告 |
| trade_date | DATE | | 交易日期 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

### 5.3 watchlist（自选股）🔵
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| stock_code | VARCHAR(20) | NOT NULL, UNIQUE | 如 000001.SZ |
| stock_name | VARCHAR(100) | | 股票名称 |
| sector | VARCHAR(50) | | 所属板块/行业 |
| market | VARCHAR(20) | | 交易所：SH / SZ / HK / US |
| is_watched | BOOLEAN | DEFAULT TRUE | 是否在关注 |
| memo_id | UUID | FK → investment_memo.id | 关联投资备忘录 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

### 5.4 investment_memo（投资备忘录）🔵【核心表】
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| stock_code | VARCHAR(20) | NOT NULL | 股票代码 |
| target_price | NUMERIC(10,4) | | 目标股价（估值） |
| valuation_method | VARCHAR(50) | | 估值方法：PE / DCF / 可比公司 |
| business_scope | TEXT | | 业务范围/供需关系/产业链生态位 |
| short_trend | VARCHAR(20) | | 短线趋势：up / down / sideways |
| mid_trend | VARCHAR(20) | | 中线趋势：up / down / sideways |
| long_trend | VARCHAR(20) | | 长期趋势：up / down / sideways |
| trend_logic | TEXT | | 趋势预测核心逻辑（Agent 生成，可编辑） |
| notes | TEXT | | 用户自定义备注 |
| last_updated_by | VARCHAR(50) | | 最后更新来源：user / fundamental_agent / news_agent / technical_agent |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

### 5.5 memo_event（备忘录关联事件）🔵
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| memo_id | UUID | FK → investment_memo.id | 关联备忘录 |
| event_name | VARCHAR(200) | NOT NULL | 事件名称，如"Q3 财报发布" |
| event_type | VARCHAR(20) | | 类型：earnings / order / geopolitical / policy / other |
| impact_tag | VARCHAR(20) | | 影响标签：bullish / bearish / neutral |
| expected_date | DATE | | 预期发生日期 |
| actual_date | DATE | | 实际发生日期 |
| result_status | VARCHAR(20) | DEFAULT 'pending' | 结果状态：pending / occurred / expired / cancelled |
| result_summary | TEXT | | 事件结果摘要（发生后填写） |
| source_url | TEXT | | 信息来源 |
| agent_analysis | TEXT | | Agent 分析摘要 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

### 5.6 event_node（世界热点事件节点）🔵
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| title | VARCHAR(300) | NOT NULL | 事件标题，如"美联储 2024 年 12 月利率决议" |
| category | VARCHAR(50) | | 分类：monetary_policy / geopolitical / macro_data / trade_policy / energy / tech |
| occurred_at | DATE | | 已发生节点日期（空表示尚未发生） |
| description | TEXT | | 事件描述 |
| source_url | TEXT | | 信息来源 |
| status | VARCHAR(20) | DEFAULT 'pending' | 状态：pending / occurred / materialized |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

### 5.7 event_prediction（事件预测结果）🔵
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| event_node_id | UUID | FK → event_node.id | 关联事件节点 |
| outcome_label | VARCHAR(200) | NOT NULL | 结果标签，如"加息 25bp" |
| outcome_description | TEXT | | 结果描述 |
| probability_estimate | NUMERIC(3,2) | | Agent 评估概率（0.00-1.00） |
| impact_brief | TEXT | | 若此结果发生，后续影响简要解析 |
| is_actual_result | BOOLEAN | DEFAULT FALSE | 是否为实际发生结果（事件发生后标记） |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间 |

### 5.8 analysis_report（分析报告）✅
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| stock_code | VARCHAR(20) | NOT NULL | 股票代码 |
| trigger_type | VARCHAR(20) | | manual / scheduled |
| final_rating | VARCHAR(20) | | strong_buy / buy / accumulate / neutral / reduce / sell |
| summary | TEXT | | 报告摘要 |
| valuation_status | VARCHAR(20) | | overvalued / fair / undervalued |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

### 5.9 agent_log（Agent 思考过程）✅
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| report_id | UUID | FK → analysis_report.id | 关联报告 |
| agent_name | VARCHAR(50) | NOT NULL | 如 fundamental_agent |
| agent_role | VARCHAR(50) | | fundamental / news_bull / news_bear / technical |
| reasoning | TEXT | | 完整思考文本 |
| conclusion | TEXT | | 结论摘要 |
| meta_data | JSONB | | 结构化输出 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

### 5.10 strategy（策略定义）✅
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| name | VARCHAR(100) | NOT NULL | 策略名称 |
| description | TEXT | | 策略描述 |
| rules | JSONB | NOT NULL | 指标组合规则 |
| is_active | BOOLEAN | DEFAULT TRUE | 是否启用 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

### 5.11 strategy_signal（策略信号记录）✅
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| strategy_id | UUID | FK → strategy.id | 关联策略 |
| stock_code | VARCHAR(20) | NOT NULL | 股票代码 |
| signal_date | DATE | NOT NULL | 信号日期 |
| signal_type | VARCHAR(20) | | buy / sell / hold / overvalued / undervalued |
| raw_data | JSONB | | 当日指标原始值 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

---

## 6. API 接口规范

### 6.1 健康检查 ✅
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 服务健康检查 |

### 6.2 持仓管理 ✅
| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| POST | `/api/portfolio` | 创建持仓 | ✅ |
| GET | `/api/portfolio` | 获取持仓列表 | ✅ |
| GET | `/api/portfolio/dashboard` | 仓位管理 Dashboard | ✅ |
| GET | `/api/portfolio/{id}` | 获取单条持仓 | ✅ |
| PUT | `/api/portfolio/{id}` | 更新持仓 | ✅ |
| DELETE | `/api/portfolio/{id}` | 删除持仓 | ✅ |
| POST | `/api/portfolio/{id}/trade` | 记录买卖点 | ✅ |
| GET | `/api/portfolio/{id}/trades` | 获取交易点列表 | ✅ |

### 6.3 自选股与投资备忘录 🔵
| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| POST | `/api/watchlist` | 添加自选股 | 🔵 |
| GET | `/api/watchlist` | 获取自选股列表 | 🔵 |
| DELETE | `/api/watchlist/{id}` | 移除自选股 | 🔵 |
| GET | `/api/watchlist/{code}/memo` | 获取某股票的备忘录 | 🔵 |
| PUT | `/api/watchlist/{code}/memo` | 更新备忘录（用户手动编辑） | 🔵 |
| POST | `/api/watchlist/{code}/memo/events` | 为备忘录添加事件 | 🔵 |
| GET | `/api/watchlist/{code}/memo/events` | 获取备忘录事件列表 | 🔵 |
| PUT | `/api/watchlist/{code}/memo/events/{id}` | 更新事件（标记结果） | 🔵 |
| DELETE | `/api/watchlist/{code}/memo/events/{id}` | 删除事件 | 🔵 |

### 6.4 世界热点事件 🔵
| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| POST | `/api/event-nodes` | 创建事件节点 | 🔵 |
| GET | `/api/event-nodes` | 获取事件节点列表（时间线） | 🔵 |
| GET | `/api/event-nodes/{id}` | 获取事件节点详情 | 🔵 |
| PUT | `/api/event-nodes/{id}` | 更新事件节点 | 🔵 |
| DELETE | `/api/event-nodes/{id}` | 删除事件节点 | 🔵 |
| POST | `/api/event-nodes/{id}/predictions` | 添加预测结果 | 🔵 |
| GET | `/api/event-nodes/{id}/predictions` | 获取预测结果列表 | 🔵 |
| PUT | `/api/event-nodes/{id}/predictions/{pid}` | 更新预测（标记实际结果） | 🔵 |
| POST | `/api/event-nodes/{id}/impact` | 分析事件对某股票的影响 | 🔵 |

### 6.5 Agent 分析触发 ✅
| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| POST | `/api/analyze/{code}/fundamental` | 触发基本面分析，更新备忘录估值 | ✅ |
| POST | `/api/analyze/{code}/news` | 触发网络消息分析，更新备忘录事件 | ✅ |
| POST | `/api/analyze/{code}/technical` | 触发交易数据分析，更新备忘录趋势 | ✅ |
| GET | `/api/analyze/{code}/reports` | 获取历史分析报告 | ⏳ |
| GET | `/api/reports/{report_id}` | 获取报告详情（含 Agent 日志） | ⏳ |

### 6.6 策略与回测 ✅
| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| POST | `/api/strategies` | 创建策略 | ✅ |
| GET | `/api/strategies` | 获取策略列表 | ✅ |
| PUT | `/api/strategies/{id}` | 更新策略 | ✅ |
| DELETE | `/api/strategies/{id}` | 删除策略 | ✅ |
| POST | `/api/strategies/{id}/run` | 对个股运行策略 | ✅ |
| POST | `/api/strategies/backtest` | 执行回测 | ✅ |

### 6.7 输出与投递 ✅
| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | `/api/output/memos?format=markdown` | 备忘录报告（Markdown） | ✅ |
| GET | `/api/output/memos?format=json` | 备忘录报告（JSON） | ✅ |
| GET | `/api/output/memos?format=rss` | 备忘录 RSS 订阅 | ✅ |
| GET | `/api/output/strategy-signals?format=markdown` | 策略信号报告（Markdown） | ✅ |
| GET | `/api/output/strategy-signals?format=json` | 策略信号报告（JSON） | ✅ |
| GET | `/api/output/strategy-signals?format=rss` | 策略信号 RSS 订阅 | ✅ |
| POST | `/api/output/email/memos` | 发送备忘录日报邮件 | ✅ |

---

## 7. 前端页面（Streamlit MVP）

### 7.1 持仓总览页（首页） ✅
- 顶部卡片：总市值 · 总成本 · 浮动盈亏 · 收益率 · 持仓数量
- 持仓明细表格：代码、名称、数量、成本、最新价、市值、盈亏、盈亏率
- 操作按钮：分析 / 加仓 / 减仓 / 删除
- 新增持仓表单（折叠面板）
- 板块概览饼图（Plotly）
- 对接后端：`GET /api/portfolio/dashboard` + `POST /api/portfolio` + `DELETE /api/portfolio/{id}`

### 7.2 自选股与投资备忘录页 🔵【核心页面】
- **自选股列表**：股票代码、名称、板块、最新价、备忘录最后更新时间
- **投资备忘录编辑器**：
  - 估值区域：目标股价、估值方法（可编辑）
  - 重要事件列表：事件名称、预期日期、影响标签（利好/利空）、结果状态（待发生/已发生/已过期）
  - 业务分析：业务范围、供需关系、产业链生态位（文本编辑区）
  - 趋势预测：短线/中线/长期 的 上涨/下降/震荡，附核心逻辑（可编辑）
  - 用户备注：自由文本编辑区
- **Agent 触发按钮**：
  - 「🔍 基本面分析」→ 更新估值
  - 「📰 消息分析」→ 多空辩论，更新事件列表
  - 「📈 技术分析」→ 更新趋势预测
- 对接后端：`GET/PUT /api/watchlist/{code}/memo` + `POST /api/analyze/{code}/...`

### 7.3 世界热点事件时间线页 🔵
- **事件时间线**：按时间倒序展示事件节点（已发生 + 待发生）
- **事件卡片**：
  - 已发生事件：标题、日期、描述、结果摘要
  - 未发生事件：标题、预测结果列表（PolyMarket 风格互斥选项）、每个结果的简要影响解析、Agent 评估概率
- **新增事件表单**：标题、分类、预期日期、描述
- **添加预测**：为未发生事件添加互斥对立的预测结果
- 对接后端：`GET/POST /api/event-nodes` + `POST /api/event-nodes/{id}/predictions`

### 7.4 策略与回测页 ✅
- 策略列表（启用/停用）
- 新建策略表单（预设模板：MA金叉、RSI超卖/超买、组合策略）
- 回测入口：选择股票 + 策略 + 时间区间 + 初始资金
- 回测结果：收益曲线、交易记录、胜率、最大回撤
- 最新信号：实时运行策略获取当前买卖信号
- 对接后端：`POST /api/strategies` + `POST /api/strategies/backtest` + `POST /api/strategies/{id}/run`

### 7.5 设置与投递页 ✅
- RSS 订阅链接展示（备忘录、策略信号）
- 邮件测试发送（检查 SMTP 配置）
- 报告导出入口（Markdown / JSON / RSS XML）
- 对接后端：`GET /api/output/memos` + `GET /api/output/strategy-signals` + `POST /api/output/email/memos`

---

## 8. Agent 角色定义（重新定位）

系统精简为 **3 类核心 Agent**，直接对应投资备忘录的 3 大更新维度：

| Agent | 职责 | 输入 | 输出 | 更新目标 |
|-------|------|------|------|----------|
| **FundamentalAgent** 🔵 | 分析股票公司基本面（财务数据、行业地位、估值模型） | stock_code, 财务数据 | JSON: {target_price, valuation_method, business_analysis, confidence} | 投资备忘录：估值、业务分析 |
| **NewsAgent** 🔵 | 搜集并分析网络消息（新闻、公告、社交媒体），通过**多空辩论**评估事件影响 | stock_code, 关键词, 时间窗口 | JSON: {events: [{name, impact_tag, expected_date, reasoning}], bull_case, bear_case, consensus} | 投资备忘录：重要事件列表 |
| **TechnicalAgent** 🔵 | 分析历史交易数据（价格走势、成交量、技术指标） | stock_code, K线数据, 指标规则 | JSON: {short_trend, mid_trend, long_trend, logic, key_levels} | 投资备忘录：趋势预测 + 核心逻辑 |

### 8.1 多 Agent 辩论机制（NewsAgent 内部）

NewsAgent 不是单一 Agent，而是内部包含 **3 个子 Agent** 的辩论流程：

1. **NewsBullAgent** — 从利好角度分析消息，输出 `bull_case`（看多理由）
2. **NewsBearAgent** — 从利空角度分析消息，输出 `bear_case`（看空理由）
3. **NewsRefereeAgent** — 综合多空观点，输出 `consensus`（共识判断）和事件影响评估

所有 3 个子 Agent 的推理过程完整存入 `agent_log`。

### 8.2 世界热点事件的 Agent 辅助

- 对 **未发生事件**，Agent 可根据历史数据和当前形势，为每个预测结果生成 `probability_estimate` 和 `impact_brief`
- 对 **已发生事件**，Agent 自动生成 `result_summary` 和后续影响分析

---

## 9. 环境变量（.env）

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

---

## 10. 开发里程碑（重新规划）

### Milestone 1: 骨架与数据 ✅（已完成）
- [x] Docker Compose 环境跑通（backend + db + frontend）
- [x] Alembic 配置完成，能执行 upgrade/downgrade
- [x] 基础数据库模型创建完成（portfolio, trade_point, analysis_report, agent_log, strategy, strategy_signal）
- [x] TuShare 客户端封装完成（含错误重试、缓存）
- [x] 持仓 CRUD API 完成（含 Dashboard 聚合接口）
- [x] Streamlit 首页展示持仓列表和实时盈亏
- [x] 项目级文档 `PROJECT.md` 建立

### Milestone 2: 自选股与投资备忘录 ✅（已完成）
- [x] 新增数据库模型：watchlist, investment_memo, memo_event
- [x] 自选股 CRUD API
- [x] 投资备忘录 API（读写 + 事件管理）
- [x] Streamlit 自选股与备忘录页面
- [x] 新增数据库迁移 `003_add_watchlist_memo_event.py` + `004_add_event_node_prediction.py`

### Milestone 3: 世界热点事件 ✅（已完成）
- [x] 新增数据库模型：event_node, event_prediction
- [x] 事件节点 CRUD API
- [x] 预测结果管理 API
- [x] Streamlit 事件时间线页面
- [x] 新增数据库迁移

### Milestone 4: LLM 与 Agent 分析 ✅（已完成）
- [x] LLM Router 封装（DeepSeek + 备选）
- [x] FundamentalAgent 实现（基本面分析）
- [x] NewsAgent 实现（网络消息 + 多空辩论）
- [x] TechnicalAgent 实现（交易数据分析）
- [x] Agent 分析触发 API（/api/analyze/{code}/...）
- [x] 备忘录自动更新机制（Orchestrator）
- [x] Streamlit 备忘录页 Agent 触发按钮

### Milestone 5: 策略与回测 ✅（已完成）
- [x] 策略规则引擎（JSON 解析 + 技术指标计算：SMA/EMA/RSI）
- [x] 策略 CRUD API（POST/GET/PUT/DELETE `/api/strategies`）
- [x] 策略运行 API（POST `/api/strategies/{id}/run`）
- [x] BacktestAgent 回测引擎（收益曲线、交易记录、胜率、最大回撤）
- [x] Streamlit 策略页（策略列表 + 预设模板 + 回测配置 + 结果展示）

### Milestone 6: 输出与部署 ✅（已完成）
- [x] RSS 结构化输出接口（Markdown / JSON / RSS XML）
- [x] 邮件发送接口（SMTP 封装 + 测试发送）
- [x] .env 模板和配置说明（`.env.example` 完善）
- [x] 局域网部署文档（`DEPLOYMENT.md`）

---

## 11. 快速启动

### 11.1 首次启动
```bash
# 1. 准备环境变量
cp .env.example .env
# 编辑 .env，填入 TUSHARE_TOKEN 和 DEEPSEEK_API_KEY

# 2. 构建并启动所有服务
docker compose up --build -d

# 3. 验证服务
# 后端:  http://localhost:8080/health
# 前端:  http://localhost:8501
# API文档: http://localhost:8080/docs
```

### 11.2 日常操作
```bash
docker compose up -d          # 启动
docker compose down -v        # 停止并删除数据卷（重置）
docker compose logs -f backend # 查看后端日志
docker compose build backend  # 重新构建后端
```

### 11.3 数据库迁移
```bash
# 进入后端容器执行
 docker exec -it trading-backend bash
 alembic upgrade head        # 升级
 alembic downgrade -1        # 回退一级
 alembic revision --autogenerate -m "新增 xxx 表"  # 生成新迁移（需模型已注册）
```

---

## 12. 关键约束（开发红线）

1. **用户不直接输入 Prompt**：所有 Agent 输入由 Dashboard 操作转化为结构化 JSON
2. **思考过程必须保留**：每个 Agent 的完整推理存入 `agent_log` 表
3. **TuShare 限流处理**：所有 TuShare 请求必须加缓存（1 小时 TTL）和重试（3 次 + 指数退避）
4. **LLM 输出校验**：强制 JSON 模式，失败重试 3 次
5. **数据安全**：API Key 不提交 Git，使用 `.env`
6. **文档同步**：任何功能变更必须先修改 `PROJECT.md`，再修改代码
7. **投资备忘录是核心数据枢纽**：所有 Agent 分析结果最终落地到 `investment_memo` 或其关联表
8. **PolyMarket 预测原则**：每个未发生事件的预测结果必须是**互斥对立**的；若事件复杂，拆分为多个事件节点

---

## 13. 文档版本变更日志

| 版本 | 日期 | 变更内容 | 变更人 |
|------|------|----------|--------|
| 0.1.0 | 2024-06-13 | 项目骨架 + 数据库模型 + TuShare + 持仓 API + Streamlit 前端 | Agent |
| 0.2.0 | 2024-06-13 | 重大重构：新增自选股/投资备忘录/世界热点事件模型；重新定位 3 类 Agent | Agent |
| 0.3.0 | 2024-06-19 | Milestone 2-4 完成：自选股/备忘录/事件追踪/LLM Router/3 Agent 分析/Orchestrator 自动写入/前端联动 | Agent |
| 0.4.0 | 2024-06-19 | Milestone 5 完成：策略规则引擎（SMA/EMA/RSI）/ 策略 CRUD / BacktestAgent / 回测 API / Streamlit 策略页 | Agent |
| 0.5.0 | 2024-06-19 | Milestone 6 完成：RSS 结构化输出 / SMTP 邮件发送 / .env 模板 / 局域网部署文档 / Streamlit 设置与投递页 | Agent |

