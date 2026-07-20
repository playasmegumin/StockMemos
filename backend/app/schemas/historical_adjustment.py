"""历史盈亏调整 Pydantic 请求/响应模型"""

import math
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


ALLOWED_CURRENCIES = {"CNY", "HKD", "USD"}


def _validate_amount(v: float) -> float:
    """Reject zero, NaN, and +/-Infinity."""
    if math.isnan(v) or math.isinf(v):
        raise ValueError("Amount must be a finite number")
    if v == 0:
        raise ValueError("Amount must not be zero")
    return v


def _validate_currency(v: Optional[str]) -> Optional[str]:
    """Validate currency is one of CNY/HKD/USD; normalize to uppercase."""
    if v is None:
        return None
    upper = v.upper()
    if upper not in ALLOWED_CURRENCIES:
        raise ValueError(f"Currency must be one of {', '.join(sorted(ALLOWED_CURRENCIES))}")
    return upper


class HistoricalAdjustmentCreate(BaseModel):
    """创建历史盈亏调整请求"""
    amount: float = Field(..., description="调整金额（正=盈利，负=亏损）")
    currency: str = Field("CNY", max_length=3, description="币种（CNY/HKD/USD）")
    note: Optional[str] = Field(None, max_length=500, description="备注")

    _validate_amount = field_validator("amount")(_validate_amount)
    _validate_currency = field_validator("currency")(_validate_currency)


class HistoricalAdjustmentUpdate(BaseModel):
    """更新历史盈亏调整请求"""
    amount: float = Field(..., description="调整金额（正=盈利，负=亏损）")
    currency: Optional[str] = Field(None, max_length=3, description="币种（CNY/HKD/USD，不填则保留原值）")
    note: Optional[str] = Field(None, max_length=500, description="备注")

    _validate_amount = field_validator("amount")(_validate_amount)
    _validate_currency = field_validator("currency")(_validate_currency)


class HistoricalAdjustmentResponse(BaseModel):
    """历史盈亏调整响应"""
    id: str
    amount: float
    currency: str
    note: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
