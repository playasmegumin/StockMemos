"""AKShareProvider — 港股数据源适配器

覆盖 HK 市场数据：
- 实时行情 → AKShare stock_hk_hist（最新日K收盘价）
- 日 K 线   → AKShare stock_hk_hist
- 基本面    → AKShare stock_hk_spot_em（实时全市场，缓存读取）

AKShare 从东方财富/新浪等公开数据源采集数据，无需 API Key。
"""

import logging
import time
from datetime import date, datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any

import akshare as ak

from app.services.market_data.provider_base import BaseProvider
from app.services.market_data.schemas import CurrentPrice, DailyKline, Fundamentals

logger = logging.getLogger(__name__)

TZ_CST = timezone(timedelta(hours=8))
# 港股收盘时间 16:00 HKT
HK_CLOSE_HOUR = 16
HK_CLOSE_MINUTE = 0


class AKShareProvider(BaseProvider):
    """港股数据源适配器（基于 AKShare）"""

    def __init__(self) -> None:
        self._spot_cache: Tuple[float, Optional[Dict[str, Any]]] = (0.0, None)
        """实时全市场缓存：(fetch_time, {symbol: row_dict})，缓存 60 秒"""
        logger.info("AKShareProvider initialized")

    # ─── 缓存工具 ─────────────────────────────────────

    def _get_spot_map(self) -> Dict[str, Any]:
        """获取港股实时行情全市场数据（缓存 60 秒）"""
        cache_time, cache_data = self._spot_cache
        now = time.time()
        if cache_data and (now - cache_time) < 60:
            return cache_data

        logger.info("[akshare] fetching HK spot market data...")
        try:
            df = ak.stock_hk_spot_em()
        except Exception as e:
            logger.error("[akshare] spot fetch failed: %s", e)
            return cache_data or {}

        if df is None or df.empty:
            logger.warning("[akshare] spot data empty")
            return cache_data or {}

        # 构建 symbol → row 映射
        spot_map: Dict[str, Any] = {}
        for _, row in df.iterrows():
            code = str(row.get("代码", "")).strip()
            if code:
                spot_map[code] = row

        self._spot_cache = (now, spot_map)
        logger.info("[akshare] spot cache updated: %d stocks", len(spot_map))
        return spot_map

    # ─── 实时行情 ───────────────────────────────────

    def get_current_price(self, symbol: str, exchange: str) -> CurrentPrice:
        """获取最新收盘价（通过 stock_hk_hist 取最近交易日）"""
        today_str = date.today().strftime("%Y%m%d")
        yesterday_str = (date.today() - timedelta(days=7)).strftime("%Y%m%d")

        try:
            df = ak.stock_hk_hist(
                symbol=symbol,
                period="daily",
                start_date=yesterday_str,
                end_date=today_str,
            )
        except Exception as e:
            logger.error("[akshare] hist failed for %s: %s", symbol, e)
            df = None

        if df is not None and not df.empty:
            last = df.iloc[-1]
            close = float(last.get("收盘", last.get("close", 0)))
            trade_date = last.get("日期", last.get("date", ""))
            if isinstance(trade_date, str):
                try:
                    dt = datetime.strptime(trade_date, "%Y-%m-%d")
                except ValueError:
                    dt = datetime.now()
            else:
                dt = datetime.now()
            price_time = dt.replace(
                hour=HK_CLOSE_HOUR, minute=HK_CLOSE_MINUTE, tzinfo=TZ_CST
            )

            return CurrentPrice(
                symbol=symbol,
                exchange=exchange,
                price=close,
                price_time=price_time,
                currency="HKD",
                volume=None,
                source="akshare",
                data_quality="degraded",
            )

        # 降级：从全市场 spot 数据取
        spot_map = self._get_spot_map()
        row = spot_map.get(symbol)
        if row is not None:
            close = float(row.get("最新价", 0))
            return CurrentPrice(
                symbol=symbol,
                exchange=exchange,
                price=close,
                price_time=datetime.now(TZ_CST),
                currency="HKD",
                volume=None,
                source="akshare",
                data_quality="degraded",
            )

        raise RuntimeError(f"AKShare: no data for {symbol}")

    # ─── 日 K 线 ─────────────────────────────────────

    def get_daily_kline(
        self,
        symbol: str,
        exchange: str,
        start_date: date,
        end_date: date,
    ) -> List[DailyKline]:
        """获取日 K 线数据（stock_hk_hist）"""
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")

        try:
            df = ak.stock_hk_hist(
                symbol=symbol,
                period="daily",
                start_date=start_str,
                end_date=end_str,
            )
        except Exception as e:
            logger.error("[akshare] kline failed for %s: %s", symbol, e)
            return []

        if df is None or df.empty:
            logger.warning("[akshare] no kline data for %s", symbol)
            return []

        result: List[DailyKline] = []
        for _, row in df.iterrows():
            try:
                trade_date_str = row.get("日期", row.get("date", ""))
                if isinstance(trade_date_str, str):
                    trade_date = datetime.strptime(
                        trade_date_str, "%Y-%m-%d"
                    ).date()
                else:
                    continue

                kline = DailyKline(
                    date=trade_date,
                    open=float(row.get("开盘", row.get("open", 0))),
                    high=float(row.get("最高", row.get("high", 0))),
                    low=float(row.get("最低", row.get("low", 0))),
                    close=float(row.get("收盘", row.get("close", 0))),
                    volume=float(row.get("成交量", row.get("volume", 0))),
                    amount=float(row.get("成交额", row.get("amount", 0))),
                )
                result.append(kline)
            except (ValueError, TypeError) as e:
                logger.warning("[akshare] skip kline row: %s", e)
                continue

        return result

    # ─── 基本面 ─────────────────────────────────────

    def get_fundamentals(self, symbol: str, exchange: str) -> Fundamentals:
        """获取基本面数据（从全市场 spot 数据解析）"""
        spot_map = self._get_spot_map()
        row = spot_map.get(symbol)

        if row is None:
            raise RuntimeError(f"AKShare: no fundamentals for {symbol}")

        name = str(row.get("名称", ""))
        price = float(row.get("最新价", 0))
        pe = float(row.get("市盈率-动态", 0)) or None
        pb = float(row.get("市净率", 0)) or None
        market_cap = float(row.get("总市值", 0)) or None

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
        return {"price", "kline", "fundamentals"}
