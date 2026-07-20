# StockMemos — 项目文档

> **文档版本**: 0.16.0
> **文档职责**: 本文件是项目唯一的架构说明书、用户手册和开发需求文档。任何功能变更必须先修改此文档，再修改代码。
> **文档驱动开发原则**: 后续每次迭代（Milestone / 功能模块）必须遵循「先更新本文档 → 再实现代码 → 再验证文档与代码一致」的流程。

---

## 1. 项目概述

构建一个本地部署（LAN 级）的智能投研助手。用户通过可视化 Dashboard 管理自选股、追踪交易记录与分析报告，并触发多 Agent 协作分析。系统**不涉及实盘交易**，仅提供研究与决策支持。

**核心功能模块**:
- **持仓管理**: 以个股（Stock）为基本单位，通过交易记录（Transaction）自动计算持仓、历史盈亏
- **个股分析**: 每只个股关联一份分析记录（StockAnalyze），通过 JSONB 灵活存储基本面数据，支持自定义标签（StockTag）和止盈止损点（TpSlPoint）
- **分析报告**: StockAnalyze 的子表（Report），存储多 Agent 或手动添加的分析报告
- **Agent 智能分析**: 3 类 Agent 自动生成分析报告 — 基本面分析、网络消息分析、交易数据分析（NewsAgent 内部含多空辩论）

**核心用户故事**:
- US-001: 录入个股并记录买入/卖出交易，自动计算持仓和历史盈亏
- US-002: 为个股添加标签进行分类（如"分红/投机/成长/价值"）
- US-003: 设置止盈止损点和目标估值
- US-004: 记录和分析基本面数据（PE/PB/ROE/市值等）
- US-005: 触发 Agent 分析股票基本面，生成分析报告
- US-006: 触发 Agent 分析网络消息，通过多空辩论评估事件影响
- US-007: 触发 Agent 分析历史交易数据，更新趋势预测
- US-008: ✅ 市场行情数据实时展示与 K 线图（ECharts 交互式）
- US-009: ✅ 投资备忘：Markdown 笔记，可关联个股（独立页面 + 个股详情标签页）

---

## 2. 系统架构（必须严格遵循）

```
┌─────────────────────────────────────────────────────────────┐
│              Vue 3 Frontend (Vite + TDesign)                 │  ✅ v0.11.0
│  持仓概览 │ 个股详情(分栏布局: K线/交易/报告/止盈止损/备忘)  │
├─────────────────────────────────────────────────────────────┤
│              FastAPI Backend                                 │  ✅ 已实现
│  个股CRUD │ 交易记录CRUD │ 个股分析CRUD │ Agent分析API       │
├─────────────────────────────────────────────────────────────┤
│              Agent 核心（3 类）                               │  ✅ 已实现
│  FundamentalAgent │ NewsAgent(多空辩论) │ TechnicalAgent     │
├─────────────────────────────────────────────────────────────┤
│              LLM Provider Router                             │  ✅ 已实现
│  DeepSeek(默认) / OpenAI / Claude                            │
├─────────────────────────────────────────────────────────────┤
│              Data & Persistence                              │  ✅ 已实现
│  TuShare(A股) │ yfinance(港股/美股) │ PostgreSQL │ SMTP     │
├─────────────────────────────────────────────────────────────┤
│              Output & Delivery                               │  ✅ 已实现
│  分析报告 │ Agent 日志                                        │
└─────────────────────────────────────────────────────────────┘
```

### 2.5 数据源 Provider 能力抽象接口（未来规划）

当前各市场 Provider 通过 `BaseProvider` 定义基础接口。随着数据源增多，需统一的能力抽象：

**待设计能力清单：**
- `capabilities` → `{ "price", "kline", "name_cn", "name_en", "description", "pe", "pb", "market_cap", "industry" }`
- 每个 Provider 只实现它能提供的子集
- 消费方通过 `capabilities` 查询可用能力，不做假设

**当前各 Provider 能力矩阵（待对齐）：**

| Provider | 市场 | 价格 | K线 | 中文名 | 英文名 | 简介 | PE/PB |
|---------|------|:---:|:---:|:------:|:-----:|:---:|:----:|
| TuShareProvider | A股 | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ |
| AKShareProvider | HK/US | ✅ | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| YFinanceProvider | HK/US | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |

