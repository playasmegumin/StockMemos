"""自选股请求/响应模型"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class WatchlistCreate(BaseModel):
    """添加自选股请求"""
    stock_code: str = Field(..., max_length=20, description="股票代码，如 000001.SZ")
    stock_name: Optional[str] = Field(None, max_length=100, description="股票名称")
    sector: Optional[str] = Field(None, max_length=50, description="所属板块/行业")
    market: Optional[str] = Field(None, max_length=20, description="交易所：SH/SZ/HK/US")


class WatchlistResponse(BaseModel):
    """自选股响应"""
    id: str
    stock_code: str
    stock_name: Optional[str] = None
    sector: Optional[str] = None
    market: Optional[str] = None
    is_watched: bool = True
    memo_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
