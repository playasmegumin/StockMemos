"""自选股 + 投资备忘录 API

Endpoints:
    POST   /api/watchlist                    — 添加自选股
    GET    /api/watchlist                    — 获取自选股列表
    DELETE /api/watchlist/{id}               — 移除自选股
    GET    /api/watchlist/{code}/memo        — 获取某股票的备忘录
    PUT    /api/watchlist/{code}/memo        — 更新备忘录
    POST   /api/watchlist/{code}/memo/events — 添加事件
    GET    /api/watchlist/{code}/memo/events — 获取事件列表
    PUT    /api/watchlist/{code}/memo/events/{id} — 更新事件
    DELETE /api/watchlist/{code}/memo/events/{id} — 删除事件
"""

from typing import List
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.watchlist import Watchlist
from app.models.investment_memo import InvestmentMemo
from app.models.memo_event import MemoEvent
from app.schemas.watchlist import WatchlistCreate, WatchlistResponse
from app.schemas.investment_memo import InvestmentMemoCreate, InvestmentMemoResponse
from app.schemas.memo_event import MemoEventCreate, MemoEventResponse

router = APIRouter()


# ────────────────────────────────
# 辅助函数：ORM → Pydantic 转换
# ────────────────────────────────

def _to_watchlist_response(item: Watchlist) -> WatchlistResponse:
    return WatchlistResponse(
        id=item.id,
        stock_code=item.stock_code,
        stock_name=item.stock_name,
        sector=item.sector,
        market=item.market,
        is_watched=item.is_watched,
        memo_id=item.memo_id,
        created_at=str(item.created_at) if item.created_at else None,
        updated_at=str(item.updated_at) if item.updated_at else None,
    )


def _to_memo_response(item: InvestmentMemo) -> InvestmentMemoResponse:
    return InvestmentMemoResponse(
        id=item.id,
        stock_code=item.stock_code,
        target_price=float(item.target_price) if item.target_price is not None else None,
        valuation_method=item.valuation_method,
        business_scope=item.business_scope,
        short_trend=item.short_trend,
        mid_trend=item.mid_trend,
        long_trend=item.long_trend,
        trend_logic=item.trend_logic,
        notes=item.notes,
        last_updated_by=item.last_updated_by,
        created_at=str(item.created_at) if item.created_at else None,
        updated_at=str(item.updated_at) if item.updated_at else None,
    )


def _to_memo_event_response(item: MemoEvent) -> MemoEventResponse:
    return MemoEventResponse(
        id=item.id,
        memo_id=item.memo_id,
        event_name=item.event_name,
        event_type=item.event_type,
        impact_tag=item.impact_tag,
        expected_date=str(item.expected_date) if item.expected_date else None,
        actual_date=str(item.actual_date) if item.actual_date else None,
        result_status=item.result_status,
        result_summary=item.result_summary,
        source_url=item.source_url,
        agent_analysis=item.agent_analysis,
        created_at=str(item.created_at) if item.created_at else None,
        updated_at=str(item.updated_at) if item.updated_at else None,
    )


# ────────────────────────────────
# 自选股 CRUD
# ────────────────────────────────

