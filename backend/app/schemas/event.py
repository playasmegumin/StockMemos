"""事件请求/响应模型"""

from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class EventCreate(BaseModel):
    """创建事件请求模型"""
    name: str = Field(..., max_length=200, description="事件名称")
    category: Optional[str] = Field(None, max_length=50, description="事件类型：monetary_policy/geopolitical/macro_data/company_event")
    expected_date: Optional[date] = Field(None, description="预期发生日期")
    status: Optional[str] = Field("pending", description="状态：pending/occurred/materialized")
    source_url: Optional[str] = Field(None, description="信息来源链接")
    description: Optional[str] = Field(None, description="事件描述")


class EventResponse(EventCreate):
    """事件响应模型"""
    id: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
