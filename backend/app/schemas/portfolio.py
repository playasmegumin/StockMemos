"""Pydantic 请求/响应模型"""

from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class PortfolioCreate(BaseModel):
    """创建持仓请求模型"""
    stock_code: str = Field(..., max_length=20, description="股票代码")
    stock_name: Optional[str] = Field(None, max_length=100, description="股票名称")
    quantity: int = Field(..., gt=0, description="持股数量")
    cost_price: float = Field(..., gt=0, description="成本价")
    build_date: date = Field(..., description="建仓日期")
    status: Optional[str] = Field("holding", description="状态：holding/closed")

class PortfolioResponse(PortfolioCreate):
    """持仓响应模型"""
    id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class PortfolioWithPnl(BaseModel):
    """含实时盈亏的持仓条目（Dashboard 用）"""
    id: str
    stock_code: str
    stock_name: Optional[str] = None
    quantity: int
    cost_price: float
    build_date: date
    latest_price: float = Field(0.0, description="最新收盘价")
    market_value: float = Field(0.0, description="持仓市值")
    floating_pnl: float = Field(0.0, description="浮动盈亏")
    pnl_rate: float = Field(0.0, description="盈亏率")
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PortfolioDashboardSummary(BaseModel):
    """仓位管理 Dashboard 汇总"""
    total_cost: float = Field(0.0, description="总成本")
    total_market_value: float = Field(0.0, description="总市值")
    total_floating_pnl: float = Field(0.0, description="总浮动盈亏")
    total_pnl_rate: float = Field(0.0, description="总收益率")
    position_count: int = Field(0, description="持仓数量")


class PortfolioDashboardResponse(BaseModel):
    """仓位管理 Dashboard 响应"""
    positions: list[PortfolioWithPnl] = []
    summary: PortfolioDashboardSummary
