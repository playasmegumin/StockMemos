"""Diagnostics API

后端各外部服务连通性检测。

Endpoints:
    GET  /api/diagnostics?scope=all|datasource|llm  — 按范围执行诊断
"""

import os
import time
import logging
from fastapi import APIRouter, Query

logger = logging.getLogger(__name__)

router = APIRouter()

# ─── 超时控制 ────────────────────────────────────


def _run_with_timeout(func, args=(), kwargs=None, timeout=10):
    """同步执行 func，超时抛 TimeoutError"""
    import threading

    result = [None]
    exception = [None]
    done = threading.Event()

    def worker():
        try:
            result[0] = func(*args, **(kwargs or {}))
        except Exception as e:
            exception[0] = e
        finally:
            done.set()

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    if not done.wait(timeout=timeout):
        raise TimeoutError(f"timeout after {timeout}s")
    if exception[0]:
        raise exception[0]
    return result[0]


class TimeoutError(RuntimeError):
    pass


# ─── 动态「被用于」信息 ────────────────────────────


def _get_datasource_usage(name: str) -> str:
    """根据环境变量确定该数据源服务于哪些市场"""
    cn = os.getenv("MARKET_DATA_SOURCE_CN", "tushare").lower()
    hk = os.getenv("MARKET_DATA_SOURCE_HK", "yfinance").lower()
    us = os.getenv("MARKET_DATA_SOURCE_US", "yfinance").lower()
    name_lower = name.lower()

    # 规范化名称映射（env 值和显示名的对应关系）
    name_norm = name_lower.replace("&", "").replace("(", "").replace(")", "").replace(" ", "")
    cn_norm = cn.replace("&", "").replace("(", "").replace(")", "").replace(" ", "")
    hk_norm = hk.replace("&", "").replace("(", "").replace(")", "").replace(" ", "")
    us_norm = us.replace("&", "").replace("(", "").replace(")", "").replace(" ", "")

    markets = []
    if cn_norm == name_norm or (name_lower == "tushare" and cn == "tushare"):
        markets.append("A 股")
    if hk_norm == name_norm:
        markets.append("港股")
    if us_norm == name_norm:
        markets.append("美股")

    if not markets:
        return "未配置"
    if len(markets) == 1:
        return markets[0]
    return "、".join(markets)


def _get_llm_usage(name: str) -> str:
    """根据 API Key 判断 LLM 是否已配置"""
    env_map = {
        "DeepSeek": "DEEPSEEK_API_KEY",
        "OpenAI": "OPENAI_API_KEY",
        "Claude (Anthropic)": "ANTHROPIC_API_KEY",
    }
    key = os.getenv(env_map.get(name, ""), "")
    return "已启用" if key else "未配置"


def _get_registration_type(name: str) -> str:
    """服务注册/接入方式"""
    registry = {
        "TuShare": "API Key",
        "AKShare": "免费公开接口",
        "Yahoo Finance (US)": "免费公开接口",
        "Yahoo Finance (HK)": "免费公开接口",
        "Finnhub": "API Key",
        "DeepSeek": "API Key",
        "OpenAI": "API Key",
        "Claude (Anthropic)": "API Key",
    }
    return registry.get(name, "-")


# ─── 服务定义（构建时确定的元数据） ────────────────

SERVICE_DEFS = [
    {"name": "TuShare", "category": "datasource"},
    {"name": "AKShare", "category": "datasource"},
    {"name": "Yahoo Finance (US)", "category": "datasource"},
    {"name": "Yahoo Finance (HK)", "category": "datasource"},
    {"name": "Finnhub", "category": "datasource"},
    {"name": "DeepSeek", "category": "llm"},
    {"name": "OpenAI", "category": "llm"},
    {"name": "Claude (Anthropic)", "category": "llm"},
]


def _get_service_metadata(service: dict) -> dict:
    """为服务定义添加动态元数据（usage/registration_type）"""
    name = service["name"]
    cat = service["category"]
    usage = (
        _get_datasource_usage(name) if cat == "datasource"
        else _get_llm_usage(name)
    )
    return {
        "name": name,
        "category": cat,
        "usage": usage,
        "registration_type": _get_registration_type(name),
    }


# ─── 各检查项 ────────────────────────────────────


def _check_tushare():
    import tushare as ts
    token = os.getenv("TUSHARE_TOKEN", "")
    if not token:
        return {"status": "skipped", "latency_ms": 0, "error": "TUSHARE_TOKEN 未配置"}
    try:
        ts.set_token(token)
        pro = ts.pro_api()
        start = time.monotonic()
        df = pro.stock_basic(exchange="", list_status="L",
                             fields="ts_code", limit=1)
        elapsed = int((time.monotonic() - start) * 1000)
        if df is not None and len(df) > 0:
            return {"status": "ok", "latency_ms": elapsed, "error": None}
        return {"status": "error", "latency_ms": elapsed, "error": "empty response"}
    except Exception as e:
        return {"status": "error", "latency_ms": 0, "error": str(e)}


