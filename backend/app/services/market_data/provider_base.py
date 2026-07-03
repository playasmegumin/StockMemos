"""BaseProvider — 行情数据源适配器抽象基类

所有数据源 provider 必须继承此类，实现统一接口。
"""

from abc import ABC, abstractmethod
from typing import List, Set
from datetime import date

from app.services.market_data.schemas import CurrentPrice, DailyKline, Fundamentals


class BaseProvider(ABC):
    """行情数据源适配器抽象基类"""

    @abstractmethod
    def get_current_price(self, symbol: str, exchange: str) -> CurrentPrice:
        """获取实时行情（纯内存，不落盘）"""
        ...

    @abstractmethod
    def get_daily_kline(
        self,
        symbol: str,
        exchange: str,
        start_date: date,
        end_date: date,
    ) -> List[DailyKline]:
        """获取日 K 线数据（持久化到 kline_daily 表）"""
        ...

    @abstractmethod
    def get_fundamentals(self, symbol: str, exchange: str) -> Fundamentals:
        """获取基本面数据（PE/PB/ROE/市值等，持久化到 stock_analyze.fundamentals_data）"""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> Set[str]:
        """返回该 provider 支持的能力集合

        可能的值: {"price", "kline", "fundamentals"}
        TuShare: {"kline", "fundamentals"}（不支持实时行情）
        yfinance: {"price", "kline", "fundamentals"}
        """
        ...
