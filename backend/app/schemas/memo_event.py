"""备忘录关联事件请求/响应模型"""

from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class MemoEventCreate(BaseModel):
    """为备忘录添加事件请求"""
    memo_id: str = Field(..., description="关联备忘录ID")
    event_name: str = Field(..., max_length=200, description="事件名称，如 Q3财报发布")
    event_type: Optional[str] = Field(None, max_length=20, description="类型：earnings/order/geopolitical/policy/other")
    impact_tag: Optional[str] = Field(None, max_length=20, description="影响标签：bullish/bearish/neutral")
    expected_date: Optional[date] = Field(None, description="预期发生日期")
    actual_date: Optional[date] = Field(None, description="实际发生日期")
    result_status: Optional[str] = Field("pending", max_length=20, description="pending/occurred/expired/cancelled")
    result_summary: Optional[str] = Field(None, description="事件结果摘要")
    source_url: Optional[str] = Field(None, description="信息来源")
    agent_analysis: Optional[str] = Field(None, description="Agent分析摘要")


class MemoEventResponse(BaseModel):
    """备忘录事件响应"""
    id: str
    memo_id: str
    event_name: str
    event_type: Optional[str] = None
    impact_tag: Optional[str] = None
    expected_date: Optional[str] = None
    actual_date: Optional[str] = None
    result_status: str
    result_summary: Optional[str] = None
    source_url: Optional[str] = None
    agent_analysis: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