def _check_yfinance(tag, symbol):
    import yfinance as yf
    try:
        tk = yf.Ticker(symbol)
        start = time.monotonic()
        info = tk.info
        elapsed = int((time.monotonic() - start) * 1000)
        name = info.get("longName") or info.get("shortName") or ""
        if name:
            return {"status": "ok", "latency_ms": elapsed, "error": None}
        return {"status": "error", "latency_ms": elapsed, "error": "no name returned"}
    except Exception as e:
        return {"status": "error", "latency_ms": 0, "error": str(e)}


def _check_finnhub():
    key = os.getenv("FINNHUB_API_KEY", "")
    if not key:
        return {"status": "skipped", "latency_ms": 0, "error": "FINNHUB_API_KEY 未配置"}
    try:
        import finnhub
        client = finnhub.Client(api_key=key)
        start = time.monotonic()
        client.quote("AAPL")
        elapsed = int((time.monotonic() - start) * 1000)
        return {"status": "ok", "latency_ms": elapsed, "error": None}
    except Exception as e:
        return {"status": "error", "latency_ms": 0, "error": str(e)}


def _check_akshare():
    """Check AKShare free API (mainly for HK/historical data)"""
    try:
        import akshare as ak
        start = time.monotonic()
        # Try fetching SSE Composite Index as a simple connectivity check
        df = ak.stock_zh_index_daily(symbol="sh000001")
        elapsed = int((time.monotonic() - start) * 1000)
        if df is not None and len(df) > 0:
            return {"status": "ok", "latency_ms": elapsed, "error": None}
        return {"status": "error", "latency_ms": elapsed, "error": "empty response"}
    except ImportError:
        return {"status": "skipped", "latency_ms": 0, "error": "akshare 未安装"}
    except Exception as e:
        return {"status": "error", "latency_ms": 0, "error": str(e)}


def _check_llm(env_var, display_name):
    val = os.getenv(env_var, "")
    if not val:
        return {"status": "skipped", "latency_ms": 0, "error": f"{env_var} 未配置"}
    if len(val) > 8:
        return {"status": "ok", "latency_ms": 0, "error": None}
    return {"status": "error", "latency_ms": 0, "error": f"{env_var} 格式异常"}


def _read_version():
    version_file = os.path.join(os.path.dirname(__file__), "..", "..", "VERSION")
    version_file = os.path.normpath(version_file)
    info = {"project_version": "unknown", "db_version": "unknown"}
    if os.path.isfile(version_file):
        with open(version_file) as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    info[k.strip()] = v.strip()
    try:
        from alembic.migration import MigrationContext
        from sqlalchemy import create_engine
        from app.config import settings as app_settings
        engine = create_engine(app_settings.database_url)
        with engine.connect() as conn:
            ctx = MigrationContext.configure(conn)
            info["db_version"] = ctx.get_current_revision() or "none"
    except Exception:
        info["db_version"] = "unknown"
    return info


# ─── 统一诊断端点 ────────────────────────────────


# ─── 静态服务元数据端点 ────────────────────────────

_SERVICE_METADATA_CACHE = None


def _get_all_service_metadata() -> list:
    """返回所有服务的元数据（构建时确定的静态信息）"""
    global _SERVICE_METADATA_CACHE
    if _SERVICE_METADATA_CACHE is None:
        _SERVICE_METADATA_CACHE = [_get_service_metadata(s) for s in SERVICE_DEFS]
    return _SERVICE_METADATA_CACHE


@router.get("/diagnostics/services")
def list_services():
    """返回静态服务元数据（名称/被用于/注册方式），不做延迟检测"""
    return {"services": _get_all_service_metadata()}


# ─── 动态诊断端点 ────────────────────────────────

# 检查函数映射（name → check_fn）
_CHECK_FN_MAP = {
    "TuShare": _check_tushare,
    "AKShare": _check_akshare,
    "Yahoo Finance (US)": lambda: _check_yfinance("US", "SPY"),
    "Yahoo Finance (HK)": lambda: _check_yfinance("HK", "0700.HK"),
    "Finnhub": _check_finnhub,
    "DeepSeek": lambda: _check_llm("DEEPSEEK_API_KEY", "DeepSeek"),
    "OpenAI": lambda: _check_llm("OPENAI_API_KEY", "OpenAI"),
    "Claude (Anthropic)": lambda: _check_llm("ANTHROPIC_API_KEY", "Claude"),
}


@router.get("/diagnostics")
def run_diagnostics(
    scope: str = Query("all", pattern="^(all|datasource|llm)$"),
):
    """全量诊断 — 按 scope 执行串行检查"""
    start_total = time.monotonic()
    results = []

    for svc in SERVICE_DEFS:
        name = svc["name"]
        category = svc["category"]
        if scope == "datasource" and category != "datasource":
            continue
        if scope == "llm" and category != "llm":
            continue

        check_fn = _CHECK_FN_MAP.get(name)
        if check_fn is None:
            continue

        try:
            r = _run_with_timeout(check_fn, timeout=10)
        except TimeoutError:
            r = {"status": "error", "latency_ms": 0, "error": "timeout (10s)"}
        except Exception as e:
            r = {"status": "error", "latency_ms": 0, "error": str(e)}

        meta = _get_service_metadata(svc)
        results.append({
            **meta,
            **r,
            "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })

    versions = _read_version()
    total_elapsed = int((time.monotonic() - start_total) * 1000)

    return {
        "services": results,
        "versions": versions,
        "total_latency_ms": total_elapsed,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
