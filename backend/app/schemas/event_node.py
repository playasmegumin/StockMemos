"""事件节点请求/响应模型"""

from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class EventNodeCreate(BaseModel):
    """创建事件节点请求"""
    title: str = Field(..., max_length=300, description="事件标题")
    category: Optional[str] = Field(None, max_length=50, description="monetary_policy/geopolitical/macro_data/trade_policy/energy/tech")
    occurred_at: Optional[date] = Field(None, description="已发生节点日期（空表示未发生）")
    description: Optional[str] = Field(None, description="事件描述")
    source_url: Optional[str] = Field(None, description="信息来源")
    status: Optional[str] = Field("pending", max_length=20, description="pending/occurred/materialized")


class EventNodeResponse(EventNodeCreate):
    """事件节点响应"""
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
