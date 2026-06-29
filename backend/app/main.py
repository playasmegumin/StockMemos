"""FastAPI 入口模块"""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from fastapi.middleware.cors import CORSMiddleware

from app.logging_config import setup_logging
from app.routers import health, stock, transaction, watchlist, event_node, analyze, strategy, output

# 初始化日志配置
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="StockMemos",
    description="基于多Agent协作的智能投研助手",
    version="0.1.0",
)

# ── CORS 中间件（允许本地文件测试页面访问）──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 请求日志中间件（中文，过滤 health）──
@app.middleware("http")
async def log_requests(request: Request, call_next):
    path = request.url.path
    if path in ("/health", "/docs", "/openapi.json") or path.startswith("/health"):
        return await call_next(request)

    method = request.method
    logger.info("【请求】%s %s — 处理中", method, path)
    
    try:
        response = await call_next(request)
        status = response.status_code
        if status < 400:
            logger.info("【成功】%s %s — 状态码 %d", method, path, status)
        elif status < 500:
            logger.warning("【客户端错误】%s %s — 状态码 %d", method, path, status)
        else:
            logger.error("【服务端错误】%s %s — 状态码 %d", method, path, status)
        return response
    except Exception as e:
        logger.error("【异常】%s %s — %s", method, path, e)
        raise

# ── 启动/关闭事件 ──
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 StockMemos 后端服务启动中...")
    logger.info("📡 API 文档地址: http://localhost:8080/docs")

    # 自动创建缺失的数据表（暂不依赖 Alembic）
    from app.database import Base, engine
    Base.metadata.create_all(bind=engine)
    logger.info("【DB】数据表检查完成")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 StockMemos 后端服务关闭")

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(stock.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(transaction.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(event_node.router, prefix="/api/event-nodes", tags=["event-nodes"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["analyze"])
app.include_router(strategy.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(output.router, prefix="/api/output", tags=["output"])

@app.get("/health")
async def root_health():
    """根路径健康检查（冗余兼容）"""
    return {"status": "ok"}
