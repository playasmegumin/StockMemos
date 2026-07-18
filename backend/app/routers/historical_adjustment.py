"""历史盈亏调整 API

Endpoints:
    GET    /api/historical-adjustments      — 列表
    POST   /api/historical-adjustments      — 创建
    PUT    /api/historical-adjustments/{id}  — 更新
    DELETE /api/historical-adjustments/{id}  — 删除
"""

from typing import List
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.historical_adjustment import HistoricalAdjustment
from app.schemas.historical_adjustment import (
    HistoricalAdjustmentCreate,
    HistoricalAdjustmentUpdate,
    HistoricalAdjustmentResponse,
)

router = APIRouter()


# ─── 列表 ────────────────────────────────────


@router.get("", response_model=List[HistoricalAdjustmentResponse])
def list_adjustments(db: Session = Depends(get_db)):
    """获取所有历史盈亏调整记录（按创建时间降序）"""
    items = (
        db.query(HistoricalAdjustment)
        .order_by(HistoricalAdjustment.created_at.desc())
        .all()
    )
    return [
        HistoricalAdjustmentResponse(
            id=item.id,
            amount=float(item.amount),
            note=item.note,
            created_at=str(item.created_at) if item.created_at else None,
            updated_at=str(item.updated_at) if item.updated_at else None,
        )
        for item in items
    ]


# ─── 创建 ────────────────────────────────────


@router.post("", response_model=HistoricalAdjustmentResponse,
             status_code=status.HTTP_201_CREATED)
def create_adjustment(data: HistoricalAdjustmentCreate,
                      db: Session = Depends(get_db)):
    """创建一条历史盈亏调整记录"""
    db_item = HistoricalAdjustment(
        id=str(uuid4()),
        amount=data.amount,
        note=data.note,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return HistoricalAdjustmentResponse(
        id=db_item.id,
        amount=float(db_item.amount),
        note=db_item.note,
        created_at=str(db_item.created_at) if db_item.created_at else None,
        updated_at=str(db_item.updated_at) if db_item.updated_at else None,
    )


# ─── 更新 ────────────────────────────────────


@router.put("/{id}", response_model=HistoricalAdjustmentResponse)
def update_adjustment(id: str, data: HistoricalAdjustmentUpdate,
                      db: Session = Depends(get_db)):
    """更新一条历史盈亏调整记录"""
    item = db.query(HistoricalAdjustment).filter(
        HistoricalAdjustment.id == id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="历史盈亏调整记录不存在")
    item.amount = data.amount
    item.note = data.note
    db.commit()
    db.refresh(item)
    return HistoricalAdjustmentResponse(
        id=item.id,
        amount=float(item.amount),
        note=item.note,
        created_at=str(item.created_at) if item.created_at else None,
        updated_at=str(item.updated_at) if item.updated_at else None,
    )


# ─── 删除 ────────────────────────────────────


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_adjustment(id: str, db: Session = Depends(get_db)):
    """删除一条历史盈亏调整记录"""
    item = db.query(HistoricalAdjustment).filter(
        HistoricalAdjustment.id == id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="调整记录不存在")
    db.delete(item)
    db.commit()
    return None
