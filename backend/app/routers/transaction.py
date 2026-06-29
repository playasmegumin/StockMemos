"""交易记录 CRUD API

Endpoints:
    POST   /api/transactions                    — 创建交易记录
    GET    /api/transactions                    — 获取所有交易记录
    GET    /api/transactions/{id}              — 获取单条交易记录
    GET    /api/transactions/stock/{stock_id}  — 获取某个股的所有交易记录
    PUT    /api/transactions/{id}              — 更新交易记录
    DELETE /api/transactions/{id}              — 删除交易记录
"""

from typing import List
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.stock import Stock
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionResponse

router = APIRouter()


# ────────────────────────────────
# 辅助函数
# ────────────────────────────────

def _to_transaction_response(item: Transaction) -> TransactionResponse:
    """将 Transaction ORM 对象转换为 Pydantic 响应（处理 Decimal / datetime）"""
    return TransactionResponse(
        id=item.id,
        stock_id=item.stock_id,
        quantity=float(item.quantity),
        price=float(item.price),
        gas=float(item.gas),
        traded_at=item.traded_at,
        created_at=str(item.created_at) if item.created_at else None,
    )


def _recalc_stock(stock_id: str, db: Session):
    """重新计算某个股的 position 和 historical_pnl"""
    result = db.query(
        func.sum(Transaction.quantity).label("total_qty"),
        func.sum(-(Transaction.quantity * Transaction.price + Transaction.gas)).label("total_pnl")
    ).filter(Transaction.stock_id == stock_id).first()

    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if stock:
        stock.position = float(result.total_qty) if result.total_qty is not None else 0.0
        stock.historical_pnl = float(result.total_pnl) if result.total_pnl is not None else 0.0
        db.commit()


# ────────────────────────────────
# 创建交易记录
# ────────────────────────────────

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(data: TransactionCreate, db: Session = Depends(get_db)):
    """创建交易记录，并自动更新对应个股的 position 和 historical_pnl"""
    # 验证关联个股存在
    stock = db.query(Stock).filter(Stock.id == data.stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="关联个股不存在")

    db_item = Transaction(
        id=str(uuid4()),
        stock_id=data.stock_id,
        quantity=data.quantity,
        price=data.price,
        gas=data.gas,
        traded_at=data.traded_at,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # 重新计算该个股的持仓与历史盈亏
    _recalc_stock(data.stock_id, db)

    return _to_transaction_response(db_item)


# ────────────────────────────────
# 获取所有交易记录
# ────────────────────────────────

@router.get("", response_model=List[TransactionResponse])
def list_transactions(db: Session = Depends(get_db)):
    """获取所有交易记录"""
    items = db.query(Transaction).order_by(Transaction.traded_at.desc()).all()
    return [_to_transaction_response(i) for i in items]


# ────────────────────────────────
# 获取单条交易记录
# ────────────────────────────────

@router.get("/{id}", response_model=TransactionResponse)
def get_transaction(id: str, db: Session = Depends(get_db)):
    """获取单条交易记录详情"""
    item = db.query(Transaction).filter(Transaction.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="交易记录不存在")
    return _to_transaction_response(item)


# ────────────────────────────────
# 获取某个股的所有交易记录
# ────────────────────────────────

@router.get("/stock/{stock_id}", response_model=List[TransactionResponse])
def list_stock_transactions(stock_id: str, db: Session = Depends(get_db)):
    """获取某个股的所有交易记录"""
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="个股不存在")
    items = (
        db.query(Transaction)
        .filter(Transaction.stock_id == stock_id)
        .order_by(Transaction.traded_at.desc())
        .all()
    )
    return [_to_transaction_response(i) for i in items]


# ────────────────────────────────
# 更新交易记录
# ────────────────────────────────

@router.put("/{id}", response_model=TransactionResponse)
def update_transaction(id: str, data: TransactionUpdate, db: Session = Depends(get_db)):
    """更新交易记录，并重新计算对应个股"""
    item = db.query(Transaction).filter(Transaction.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="交易记录不存在")

    stock_id = item.stock_id

    if data.quantity is not None:
        item.quantity = data.quantity
    if data.price is not None:
        item.price = data.price
    if data.gas is not None:
        item.gas = data.gas
    if data.traded_at is not None:
        item.traded_at = data.traded_at

    db.commit()
    db.refresh(item)

    # 重新计算该个股
    _recalc_stock(stock_id, db)

    return _to_transaction_response(item)


# ────────────────────────────────
# 删除交易记录
# ────────────────────────────────

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(id: str, db: Session = Depends(get_db)):
    """删除交易记录，并重新计算对应个股"""
    item = db.query(Transaction).filter(Transaction.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="交易记录不存在")

    stock_id = item.stock_id

    db.delete(item)
    db.commit()

    # 重新计算该个股
    _recalc_stock(stock_id, db)

    return None
