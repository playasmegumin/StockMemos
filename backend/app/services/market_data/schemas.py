"""Market Data — 统一 Pydantic 数据模型

各数据源返回的原始数据统一转换为这些模型，对外提供一致接口。
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class CurrentPrice(BaseModel):
    """实时行情（纯内存，不落盘，前端驱动刷新）"""
    symbol: str
    exchange: str           # SH/SZ/HK/US
    price: float
    price_time: datetime
    currency: str           # CNY/HKD/USD
    volume: Optional[float] = None
    source: str             # "tushare" / "yfinance"
    data_quality: Optional[str] = None
    """数据质量标识：None/缺失 = 正常实时，'degraded' = 降级为日K收盘价"""


class DailyKline(BaseModel):
    """日 K 线数据（持久化到 kline_daily 表）"""
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float


class Fundamentals(BaseModel):
    """基本面数据（持久化到 stock_analyze.fundamentals_data JSONB）"""
    symbol: str
    exchange: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    eps: Optional[float] = None
    roe: Optional[float] = None
    profit_margin: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    beta: Optional[float] = None
    avg_volume: Optional[float] = None
    week52_high: Optional[float] = None
    week52_low: Optional[float] = None
    source: str
    data_date: date
