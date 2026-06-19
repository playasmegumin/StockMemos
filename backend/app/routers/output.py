"""输出与投递 API

Endpoints:
    GET  /api/output/memos          — 获取自选股备忘录报告（?format=markdown|json|rss）
    GET  /api/output/strategy-signals — 获取策略信号报告（?format=markdown|json|rss）
    POST /api/output/email/memos     — 发送备忘录日报邮件

"""

from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.models.investment_memo import InvestmentMemo
from app.models.watchlist import Watchlist
from app.models.strategy_signal import StrategySignal
from app.models.strategy import Strategy
from app.services.report_generator import generate_memo_report, generate_strategy_report
from app.services.email_service import EmailService

router = APIRouter()


@router.get("/memos")
def get_memo_report(format: str = Query("markdown", enum=["markdown", "json", "rss"]), db: Session = Depends(get_db)):
    """获取自选股备忘录报告"""
    # 获取所有在关注列表中的股票及其备忘录
    watchlist_items = db.query(Watchlist).filter(Watchlist.is_watched == True).all()
    watchlist_data = [{"stock_code": w.stock_code, "stock_name": w.stock_name} for w in watchlist_items]

    memos = db.query(InvestmentMemo).filter(
        InvestmentMemo.stock_code.in_([w.stock_code for w in watchlist_items])
    ).all()

    memos_data = [{
        "id": m.id,
        "stock_code": m.stock_code,
        "target_price": float(m.target_price) if m.target_price else None,
        "valuation_method": m.valuation_method,
        "business_scope": m.business_scope,
        "short_trend": m.short_trend,
        "mid_trend": m.mid_trend,
        "long_trend": m.long_trend,
        "trend_logic": m.trend_logic,
        "notes": m.notes,
        "last_updated_by": m.last_updated_by,
    } for m in memos]

    content = generate_memo_report(memos_data, watchlist_data, format=format)

    media_types = {
        "markdown": "text/markdown; charset=utf-8",
        "json": "application/json; charset=utf-8",
        "rss": "application/rss+xml; charset=utf-8",
    }

    return Response(content=content, media_type=media_types.get(format, "text/plain"))


@router.get("/strategy-signals")
def get_strategy_signal_report(
    format: str = Query("markdown", enum=["markdown", "json", "rss"]),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """获取策略信号报告"""
    signals = db.query(StrategySignal).order_by(StrategySignal.signal_date.desc()).limit(limit).all()
    strategies = db.query(Strategy).all()

    signals_data = [{
        "id": s.id,
        "strategy_id": s.strategy_id,
        "stock_code": s.stock_code,
        "signal_date": str(s.signal_date),
        "signal_type": s.signal_type,
        "raw_data": s.raw_data,
    } for s in signals]

    strategies_data = [{"id": s.id, "name": s.name} for s in strategies]

    content = generate_strategy_report(signals_data, strategies_data, format=format)

    media_types = {
        "markdown": "text/markdown; charset=utf-8",
        "json": "application/json; charset=utf-8",
        "rss": "application/rss+xml; charset=utf-8",
    }

    return Response(content=content, media_type=media_types.get(format, "text/plain"))


@router.post("/email/memos")
def email_memo_report(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """发送备忘录日报邮件

    Payload:
        {
            "to": ["user@example.com"],
            "subject_prefix": "可选前缀"
        }
    """
    to = payload.get("to", [])
    if not to:
        return {"status": "error", "message": "收件人列表不能为空"}

    watchlist_items = db.query(Watchlist).filter(Watchlist.is_watched == True).all()
    watchlist_data = [{"stock_code": w.stock_code, "stock_name": w.stock_name} for w in watchlist_items]

    memos = db.query(InvestmentMemo).filter(
        InvestmentMemo.stock_code.in_([w.stock_code for w in watchlist_items])
    ).all()

    memos_data = [{
        "id": m.id,
        "stock_code": m.stock_code,
        "target_price": float(m.target_price) if m.target_price else None,
        "valuation_method": m.valuation_method,
        "business_scope": m.business_scope,
        "short_trend": m.short_trend,
        "mid_trend": m.mid_trend,
        "long_trend": m.long_trend,
        "trend_logic": m.trend_logic,
        "notes": m.notes,
        "last_updated_by": m.last_updated_by,
    } for m in memos]

    service = EmailService()
    success = service.send_memo_report(to, memos_data, watchlist_data)

    return {
        "status": "sent" if success else "failed",
        "to": to,
        "memo_count": len(memos_data),
    }
