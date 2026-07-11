"""个股 Pydantic 请求/响应模型"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import date
from typing import Optional


class StockCreate(BaseModel):
    """创建个股请求"""
    symbol: str = Field(..., max_length=20, description="个股代码")
    name: Optional[str] = Field(None, max_length=100, description="个股名称（可选，不填则自动查询）")
    exchange: Optional[str] = Field(None, max_length=8, description="交易所（可选，不填则自动推断）")
    currency: Optional[str] = Field(None, max_length=10, description="交易货币（可选，不填则自动推断）")


class StockUpdate(BaseModel):
    """更新个股请求"""
    exchange: Optional[str] = Field(None, max_length=8, description="交易所类型")
    symbol: Optional[str] = Field(None, max_length=20, description="个股标识")
    name: Optional[str] = Field(None, max_length=100, description="个股名称")
    currency: Optional[str] = Field(None, max_length=10, description="交易货币")


class StockResponse(BaseModel):
    """个股响应"""
    id: str
    exchange: str
    symbol: str
    name: str
    currency: str
    position: float = Field(0.0, description="当前持仓数量")
    historical_pnl: float = Field(0.0, description="历史盈亏")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
