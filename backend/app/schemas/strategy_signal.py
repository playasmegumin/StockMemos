"""策略信号请求/响应模型"""

from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, Dict, Any


class StrategySignalCreate(BaseModel):
    """创建策略信号请求模型"""
    strategy_id: str = Field(..., description="关联策略ID")
    stock_code: str = Field(..., max_length=20, description="股票代码")
    signal_date: date = Field(..., description="信号日期")
    signal_type: Optional[str] = Field(None, max_length=20, description="信号类型：buy/sell/hold/overvalued/undervalued")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="当日指标原始值(JSON)")


class StrategySignalResponse(StrategySignalCreate):
    """策略信号响应模型"""
    id: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
