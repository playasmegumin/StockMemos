"""ProviderRouter — 按 exchange 路由到对应数据源 Provider

从 settings 读取 MARKET_DATA_SOURCE_CN/HK/US 配置，
返回对应的 Provider 实例（懒加载单例）。
"""

import logging
from typing import Dict

from app.config import settings
from app.services.market_data.provider_base import BaseProvider

logger = logging.getLogger(__name__)


class ProviderRouter:
    """按交易所路由到对应的 Provider 实现

    使用示例：
        router = ProviderRouter()
        provider = router.get_provider("SH")  # → TuShareProvider
        provider = router.get_provider("HK")  # → YFinanceProvider
    """

    def __init__(self) -> None:
        self._providers: Dict[str, BaseProvider] = {}
        self._source_map: Dict[str, str] = self._build_source_map()
        logger.info(
            "ProviderRouter initialized: CN=%s, HK=%s, US=%s",
            self._source_map.get("CN"),
            self._source_map.get("HK"),
            self._source_map.get("US"),
        )

    def _build_source_map(self) -> Dict[str, str]:
        """从 settings 构建 exchange → source 映射"""
        return {
            "CN": settings.market_data_source_cn,
            "HK": settings.market_data_source_hk,
            "US": settings.market_data_source_us,
        }

    def _map_exchange_to_source_key(self, exchange: str) -> str:
        """将具体交易所代码映射到配置键

        SH/SZ → CN
        HK → HK
        US → US
        """
        if exchange in ("SH", "SZ"):
            return "CN"
        return exchange

    def get_provider(self, exchange: str) -> BaseProvider:
        """返回对应交易所的 Provider 实例（懒加载单例）"""
        source_key = self._map_exchange_to_source_key(exchange)
        source = self._source_map.get(source_key, "yfinance")

        if source not in self._providers:
            self._providers[source] = self._create_provider(source)

        return self._providers[source]

    def _create_provider(self, source: str) -> BaseProvider:
        """根据数据源名称创建 Provider 实例"""
        source_lower = source.lower()

        if source_lower == "tushare":
            from app.services.market_data.providers.tushare_provider import (
                TuShareProvider,
            )
            logger.info("Creating TuShareProvider")
            return TuShareProvider()

        elif source_lower == "yfinance":
            from app.services.market_data.providers.yfinance_provider import (
                YFinanceProvider,
            )
            logger.info("Creating YFinanceProvider")
            return YFinanceProvider()

        elif source_lower == "finnhub":
            from app.services.market_data.providers.finnhub_provider import (
                FinnhubProvider,
            )
            logger.info("Creating FinnhubProvider")
            return FinnhubProvider()

        elif source_lower == "akshare":
            from app.services.market_data.providers.akshare_provider import (
                AKShareProvider,
            )
            logger.info("Creating AKShareProvider")
            return AKShareProvider()

        else:
            logger.warning(
                "Unknown data source '%s', falling back to yfinance", source
            )
            from app.services.market_data.providers.yfinance_provider import (
                YFinanceProvider,
            )
            return YFinanceProvider()
