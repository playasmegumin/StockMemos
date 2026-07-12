"""投资备忘 Pydantic 请求/响应模型"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class InvestmentMemoCreate(BaseModel):
    """创建投资备忘请求"""
    title: str = Field(..., min_length=1, max_length=200, description="标题")
    content: str = Field(..., min_length=1, description="正文（Markdown）")
    stock_id: Optional[str] = Field(None, description="关联个股 ID")


class InvestmentMemoUpdate(BaseModel):
    """更新投资备忘请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="标题")
    content: Optional[str] = Field(None, min_length=1, description="正文（Markdown）")
    stock_id: Optional[str] = Field(None, description="关联个股 ID（null 取消关联）")


class InvestmentMemoResponse(BaseModel):
    """投资备忘响应"""
    id: str
    title: str
    content: str
    stock_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InvestmentMemoListItem(BaseModel):
    """投资备忘列表项（不含 content，减少传输量）"""
    id: str
    title: str
    stock_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
