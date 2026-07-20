"""TuShare Pro 客户端封装

封装目标：
- 从 app.config 读取 Token
- 请求带 3 次重试 + 指数退避（应对 TuShare 频率限制）
- 内存缓存（1 小时 TTL），避免重复拉取相同数据
- 自动记录每次请求输入输出，便于调试
"""

import time
import logging
from typing import Any, Dict, List, Optional
import tushare as ts
import pandas as pd
from app.config import settings

logger = logging.getLogger(__name__)


class TushareClient:
    """TuShare Pro API 统一封装

    使用示例：
        client = TushareClient()
        kline = client.get_daily_kline("000001.SZ", "20240101", "20240630")
    """

    def __init__(self) -> None:
        self._token = settings.tushare_token
        if not self._token:
            raise ValueError("TUSHARE_TOKEN 未配置，请检查 .env 文件")

        self._pro = ts.pro_api(self._token)
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._cache_ttl = 3600  # 1 小时
        logger.info("TushareClient initialized")

    # ─── 缓存工具 ─────────────────────────────────────

    def _cache_key(self, func_name: str, **kwargs) -> str:
        """根据接口名和参数生成缓存键"""
        sorted_kwargs = sorted(kwargs.items())
        return f"{func_name}:{sorted_kwargs}"

    def _get_cache(self, key: str) -> Optional[Any]:
        """读取缓存，TTL 过期则失效"""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                logger.debug("[tushare] cache hit: %s", key)
                return value
        return None

    def _set_cache(self, key: str, value: Any) -> None:
        """写入缓存"""
        self._cache[key] = (value, time.time())

    # ─── 核心请求层（重试 + 日志）──────────────────────

    def _call_with_retry(self, func_name: str, **kwargs) -> Optional[pd.DataFrame]:
        """调用 TuShare 接口，3 次重试 + 指数退避"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(
                    "[tushare] calling %s %s (attempt %d/%d)",
                    func_name, kwargs, attempt + 1, max_retries,
                )
                df = getattr(self._pro, func_name)(**kwargs)
                if df is not None and not df.empty:
                    logger.info("[tushare] %s success, rows=%d", func_name, len(df))
                else:
                    logger.warning("[tushare] %s returned empty", func_name)
                return df
            except Exception as e:
                wait = 2 ** attempt  # 1, 2, 4 秒
                logger.warning(
                    "[tushare] %s attempt %d failed: %s, retrying in %ds",
                    func_name, attempt + 1, e, wait,
                )
                if attempt < max_retries - 1:
                    time.sleep(wait)
                else:
                    logger.error(
                        "[tushare] %s failed after %d attempts: %s",
                        func_name, max_retries, e,
                    )
                    raise RuntimeError(
                        f"TuShare {func_name} failed: {e}"
                    ) from e
        return None

    def _call(self, func_name: str, use_cache: bool = True, **kwargs) -> Optional[pd.DataFrame]:
        """统一调用入口：缓存 → 请求 → 写缓存"""
        key = self._cache_key(func_name, **kwargs)
        if use_cache:
            cached = self._get_cache(key)
            if cached is not None:
                return cached
        df = self._call_with_retry(func_name, **kwargs)
        if use_cache and df is not None:
            self._set_cache(key, df)
        return df

    # ─── 辅助工具 ─────────────────────────────────────

    def get_latest_price(self, stock_code: str) -> tuple[float, str | None]:
        """获取最新交易日收盘价 + 交易日（缓存 1 小时）

        Returns:
            (price, trade_date_str)  — 如 (124.12, "20260703")
            (0.0, None)              — 无数据
        """
        df = self._call(
            "daily",
            ts_code=stock_code,
            limit=1,
            fields="ts_code,trade_date,close",
        )
        if df is not None and not df.empty:
            close_price = df.iloc[0]["close"]
            trade_date = str(df.iloc[0]["trade_date"])
            return float(close_price), trade_date
        return 0.0, None

    def get_stock_basic(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取股票基本信息（名称、行业、地区、上市日期）"""
        df = self._call(
            "stock_basic",
            ts_code=stock_code,
            fields="ts_code,name,industry,area,list_date",
        )
        if df is not None and not df.empty:
            return df.where(pd.notnull(df), None).iloc[0].to_dict()
        return None

    def get_daily_kline(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        freq: str = "D",
    ) -> List[Dict[str, Any]]:
        """获取 K 线数据

        Args:
            stock_code: 如 000001.SZ
            start_date: 如 20240101
            end_date: 如 20240630
            freq: D=日, W=周, M=月
        """
        func_map = {"D": "daily", "W": "weekly", "M": "monthly"}
        func_name = func_map.get(freq, "daily")
        df = self._call(
            func_name,
            ts_code=stock_code,
            start_date=start_date,
            end_date=end_date,
        )
        if df is not None and not df.empty:
            records = df.where(pd.notnull(df), None).to_dict(orient="records")
            return records
        return []

    def get_daily_basic(self, stock_code: str, trade_date: str) -> Optional[Dict[str, Any]]:
        """获取每日指标（PE, PB, turnover_rate, volume_ratio 等）"""
        df = self._call(
            "daily_basic",
            ts_code=stock_code,
            trade_date=trade_date,
        )
        if df is not None and not df.empty:
            return df.where(pd.notnull(df), None).iloc[0].to_dict()
        return None

    def get_moneyflow(self, stock_code: str, trade_date: str) -> Optional[Dict[str, Any]]:
        """获取资金流向（需要 TuShare Pro 积分权限）"""
        df = self._call(
            "moneyflow",
            ts_code=stock_code,
            trade_date=trade_date,
        )
        if df is not None and not df.empty:
            return df.where(pd.notnull(df), None).iloc[0].to_dict()
        return None

    # ─── 基金/ETF 接口 ────────────────────────────────

    def get_fund_basic(self, ts_code: str) -> Optional[Dict[str, Any]]:
        """获取基金基本信息（ETF/LOF 等）

        Args:
            ts_code: 如 518600.SH

        Returns:
            {"ts_code", "name", "management", "market", ...} 或 None（无数据）
        """
        df = self._call(
            "fund_basic",
            ts_code=ts_code,
            fields="ts_code,name,management,custodian,found_date,issue_date,market,issue_amount",
        )
        if df is not None and not df.empty:
            return df.where(pd.notnull(df), None).iloc[0].to_dict()
        return None

    def get_fund_daily(
        self,
        ts_code: str,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """获取基金日行情（含 ETF/LOF 的日 K 线）

        Args:
            ts_code: 如 518600.SH
            start_date: 如 20240101
            end_date: 如 20240630

        Returns:
            [{"ts_code", "trade_date", "open", "high", "low", "close",
              "pre_close", "pct_chg", "vol", "amount"}, ...]
        """
        df = self._call(
            "fund_daily",
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
        )
        if df is not None and not df.empty:
            records = df.where(pd.notnull(df), None).to_dict(orient="records")
            return records
        return []

    def get_fund_latest_price(self, ts_code: str) -> tuple[float, str | None]:
        """获取基金/ETF 最新交易日收盘价

        Returns:
            (price, trade_date_str)  — 如 (8.902, "20260710")
            (0.0, None)              — 无数据
        """
        df = self._call(
            "fund_daily",
            ts_code=ts_code,
            limit=1,
            fields="ts_code,trade_date,close",
        )
        if df is not None and not df.empty:
            close_price = df.iloc[0]["close"]
            trade_date = str(df.iloc[0]["trade_date"])
            return float(close_price), trade_date
        return 0.0, None