此项设计待后续 Change 推进，详见 [1.1 数据源 Provider](#11-投资备忘持仓总览增强数据源-provider等未来功能)。

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
| 前端 | **Vue 3** | 3.5.x | ✅ v0.8.0 |
| 前端 | **Vite** | 6.x | ✅ |
| 前端 | **TypeScript (strict)** | 5.x | ✅ |
| 前端 | **TDesign Vue Next** | 1.20.x | ✅ |
| 前端 | **Pinia** | 3.x | ✅ |
| 前端 | **Vue Router 4** | 4.x | ✅ |
| 前端 | **ECharts + vue-echarts** | 5.x / 7.x | ✅ |
| 前端 | **UnoCSS** | 66.x | ✅ |
| 数据 | TuShare Pro（A 股） | 1.4.29 | ✅ |
| 数据 | yfinance（港股/美股） | 0.2.58+ | ✅ |
| LLM | DeepSeek | | ✅ 已接入 |
| LLM | OpenAI / Claude | | ✅ 备选（自动降级）|

**严禁更换的技术栈**:
- 不使用 LangChain / CrewAI 等重型框架（自研轻量 Agent）
- 不在生产环境使用 SQLite
- 不做过度抽象（如过早引入微服务、消息队列）

---

## 4. 项目目录结构

```
StockMemos/
├── docker-compose.yml          # 编排 db + backend + frontend
├── .env                        # 环境变量（不提交 Git）
├── .env.example                # 环境变量模板
├── PROJECT.md                  # 本文档（项目级唯一文档）
│
├── backend/
│   ├── Dockerfile              # Python 3.11 Slim
│   ├── requirements.txt        # 后端依赖
│   ├── alembic.ini             # Alembic 配置
│   ├── alembic/
│   │   ├── env.py              # 迁移环境（从 .env 读取 DB URL）
│   │   ├── script.py.mako      # 迁移模板
│   │   └── versions/
│   │       ├── 001_create_portfolio.py          # 旧：持仓表（已废弃）
│   │       ├── 002_add_remaining_tables.py      # 旧：基础表（已废弃）
│   │       ├── 003_add_watchlist_memo_event.py  # 旧：自选股/备忘录（已废弃）
│   │       ├── 004_add_event_node_prediction.py # 旧：事件节点（已废弃）
│   │       ├── 005_drop_portfolio_trade_point.py # 删除旧持仓表
│   │       └── 006_create_stock_analyze_drop_orphaned.py # 新模型+删除废弃表
│   └── app/
│       ├── __init__.py
│       ├── main.py             # FastAPI 入口 + 路由注册
│       ├── config.py           # pydantic-settings 读取 .env
│       ├── database.py         # SQLAlchemy Engine + Session + Base
│       ├── models/             # ORM 模型（SQLAlchemy 2.0 Mapped）
│       │   ├── __init__.py
│       │   ├── stock.py        # ✅ 个股（exchange/symbol 联合唯一）
│       │   ├── transaction.py  # ✅ 交易记录（signed quantity 编码方向）
│       │   ├── stock_analyze.py # ✅ 个股分析（1:1 关联 stock）
│       │   ├── report.py       # ✅ 分析报告（stock_analyze 子表）
│       │   ├── tp_sl_point.py  # ✅ 止盈止损点（stock_analyze 子表）
│       │   └── stock_tag.py    # ✅ 个股标签（stock_analyze 子表）
│       ├── schemas/            # Pydantic 请求/响应模型
│       │   ├── __init__.py
│       │   ├── stock.py
│       │   ├── transaction.py
│       │   ├── stock_analyze.py
│       │   ├── report.py
│       │   ├── tp_sl_point.py
│       │   └── stock_tag.py
│       ├── routers/            # FastAPI API 路由
│       │   ├── __init__.py
│       │   ├── health.py       # 健康检查
│       │   ├── stock.py        # ✅ 个股 CRUD
│       │   ├── transaction.py  # ✅ 交易记录 CRUD
│       │   └── stock_analyze.py # ✅ 个股分析 CRUD + 子路由
│       ├── services/           # 业务服务层
│       │   ├── __init__.py
│       │   ├── market_data/    # 📅 多数据源行情适配层（骨架，待实现）
│       │   │   ├── __init__.py
│       │   │   ├── provider_base.py     # BaseProvider 抽象基类
│       │   │   ├── providers/
│       │   │   │   └── __init__.py
│       │   │   └── schemas.py           # 统一数据结构
│       │   ├── tushare_client.py # ✅ TuShare 客户端
│       │   ├── llm_router.py   # ✅ LLM 路由
│       │   ├── strategy_engine.py # ✅ 策略规则引擎（简单指标计算）
│       │   ├── report_generator.py # ✅ 报告生成器
│       │   └── email_service.py  # ✅ 邮件发送服务
│       └── agents/             # AI Agent 实现
│           ├── __init__.py
│           ├── fundamental_agent.py   # ✅ 基本面分析
│           ├── news_agent.py        # ✅ 网络消息分析（多空辩论）
│           └── technical_agent.py   # ✅ 交易数据分析
│
└── frontend/
    ├── Dockerfile              # Node 22 Alpine → nginx:alpine
    ├── Dockerfile.streamlit    # (已废弃) Streamlit Python Dockerfile
    ├── nginx.conf              # SPA fallback + /api proxy
    ├── package.json            # pnpm 依赖管理
    ├── pnpm-lock.yaml
    ├── tsconfig.json           # TypeScript strict 模式
    ├── vite.config.ts          # Vite 构建 + API proxy + UnoCSS
    ├── vitest.config.ts        # 单元测试配置
    ├── uno.config.ts           # UnoCSS 原子类配置
    ├── .npmrc                  # pnpm 配置（允许 esbuild/vue-demi 构建脚本）
    ├── index.html              # 入口 HTML
    ├── src/
    │   ├── main.ts             # Vue 应用入口（注册 Pinia/Router/TDesign）
    │   ├── App.vue             # 根组件（侧边栏 + router-view）
    │   ├── router/index.ts     # 路由：/ 持仓概览，/stock/:id 个股详情
    │   ├── stores/             # Pinia 状态管理
    │   │   ├── portfolio.ts    # 持仓列表（离开清除）
    │   │   ├── stock.ts        # 个股详情（离开清除）
    │   │   └── kline.ts        # K 线数据（缓存保持）
    │   ├── api/                # Axios API 层（Result<T> 模式）
    │   │   ├── client.ts       # 统一客户端 + 请求去重
    │   │   ├── stocks.ts
    │   │   ├── transactions.ts
    │   │   ├── stockAnalyze.ts # 分析/报告/标签/止盈止损
    │   │   └── market.ts       # 行情/价格/K线/刷新
    │   ├── types/              # TypeScript 类型定义
    │   │   ├── api.ts          # Result<T> 通用类型
    │   │   ├── stock.ts
    │   │   ├── transaction.ts
    │   │   ├── stockAnalyze.ts
    │   │   └── market.ts
    │   ├── pages/
    │   │   ├── PortfolioDashboard.vue  # 持仓概览首页
    │   │   └── StockDetail.vue         # 个股详情（分栏布局）
    │   ├── components/
    │   │   ├── layout/
    │   │   │   └── AppSidebar.vue      # TDesign Menu 侧边栏
    │   │   ├── dashboard/
    │   │   │   ├── KpiCards.vue        # KPI 汇总卡片
    │   │   │   └── StockTable.vue      # 可排序持仓表格
    │   │   ├── stock/
    │   │   │   ├── InfoPanel.vue       # 左侧信息面板
    │   │   │   ├── TransactionList.vue
    │   │   │   ├── TransactionEditor.vue
    │   │   │   ├── ReportList.vue
    │   │   │   └── TpSlManager.vue
    │   │   └── chart/
    │   │       └── KlineChart.vue      # ECharts K线图
    │   └── utils/
    │       └── format.ts       # 金额/百分比/日期格式化（万/亿）
    └── tests/
        ├── api/
        │   └── client.test.ts
        ├── stores/
        │   └── portfolio.test.ts
        └── utils/
            └── format.test.ts
```

---

## 5. 数据库 Schema

所有表通过 Alembic 迁移管理，严禁手动改表。

### 5.1 Stock（个股）✅
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(36) | PK | UUID 主键 |
| exchange | VARCHAR(8) | NOT NULL | 交易所：SH / SZ / HK / US |
| symbol | VARCHAR(20) | NOT NULL | 个股标识，如 600519 / AAPL |
| name | VARCHAR(100) | NOT NULL | 个股名称 |
| currency | VARCHAR(10) | NOT NULL | 交易货币：CNY / USD / HKD |
| position | NUMERIC(15,4) | NOT NULL, DEFAULT 0 | 当前持仓数量（Σ 交易记录数量，自动计算） |
| historical_pnl | NUMERIC(15,4) | NOT NULL, DEFAULT 0 | 历史盈亏（-Σ(数量×价格+手续费)，自动计算） |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间（自动） |

> 联合唯一约束 (exchange, symbol)，确保同一交易所内股票代码不重复。

### 5.2 Transaction（交易记录）✅
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(36) | PK | UUID 主键 |
| stock_id | VARCHAR(36) | FK → stock.id, NOT NULL | 关联个股 |
| quantity | NUMERIC(15,4) | NOT NULL | 交易数量：正为买入，负为卖出 |
| price | NUMERIC(12,4) | NOT NULL | 交易价格 |
| gas | NUMERIC(12,4) | NOT NULL, DEFAULT 0 | 手续费 |
| traded_at | DATE | NOT NULL | 交易日期 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

> 通过 signed quantity 编码方向（positive=buy, negative=sell），避免布尔字段。Stock.position 和 Stock.historical_pnl 由 Transaction 变化时自动聚合计算。

### 5.3 StockAnalyze（个股分析）✅
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(36) | PK | UUID 主键 |
| stock_id | VARCHAR(36) | FK → stock.id, UNIQUE, NOT NULL | 关联个股（1:1） |
| fundamentals_data | JSONB | nullable | 基本面数据（PE/PB/ROE/市值等动态指标） |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新时间（自动） |

> 与 Stock 是 1:1 关系，专为 Agent 产出的基本面分析设计，JSONB 允许灵活 schema 演化。

### 5.4 Report（分析报告）✅
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(36) | PK | UUID 主键 |
| stock_analyze_id | VARCHAR(36) | FK → stock_analyze.id, NOT NULL | 关联个股分析 |
| generated_at | TIMESTAMP | NOT NULL | 报告生成时间 |
| title | VARCHAR(200) | NOT NULL | 报告标题 |
| content | TEXT | NOT NULL | 报告正文 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

> StockAnalyze 的子表，存储 Agent 产生的分析报告。

### 5.5 TpSlPoint（止盈止损点）✅
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(36) | PK | UUID 主键 |
| stock_analyze_id | VARCHAR(36) | FK → stock_analyze.id, NOT NULL | 关联个股分析 |
| price | NUMERIC(12,4) | NOT NULL | 股价/目标价 |
| label | VARCHAR(20) | NOT NULL | 标签：止盈 / 止损 / 目标估值 |
| notes | TEXT | nullable | 备注 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

### 5.6 StockTag（个股标签）✅
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(36) | PK | UUID 主键 |
| stock_analyze_id | VARCHAR(36) | FK → stock_analyze.id, NOT NULL | 关联个股分析 |
| tag | VARCHAR(50) | NOT NULL | 标签（自由文本，如分红/投机/成长/价值） |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

### 5.7 kline_daily（日 K 线）✅ 已实现
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| stock_id | VARCHAR(36) | PK, FK → stock.id ON DELETE CASCADE | 关联股票 |
| trade_date | DATE | PK | 交易日 |
| open | NUMERIC(12,4) | NOT NULL | 开盘价 |
| high | NUMERIC(12,4) | NOT NULL | 最高价 |
| low | NUMERIC(12,4) | NOT NULL | 最低价 |
| close | NUMERIC(12,4) | NOT NULL | 收盘价 |
| volume | NUMERIC(20,4) | NOT NULL | 成交量（股数） |
| amount | NUMERIC(20,4) | NOT NULL | 成交额（元/港币/美元） |

> PK 为 (stock_id, trade_date)，天然去重。Provider 层自动拉取并 UPSERT 写入。

---

## 6. API 接口规范

### 6.1 健康检查 ✅
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 服务健康检查 |

### 6.2 Stock 个股 ✅
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/stocks` | 创建个股（exchange + symbol 唯一约束） |
| GET | `/api/stocks` | 获取个股列表 |
| GET | `/api/stocks/{id}` | 获取单条个股 |
| PUT | `/api/stocks/{id}` | 更新个股 |
| DELETE | `/api/stocks/{id}` | 删除个股（级联删除关联交易记录） |

### 6.3 Transaction 交易记录 ✅
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/transactions` | 创建交易记录（自动更新 Stock.position/pnl） |
| GET | `/api/transactions` | 获取所有交易记录 |
| GET | `/api/transactions/{id}` | 获取单条交易记录 |
| GET | `/api/transactions/stock/{stock_id}` | 获取某个股的所有交易记录 |
| PUT | `/api/transactions/{id}` | 更新交易记录（自动重算） |
| DELETE | `/api/transactions/{id}` | 删除交易记录（自动重算） |

### 6.4 StockAnalyze 个股分析 ✅
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stock-analyze/stock/{stock_id}` | 获取个股分析（不存在则自动创建） |
| PUT | `/api/stock-analyze/{id}` | 更新基本面数据 |
| DELETE | `/api/stock-analyze/{id}` | 删除个股分析（级联删子表） |
| | | |
| GET | `/api/stock-analyze/{id}/reports` | 获取分析报告列表 |
| POST | `/api/stock-analyze/{id}/reports` | 创建分析报告 |
| GET | `/api/stock-analyze/{id}/reports/{rid}` | 获取单条报告 |
| PUT | `/api/stock-analyze/{id}/reports/{rid}` | 更新报告 |
| DELETE | `/api/stock-analyze/{id}/reports/{rid}` | 删除报告 |
| | | |
| GET | `/api/stock-analyze/{id}/tp-sl-points` | 获取止盈止损点列表 |
| POST | `/api/stock-analyze/{id}/tp-sl-points` | 创建止盈止损点 |
| PUT | `/api/stock-analyze/{id}/tp-sl-points/{pid}` | 更新止盈止损点 |
| DELETE | `/api/stock-analyze/{id}/tp-sl-points/{pid}` | 删除止盈止损点 |
| | | |
| GET | `/api/stock-analyze/{id}/stock-tags` | 获取标签列表 |
| POST | `/api/stock-analyze/{id}/stock-tags` | 创建标签 |
| DELETE | `/api/stock-analyze/{id}/stock-tags/{tid}` | 删除标签 |

### 6.5 行情数据 API ✅ 已实现
| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | `/api/stocks/{id}/price` | 获取实时行情（纯内存，不落盘） | ✅ |
| GET | `/api/stocks/{id}/kline?start=&end=` | 获取日 K 线（DB 持久化） | ✅ |
| GET | `/api/stocks/{id}/fundamentals` | 获取基本面数据（DB 持久化） | ✅ |
| POST | `/api/market/refresh` | 批量刷新所有股票日K+基本面 | ✅ |
| POST | `/api/market/refresh-fundamentals` | 仅批量刷新所有股票基本面 | ✅ |

> 实时行情不持久化，仅在前端页面打开时调用。日K + 基本面存储在 PostgreSQL。

---

## 7. 前端页面（Vue 3 + TDesign）

### 7.1 持仓概览（首页） ✅
- 顶部 4 个 KPI 卡片：股票数量 · 总持仓量 · 总盈亏 · 盈利股票数
- 可排序股票表格：代码、名称、交易所、持仓量、盈亏（颜色编码）、现价、标签、操作
- 股票名称可点击跳转个股详情，现价自动拉取（超 1 小时提示过期）
- 添加个股弹窗（交易所/代码/名称/货币表单）
- 删除个股确认弹窗
- 刷新行情按钮（调用 `POST /api/market/refresh`）
- 对接后端：`GET /api/stocks` + `DELETE /api/stocks/{id}` + `POST /api/stocks`

### 7.2 个股详情页（分栏布局） ✅
- **左侧信息面板**：股票代码/名称、当前价、持仓量、盈亏（颜色编码）
- **基本面**：key-value 列表（PE/PB/ROE/市值/股息率/净利润率/负债比等），支持 万/亿 格式化
- **标签管理**：TDesign Tag 组件，支持添加（回车）和删除（×）
- **右上方**：**ECharts 交互式 K 线图**（日K + MA5/20/60 + 成交量柱状图 + brush 缩放）
- **右下方 Tab**：交易记录 / 分析报告 / 止盈止损
- 对接后端：`GET/PUT /api/stocks/{id}` + `/api/stock-analyze/**` + `/api/transactions/**`

### 7.3 交易记录管理 ✅
- 可排序表格：交易日期、方向（买入=红/卖出=绿）、价格、数量、佣金、合计
- 内联添加表单（日期选择器 + 买卖方向 + 数量 + 价格 + 佣金）
- 行内编辑（点击行进入编辑模式）
- 删除确认弹窗
- 增删改自动重算持仓和盈亏

### 7.4 分析报告 ✅
- 报告列表（按生成时间降序），点击展开/折叠内容
- 添加报告表单（标题 + 正文）

### 7.5 止盈止损 ✅
- 止盈/止损/目标估值点列表（类型颜色编码）
- 添加表单 + 删除确认

---

## 8. Agent 角色定义

系统精简为 **3 类核心 Agent**，直接对应分析报告的 3 个维度：

| Agent | 职责 | 输入 | 输出 |
|-------|------|------|------|
| **FundamentalAgent** ✅ | 分析股票公司基本面（财务数据、行业地位、估值模型） | stock_id, 财务数据 | JSON: {target_price, valuation_method, business_analysis, confidence} |
| **NewsAgent** ✅ | 搜集并分析网络消息，通过**多空辩论**评估事件影响 | stock_id, 关键词, 时间窗口 | JSON: {events: [{name, impact_tag, expected_date, reasoning}], bull_case, bear_case, consensus} |
| **TechnicalAgent** ✅ | 分析历史交易数据（价格走势、成交量、技术指标） | stock_id, 交易数据 | JSON: {trend_analysis, key_levels, signals} |

### 8.1 多 Agent 辩论机制（NewsAgent 内部）

NewsAgent 不是单一 Agent，而是内部包含 **3 个子 Agent** 的辩论流程：
1. **NewsBullAgent** — 从利好角度分析消息，输出 `bull_case`（看多理由）
2. **NewsBearAgent** — 从利空角度分析消息，输出 `bear_case`（看空理由）
3. **NewsRefereeAgent** — 综合多空观点，输出 `consensus`（共识判断）和事件影响评估

---

## 9. 环境变量（.env）

```bash
# 数据库
DATABASE_URL=postgresql+psycopg2://trading:changeme@db:5432/agent_trading
DB_PASSWORD=changeme

# TuShare（A 股）
TUSHARE_TOKEN=your_tushare_pro_token_here

# 行情数据源（按交易所配置）
# 可选值: yfinance / Tushare
MARKET_DATA_SOURCE_CN=Tushare
MARKET_DATA_SOURCE_HK=yfinance
MARKET_DATA_SOURCE_US=yfinance

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

## 10. 开发里程碑

### Milestone 1: 骨架与旧模型 ✅（已完成）
- [x] Docker Compose 环境跑通（backend + db + frontend）
- [x] Alembic 配置完成，能执行 upgrade/downgrade
- [x] 原基础模型（portfolio, trade_point, analysis_report, agent_log, strategy, strategy_signal）
- [x] TuShare 客户端封装（含错误重试、缓存）
- [x] Streamlit 首页展示持仓列表
- [x] 项目级文档 PROJECT.md 建立

### Milestone 2: 扩展旧模型 ✅（已完成）
- [x] 新增旧模型：watchlist, investment_memo, memo_event, event_node, event_prediction
- [x] 对应 API 和 Streamlit 页面

### Milestone 3: 架构重构 ✅（已完成）
- [x] 重构为新模型体系：Stock, Transaction, StockAnalyze, Report, TpSlPoint, StockTag
- [x] Migration 005-006：删除旧表 portfolio/trade_point，删除废弃表（watchlist/investment_memo/event_node/analysis_report/strategy 等），创建新表
- [x] 重写 API 路由：/api/stocks、/api/transactions、/api/stock-analyze（含子路由）
- [x] 重写前端页面：持仓概览 + 个股详情（当时 Streamlit，后替换为 Vue）

### Milestone 4: Agent 分析 ✅（已完成）
- [x] LLM Router 封装（DeepSeek + 备选）
- [x] FundamentalAgent 实现（基本面分析）
- [x] NewsAgent 实现（网络消息 + 多空辩论）
- [x] TechnicalAgent 实现（交易数据分析）

### Milestone 5: 基础设施与部署 ✅（已完成）
- [x] 策略规则引擎（简单指标计算）
- [x] 邮件发送接口（SMTP 封装）
- [x] .env 模板和配置说明（.env.example）
- [x] 局域网部署文档（DEPLOYMENT.md）

### Milestone 6: 市场行情数据 ✅（已完成）
- [x] 添加 yfinance 依赖 + Alembic 迁移（kline_daily 表）
- [x] Provider 适配器层：BaseProvider + TuShareProvider + YFinanceProvider + Router + Service
- [x] REST API 端点：/price /kline /fundamentals /refresh
- [x] 前端行情展示 + 刷新按钮（Vue + ECharts）
- [x] MA5/MA20/MA60 均线 + K 线图
- [x] ETF/基金数据源支持（TuShare fund_basic/fund_daily + 自动分类路由）
- [x] 港股前导零处理（yfinance ticker 自动去零：07709 → 7709.HK）

### Milestone 7: Vue 前端重写 ✅（已完成）
- [x] Streamlit → Vue 3 + Vite + TypeScript 全量替换
- [x] TDesign Vue Next UI 组件库 + UnoCSS 布局
- [x] Pinia 状态管理 + Axios Result<T> 模式
- [x] ECharts 交互式 K 线图（brush 缩放）
- [x] 个股详情分栏布局（左侧面板 + K 线 + Tab 内容）
- [x] Docker 多阶段构建（node:22 → nginx）
- [x] vitest 单元测试（API 层 + stores + 工具函数）

### Milestone 8: 持仓总览增强 & 个股列表独立 📅（规划中）
- [ ] 主标签系统：首个标签默认为主标签（按创建时间），删除后重新排序，无标签归入"未分类"
- [ ] 板块配置：水平长条图，各板块按持仓占比从左到右排列
- [ ] 板块明细：各板块下个股列表（名称 + 持仓市值 + 占比）
- [ ] 个股列表独立页：持仓表格移至 `/stocks`，侧边栏新增入口
- [ ] 个股详情「返回列表」改为返回 `/stocks`
- [ ] 侧边栏更新：持仓总览 / 个股列表 / 资金管理 / 投资备忘 / 设置

### Milestone 9: 数据备份系统 ✅（已完成）
- [x] 后端 API：POST /api/backup/export（StreamingResponse 输出 ZIP）+ POST /api/backup/import（multipart 上传）
- [x] CLI 脚本：python -m scripts.backup export/import（复用后端 ORM）
- [x] 前端：设置页备份模块（复选框 + 导出/导入按钮 + 结果展示 + 数据自动刷新）
- [x] 导出/导入格式：ZIP（含 stocks.json / transactions.json / memos.json / capital_flows.json / kline/*.csv）
- [x] 导入去重：transactions 内存 + DB 双层去重，kline UPSERT by stock_id + date
- [x] 导入后自动重算：Stock.position/historical_pnl + capital_meta 触发器

### Milestone 10: 平台可用性监测 ✅（已完成）

- [x] 后端诊断 API：`GET /api/diagnostics`（8 项串行检测，scope=datasource|llm 参数）
- [x] 服务元数据端点：`GET /api/diagnostics/services`（名称/被用于/注册方式，构建时可确定）
- [x] 前端诊断面板：设置页双区表格（数据源/大模型），localStorage 持久化，动态列
- [x] 只读汇率展示（去掉前端编辑功能）
- [x] AKShare 数据源扩展：HK + US 双市场支持（日线/价格/中文名）
- [x] 数据源 Provider 能力抽象（2.5 节，约束 10）
- [x] VERSION 文件 + DB 版本号
- [x] K 线图布局优化：dataZoom 移除，容器 auto 自适应

### Milestone 11: 前端缓存优化 📅（规划中）
- [ ] 行情现价并发请求 + Map 响应式修复
- [ ] 封装通用缓存 composable（TTL + 内存缓存）

### Milestone 12: K 线图增强 📅（规划中）
- [ ] K 线图止盈止损水平虚线
- [ ] K 线图交易点标注（B=买入蓝色，S=卖出红色）
- [ ] K 线图默认显示范围 30 日

---

## 11. 规划功能需求定义

### 11.1 持仓总览增强

#### 主标签系统

- **主标签确定规则**：StockTag 按 `created_at` 排序，第一个标签即为主标签（代表行业/板块）
- **标签删除后**：重新排序，次早的标签自动成为主标签
- **无标签的股票**：在板块统计中归入"未分类"

#### 板块配置（水平长条图）

- 展示位置：持仓总览页面，Treemap 下方
- 展示形式：一条完整的水平长条，各板块按持仓占比从左到右排列
- 每个板块段显示：`{板块名称} {占比百分比}`
- 数据范围：所有持仓股票，按主标签聚合
- 无交互（仅展示）

#### 板块明细

- 展示位置：板块配置下方
- 展示内容：每个板块一行，列出该板块包含的个股
  - 个股名称
  - 持仓市值（数量 × 现价 × 汇率，CNY）
  - 在总仓位中的占比
- 参考样式：Money or Life 美股频道板块明细

#### 个股列表独立页

- 新页面 `/stocks`，侧边栏新增「个股列表」
- 表格保持现有完整功能：添加/删除/重置/查看详情
- 个股详情页「返回列表」改为返回 `/stocks`
- 持仓总览页面不再显示个股列表表格

### 11.2 K 线图增强

- **止盈止损线**：ECharts `markLine` 水平虚线贯穿，标注止盈/止损价格
- **交易点标注**：根据 Transaction 记录的 traded_at 和 quantity，在对应日期 K 线上标注
  - B（买入，蓝色箭头）：quantity > 0
  - S（卖出，红色箭头）：quantity < 0
- **默认显示范围**：最近 30 个交易日，可通过 zoom 查看更早数据

### 11.3 数据备份系统

- 触发方式：设置页「数据备份」模块（复选框选择内容 + 导出/导入按钮）
- 导出格式：ZIP（`stockmemos_export_YYYYMMDD.zip`）
- 压缩包结构：
  - `stocks.json` — 个股列表（exchange + symbol + name + tags）
  - `transactions.json` — 交易记录
  - `memos.json` — 投资备忘
  - `capital_flows.json` — 现金流记录
  - `kline/{symbol}_{exchange}.csv` — K 线数据（可选）
- CLI 脚本：`docker compose exec backend python -m scripts.backup export --types stocks,transactions --output /backup.zip`
- 导入规则：
  - Stocks：exchange+symbol 已存在则跳过，不存在则创建
  - Transactions：Stock 存在且非重复则创建，否则跳过（内存 + DB 双层去重）
  - Memos：title+created_at 判重，Stock 存在则关联
  - Kline：stock_id+date UPSERT
  - Capital flows：直接创建（无判重）
- 导入后自动：刷新 Stock.position/historical_pnl、刷新前端 Pinia stores
- 不包含：基本面（实时拉取）、分析报告

### 11.4 平台可用性监测

- 页面风格：详细诊断表（延迟、可用性、最后检查时间）
- 监测项：
  - 数据源：TuShare、yfinance(US)、yfinance(HK) 等（延迟 + 可用性）
  - LLM API：DeepSeek、OpenAI、Claude 的 API Key 有效性（余额检测）
  - 数据库：PostgreSQL 连接状态
- 后端提供统一检测端点，前端展示

### 11.5 前端缓存优化（延后）

- 当前问题：
  - 行情现价串行请求（每只股票依次请求）
  - `ref(Map)` 不触发 Vue 响应式更新
  - 无跨会话缓存，每次页面刷新全部重拉
- 待实现：通用 `useCache` composable、并发请求、TTL 策略

---

## 12. 需求管理方法

### 12.1 OpenSpec 工作流

本项目使用 OpenSpec 进行需求登记和变更管理，工作流如下：

```
grilling（多轮问答明确需求）
    → openspec propose（生成 proposal / design / specs / tasks）
    → 实现（按 tasks 逐项完成）
    → openspec archive（归档变更，记录 result.json）
```

### 12.2 OpenSpec 与 Git 的关系

`openspec/` 目录**不被 Git 追踪**（在 `.gitignore` 中排除）。原因：

1. **OpenSpec 是本地工作缓存**：change 目录中的 artifacts（proposal、design、specs、tasks）是开发过程中的临时产物，archived 后可通过 `result.json` 追溯
2. **避免噪音**：specs 频繁随讨论调整，追踪会产生大量与源代码无关的变更
3. **主规格文档在 PROJECT.md 中**：功能定义的权威来源是本文档的"规划功能需求定义"章节，OpenSpec specs 是过程记录
4. **归档即持久化**：完成 change 后 `result.json` 记录了关键决策，足以复盘

### 12.3 变更记录流程

1. 新需求或 Bug → 在当前会话中通过 grilling 明确需求
2. 需求明确后 → 更新 PROJECT.md 对应章节
3. 实现完成后 → 更新 PROJECT.md 版本号和变更日志

## 13. 快速启动

### 13.1 首次启动
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

### 13.2 日常操作
```bash
docker compose up -d          # 启动
docker compose up -d --build frontend  # 重新构建前端
docker compose down -v        # 停止并删除数据卷（重置）
docker compose logs -f backend # 查看后端日志
docker compose build backend  # 重新构建后端
```

### 13.3 数据库迁移
```bash
# 进入后端容器执行
 docker exec -it trading-backend bash
 alembic upgrade head        # 升级
 alembic downgrade -1        # 回退一级
 alembic revision --autogenerate -m "新增 xxx 表"  # 生成新迁移（需模型已注册）
```

---

## 14. 关键约束（开发红线）

1. **用户不直接输入 Prompt**：所有 Agent 输入由 Dashboard 操作转化为结构化 JSON
2. **数据源限流处理**：所有外部数据源请求必须加缓存和重试（3 次 + 指数退避）。TuShare 遵守 1 小时 TTL，yfinance 遵守每秒最多 1 次请求
3. **LLM 输出校验**：强制 JSON 模式，失败重试 3 次
4. **数据安全**：API Key 不提交 Git，使用 `.env`
5. **文档同步**：任何功能变更必须先修改 PROJECT.md，再修改代码
6. **行情数据源按交易所配置**：不可运行时切换，环境变量 MARKET_DATA_SOURCE_CN/HK/US 控制。数据源自身负责任何降级逻辑，对外提供统一接口
7. **不引入重型框架**：不在 Agent 调度中使用 LangChain / CrewAI，使用自研轻量封装
8. **不使用 SQLite**：生产环境仅使用 PostgreSQL
9. **不过度抽象**：不引入微服务、消息队列等重型基础设施
10. **（未来）数据源 Provider 统一能力抽象**：各市场 Provider 需定义清晰的能力清单（名称/简介/基本面/K线等），消费方通过 `capabilities` 查询可用能力。详见 2.5 节

---

## 15. 文档版本变更日志

| 版本 | 日期 | 变更内容 | 变更人 |
|------|------|----------|--------|
| 0.1.0 | 2024-06-13 | 项目骨架 + 数据库模型 + TuShare + 持仓 API + Streamlit 前端 | Agent |
| 0.2.0 | 2024-06-13 | 重大重构：新增自选股/投资备忘录/世界热点事件模型；重新定位 3 类 Agent | Agent |
| 0.3.0 | 2024-06-19 | Milestone 2-4 完成：自选股/备忘录/事件追踪/LLM Router/3 Agent 分析/Orchestrator 自动写入/前端联动 | Agent |
| 0.4.0 | 2024-06-19 | Milestone 5 完成：策略规则引擎（SMA/EMA/RSI）/ 策略 CRUD / BacktestAgent / 回测 API / Streamlit 策略页 | Agent |
| 0.5.0 | 2024-06-19 | Milestone 6 完成：RSS 结构化输出 / SMTP 邮件发送 / .env 模板 / 局域网部署文档 / Streamlit 设置与投递页 | Agent |
| 0.6.0 | 2026-07-03 | 多数据源行情扩展方案前置：yfinance 港股/美股支持方案、Provider 适配器模式设计、kline_daily 表设计、降级策略 | Agent |
| 0.7.0 | 2026-07-03 | 全局设计文档对齐实际代码：移除旧模型/API 描述，重写为新模型体系（Stock/Transaction/StockAnalyze/Report/TpSlPoint/StockTag）+ 简化前端结构 + 市场数据配置骨架 | Agent |
| 0.7.1 | 2026-07-04 | P0/P1 bugfix 版本：修复最新价跨股串号、删除股票 500、基本面首屏不展示、TuShareProvider 空壳穿透 | Agent |
| 0.8.0 | 2026-07-09 | Streamlit → Vue 3 全量替换：Vite + TypeScript + TDesign Vue Next + Pinia + ECharts + UnoCSS。分栏布局个股详情、Result<T> API 模式、Docker 多阶段构建 | Agent |
| 0.8.1 | 2026-07-10 | Portfolio treemap 可视化（分层/标签着色/其他聚合）、KPI 卡片重设计、CNY 汇率换算 + 各种 UI bugfix | Agent |
| **0.11.0** | **2026-07-12** | **投资备忘系统：独立页面 `/memos` + 个股详情标签页。Markdown 笔记编辑回填、关联个股跳转、卡片展开/收起。DB 迁移 009。** | **Agent** |
| **0.10.0** | **2026-07-12** | **资金管理 + KPI 重构：capital_flow 流水表、capital_meta 聚合表、汇率配置（settings 页面）、8 卡 KPI 指标面板（总资产/总收益率/总仓位/现金等）、DB trigger 自动重算。** | **Agent** |
| 0.12.0 | 2026-07-13 | 平台可用性监测：诊断 API（8 项串行检测 + scope 参数）、设置页只读汇率 + 双区面板（数据源/大模型）、localStorage 持久化 + VERSION 文件 | Agent |
| 0.12.1 | 2026-07-13 | 文档更新：新增 2.5 数据源 Provider 能力抽象接口（未来规划）、约束 10、AKShareProvider 完成度现状记录 | Agent |
| **0.14.0** | **2026-07-14** | **数据备份系统：POST /api/backup/export 导出 ZIP（StreamingResponse）、POST /api/backup/import 导入（内存+DB 双层去重 + Stock position/pnl 自动重算）、CLI 脚本（argparse）、前端设置页备份模块（复选框+导出/导入+自动刷新）。Milestone 9 完成。** | **Agent** |
| **0.15.0** | **2026-07-14** | **曾引入同花顺截图 OCR 实验模块；该方案因金融数据入口可靠性与维护成本问题，已在 0.16.0 移除。** | **Agent** |
| **0.16.0** | **2026-07-20** | **移除废弃的同花顺截图 OCR 模块（`backend/app/ocr/`）。清理 `tushare_client.py` 中 OCR-only 的 `get_stock_basic_by_name` 方法。备份导入（`POST /api/backup/import`）仍是截图数据的推荐接入方式。** | **Agent** |
| **0.13.0** | **2026-07-13** | **平台可用性监测 + AKShare 数据源扩展 + K 线布局优化：诊断 API/面板、只读汇率、AKShare 港美股支持、Provider 能力抽象、VERSION 文件、K 线图容器自适应。Milestone 10 完成。** | **Agent** |
