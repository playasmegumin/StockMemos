"""FinnhubProvider — 美股数据源适配器

覆盖 US 市场数据：
- 实时行情 → Finnhub Quote API
- 日 K 线   → Finnhub Stock Candles API
- 基本面    → Finnhub Company Profile 2 + Basic Financials API

使用 Finnhub 免费 API Key，60 次/分钟限流。
"""

import time
import logging
from datetime import date, datetime, timezone, timedelta
from typing import List, Optional, Set

import finnhub

from app.config import settings
from app.services.market_data.provider_base import BaseProvider
from app.services.market_data.schemas import CurrentPrice, DailyKline, Fundamentals

logger = logging.getLogger(__name__)

TZ_CST = timezone(timedelta(hours=8))


class FinnhubProvider(BaseProvider):
    """美股数据源适配器（基于 Finnhub API）"""

    def __init__(self) -> None:
        api_key = settings.finnhub_api_key
        if not api_key:
            raise ValueError("FINNHUB_API_KEY 未配置，请检查 .env 文件")

        self._client = finnhub.Client(api_key=api_key)
        self._last_request_time: float = 0.0
        self._min_interval = 1.0  # 60 req/min → 1 req/sec
        logger.info("FinnhubProvider initialized")

    def _rate_limit(self) -> None:
        """Finnhub 限流：每秒最多 1 次"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    # ─── 实时行情 ───────────────────────────────────

    def get_current_price(self, symbol: str, exchange: str) -> CurrentPrice:
        """获取实时行情（Finnhub Quote API）"""
        self._rate_limit()
        quote = self._client.quote(symbol)

        if not quote or quote.get("c") is None:
            raise RuntimeError(f"Finnhub: no quote data for {symbol}")

        price = float(quote["c"])
        ts = quote.get("t")
        if ts:
            price_time = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(TZ_CST)
        else:
            price_time = datetime.now(TZ_CST)

        return CurrentPrice(
            symbol=symbol,
            exchange=exchange,
            price=price,
            price_time=price_time,
            currency="USD",
            volume=None,
            source="finnhub",
            data_quality="realtime",
        )

    # ─── 日 K 线 ─────────────────────────────────────

    def get_daily_kline(
        self,
        symbol: str,
        exchange: str,
        start_date: date,
        end_date: date,
    ) -> List[DailyKline]:
        """获取日 K 线数据

        优先走 Finnhub Stock Candles API（需付费版）；
        失败时降级为 Quote API 的昨收价，至少返回一条记录。
        """
        self._rate_limit()
        from_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp())
        to_ts = int(datetime.combine(end_date, datetime.min.time()).timestamp())

        try:
            candles = self._client.stock_candles(symbol, "D", from_ts, to_ts)
            if candles and candles.get("s") == "ok":
                return self._parse_candles(candles)
        except Exception as e:
            logger.warning(
                "[finnhub] candles unavailable for %s, degrading to quote: %s",
                symbol, e,
            )

        # 降级：从 Quote API 取昨收价
        return self._kline_from_quote(symbol, exchange)

    def _parse_candles(self, candles: dict) -> List[DailyKline]:
        """解析 Stock Candles API 响应"""
        result: List[DailyKline] = []
        closes = candles.get("c", [])
        highs = candles.get("h", [])
        lows = candles.get("l", [])
        opens = candles.get("o", [])
        volumes = candles.get("v", [])
        timestamps = candles.get("t", [])

        for i in range(len(timestamps)):
            try:
                trade_date = datetime.fromtimestamp(timestamps[i], tz=timezone.utc).date()
                kline = DailyKline(
                    date=trade_date,
                    open=float(opens[i]),
                    high=float(highs[i]),
                    low=float(lows[i]),
                    close=float(closes[i]),
                    volume=float(volumes[i]),
                    amount=float(volumes[i]) * float(closes[i]),
                )
                result.append(kline)
            except (IndexError, ValueError, TypeError) as e:
                logger.warning("[finnhub] skip candle index %d: %s", i, e)
                continue
        return result

    def _kline_from_quote(self, symbol: str, exchange: str) -> List[DailyKline]:
        """从 Quote API 的昨收价构建单条 K 线记录"""
        self._rate_limit()
        try:
            quote = self._client.quote(symbol)
            if not quote:
                return []

            c = quote.get("c")
            pc = quote.get("pc")
            ts = quote.get("t")
            if c is None and pc is None:
                return []

            close_val = float(c or pc or 0)
            prev_close = float(pc or c or 0)
            trade_date = (
                datetime.fromtimestamp(ts, tz=timezone.utc).date() if ts else date.today()
            )

            kline = DailyKline(
                date=trade_date,
                open=prev_close,
                high=max(close_val, prev_close),
                low=min(close_val, prev_close),
                close=close_val,
                volume=0,
                amount=0,
            )
            logger.info(
                "[finnhub] kline degraded from quote: %s close=%.2f prev_close=%.2f date=%s",
                symbol, close_val, prev_close, trade_date,
            )
            return [kline]
        except Exception as e:
            logger.error("[finnhub] quote degradation failed for %s: %s", symbol, e)
            return []

        return result

    # ─── 基本面 ─────────────────────────────────────

    def get_fundamentals(self, symbol: str, exchange: str) -> Fundamentals:
        """获取基本面数据

        组合 Finnhub Company Profile 2 + Basic Financials API。
        """
        self._rate_limit()
        profile = self._client.company_profile2(symbol=symbol) or {}

        self._rate_limit()
        financials = self._client.company_basic_financials(symbol, "all") or {}
        metrics = financials.get("metric", {}) or {}

        name = profile.get("name", "")
        sector = profile.get("finnhubIndustry")
        industry = profile.get("finnhubIndustry")
        market_cap = profile.get("marketCapitalization")
        share_outstanding = profile.get("shareOutstanding")

        # 从 metrics 提取
        pe = metrics.get("peExclExtraTTM") or metrics.get("peBasicExclExtraTTM")
        pb = metrics.get("priceToBook")
        dividend_yield = metrics.get("dividendYieldIndicatedAnnual")
        eps = metrics.get("epsExclExtraItemsTTM")
        roe = metrics.get("roeTTM")
        profit_margin = metrics.get("profitMarginTTM")
        beta = metrics.get("beta")


        return Fundamentals(
            symbol=symbol,
            exchange=exchange,
            name=name,
            sector=sector,
            industry=industry,
            market_cap=float(market_cap) * 1e6 if market_cap else None,
            pe_ratio=float(pe) if pe else None,
            pb_ratio=float(pb) if pb else None,
            dividend_yield=float(dividend_yield) if dividend_yield else None,
            eps=float(eps) if eps else None,
            roe=float(roe) if roe else None,
            profit_margin=float(profit_margin) if profit_margin else None,
            beta=float(beta) if beta else None,
            source="finnhub",
            data_date=date.today(),
        )

    @property
    def capabilities(self) -> Set[str]:
        return {"price", "fundamentals"}
