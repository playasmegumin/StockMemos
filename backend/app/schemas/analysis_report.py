"""分析报告请求/响应模型"""

from pydantic import BaseModel, Field
from typing import Optional


class AnalysisReportCreate(BaseModel):
    """创建分析报告请求模型"""
    stock_code: str = Field(..., max_length=20, description="股票代码")
    trigger_type: Optional[str] = Field(None, max_length=20, description="触发类型：manual/scheduled")
    final_rating: Optional[str] = Field(None, max_length=20, description="最终评级：strong_buy/buy/accumulate/neutral/reduce/sell")
    summary: Optional[str] = Field(None, description="报告摘要")
    valuation_status: Optional[str] = Field(None, max_length=20, description="估值状态：overvalued/fair/undervalued")


class AnalysisReportResponse(AnalysisReportCreate):
    """分析报告响应模型"""
    id: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
