"""Market Data Service — 多数据源行情适配层（骨架）

当前状态：基础结构已就绪，Provider 业务逻辑待后续变更实现。
对应 PLAN.md、REQUIREMENTS_MARKET_DATA.md。
"""

from app.services.market_data.provider_base import BaseProvider
from app.services.market_data.schemas import CurrentPrice, DailyKline, Fundamentals

__all__ = [
    "BaseProvider",
    "CurrentPrice",
    "DailyKline",
    "Fundamentals",
]
