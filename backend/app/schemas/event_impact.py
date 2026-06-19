"""事件影响请求/响应模型"""

from pydantic import BaseModel, Field
from typing import Optional


class EventImpactCreate(BaseModel):
    """创建事件影响请求模型"""
    event_id: str = Field(..., description="关联事件ID")
    stock_code: str = Field(..., max_length=20, description="股票代码")
    direction: Optional[str] = Field(None, max_length=20, description="影响方向：bullish/bearish/neutral")
    magnitude: Optional[int] = Field(None, ge=1, le=5, description="影响程度：1-5")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="置信度：0.00-1.00")
    time_window: Optional[str] = Field(None, max_length=50, description="时间窗口，如 1-3个月")
    agent_reasoning: Optional[str] = Field(None, description="Agent推理过程")


class EventImpactResponse(EventImpactCreate):
    """事件影响响应模型"""
    id: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
