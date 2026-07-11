"""MarketDataService — 行情数据业务封装层

职责：
- 内存缓存管理（实时行情 60s TTL）
- DB 读写（日 K 来自 kline_daily 表，基本面来自 stock_analyze.fundamentals_data）
- Provider 编排（按 exchange 路由到对应数据源）
- 批量刷新（遍历所有 Stock，拉取最新数据）
"""

import time
import logging
from datetime import date, datetime, timedelta, timezone

TZ_CST = timezone(timedelta(hours=8))
from typing import Dict, List, Optional, Tuple, Any

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.services.market_data.schemas import CurrentPrice, DailyKline, Fundamentals
from app.services.market_data.provider_router import ProviderRouter
from app.models.stock import Stock
from app.models.stock_analyze import StockAnalyze
from app.models.kline_daily import KlineDaily

logger = logging.getLogger(__name__)


class MarketDataService:
    """行情数据业务封装层"""

    # 实时行情缓存 TTL（秒）
    PRICE_CACHE_TTL = 60

    def __init__(self, db: Session) -> None:
        self._db = db
        self._router = ProviderRouter()
        # 内存缓存：stock_id → (CurrentPrice, timestamp)
        self._price_cache: Dict[str, Tuple[CurrentPrice, float]] = {}

    # ─── 实时行情 ───────────────────────────────────

    def get_current_price(self, stock_id: str) -> Optional[CurrentPrice]:
        """获取实时行情（内存缓存 TTL 60 秒，穿透则调用 Provider）"""
        # 检查缓存
        now = time.time()
        cached = self._price_cache.get(stock_id)
        if cached and (now - cached[1]) < self.PRICE_CACHE_TTL:
            logger.debug("[market] price cache hit: %s", stock_id)
            return cached[0]

        # 查 DB 获取 Stock 的 exchange + symbol
        stock = self._db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            logger.warning("[market] stock not found: %s", stock_id)
            return None

        # 调用 Provider
        provider = self._router.get_provider(stock.exchange)
        try:
            price = provider.get_current_price(stock.symbol, stock.exchange)
            self._price_cache[stock_id] = (price, now)
            return price
        except Exception as e:
            logger.warning(
                "[market] provider price failed for %s, degrading to DB kline: %s",
                stock_id, e,
            )
            # 降级：从 kline_daily 表获取最近收盘价
            latest = (
                self._db.query(KlineDaily)
                .filter(KlineDaily.stock_id == stock_id)
                .order_by(KlineDaily.trade_date.desc())
                .first()
            )
            if latest:
                price = CurrentPrice(
                    symbol=stock.symbol,
                    exchange=stock.exchange,
                    price=float(latest.close),
                    price_time=datetime.combine(
                        latest.trade_date, datetime.min.time(), tzinfo=TZ_CST
                    ),
                    currency=stock.currency,
                    volume=None,
                    source=stock.exchange,
                    data_quality="degraded",
                )
                self._price_cache[stock_id] = (price, now)
                return price

            logger.error("[market] DB degradation also failed for %s", stock_id)
            return None

    # ─── 日 K 线 ─────────────────────────────────────

    def get_daily_kline(
        self,
        stock_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[DailyKline]:
        """获取日 K 线（优先 DB，无数据则调用 Provider 拉取并持久化）"""
        stock = self._db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            logger.warning("[market] stock not found: %s", stock_id)
            return []

        # 查询 DB
        query = self._db.query(KlineDaily).filter(
            KlineDaily.stock_id == stock_id
        )
        if start_date:
            query = query.filter(KlineDaily.trade_date >= start_date)
        if end_date:
            query = query.filter(KlineDaily.trade_date <= end_date)
        query = query.order_by(KlineDaily.trade_date.asc())

        db_records = query.all()
        if db_records:
            return self._kline_orm_to_schema(db_records)

        # DB 无数据 → 调用 Provider 拉取
        provider = self._router.get_provider(stock.exchange)
        try:
            # 默认拉取近 1 年数据
            end = end_date or date.today()
            start = start_date or (end - timedelta(days=365))
            klines = provider.get_daily_kline(stock.symbol, stock.exchange, start, end)
        except Exception as e:
            logger.error("[market] get_daily_kline failed: %s, error: %s", stock_id, e)
            return []

        # 持久化到 DB
        if klines:
            self._upsert_kline_batch(stock_id, klines)

        return klines

    def _kline_orm_to_schema(self, records: List[KlineDaily]) -> List[DailyKline]:
        """将 ORM KlineDaily 转换为 Pydantic DailyKline"""
        return [
            DailyKline(
                date=r.trade_date,
                open=float(r.open),
                high=float(r.high),
                low=float(r.low),
                close=float(r.close),
                volume=float(r.volume),
                amount=float(r.amount),
            )
            for r in records
        ]

    def _upsert_kline_batch(self, stock_id: str, klines: List[DailyKline]) -> None:
        """批量 UPSERT 日 K 线到 kline_daily 表

        使用 PostgreSQL ON CONFLICT DO UPDATE 实现幂等写入。
        """
        if not klines:
            return

        # 使用原生 SQL 实现 UPSERT
        values_clauses = []
        params: Dict[str, Any] = {}
        now_str = datetime.utcnow().isoformat()

        for i, k in enumerate(klines):
            prefix = f"k{i}"
            params[f"{prefix}_sid"] = stock_id
            params[f"{prefix}_date"] = k.date
            params[f"{prefix}_open"] = k.open
            params[f"{prefix}_high"] = k.high
            params[f"{prefix}_low"] = k.low
            params[f"{prefix}_close"] = k.close
            params[f"{prefix}_vol"] = k.volume
            params[f"{prefix}_amt"] = k.amount
            params[f"{prefix}_now"] = now_str
            values_clauses.append(
                f"(:{prefix}_sid, :{prefix}_date, :{prefix}_open, :{prefix}_high, "
                f":{prefix}_low, :{prefix}_close, :{prefix}_vol, :{prefix}_amt, :{prefix}_now)"
            )

        sql = f"""
            INSERT INTO kline_daily
                (stock_id, trade_date, open, high, low, close, volume, amount, created_at)
            VALUES {', '.join(values_clauses)}
            ON CONFLICT (stock_id, trade_date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                amount = EXCLUDED.amount
        """
        self._db.execute(text(sql), params)
        self._db.commit()
        logger.info("[market] upserted %d klines for stock %s", len(klines), stock_id)

    # ─── 基本面 ─────────────────────────────────────

    def _ensure_analyze(self, stock_id: str) -> StockAnalyze:
        """确保 StockAnalyze 记录存在，不存在则自动创建"""
        analyze = (
            self._db.query(StockAnalyze)
            .filter(StockAnalyze.stock_id == stock_id)
            .first()
        )
        if not analyze:
            analyze = StockAnalyze(
                id=str(__import__("uuid").uuid4()),
                stock_id=stock_id,
            )
            self._db.add(analyze)
            self._db.commit()
            self._db.refresh(analyze)
            logger.info("[market] auto-created StockAnalyze for %s", stock_id)
        return analyze

    def get_fundamentals(self, stock_id: str) -> Optional[Fundamentals]:
        """获取基本面数据

        优先返回 DB JSONB 数据；若空则调用 Provider 拉取、
        持久化后再返回。
        """
        stock = self._db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            logger.warning("[market] stock not found: %s", stock_id)
            return None

        analyze = self._ensure_analyze(stock_id)

        # DB 已有数据 → 校验有效性后返回（name 为空则视为空壳，重新拉取）
        if analyze.fundamentals_data:
            fd = analyze.fundamentals_data
            if isinstance(fd, dict) and fd.get("name"):
                return Fundamentals(**fd)
            # 数据无效（空壳），清掉并重新拉取
            logger.warning(
                "[market] stale empty fundamentals for %s, refetching", stock_id
            )
            analyze.fundamentals_data = None

        # DB 无数据 → 调用 Provider 拉取
        provider = self._router.get_provider(stock.exchange)
        try:
            fundamentals = provider.get_fundamentals(stock.symbol, stock.exchange)
        except Exception as e:
            logger.error(
                "[market] get_fundamentals failed: %s, error: %s", stock_id, e
            )
            return None

        # 持久化
        if fundamentals:
            analyze.fundamentals_data = fundamentals.model_dump(mode="json")
            self._db.commit()
            logger.info("[market] fetched & persisted fundamentals for %s", stock_id)

        return fundamentals

    # ─── 批量刷新 ───────────────────────────────────

    def refresh_all(self) -> Dict[str, int]:
        """批量刷新所有股票的日 K + 基本面

        Returns:
            {"stocks_processed": int, "klines_total": int, "fundamentals_updated": int}
        """
        stocks = self._db.query(Stock).all()
        stats = {"stocks_processed": 0, "klines_total": 0, "fundamentals_updated": 0}

        end_date = date.today()
        start_date = end_date - timedelta(days=7)  # 拉取近 7 天

        for stock in stocks:
            try:
                provider = self._router.get_provider(stock.exchange)

                # 拉取日 K
                klines = provider.get_daily_kline(
                    stock.symbol, stock.exchange, start_date, end_date
                )
                if klines:
                    self._upsert_kline_batch(stock.id, klines)
                    stats["klines_total"] += len(klines)

                # 拉取基本面
                fundamentals = provider.get_fundamentals(
                    stock.symbol, stock.exchange
                )
                if fundamentals:
                    analyze = self._ensure_analyze(stock.id)
                    analyze.fundamentals_data = fundamentals.model_dump(mode="json")
                    stats["fundamentals_updated"] += 1

                stats["stocks_processed"] += 1

            except Exception as e:
                logger.error(
                    "[market] refresh failed for stock %s (%s.%s): %s",
                    stock.id, stock.exchange, stock.symbol, e,
                )
                continue

        self._db.commit()
        logger.info("[market] refresh_all complete: %s", stats)
        return stats

    def refresh_single(self, stock_id: str,
                       days: int = 30) -> Dict[str, int]:
        """刷新单支股票的日 K + 基本面

        Args:
            stock_id: 股票 ID
            days: 拉取最近 N 个交易日的数据（首次建仓默认 30 天）

        Returns:
            {"klines": int, "fundamentals": int}
        """
        stock = self._db.query(Stock).filter(Stock.id == stock_id).first()
        if not stock:
            return {"klines": 0, "fundamentals": 0}

        stats = {"klines": 0, "fundamentals": 0}
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        try:
            provider = self._router.get_provider(stock.exchange)

            klines = provider.get_daily_kline(
                stock.symbol, stock.exchange, start_date, end_date
            )
            if klines:
                self._upsert_kline_batch(stock.id, klines)
                stats["klines"] = len(klines)

            fundamentals = provider.get_fundamentals(
                stock.symbol, stock.exchange
            )
            if fundamentals:
                analyze = self._ensure_analyze(stock.id)
                analyze.fundamentals_data = fundamentals.model_dump(mode="json")
                stats["fundamentals"] = 1

            self._db.commit()

        except Exception as e:
            logger.error(
                "[market] refresh_single failed for stock %s (%s): %s",
                stock_id, stock.exchange if stock else "?", e,
            )

        return stats

    def refresh_fundamentals(self) -> Dict[str, int]:
        """仅批量刷新所有股票基本面

        Returns:
            {"stocks_processed": int, "fundamentals_updated": int}
        """
        stocks = self._db.query(Stock).all()
        stats = {"stocks_processed": 0, "fundamentals_updated": 0}

        for stock in stocks:
            try:
                provider = self._router.get_provider(stock.exchange)
                fundamentals = provider.get_fundamentals(
                    stock.symbol, stock.exchange
                )
                if fundamentals:
                    analyze = self._ensure_analyze(stock.id)
                    analyze.fundamentals_data = fundamentals.model_dump(mode="json")
                    stats["fundamentals_updated"] += 1

                stats["stocks_processed"] += 1

            except Exception as e:
                logger.error(
                    "[market] refresh_fundamentals failed for stock %s (%s.%s): %s",
                    stock.id, stock.exchange, stock.symbol, e,
                )
                continue

        self._db.commit()
        logger.info("[market] refresh_fundamentals complete: %s", stats)
        return stats
