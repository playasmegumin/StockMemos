"""Agent Orchestrator — 将 Agent 分析结果写入投资备忘录

职责：
- 将 FundamentalAgent 结果 → 更新 InvestmentMemo（target_price, valuation_method, business_scope）
- 将 NewsAgent 结果 → 更新 InvestmentMemo（notes）+ 创建/更新 MemoEvent
- 将 TechnicalAgent 结果 → 更新 InvestmentMemo（short_trend, mid_trend, long_trend, trend_logic）

注意：每个函数内部负责 DB 事务，调用方需要确保 db session 已 commit。
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4
from sqlalchemy.orm import Session
from app.models.watchlist import Watchlist
from app.models.investment_memo import InvestmentMemo
from app.models.memo_event import MemoEvent

logger = logging.getLogger(__name__)


def _get_memo(db: Session, stock_code: str) -> Optional[InvestmentMemo]:
    """通过股票代码获取其备忘录（需该股票在 watchlist 中）"""
    watchlist_item = db.query(Watchlist).filter(
        Watchlist.stock_code == stock_code,
        Watchlist.is_watched == True
    ).first()
    if not watchlist_item:
        logger.warning("[Orchestrator] %s 不在自选股中，无法更新备忘录", stock_code)
        return None
    
    memo = db.query(InvestmentMemo).filter(
        InvestmentMemo.id == watchlist_item.memo_id
    ).first()
    if not memo:
        logger.warning("[Orchestrator] %s 的备忘录不存在", stock_code)
        return None
    return memo


def apply_fundamental_result(db: Session, stock_code: str, result: Dict[str, Any]) -> bool:
    """将 FundamentalAgent 分析结果写入投资备忘录

    更新字段：
    - target_price（如果有且是数字）
    - valuation_method
    - business_scope
    - last_updated_by = "fundamental_agent"

    Args:
        db: SQLAlchemy Session
        stock_code: 股票代码
        result: FundamentalAgent.analyze() 返回的 JSON 字典

    Returns:
        True 如果成功，False 如果失败
    """
    memo = _get_memo(db, stock_code)
    if not memo:
        return False

    try:
        # 目标价格（数字或 null）
        tp = result.get("target_price")
        if tp is not None and isinstance(tp, (int, float)):
            memo.target_price = float(tp)
        
        memo.valuation_method = result.get("valuation_method") or memo.valuation_method
        memo.business_scope = result.get("business_scope") or memo.business_scope
        memo.last_updated_by = "fundamental_agent"
        
        db.commit()
        logger.info("[Orchestrator] FundamentalAgent 结果已写入 %s 的备忘录", stock_code)
        return True
    except Exception as e:
        logger.error("[Orchestrator] 写入 FundamentalAgent 结果失败: %s", e)
        return False


def apply_technical_result(db: Session, stock_code: str, result: Dict[str, Any]) -> bool:
    """将 TechnicalAgent 分析结果写入投资备忘录

    更新字段：
    - short_trend, mid_trend, long_trend
    - trend_logic
    - last_updated_by = "technical_agent"

    Args:
        db: SQLAlchemy Session
        stock_code: 股票代码
        result: TechnicalAgent.analyze() 返回的 JSON 字典

    Returns:
        True 如果成功，False 如果失败
    """
    memo = _get_memo(db, stock_code)
    if not memo:
        return False

    try:
        for field in ["short_trend", "mid_trend", "long_trend"]:
            val = result.get(field)
            if val:
                setattr(memo, field, val)
        
        memo.trend_logic = result.get("trend_logic") or memo.trend_logic
        memo.last_updated_by = "technical_agent"
        
        db.commit()
        logger.info("[Orchestrator] TechnicalAgent 结果已写入 %s 的备忘录", stock_code)
        return True
    except Exception as e:
        logger.error("[Orchestrator] 写入 TechnicalAgent 结果失败: %s", e)
        return False


def apply_news_result(db: Session, stock_code: str, result: Dict[str, Any]) -> bool:
    """将 NewsAgent 分析结果写入投资备忘录和事件列表

    更新字段：
    - InvestmentMemo.notes: 附加综合判断（不覆盖用户笔记，追加）
    - MemoEvent: 创建或更新事件（根据 event_name 去重）

    Args:
        db: SQLAlchemy Session
        stock_code: 股票代码
        result: NewsAgent.analyze() 返回的 JSON 字典

    Returns:
        True 如果成功，False 如果失败
    """
    memo = _get_memo(db, stock_code)
    if not memo:
        return False

    try:
        # 1. 更新备忘录 notes（追加 Agent 综合判断）
        consensus = result.get("consensus", "")
        recommendation = result.get("recommendation", "")
        reasoning = result.get("reasoning", "")
        agent_note = f"""
[NewsAgent 分析] {datetime.now().strftime('%Y-%m-%d %H:%M')}
综合判断：{consensus}
推荐：{recommendation}
分析：{reasoning}
""".strip()

        existing_notes = memo.notes or ""
        memo.notes = f"{existing_notes}\n\n---\n{agent_note}".strip()

        # 2. 处理事件列表
        events = result.get("events", [])
        if not isinstance(events, list):
            events = []
        
        for evt in events:
            if not isinstance(evt, dict):
                continue
            event_name = evt.get("name") or evt.get("event_name")
            if not event_name:
                continue
            
            # 查找是否已存在同名事件
            existing_event = db.query(MemoEvent).filter(
                MemoEvent.memo_id == memo.id,
                MemoEvent.event_name == event_name
            ).first()
            
            expected_date_str = evt.get("expected_date")
            expected_date = None
            if expected_date_str and isinstance(expected_date_str, str):
                try:
                    expected_date = datetime.strptime(expected_date_str, "%Y-%m-%d").date()
                except ValueError:
                    pass
            
            impact_tag = evt.get("impact_tag")
            if impact_tag not in ["bullish", "bearish", "neutral"]:
                impact_tag = "neutral"
            
            event_type = "other"
            if "earnings" in event_name.lower() or "财报" in event_name:
                event_type = "earnings"
            elif "order" in event_name.lower() or "订单" in event_name:
                event_type = "order"
            elif "policy" in event_name.lower() or "政策" in event_name:
                event_type = "policy"
            
            if existing_event:
                # 更新已有事件
                existing_event.impact_tag = impact_tag
                existing_event.expected_date = expected_date or existing_event.expected_date
                existing_event.agent_analysis = evt.get("reasoning", "")
                existing_event.result_status = "pending"
            else:
                # 创建新事件
                new_event = MemoEvent(
                    id=str(uuid4()),
                    memo_id=memo.id,
                    event_name=event_name,
                    event_type=event_type,
                    impact_tag=impact_tag,
                    expected_date=expected_date,
                    result_status="pending",
                    agent_analysis=evt.get("reasoning", ""),
                )
                db.add(new_event)
        
        db.commit()
        logger.info("[Orchestrator] NewsAgent 结果已写入 %s 的备忘录（%d 个事件）", stock_code, len(events))
        return True
    except Exception as e:
        logger.error("[Orchestrator] 写入 NewsAgent 结果失败: %s", e)
        return False
