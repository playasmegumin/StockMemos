"""个股标签 Pydantic 请求/响应模型"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class StockTagCreate(BaseModel):
    """创建个股标签请求"""
    tag: str = Field(..., max_length=50, description="标签文本")


class StockTagUpdate(BaseModel):
    """更新个股标签请求"""
    tag: Optional[str] = Field(None, max_length=50, description="标签文本")


class StockTagResponse(BaseModel):
    """个股标签响应"""
    id: str
    stock_analyze_id: str
    tag: str
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
