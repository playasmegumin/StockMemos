"""历史盈亏调整 Pydantic 请求/响应模型"""

import math
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


def _validate_amount(v: float) -> float:
    """Reject zero, NaN, and +/-Infinity."""
    if math.isnan(v) or math.isinf(v):
        raise ValueError("Amount must be a finite number")
    if v == 0:
        raise ValueError("Amount must not be zero")
    return v


class HistoricalAdjustmentCreate(BaseModel):
    """创建历史盈亏调整请求"""
    amount: float = Field(..., description="调整金额（正=盈利，负=亏损）")
    note: Optional[str] = Field(None, max_length=500, description="备注")

    _validate_amount = field_validator("amount")(_validate_amount)


class HistoricalAdjustmentUpdate(BaseModel):
    """更新历史盈亏调整请求"""
    amount: float = Field(..., description="调整金额（正=盈利，负=亏损）")
    note: Optional[str] = Field(None, max_length=500, description="备注")

    _validate_amount = field_validator("amount")(_validate_amount)


class HistoricalAdjustmentResponse(BaseModel):
    """历史盈亏调整响应"""
    id: str
    amount: float
    note: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
