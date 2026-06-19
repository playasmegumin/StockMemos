"""FastAPI 入口模块"""

from fastapi import FastAPI
from app.routers import health, portfolio, watchlist, event_node, analyze, strategy, output

app = FastAPI(
    title="StockMemos",
    description="基于多Agent协作的智能投研助手",
    version="0.1.0",
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(event_node.router, prefix="/api/event-nodes", tags=["event-nodes"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["analyze"])
app.include_router(strategy.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(output.router, prefix="/api/output", tags=["output"])


@app.get("/health")
async def root_health():
    """根路径健康检查（冗余兼容）"""
    return {"status": "ok"}
