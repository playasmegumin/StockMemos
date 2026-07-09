# StockMemos

本地部署的投研助手。通过 Vue 3 Dashboard 管理自选股、交易记录和 AI 分析报告。**不涉及实盘交易**，仅提供研究与决策支持。

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI + Uvicorn | REST API 服务 |
| 前端框架 | **Vue 3 + Vite + TypeScript** | TDesign Vue Next + Pinia + ECharts |
| CSS | UnoCSS | 原子类布局 |
| 数据库 | PostgreSQL 15 | Docker 部署，Alembic 迁移管理 |
| 股票数据源 | 多个专用适配器 | TuShare(A股) / yfinance(港股/美股) |
| 容器化 | Docker Compose | db + backend + frontend 一键启动 |

## 架构概览

```
Vue 3 Frontend（Vite + TDesign + ECharts）
  ├── 持仓概览（KPI 卡片 + 可排序表格 + 现价）
  ├── 个股详情（分栏布局：信息面板 / K线图 / 交易/报告/止盈止损）
  └── 交互式 K 线图（MA5/20/60 + 缩放 + 成交量）
          │
          ▼  REST API (port 8080)
FastAPI Backend
    ├── 个股 CRUD / 交易 CRUD / 分析 CRUD
    ├── Market Data Service（多数据源适配层）
    │     ├── TuShareProvider（A 股）
    │     ├── YFinanceProvider（港股/美股）
    │     └── kline_daily 表（DB 降级兜底）
    └── Agent 分析（基本面 / 多空辩论 / 技术分析）
          │
          ▼
PostgreSQL（持久化）

## 快速启动

```bash
# 1. 克隆项目
git clone <repo-url> && cd stockmemos

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，至少填入 TUSHARE_TOKEN 和 DEEPSEEK_API_KEY

# 3. 启动全部服务
docker compose up -d --build

# 4. 访问
# 前端: http://localhost:8501
# 后端 API 文档: http://localhost:8080/docs
```

首次启动后，Alembic 会自动执行数据库迁移。

## 项目目录结构

```
stockmemos/
├── docker-compose.yml
├── .env.example
├── README.md
├── PROJECT.md                          # 项目架构说明书（权威文档）
├── BUGS.md                             # 已知问题追踪
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini                     # 数据库迁移配置
│   ├── alembic/versions/               # 迁移脚本
│   └── app/
│       ├── main.py                     # FastAPI 入口
│       ├── config.py                   # 环境变量读取
│       ├── database.py                 # Engine + Session
│       ├── models/                     # ORM 模型
│       ├── schemas/                    # Pydantic 请求/响应模型
│       ├── routers/                    # API 路由
│       ├── services/                   # 业务服务层
│       │   ├── market_data/            # 多数据源行情适配
│       │   ├── tushare_client.py       # TuShare SDK 封装
│       │   ├── llm_router.py           # LLM 路由
│       │   └── report_generator.py     # 报告生成
│       └── agents/                     # 3 类 AI Agent
│
└── frontend/                 # Vue 3 前端（Vite + TypeScript + TDesign）
    ├── Dockerfile              # Node 22 → nginx 多阶段构建
    ├── nginx.conf              # SPA fallback + /api 反向代理
    ├── package.json / pnpm-lock.yaml
    ├── vite.config.ts
    ├── src/
    │   ├── main.ts / App.vue
    │   ├── router/ / stores/ / api/ / types/
    │   ├── pages/              # PortfolioDashboard + StockDetail
    │   ├── components/         # KpiCards, StockTable, InfoPanel,
    │   │                       # KlineChart, TransactionList, etc.
    │   └── utils/
    └── tests/                  # vitest
```

## 配置说明

`.env` 核心配置项：

| 变量 | 必填 | 说明 |
|------|:--:|------|
| `TUSHARE_TOKEN` | ✅ | TuShare Pro token，[注册获取](https://tushare.pro/register) |
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek API key，[注册获取](https://platform.deepseek.com/) |
| `DATABASE_URL` | — | PostgreSQL 连接串，默认值可直接使用 |
| `FINNHUB_API_KEY` | — | 美股 Finnhub 数据源（可选） |
| `MARKET_DATA_SOURCE_CN` | — | A 股数据源，默认 `Tushare` |
| `MARKET_DATA_SOURCE_HK` | — | 港股数据源，默认 `yfinance` |

## 🙏 致谢 / Acknowledgements

### 灵感来源 / Inspirations

#### [TradingAgents-CN](https://github.com/hsliuping/TradingAgents-CN)
一切的起因是朋友给我发了个“有偿上门安装TradingAgents-CN”的群聊截图。
好笑归好笑，我自己试着安装了一下... 确实很有启发性，但是并不能完全满足我的需求；而这个项目又已经过于庞大，不太适合修改。
因此我决定开始实现一个自己的AI投研工具。

#### [FinceptTerminal](https://github.com/Fincept-Corporation/FinceptTerminal)
一个设计风格很不错的Qt桌面项目。项目内置订阅功能，由于本人最近没有米米，未能完整体验所有功能...
这个项目证明了做一个界面很好看的AI投研助手的可行性，光是知道这种项目可以做出来就很有帮助！

### AI 辅助开发

本项目完全在 AI 编程助手的协助下开发。开发环境由以下组件构成：

- **[OpenCode](https://opencode.ai)** — 终端 AI Agent 框架。提供交互式编码界面，集成 LSP 代码检查、多会话并行 Agent 调度和权限管控，是开发者与大模型之间的统一入口。
- **[OpenSpec](https://github.com/anomalyco/opencode)** — 需求一致性框架。将设计意图转化为结构化规格文档，确保需求→设计→实现→测试的链路可追溯、可验证。
- **[DeepSeek](https://deepseek.com)** 系列模型 — 提供代码生成、架构分析和逻辑推理能力。
- **OpenCode Go** 订阅 — 驱动交互引擎持续运行。

### 工具依赖

| 项目 | 用途 |
|------|------|
| [FastAPI](https://fastapi.tiangolo.com/) | 后端 API 框架 |
| [Vue 3](https://vuejs.org/) | 前端框架 |
| [TDesign Vue Next](https://tdesign.tencent.com/vue-next/) | UI 组件库 |
| [ECharts](https://echarts.apache.org/) | K 线图可视化 |
| [TuShare](https://tushare.pro/) | A 股行情与基本面数据 |
| [PostgreSQL](https://www.postgresql.org/) | 数据持久化 |
| [Docker](https://www.docker.com/) | 容器化部署 |

## License

本项目采用 [GNU General Public License v3.0](LICENSE)。

**你可以做什么：**
- 自由使用、复制、修改、分发本软件
- 将本软件用于商业或非商业项目

**你必须遵守：**
- 分发本软件或其修改版本时，必须同样以 GPL v3 协议开源全部源代码
- 保留原始版权声明和许可声明
- 修改版本必须明确标注你做了哪些修改

**不提供担保：**
- 本软件按"原样"提供，作者不承担任何因使用本软件产生的损害赔偿责任
