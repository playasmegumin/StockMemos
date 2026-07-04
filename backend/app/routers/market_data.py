"""行情数据 API

Endpoints:
    GET    /api/stocks/{id}/price             — 实时行情
    GET    /api/stocks/{id}/kline             — 日 K 线
    GET    /api/stocks/{id}/fundamentals      — 基本面数据
    POST   /api/market/refresh               — 批量刷新日K+基本面
    POST   /api/market/refresh-fundamentals  — 仅批量刷新基本面
"""

from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.stock import Stock
from app.services.market_data.market_data_service import MarketDataService
from app.services.market_data.schemas import CurrentPrice, DailyKline, Fundamentals

router = APIRouter()


# ────────────────────────────────
# 实时行情
# ────────────────────────────────

@router.get("/stocks/{id}/price", response_model=CurrentPrice)
def get_current_price(id: str, db: Session = Depends(get_db)):
    """获取实时行情（纯内存，不落盘）"""
    stock = db.query(Stock).filter(Stock.id == id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="个股不存在")

    service = MarketDataService(db)
    price = service.get_current_price(id)
    if price is None:
        raise HTTPException(status_code=502, detail="获取行情失败")
    return price


# ────────────────────────────────
# 日 K 线
# ────────────────────────────────

@router.get("/stocks/{id}/kline", response_model=List[DailyKline])
def get_daily_kline(
    id: str,
    start: Optional[date] = None,
    end: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """获取日 K 线（DB 持久化）"""
    stock = db.query(Stock).filter(Stock.id == id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="个股不存在")

    service = MarketDataService(db)
    klines = service.get_daily_kline(id, start_date=start, end_date=end)
    return klines


# ────────────────────────────────
# 基本面数据
# ────────────────────────────────

@router.get("/stocks/{id}/fundamentals", response_model=Fundamentals)
def get_fundamentals(id: str, db: Session = Depends(get_db)):
    """获取基本面数据（DB 持久化）"""
    stock = db.query(Stock).filter(Stock.id == id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="个股不存在")

    service = MarketDataService(db)
    fundamentals = service.get_fundamentals(id)
    if fundamentals is None:
        raise HTTPException(status_code=404, detail="暂无基本面数据")
    return fundamentals


# ────────────────────────────────
# 批量刷新
# ────────────────────────────────

@router.post("/market/refresh", status_code=status.HTTP_200_OK)
def refresh_all(db: Session = Depends(get_db)):
    """批量刷新所有股票日 K + 基本面"""
    service = MarketDataService(db)
    stats = service.refresh_all()
    return {
        "message": "批量刷新完成",
        "stats": stats,
    }


@router.post("/market/refresh-fundamentals", status_code=status.HTTP_200_OK)
def refresh_fundamentals(db: Session = Depends(get_db)):
    """仅批量刷新所有股票基本面"""
    service = MarketDataService(db)
    stats = service.refresh_fundamentals()
    return {
        "message": "基本面刷新完成",
        "stats": stats,
    }
