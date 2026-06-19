"""投资备忘录请求/响应模型"""

from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class InvestmentMemoCreate(BaseModel):
    """创建投资备忘录请求"""
    stock_code: str = Field(..., max_length=20, description="股票代码")
    target_price: Optional[float] = Field(None, description="目标股价（估值）")
    valuation_method: Optional[str] = Field(None, max_length=50, description="估值方法：PE/DCF/可比公司")
    business_scope: Optional[str] = Field(None, description="业务范围/供需关系/产业链生态位")
    short_trend: Optional[str] = Field(None, max_length=20, description="短线趋势：up/down/sideways")
    mid_trend: Optional[str] = Field(None, max_length=20, description="中线趋势：up/down/sideways")
    long_trend: Optional[str] = Field(None, max_length=20, description="长期趋势：up/down/sideways")
    trend_logic: Optional[str] = Field(None, description="趋势预测核心逻辑")
    notes: Optional[str] = Field(None, description="用户自定义备注")


class InvestmentMemoResponse(InvestmentMemoCreate):
    """投资备忘录响应"""
    id: str
    last_updated_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
