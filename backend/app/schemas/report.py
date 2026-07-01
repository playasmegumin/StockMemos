"""分析报告 Pydantic 请求/响应模型"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class ReportCreate(BaseModel):
    """创建分析报告请求"""
    generated_at: datetime = Field(..., description="报告生成时间")
    title: str = Field(..., max_length=200, description="报告标题")
    content: str = Field(..., description="报告正文")


class ReportUpdate(BaseModel):
    """更新分析报告请求"""
    generated_at: Optional[datetime] = Field(None, description="报告生成时间")
    title: Optional[str] = Field(None, max_length=200, description="报告标题")
    content: Optional[str] = Field(None, description="报告正文")


class ReportResponse(BaseModel):
    """分析报告响应"""
    id: str
    stock_analyze_id: str
    generated_at: Optional[str] = None
    title: str
    content: str
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
