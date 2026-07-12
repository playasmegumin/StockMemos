"""投资备忘 API

Endpoints:
    GET    /api/memos            — 备忘列表（可选 ?stock_id= 过滤）
    GET    /api/memos/{id}       — 单条备忘
    POST   /api/memos            — 创建备忘
    PUT    /api/memos/{id}       — 更新备忘
    DELETE /api/memos/{id}       — 删除备忘
"""

from typing import List, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.investment_memo import InvestmentMemo
from app.schemas.investment_memo import (
    InvestmentMemoCreate,
    InvestmentMemoUpdate,
    InvestmentMemoResponse,
    InvestmentMemoListItem,
)

router = APIRouter()


def _to_response(memo: InvestmentMemo) -> InvestmentMemoResponse:
    return InvestmentMemoResponse(
        id=memo.id,
        title=memo.title,
        content=memo.content,
        stock_id=memo.stock_id,
        created_at=str(memo.created_at) if memo.created_at else None,
        updated_at=str(memo.updated_at) if memo.updated_at else None,
    )


def _to_list_item(memo: InvestmentMemo) -> InvestmentMemoListItem:
    return InvestmentMemoListItem(
        id=memo.id,
        title=memo.title,
        stock_id=memo.stock_id,
        created_at=str(memo.created_at) if memo.created_at else None,
        updated_at=str(memo.updated_at) if memo.updated_at else None,
    )


# ─── 列表 ────────────────────────────────────────


@router.get("", response_model=List[InvestmentMemoListItem])
def list_memos(
    stock_id: Optional[str] = Query(None, description="按个股过滤"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取投资备忘列表（按创建时间降序）"""
    q = db.query(InvestmentMemo).order_by(InvestmentMemo.created_at.desc())
    if stock_id:
        q = q.filter(InvestmentMemo.stock_id == stock_id)
    items = q.offset(offset).limit(limit).all()
    return [_to_list_item(m) for m in items]


# ─── 单条详情 ────────────────────────────────────


@router.get("/{id}", response_model=InvestmentMemoResponse)
def get_memo(id: str, db: Session = Depends(get_db)):
    """获取单条投资备忘"""
    memo = db.query(InvestmentMemo).filter(InvestmentMemo.id == id).first()
    if not memo:
        raise HTTPException(status_code=404, detail="备忘不存在")
    return _to_response(memo)


# ─── 创建 ───────────────────────────────────────


@router.post("", response_model=InvestmentMemoResponse,
             status_code=status.HTTP_201_CREATED)
def create_memo(data: InvestmentMemoCreate, db: Session = Depends(get_db)):
    """创建投资备忘"""
    memo = InvestmentMemo(
        id=str(uuid4()),
        title=data.title,
        content=data.content,
        stock_id=data.stock_id or None,
    )
    db.add(memo)
    db.commit()
    db.refresh(memo)
    return _to_response(memo)


# ─── 更新 ───────────────────────────────────────


@router.put("/{id}", response_model=InvestmentMemoResponse)
def update_memo(id: str, data: InvestmentMemoUpdate,
                db: Session = Depends(get_db)):
    """更新投资备忘"""
    memo = db.query(InvestmentMemo).filter(InvestmentMemo.id == id).first()
    if not memo:
        raise HTTPException(status_code=404, detail="备忘不存在")

    if data.title is not None:
        memo.title = data.title
    if data.content is not None:
        memo.content = data.content
    update_data = data.model_dump(exclude_unset=True)
    if "stock_id" in update_data:
        memo.stock_id = data.stock_id if data.stock_id else None

    db.commit()
    db.refresh(memo)
    return _to_response(memo)


# ─── 删除 ───────────────────────────────────────


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memo(id: str, db: Session = Depends(get_db)):
    """删除投资备忘"""
    memo = db.query(InvestmentMemo).filter(InvestmentMemo.id == id).first()
    if not memo:
        raise HTTPException(status_code=404, detail="备忘不存在")
    db.delete(memo)
    db.commit()
    return None
