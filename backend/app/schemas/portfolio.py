"""Pydantic 请求/响应模型"""

from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class PortfolioCreate(BaseModel):
    """创建持仓请求模型"""
    stock_code: str = Field(..., max_length=20, description="股票代码")
    stock_name: Optional[str] = Field(None, max_length=100, description="股票名称")
    quantity: int = Field(..., gt=0, description="持股数量")
    cost_price: float = Field(..., gt=0, description="成本价")
    build_date: date = Field(..., description="建仓日期")
    status: Optional[str] = Field("holding", description="状态：holding/closed")


class PortfolioResponse(PortfolioCreate):
    """持仓响应模型"""
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
