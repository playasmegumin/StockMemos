"""Agent 分析触发 API

Endpoints:
    POST /api/analyze/{code}/fundamental   — 触发 FundamentalAgent 分析
    POST /api/analyze/{code}/news          — 触发 NewsAgent 分析（多空辩论）
    POST /api/analyze/{code}/technical     — 触发 TechnicalAgent 分析

每个端点：
1. 调用对应 Agent 分析
2. 通过 Orchestrator 将结果写入 InvestmentMemo / MemoEvent
3. 返回分析结果（JSON）

注意：如果股票不在自选股中，返回 404；如果 LLM 调用失败，返回分析结果但标记错误。
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.models.watchlist import Watchlist
from app.services.llm_router import LLMRouter
from app.services.tushare_client import TushareClient
from app.agents.fundamental_agent import FundamentalAgent
from app.agents.news_agent import NewsAgent
from app.agents.technical_agent import TechnicalAgent
from app.agents.orchestrator import apply_fundamental_result, apply_news_result, apply_technical_result

router = APIRouter()


# 单例（依赖注入复用）
_llm_router: LLMRouter | None = None
_tushare_client: TushareClient | None = None


def _get_llm() -> LLMRouter:
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router


def _get_tushare() -> TushareClient:
    global _tushare_client
    if _tushare_client is None:
        _tushare_client = TushareClient()
    return _tushare_client


def _check_watchlist(db: Session, stock_code: str) -> None:
    """检查股票是否在自选股中，否则抛 404"""
    item = db.query(Watchlist).filter(
        Watchlist.stock_code == stock_code,
        Watchlist.is_watched == True
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="该股票不在自选股中，请先添加")


@router.post("/{code}/fundamental", response_model=Dict[str, Any])
def analyze_fundamental(code: str, db: Session = Depends(get_db)):
    """触发 FundamentalAgent 基本面分析，结果写入投资备忘录"""
    _check_watchlist(db, code)
    
    agent = FundamentalAgent(_get_llm(), _get_tushare())
    result = agent.analyze(code)
    
    if "error" in result:
        return {
            "stock_code": code,
            "agent": "fundamental_agent",
            "status": "error",
            "result": result,
            "memo_updated": False,
        }
    
    memo_updated = apply_fundamental_result(db, code, result)
    return {
        "stock_code": code,
        "agent": "fundamental_agent",
        "status": "success",
        "result": result,
        "memo_updated": memo_updated,
    }


@router.post("/{code}/news", response_model=Dict[str, Any])
def analyze_news(code: str, db: Session = Depends(get_db)):
    """触发 NewsAgent 消息分析（含多空辩论），结果写入备忘录和事件列表"""
    _check_watchlist(db, code)
    
    # 获取股票名称用于 prompt
    wl = db.query(Watchlist).filter(Watchlist.stock_code == code, Watchlist.is_watched == True).first()
    stock_name = wl.stock_name or "" if wl else ""
    
    agent = NewsAgent(_get_llm())
    result = agent.analyze(code, stock_name)
    
    if "error" in result:
        return {
            "stock_code": code,
            "agent": "news_agent",
            "status": "error",
            "result": result,
            "memo_updated": False,
        }
    
    memo_updated = apply_news_result(db, code, result)
    return {
        "stock_code": code,
        "agent": "news_agent",
        "status": "success",
        "result": result,
        "memo_updated": memo_updated,
    }


@router.post("/{code}/technical", response_model=Dict[str, Any])
def analyze_technical(code: str, db: Session = Depends(get_db)):
    """触发 TechnicalAgent 技术分析，结果写入投资备忘录"""
    _check_watchlist(db, code)
    
    agent = TechnicalAgent(_get_llm(), _get_tushare())
    result = agent.analyze(code)
    
    if "error" in result:
        return {
            "stock_code": code,
            "agent": "technical_agent",
            "status": "error",
            "result": result,
            "memo_updated": False,
        }
    
    memo_updated = apply_technical_result(db, code, result)
    return {
        "stock_code": code,
        "agent": "technical_agent",
        "status": "success",
            "result": result,
            "memo_updated": memo_updated,
    }
