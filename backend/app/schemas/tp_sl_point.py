"""止盈止损点 Pydantic 请求/响应模型"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class TpSlPointCreate(BaseModel):
    """创建止盈止损点请求"""
    price: float = Field(..., gt=0, description="股价/目标价")
    label: str = Field(..., max_length=20, description="标签：买入/卖出/目标估值")
    notes: Optional[str] = Field(None, description="备注")


class TpSlPointUpdate(BaseModel):
    """更新止盈止损点请求"""
    price: Optional[float] = Field(None, gt=0, description="股价/目标价")
    label: Optional[str] = Field(None, max_length=20, description="标签")
    notes: Optional[str] = Field(None, description="备注")


class TpSlPointResponse(BaseModel):
    """止盈止损点响应"""
    id: str
    stock_analyze_id: str
    price: float
    label: str
    notes: Optional[str] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
