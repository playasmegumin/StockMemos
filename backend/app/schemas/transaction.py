"""交易记录 Pydantic 请求/响应模型"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import date
from typing import Optional


class TransactionCreate(BaseModel):
    """创建交易记录请求"""
    stock_id: str = Field(..., description="关联个股ID")
    quantity: float = Field(..., description="交易数量，正买负卖")
    price: float = Field(..., gt=0, description="交易价格")
    gas: float = Field(0.0, ge=0, description="手续费")
    traded_at: date = Field(..., description="交易日期")


class TransactionUpdate(BaseModel):
    """更新交易记录请求"""
    quantity: Optional[float] = Field(None, description="交易数量")
    price: Optional[float] = Field(None, gt=0, description="交易价格")
    gas: Optional[float] = Field(None, ge=0, description="手续费")
    traded_at: Optional[date] = Field(None, description="交易日期")


class TransactionResponse(BaseModel):
    """交易记录响应"""
    id: str
    stock_id: str
    quantity: float
    price: float
    gas: float
    traded_at: date
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
