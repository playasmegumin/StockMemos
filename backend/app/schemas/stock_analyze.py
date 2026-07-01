"""个股分析 Pydantic 请求/响应模型"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Any


class StockAnalyzeCreate(BaseModel):
    """创建/更新个股分析请求（upsert，1:1 关联）"""
    fundamentals_data: Optional[dict[str, Any]] = Field(
        None, description="基本面数据（JSON，如 PE/PB/ROE 等）"
    )


class StockAnalyzeResponse(BaseModel):
    """个股分析响应"""
    id: str
    stock_id: str
    fundamentals_data: Optional[dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
