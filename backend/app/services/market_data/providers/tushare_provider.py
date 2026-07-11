"""TuShareProvider — A 股数据源适配器

覆盖 A 股（SH/SZ）数据：
- 日 K 线 → TushareClient.get_daily_kline() 或 get_fund_daily()
- 基本面 → TushareClient.get_daily_basic() + get_stock_basic()
- 实时行情 → 降级为最近日 K 收盘价（TuShare 2000 分不支持盘中实时）

ETF/基金识别：
    使用 stock_classifier.classify() 判断标的类型。
    若 type=fund → 使用 fund_basic/fund_daily 通路。
    若 fund_basic 返回空 → fallback 到 stock 通路。
"""

import logging
from datetime import date, datetime, timezone, timedelta
from typing import List, Optional, Set

from app.services.market_data.provider_base import BaseProvider
from app.services.market_data.schemas import CurrentPrice, DailyKline, Fundamentals
from app.services.tushare_client import TushareClient
from app.services.market_data.stock_classifier import classify

logger = logging.getLogger(__name__)

# UTC+8 时区，所有 price_time 以此输出
TZ_CST = timezone(timedelta(hours=8))


class TuShareProvider(BaseProvider):
    """A 股数据源适配器（基于 TuShare Pro）"""

    def __init__(self) -> None:
        self._client = TushareClient()
        logger.info("TuShareProvider initialized")

    def _to_ts_code(self, symbol: str, exchange: str) -> str:
        """构造 TuShare ts_code

        TuShare daily/daily_basic 等接口需要交易所后缀。
        SH/SZ 直接映射。
        """
        if exchange == "SH":
            return f"{symbol}.SH"
        elif exchange == "SZ":
            return f"{symbol}.SZ"
        return symbol

    def _is_fund(self, symbol: str) -> bool:
        """判断标的在 TuShare 中是否为基金/ETF。

        通过 stock_classifier 初步分类后，用 fund_basic 确认。
        """
        result = classify(symbol)
        if result.type == "fund":
            # 用 fund_basic 确认（可能需要 exchange，但 classify 已知）
            ts_code = self._to_ts_code(symbol, result.exchange)
            fund_info = self._client.get_fund_basic(ts_code)
            if fund_info:
                return True
            # fund_basic 无数据 → fallback 到 stock
            logger.info(
                "[tushare] classify=%s but fund_basic empty for %s, fallback to stock",
                result.type, ts_code,
            )
        return False

    def _get_exchange(self, symbol: str, fallback_exchange: str) -> str:
        """获取分类器推断的交易所，若无则用参数传入的 fallback"""
        result = classify(symbol)
        return result.exchange or fallback_exchange

    # ─── 实时行情 ─────────────────────────────────────

    def get_current_price(self, symbol: str, exchange: str) -> CurrentPrice:
        """获取实时行情（降级：返回最近日 K 或 fund_daily 收盘价）"""
        ts_code = self._to_ts_code(symbol, exchange)
        close_price = 0.0
        trade_date = None

        if self._is_fund(symbol):
            close_price, trade_date = self._client.get_fund_latest_price(ts_code)

        if close_price <= 0:
            close_price, trade_date = self._client.get_latest_price(ts_code)

        # 校验
        if close_price <= 0:
            raise RuntimeError(
                f"TuShare: no price data for {ts_code}"
            )

        # 使用 A 股收盘时间 15:00 CST 作为 price_time
        if trade_date:
            dt = datetime.strptime(trade_date, "%Y%m%d")
            price_time = dt.replace(hour=15, minute=0, second=0, tzinfo=TZ_CST)
        else:
            price_time = datetime.now(TZ_CST)

        return CurrentPrice(
            symbol=symbol,
            exchange=exchange,
            price=close_price,
            price_time=price_time,
            currency="CNY",
            volume=None,
            source="tushare",
            data_quality="degraded",
        )

    # ─── 日 K 线 ──────────────────────────────────────

    def get_daily_kline(
        self,
        symbol: str,
        exchange: str,
        start_date: date,
        end_date: date,
    ) -> List[DailyKline]:
        """获取日 K 线数据（自动判断标的类型）"""
        ts_code = self._to_ts_code(symbol, exchange)
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")

        records = []
        if self._is_fund(symbol):
            records = self._client.get_fund_daily(ts_code, start_str, end_str)

        if not records:
            records = self._client.get_daily_kline(ts_code, start_str, end_str)

        result: List[DailyKline] = []
        for r in records:
            try:
                trade_date = r.get("trade_date", "")
                if isinstance(trade_date, str):
                    trade_date = datetime.strptime(trade_date, "%Y%m%d").date()
                elif isinstance(trade_date, datetime):
                    trade_date = trade_date.date()

                kline = DailyKline(
                    date=trade_date,
                    open=float(r.get("open", 0)),
                    high=float(r.get("high", 0)),
                    low=float(r.get("low", 0)),
                    close=float(r.get("close", 0)),
                    volume=float(r.get("vol", 0)),
                    amount=float(r.get("amount", 0)),
                )
                result.append(kline)
            except (ValueError, TypeError) as e:
                logger.warning("[tushare] skip kline record: %s, error: %s", r, e)
                continue

        return result

    # ─── 基本面 ───────────────────────────────────────

    def get_fundamentals(self, symbol: str, exchange: str) -> Fundamentals:
        """获取基本面数据（对基金仅返回名称）"""
        ts_code = self._to_ts_code(symbol, exchange)

        is_fund = self._is_fund(symbol)

        if is_fund:
            # 基金/ETF：用 fund_basic 获取名称，无 PE/PB
            fund_info = self._client.get_fund_basic(ts_code)
            name = (fund_info or {}).get("name", "")
            if not name:
                raise RuntimeError(f"TuShare: fund_basic not found for {ts_code}")
            return Fundamentals(
                symbol=symbol,
                exchange=exchange,
                name=name,
                sector=None,
                industry="ETF/基金",
                market_cap=None,
                pe_ratio=None,
                pb_ratio=None,
                source="tushare",
                data_date=date.today(),
            )

        # 股票：原有逻辑
        today_str = date.today().strftime("%Y%m%d")
        basic = self._client.get_stock_basic(ts_code) or {}
        daily_basic = self._client.get_daily_basic(ts_code, today_str)

        if not daily_basic:
            yesterday = (date.today() - timedelta(days=1)).strftime("%Y%m%d")
            daily_basic = self._client.get_daily_basic(ts_code, yesterday)

        name = basic.get("name", "")
        if not name:
            raise RuntimeError(
                f"TuShare: stock_basic not found for {ts_code}"
            )

        industry = basic.get("industry")
        sector = basic.get("area")

        pe = None
        pb = None
        market_cap = None
        if daily_basic:
            pe = float(daily_basic.get("pe", 0)) if daily_basic.get("pe") else None
            pb = float(daily_basic.get("pb", 0)) if daily_basic.get("pb") else None
            total_mv = daily_basic.get("total_mv")
            if total_mv:
                market_cap = float(total_mv) * 10000

        return Fundamentals(
            symbol=symbol,
            exchange=exchange,
            name=name,
            sector=sector,
            industry=industry,
            market_cap=market_cap,
            pe_ratio=pe,
            pb_ratio=pb,
            source="tushare",
            data_date=date.today(),
        )

    @property
    def capabilities(self) -> Set[str]:
        return {"kline", "fundamentals"}
