"""个股 CRUD API

Endpoints:
    POST   /api/stocks              — 创建个股
    GET    /api/stocks               — 获取个股列表
    GET    /api/stocks/{id}          — 获取单条个股
    PUT    /api/stocks/{id}          — 更新个股
    DELETE /api/stocks/{id}          — 删除个股（级联删交易记录）
"""

from typing import List
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.stock import Stock
from app.schemas.stock import StockCreate, StockUpdate, StockResponse

router = APIRouter()


# ────────────────────────────────
# 辅助函数：ORM → Pydantic 响应转换
# ────────────────────────────────

def _to_stock_response(item: Stock) -> StockResponse:
    """将 Stock ORM 对象转换为 Pydantic 响应（处理 Decimal）"""
    return StockResponse(
        id=item.id,
        exchange=item.exchange,
        symbol=item.symbol,
        name=item.name,
        currency=item.currency,
        position=float(item.position) if item.position is not None else 0.0,
        historical_pnl=float(item.historical_pnl) if item.historical_pnl is not None else 0.0,
        created_at=str(item.created_at) if item.created_at else None,
        updated_at=str(item.updated_at) if item.updated_at else None,
    )


# ────────────────────────────────
# 创建个股
# ────────────────────────────────

@router.post("", response_model=StockResponse, status_code=status.HTTP_201_CREATED)
def create_stock(data: StockCreate, db: Session = Depends(get_db)):
    """录入新个股（exchange + symbol 必须唯一）"""
    existing = db.query(Stock).filter(
        Stock.exchange == data.exchange,
        Stock.symbol == data.symbol
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"该股票已存在：{data.exchange}/{data.symbol}"
        )

    db_item = Stock(
        id=str(uuid4()),
        exchange=data.exchange,
        symbol=data.symbol,
        name=data.name,
        currency=data.currency,
        position=0,
        historical_pnl=0,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return _to_stock_response(db_item)


# ────────────────────────────────
# 获取个股列表
# ────────────────────────────────

@router.get("", response_model=List[StockResponse])
def list_stocks(db: Session = Depends(get_db)):
    """获取所有个股"""
    items = db.query(Stock).order_by(Stock.created_at.desc()).all()
    return [_to_stock_response(i) for i in items]


# ────────────────────────────────
# 获取单条个股
# ────────────────────────────────

@router.get("/{id}", response_model=StockResponse)
def get_stock(id: str, db: Session = Depends(get_db)):
    """获取单条个股详情"""
    item = db.query(Stock).filter(Stock.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="个股不存在")
    return _to_stock_response(item)


# ────────────────────────────────
# 更新个股
# ────────────────────────────────

@router.put("/{id}", response_model=StockResponse)
def update_stock(id: str, data: StockUpdate, db: Session = Depends(get_db)):
    """更新个股基本信息（exchange + symbol 组合不能与其他记录冲突）"""
    item = db.query(Stock).filter(Stock.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="个股不存在")

    new_exchange = data.exchange if data.exchange is not None else item.exchange
    new_symbol = data.symbol if data.symbol is not None else item.symbol

    # 检查新组合是否与其他记录冲突
    if new_exchange != item.exchange or new_symbol != item.symbol:
        conflict = db.query(Stock).filter(
            Stock.exchange == new_exchange,
            Stock.symbol == new_symbol,
            Stock.id != id
        ).first()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"该股票已存在：{new_exchange}/{new_symbol}"
            )

    if data.exchange is not None:
        item.exchange = data.exchange
    if data.symbol is not None:
        item.symbol = data.symbol
    if data.name is not None:
        item.name = data.name
    if data.currency is not None:
        item.currency = data.currency

    db.commit()
    db.refresh(item)
    return _to_stock_response(item)


# ────────────────────────────────
# 删除个股
# ────────────────────────────────

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stock(id: str, db: Session = Depends(get_db)):
    """删除个股（级联删除关联交易记录）"""
    item = db.query(Stock).filter(Stock.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="个股不存在")
    db.delete(item)
    db.commit()
    return None
