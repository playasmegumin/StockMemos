"""AKShareProvider — 港股、美股数据源适配器

多市场支持：
- 港股 → AKShare stock_hk_daily（个股日线）
- 美股 → AKShare stock_us_daily（个股日线）

AKShare 从公开数据源采集数据，无需 API Key。

注意：
- stock_hk_hist / stock_hk_spot_em 等东方财富端点可能在 Docker 环境被阻断，
  优先使用 stock_hk_daily / stock_us_daily 等个股查询端点。
- 基本面数据依赖全市场快照（spot），在网络受限环境下可用性可能受限。
"""

import logging
from datetime import date, datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any

import akshare as ak
import pandas as pd

from app.services.market_data.provider_base import BaseProvider
from app.services.market_data.schemas import CurrentPrice, DailyKline, Fundamentals

logger = logging.getLogger(__name__)

TZ_CST = timezone(timedelta(hours=8))
TZ_ET = timezone(timedelta(hours=-5))  # 粗略美国东岸，用于标记


# ─── 市场配置 ─────────────────────────────────────

class MarketConfig:
    """单个市场的 AKShare 配置"""

    def __init__(
        self,
        daily_func,
        spot_func=None,
        currency: str = "HKD",
        tz=timezone.utc,
    ):
        self.daily_func = daily_func  # 日线函数，如 ak.stock_hk_daily
        self.spot_func = spot_func    # 全市场快照函数（可选）
        self.currency = currency
        self.tz = tz


def _hk_daily(symbol: str) -> pd.DataFrame:
    return ak.stock_hk_daily(symbol=symbol, adjust="qfq")


def _us_daily(symbol: str) -> pd.DataFrame:
    return ak.stock_us_daily(symbol=symbol, adjust="qfq")


MARKET_CONFIGS: Dict[str, MarketConfig] = {
    "HK": MarketConfig(daily_func=_hk_daily, currency="HKD", tz=TZ_CST),
    "US": MarketConfig(daily_func=_us_daily, currency="USD", tz=timezone.utc),
}


# ─── Provider ─────────────────────────────────────

class AKShareProvider(BaseProvider):
    """多市场数据源适配器（基于 AKShare）

    通过 exchange 参数自动路由到对应市场的 AKShare 函数。
    """

    def __init__(self) -> None:
        logger.info("AKShareProvider initialized (markets: HK, US)")

    # ─── 市场路由 ────────────────────────────────

    def _get_config(self, exchange: str) -> MarketConfig:
        """按交易所代码返回 AKShare 参数配置"""
        cfg = MARKET_CONFIGS.get(exchange)
        if cfg is None:
            logger.warning("AKShare: unsupported exchange %s, defaulting to HK", exchange)
            return MARKET_CONFIGS["HK"]
        return cfg

    @staticmethod
    def _parse_date(v) -> date:
        """统一处理 date/datetime 类型"""
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, date):
            return v
        raise TypeError(f"unexpected date type: {type(v)}")

    # ─── 实时行情 ───────────────────────────────────

    def get_current_price(self, symbol: str, exchange: str) -> CurrentPrice:
        """获取最新收盘价（通过个股日线查询）"""
        cfg = self._get_config(exchange)
        today_str = date.today().strftime("%Y%m%d")

        try:
            # 取最近 7 天的数据以覆盖非交易日
            df = cfg.daily_func(symbol)
        except Exception as e:
            logger.error("[akshare] %s %s daily failed: %s", exchange, symbol, e)
            raise RuntimeError(f"AKShare: no data for {symbol} ({exchange})")

        if df is None or df.empty:
            raise RuntimeError(f"AKShare: empty data for {symbol} ({exchange})")

        last = df.iloc[-1]
        close = float(last.get("close", 0))
        trade_date = self._parse_date(last.get("date", date.today()))
        price_time = datetime.combine(trade_date, datetime.min.time(), tzinfo=cfg.tz)

        return CurrentPrice(
            symbol=symbol,
            exchange=exchange,
            price=close,
            price_time=price_time,
            currency=cfg.currency,
            volume=None,
            source="akshare",
            data_quality="degraded",
        )

    # ─── 日 K 线 ─────────────────────────────────────

    def get_daily_kline(
        self,
        symbol: str,
        exchange: str,
        start_date: date,
        end_date: date,
    ) -> List[DailyKline]:
        """获取日 K 线数据"""
        cfg = self._get_config(exchange)

        try:
            df = cfg.daily_func(symbol)
        except Exception as e:
            logger.error("[akshare] %s %s kline failed: %s", exchange, symbol, e)
            return []

        if df is None or df.empty:
            return []

        result: List[DailyKline] = []
        for _, row in df.iterrows():
            try:
                trade_date = self._parse_date(row.get("date"))

                # 过滤日期范围
                if trade_date < start_date or trade_date > end_date:
                    continue

                volume = float(row.get("volume", 0))
                amount: Optional[float] = None
                if "amount" in row and pd.notna(row.get("amount")):
                    amount = float(row["amount"])

                kline = DailyKline(
                    date=trade_date,
                    open=float(row.get("open", 0)),
                    high=float(row.get("high", 0)),
                    low=float(row.get("low", 0)),
                    close=float(row.get("close", 0)),
                    volume=float(row.get("volume", 0)),
                    amount=float(amount) if amount is not None else 0.0,
                )
                result.append(kline)
            except (ValueError, TypeError) as e:
                logger.warning("[akshare] skip kline row: %s", e)
                continue

        return result

    # ─── 基本面 ─────────────────────────────────────

    def get_fundamentals(self, symbol: str, exchange: str) -> Fundamentals:
        """获取基本面数据（降级：仅返回价格）

        AKShare 日线数据不含股票名称和基本面指标。
        港股可通过 stock_hk_company_profile_em 获取公司名称（ETF/基金返回管理公司名而非产品名）。
        美股暂无纯 AKShare 的名称获取方式。
        """
        cfg = self._get_config(exchange)

        name: str = symbol

        # HK：用公司概况获取中文名称（返回管理公司名）
        if exchange == "HK":
            try:
                profile = ak.stock_hk_company_profile_em(symbol=symbol)
                if profile is not None and not profile.empty:
                    raw = profile.iloc[0, 0]
                    if raw and str(raw).strip():
                        name = str(raw).strip()
            except Exception as e:
                logger.warning("[akshare] %s %s company profile failed: %s", exchange, symbol, e)

        pe, pb, market_cap = None, None, None

        return Fundamentals(
            symbol=symbol,
            exchange=exchange,
            name=name,
            sector=None,
            industry=None,
            market_cap=market_cap,
            pe_ratio=pe,
            pb_ratio=pb,
            source="akshare",
            data_date=date.today(),
        )

    @property
    def capabilities(self) -> Set[str]:
        return {"price", "kline"}

    @property
    def name(self) -> str:
        return "AKShare"
