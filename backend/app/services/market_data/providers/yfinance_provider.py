"""YFinanceProvider — 港股/美股数据源适配器

覆盖 HK/US 数据：
- 实时行情 → yfinance.Ticker.info 实时/延迟报价
- 日 K 线 → yfinance.Ticker.history()
- 基本面 → yfinance.Ticker.info（50+ 字段）

遵守每秒最多 1 次请求的限流约束。
"""

import time
import logging
from datetime import date, datetime, timezone, timedelta
from typing import List, Optional, Set

import yfinance as yf

from app.services.market_data.provider_base import BaseProvider
from app.services.market_data.schemas import CurrentPrice, DailyKline, Fundamentals

logger = logging.getLogger(__name__)

# UTC+8 时区，所有 price_time 以此输出
TZ_CST = timezone(timedelta(hours=8))

# yfinance ticker 后缀映射
_EXCHANGE_TO_YF_SUFFIX = {
    "HK": ".HK",
    "US": "",  # 美股无后缀
}


class YFinanceProvider(BaseProvider):
    """港股/美股数据源适配器（基于 yfinance）"""

    def __init__(self) -> None:
        self._last_request_time: float = 0.0
        self._min_interval = 1.0  # 每秒最多 1 次
        logger.info("YFinanceProvider initialized")

    def _to_yf_ticker(self, symbol: str, exchange: str) -> str:
        """将 symbol + exchange 转为 yfinance ticker 格式"""
        suffix = _EXCHANGE_TO_YF_SUFFIX.get(exchange, "")
        return f"{symbol}{suffix}"

    def _rate_limit(self) -> None:
        """yfinance 限流：每秒最多 1 次请求"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            sleep_time = self._min_interval - elapsed
            logger.debug("[yfinance] rate limit: sleep %.2fs", sleep_time)
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def _get_currency(self, exchange: str) -> str:
        return {"HK": "HKD", "US": "USD"}.get(exchange, "USD")

    def get_current_price(self, symbol: str, exchange: str) -> CurrentPrice:
        """获取实时/延迟行情

        优先从 Ticker.info 获取实时价；若失败（限流/超时等），
        自动降级为最近日 K 收盘价，data_quality 标记为 "degraded"。
        """
        ticker_str = self._to_yf_ticker(symbol, exchange)
        self._rate_limit()

        ticker = yf.Ticker(ticker_str)
        info = ticker.info or {}

        price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose")
        )
        volume = info.get("regularMarketVolume")

        # 使用实际市场时间（Unix 时间戳）而非当前时间
        market_time = info.get("regularMarketTime")
        if market_time:
            price_time = datetime.fromtimestamp(market_time, tz=timezone.utc).astimezone(TZ_CST)
        else:
            price_time = datetime.now(TZ_CST)

        # 实时价获取成功
        if price is not None and price != 0.0:
            return CurrentPrice(
                symbol=symbol,
                exchange=exchange,
                price=float(price),
                price_time=price_time,
                currency=self._get_currency(exchange),
                volume=float(volume) if volume else None,
                source="yfinance",
                data_quality="realtime",
            )

        # 实时价获取失败 → 降级：取最近日 K 收盘价
        logger.warning(
            "[yfinance] realtime price unavailable for %s, degrading to kline close",
            ticker_str,
        )
        try:
            hist = ticker.history(period="5d")
            if not hist.empty:
                last_row = hist.iloc[-1]
                close_price = float(last_row.get("Close", 0))
                # 使用 history 数据中的实际时间戳（US 约 16:00 ET）
                close_time = last_row.name
                if hasattr(close_time, "to_pydatetime"):
                    close_time = close_time.to_pydatetime()
                elif not isinstance(close_time, datetime):
                    close_time = datetime.combine(close_time, datetime.min.time(), tzinfo=timezone.utc)
                # 统一转为 UTC+8
                if close_time.tzinfo:
                    close_time = close_time.astimezone(TZ_CST)
                else:
                    close_time = close_time.replace(tzinfo=TZ_CST)
                return CurrentPrice(
                    symbol=symbol,
                    exchange=exchange,
                    price=close_price,
                    price_time=close_time,
                    currency=self._get_currency(exchange),
                    volume=None,
                    source="yfinance",
                    data_quality="degraded",
                )
        except Exception as e:
            logger.error("[yfinance] degradation failed for %s: %s", ticker_str, e)

        # 完全失败
        raise RuntimeError(f"yfinance: unable to get price for {ticker_str}")

    def get_daily_kline(
        self,
        symbol: str,
        exchange: str,
        start_date: date,
        end_date: date,
    ) -> List[DailyKline]:
        """获取日 K 线数据"""
        ticker_str = self._to_yf_ticker(symbol, exchange)
        self._rate_limit()

        ticker = yf.Ticker(ticker_str)
        # 拉取足够的历史数据
        hist = ticker.history(period="max")

        if hist.empty:
            logger.warning("[yfinance] no history data for %s", ticker_str)
            return []

        # 过滤日期范围
        hist = hist.loc[start_date:end_date]

        result: List[DailyKline] = []
        for idx, row in hist.iterrows():
            try:
                trade_date = idx.date() if hasattr(idx, "date") else idx
                kline = DailyKline(
                    date=trade_date,
                    open=float(row.get("Open", 0)),
                    high=float(row.get("High", 0)),
                    low=float(row.get("Low", 0)),
                    close=float(row.get("Close", 0)),
                    volume=float(row.get("Volume", 0)),
                    amount=float(row.get("Volume", 0)) * float(row.get("Close", 0)),  # 近似成交额
                )
                result.append(kline)
            except (ValueError, TypeError) as e:
                logger.warning("[yfinance] skip row: %s, error: %s", idx, e)
                continue

        return result

    def get_fundamentals(self, symbol: str, exchange: str) -> Fundamentals:
        """获取基本面数据（基于 yfinance Ticker.info）"""
        ticker_str = self._to_yf_ticker(symbol, exchange)
        self._rate_limit()

        ticker = yf.Ticker(ticker_str)
        info = ticker.info or {}

        sector = info.get("sector")
        industry = info.get("industry")
        market_cap = info.get("marketCap")
        pe = info.get("trailingPE") or info.get("forwardPE")
        pb = info.get("priceToBook")
        dividend_yield = info.get("dividendYield")
        eps = info.get("trailingEps")
        roe = info.get("returnOnEquity")
        profit_margin = info.get("profitMargins")
        debt_to_equity = info.get("debtToEquity")
        current_ratio = info.get("currentRatio")
        beta = info.get("beta")
        avg_volume = info.get("averageVolume")
        week52_high = info.get("fiftyTwoWeekHigh")
        week52_low = info.get("fiftyTwoWeekLow")

        return Fundamentals(
            symbol=symbol,
            exchange=exchange,
            name=info.get("longName") or info.get("shortName", ""),
            sector=str(sector) if sector else None,
            industry=str(industry) if industry else None,
            market_cap=float(market_cap) if market_cap else None,
            pe_ratio=float(pe) if pe else None,
            pb_ratio=float(pb) if pb else None,
            dividend_yield=float(dividend_yield) if dividend_yield else None,
            eps=float(eps) if eps else None,
            roe=float(roe) if roe else None,
            profit_margin=float(profit_margin) if profit_margin else None,
            debt_to_equity=float(debt_to_equity) if debt_to_equity else None,
            current_ratio=float(current_ratio) if current_ratio else None,
            beta=float(beta) if beta else None,
            avg_volume=float(avg_volume) if avg_volume else None,
            week52_high=float(week52_high) if week52_high else None,
            week52_low=float(week52_low) if week52_low else None,
            source="yfinance",
            data_date=date.today(),
        )

    @property
    def capabilities(self) -> Set[str]:
        return {"price", "kline", "fundamentals"}