@router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
def create_watchlist(data: WatchlistCreate, db: Session = Depends(get_db)):
    """添加自选股，自动创建空备忘录"""
    # 检查是否已存在
    existing = db.query(Watchlist).filter(Watchlist.stock_code == data.stock_code).first()
    if existing:
        raise HTTPException(status_code=409, detail="该股票已在自选股中")

    # 创建空备忘录
    memo = InvestmentMemo(
        id=str(uuid4()),
        stock_code=data.stock_code,
    )
    db.add(memo)
    db.flush()  # 获取 memo.id

    db_item = Watchlist(
        id=str(uuid4()),
        stock_code=data.stock_code,
        stock_name=data.stock_name,
        sector=data.sector,
        market=data.market,
        memo_id=memo.id,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return _to_watchlist_response(db_item)


@router.get("", response_model=List[WatchlistResponse])
def list_watchlist(db: Session = Depends(get_db)):
    """获取自选股列表"""
    items = db.query(Watchlist).filter(Watchlist.is_watched == True).order_by(Watchlist.created_at.desc()).all()
    return [_to_watchlist_response(i) for i in items]


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist(id: str, db: Session = Depends(get_db)):
    """移除自选股（软删除：标记 is_watched=False）"""
    item = db.query(Watchlist).filter(Watchlist.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="自选股不存在")
    item.is_watched = False
    db.commit()
    return None


# ────────────────────────────────
# 投资备忘录
# ────────────────────────────────

@router.get("/{code}/memo", response_model=InvestmentMemoResponse)
def get_memo(code: str, db: Session = Depends(get_db)):
    """获取某股票的备忘录"""
    watchlist_item = db.query(Watchlist).filter(Watchlist.stock_code == code, Watchlist.is_watched == True).first()
    if not watchlist_item:
        raise HTTPException(status_code=404, detail="该股票不在自选股中")
    
    memo = db.query(InvestmentMemo).filter(InvestmentMemo.id == watchlist_item.memo_id).first()
    if not memo:
        raise HTTPException(status_code=404, detail="备忘录不存在")
    return _to_memo_response(memo)


@router.put("/{code}/memo", response_model=InvestmentMemoResponse)
def update_memo(code: str, data: InvestmentMemoCreate, db: Session = Depends(get_db)):
    """更新备忘录（用户手动编辑）"""
    watchlist_item = db.query(Watchlist).filter(Watchlist.stock_code == code, Watchlist.is_watched == True).first()
    if not watchlist_item:
        raise HTTPException(status_code=404, detail="该股票不在自选股中")
    
    memo = db.query(InvestmentMemo).filter(InvestmentMemo.id == watchlist_item.memo_id).first()
    if not memo:
        raise HTTPException(status_code=404, detail="备忘录不存在")
    
    memo.target_price = data.target_price
    memo.valuation_method = data.valuation_method
    memo.business_scope = data.business_scope
    memo.short_trend = data.short_trend
    memo.mid_trend = data.mid_trend
    memo.long_trend = data.long_trend
    memo.trend_logic = data.trend_logic
    memo.notes = data.notes
    memo.last_updated_by = "user"
    
    db.commit()
    db.refresh(memo)
    return _to_memo_response(memo)


# ────────────────────────────────
# 备忘录事件
# ────────────────────────────────

@router.post("/{code}/memo/events", response_model=MemoEventResponse, status_code=status.HTTP_201_CREATED)
def create_memo_event(code: str, data: MemoEventCreate, db: Session = Depends(get_db)):
    """为某股票的备忘录添加事件"""
    watchlist_item = db.query(Watchlist).filter(Watchlist.stock_code == code, Watchlist.is_watched == True).first()
    if not watchlist_item:
        raise HTTPException(status_code=404, detail="该股票不在自选股中")
    
    db_item = MemoEvent(
        id=str(uuid4()),
        memo_id=watchlist_item.memo_id,
        event_name=data.event_name,
        event_type=data.event_type,
        impact_tag=data.impact_tag,
        expected_date=data.expected_date,
        actual_date=data.actual_date,
        result_status=data.result_status or "pending",
        result_summary=data.result_summary,
        source_url=data.source_url,
        agent_analysis=data.agent_analysis,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return _to_memo_event_response(db_item)


@router.get("/{code}/memo/events", response_model=List[MemoEventResponse])
def list_memo_events(code: str, db: Session = Depends(get_db)):
    """获取某股票备忘录的事件列表"""
    watchlist_item = db.query(Watchlist).filter(Watchlist.stock_code == code, Watchlist.is_watched == True).first()
    if not watchlist_item:
        raise HTTPException(status_code=404, detail="该股票不在自选股中")
    
    items = db.query(MemoEvent).filter(MemoEvent.memo_id == watchlist_item.memo_id).order_by(MemoEvent.created_at.desc()).all()
    return [_to_memo_event_response(i) for i in items]


@router.put("/{code}/memo/events/{id}", response_model=MemoEventResponse)
def update_memo_event(code: str, id: str, data: MemoEventCreate, db: Session = Depends(get_db)):
    """更新备忘录事件（标记结果等）"""
    item = db.query(MemoEvent).filter(MemoEvent.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="事件不存在")
    
    item.event_name = data.event_name
    item.event_type = data.event_type
    item.impact_tag = data.impact_tag
    item.expected_date = data.expected_date
    item.actual_date = data.actual_date
    item.result_status = data.result_status or item.result_status
    item.result_summary = data.result_summary
    item.source_url = data.source_url
    item.agent_analysis = data.agent_analysis
    
    db.commit()
    db.refresh(item)
    return _to_memo_event_response(item)


@router.delete("/{code}/memo/events/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memo_event(code: str, id: str, db: Session = Depends(get_db)):
    """删除备忘录事件"""
    item = db.query(MemoEvent).filter(MemoEvent.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="事件不存在")
    db.delete(item)
    db.commit()
    return None
