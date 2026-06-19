"""Agent日志请求/响应模型"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class AgentLogCreate(BaseModel):
    """创建Agent日志请求模型"""
    report_id: str = Field(..., description="关联报告ID")
    agent_name: str = Field(..., max_length=50, description="Agent名称，如 bull_agent")
    agent_role: Optional[str] = Field(None, max_length=50, description="角色：intelligence/event_analysis/bull/bear/referee/valuation/reporter")
    reasoning: Optional[str] = Field(None, description="完整思考文本")
    conclusion: Optional[str] = Field(None, description="结论摘要")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="结构化输出(JSON)")


class AgentLogResponse(AgentLogCreate):
    """Agent日志响应模型"""
    id: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
