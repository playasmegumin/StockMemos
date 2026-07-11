"""资金管理 API

Endpoints:
    GET    /api/capital/summary        — 资金汇总
    GET    /api/capital/flows          — 流水列表
    POST   /api/capital/flows          — 添加流水
    DELETE /api/capital/flows/{id}     — 删除流水
"""

from typing import List, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.capital_flow import CapitalFlow
from app.models.capital_meta import CapitalMeta
from app.models.exchange_rate import ExchangeRate
from app.schemas.capital import (
    CapitalFlowCreate,
    CapitalFlowResponse,
    CapitalSummaryResponse,
)

router = APIRouter()


# ─── 资金汇总 ────────────────────────────────────


@router.get("/summary", response_model=CapitalSummaryResponse)
def get_capital_summary(db: Session = Depends(get_db)):
    """获取资金汇总数据"""
    meta = db.query(CapitalMeta).filter(CapitalMeta.id == 1).first()
    if not meta:
        return CapitalSummaryResponse()
    return CapitalSummaryResponse(
        total_invested_cny=float(meta.total_invested_cny),
        total_historical_pnl_cny=float(meta.total_historical_pnl_cny),
        total_position_value_cny=float(meta.total_position_value_cny),
    )


# ─── 流水列表 ────────────────────────────────────


@router.get("/flows", response_model=List[CapitalFlowResponse])
def list_capital_flows(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """获取现金流水列表（按创建时间降序）"""
    items = (
        db.query(CapitalFlow)
        .order_by(CapitalFlow.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        CapitalFlowResponse(
            id=item.id,
            type=item.type,
            amount=float(item.amount),
            currency=item.currency,
            note=item.note,
            created_at=str(item.created_at) if item.created_at else None,
        )
        for item in items
    ]


# ─── 添加流水 ────────────────────────────────────


@router.post("/flows", response_model=CapitalFlowResponse,
             status_code=status.HTTP_201_CREATED)
def create_capital_flow(data: CapitalFlowCreate, db: Session = Depends(get_db)):
    """添加资金流水记录

    用户永远填写正数，后端根据 type 转换符号：
    - deposit: amount 保持正数
    - withdraw: amount 转负数
    - fee: amount 转负数
    """
    signed_amount = data.amount
    if data.type in ("withdraw", "fee"):
        signed_amount = -data.amount

    db_item = CapitalFlow(
        id=str(uuid4()),
        type=data.type,
        amount=signed_amount,
        currency=data.currency or "CNY",
        note=data.note,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # DB trigger recalc_invested() 自动触发
    return CapitalFlowResponse(
        id=db_item.id,
        type=db_item.type,
        amount=float(db_item.amount),
        currency=db_item.currency,
        note=db_item.note,
        created_at=str(db_item.created_at) if db_item.created_at else None,
    )


# ─── 删除流水 ────────────────────────────────────


@router.delete("/flows/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_capital_flow(id: str, db: Session = Depends(get_db)):
    """删除一条资金流水记录"""
    item = db.query(CapitalFlow).filter(CapitalFlow.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="流水记录不存在")
    db.delete(item)
    db.commit()
    # DB trigger recalc_invested() 自动触发
    return None


# ─── 汇率配置 ────────────────────────────────────


@router.get("/exchange-rates")
def list_exchange_rates(db: Session = Depends(get_db)):
    """获取所有汇率配置"""
    rates = db.query(ExchangeRate).all()
    return [
        {
            "currency": r.currency,
            "rate_to_cny": float(r.rate_to_cny),
            "updated_at": str(r.updated_at) if r.updated_at else None,
        }
        for r in rates
    ]


@router.put("/exchange-rates/{currency}")
def update_exchange_rate(currency: str, body: dict, db: Session = Depends(get_db)):
    """更新指定币种汇率"""
    rate = body.get("rate_to_cny")
    if rate is None or rate <= 0:
        raise HTTPException(status_code=400, detail="rate_to_cny 必须为正数")
    item = db.query(ExchangeRate).filter(ExchangeRate.currency == currency.upper()).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"币种 {currency} 不存在")
    item.rate_to_cny = rate
    db.commit()
    db.refresh(item)
    return {
        "currency": item.currency,
        "rate_to_cny": float(item.rate_to_cny),
        "updated_at": str(item.updated_at) if item.updated_at else None,
    }
