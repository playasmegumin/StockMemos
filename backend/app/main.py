"""FastAPI 入口模块"""

from fastapi import FastAPI
from app.routers import health

app = FastAPI(
    title="Agent股票交易决策系统",
    description="基于多Agent协作的智能投研助手",
    version="0.1.0",
)

app.include_router(health.router, prefix="/health", tags=["health"])


@app.get("/health")
async def root_health():
    """根路径健康检查（冗余兼容）"""
    return {"status": "ok"}
