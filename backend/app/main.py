"""FastAPI 入口模块"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from fastapi.middleware.cors import CORSMiddleware

from app.logging_config import setup_logging
from app.routers import health, stock, transaction, stock_analyze, market_data, capital, memos

# 初始化日志配置
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 StockMemos 后端服务启动中...")
    logger.info("📡 API 文档地址: http://localhost:8080/docs")

    # 自动创建缺失的数据表（暂不依赖 Alembic）
    from app.database import Base, engine
    Base.metadata.create_all(bind=engine)
    logger.info("【DB】数据表检查完成")
    yield
    logger.info("🛑 StockMemos 后端服务关闭")


app = FastAPI(
    title="StockMemos",
    description="基于多Agent协作的智能投研助手",
    version="0.1.0",
    lifespan=lifespan,
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

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(stock.router, prefix="/api/stocks", tags=["stocks"])
app.include_router(transaction.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(stock_analyze.router, prefix="/api/stock-analyze", tags=["stock-analyze"])
app.include_router(market_data.router, prefix="/api", tags=["market-data"])
app.include_router(capital.router, prefix="/api/capital", tags=["capital"])
app.include_router(memos.router, prefix="/api/memos", tags=["memos"])

# ── 提供测试页面（/test 路径，仅 Docker 环境存在）──
import os as _os
_test_dir = "/app/test"
if _os.path.isdir(_test_dir):
    app.mount("/test", StaticFiles(directory=_test_dir, html=True), name="test")

@app.get("/health")
async def root_health():
    """根路径健康检查（冗余兼容）"""
    return {"status": "ok"}
