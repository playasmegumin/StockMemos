"""交易点请求/响应模型"""

from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class TradePointCreate(BaseModel):
    """创建交易点请求模型"""
    portfolio_id: str = Field(..., description="关联持仓ID")
    type: str = Field(..., max_length=20, description="操作类型：add_position/reduce_position/stop_loss/take_profit")
    price: Optional[float] = Field(None, description="交易价格")
    reason: Optional[str] = Field(None, description="交易理由")
    report_id: Optional[str] = Field(None, description="关联分析报告ID")
    trade_date: Optional[date] = Field(None, description="交易日期")


class TradePointResponse(TradePointCreate):
    """交易点响应模型"""
    id: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
