"""个股 CRUD API

Endpoints:
    POST   /api/stocks              — 创建个股
    GET    /api/stocks               — 获取个股列表
    GET    /api/stocks/{id}          — 获取单条个股
    PUT    /api/stocks/{id}          — 更新个股
    DELETE /api/stocks/{id}          — 删除个股（级联删交易记录）
"""

from typing import List, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models.stock import Stock
from app.schemas.stock import StockCreate, StockUpdate, StockResponse
from app.services.market_data.market_data_service import MarketDataService
from app.services.market_data.provider_router import ProviderRouter
from app.services.tushare_client import TushareClient
from app.services.market_data.stock_classifier import (
    classify as classify_stock,
    normalize_symbol as normalize_stock_symbol,
)

router = APIRouter()

# 交易所 → 货币映射
_EXCHANGE_CURRENCY = {
    "SH": "CNY", "SZ": "CNY", "CN": "CNY",
    "HK": "HKD",
    "US": "USD",
}


# ────────────────────────────────
# 股票查询（按代码自动获取名称）
# ────────────────────────────────
# 设计决策（2026-07-10）：
#   用户不可手动指定交易所，全部由分类器根据代码决定。
#   exchange 参数保留为可选，用于覆盖或兼容旧接口。

@router.get("/lookup")
def lookup_stock(symbol: str, exchange: Optional[str] = None):
    """根据股票代码查询股票信息

    从 symbol 自动推断交易所和品种类型。
    可选传入 exchange 参数用于覆盖分类器结果。
    """
    # 分类器推断交易所
    result = classify_stock(symbol)
    exchange = exchange or result.exchange

    if not exchange:
        raise HTTPException(
            status_code=400,
            detail=f"无法推断交易所: {symbol}",
        )

    # 若有交易所后缀（如 00700.HK），剥离后缀，只传递纯代码给 Provider
    clean_symbol = symbol
    if '.' in symbol:
        parts = symbol.rsplit('.', 1)
        if len(parts) == 2 and parts[1].upper() in ('SH', 'SZ', 'HK', 'US'):
            clean_symbol = parts[0]

    currency = _EXCHANGE_CURRENCY.get(exchange, "USD")
    name = None

    # 尝试当前数据源查询名称
    router_p = ProviderRouter()
    try:
        provider = router_p.get_provider(exchange)
    except Exception:
        provider = None

    # 尝试从 Provider 获取名称（通过 fundamentals）
    if provider is not None:
        try:
            fund = provider.get_fundamentals(clean_symbol, exchange)
            if fund and fund.name:
                name = fund.name
        except Exception:
            pass

    # TuShare 兜底（Provider 未返回时直接查）
    if not name and exchange in ("SH", "SZ"):
        try:
            ts_client = TushareClient()
            ts_code = f"{clean_symbol}.{exchange}"
            basic = ts_client.get_stock_basic(ts_code)
            if basic and basic.get("name"):
                name = basic["name"]
            if not name:
                # 可能是基金，查 fund_basic
                fund_info = ts_client.get_fund_basic(ts_code)
                if fund_info and fund_info.get("name"):
                    name = fund_info["name"]
        except Exception:
            pass

    # Finnhub 兜底
    if not name and exchange == "US":
        try:
            import finnhub
            from app.config import settings as app_settings
            if app_settings.finnhub_api_key:
                fc = finnhub.Client(api_key=app_settings.finnhub_api_key)
                profile = fc.company_profile2(symbol=clean_symbol)
                if profile and profile.get("name"):
                    name = profile["name"]
        except Exception:
            pass

    # yfinance 兜底（港股/其他）
    if not name:
        try:
            import yfinance as yf
            if exchange == "HK":
                yf_symbol = clean_symbol.lstrip("0")
                ticker = yf.Ticker(f"{yf_symbol}.HK")
            else:
                ticker = yf.Ticker(clean_symbol)
            info = ticker.info or {}
            name = info.get("longName") or info.get("shortName")
        except Exception:
            pass

    if not name:
        raise HTTPException(
            status_code=404,
            detail=f"无法自动获取股票名称: {exchange}/{clean_symbol}",
        )

    return {"name": name, "currency": currency}


# ────────────────────────────────
# 辅助函数：ORM → Pydantic 响应转换
# ────────────────────────────────

def _to_stock_response(item: Stock) -> StockResponse:
    """将 Stock ORM 对象转换为 Pydantic 响应（处理 Decimal）"""
    return StockResponse(
        id=item.id,
        exchange=item.exchange,
        symbol=item.symbol,
        name=item.name,
        currency=item.currency,
        position=float(item.position) if item.position is not None else 0.0,
        historical_pnl=float(item.historical_pnl) if item.historical_pnl is not None else 0.0,
        created_at=str(item.created_at) if item.created_at else None,
        updated_at=str(item.updated_at) if item.updated_at else None,
    )


# 个股创建后后台预拉 K 线
def _background_refresh_kline(stock_id: str):
    try:
        db = SessionLocal()
        service = MarketDataService(db)
        service.refresh_single(stock_id, days=30)
        db.close()
    except Exception:
        pass


# ────────────────────────────────
# 创建个股
# ────────────────────────────────

@router.post("", response_model=StockResponse, status_code=status.HTTP_201_CREATED)
def create_stock(data: StockCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """录入新个股（只需 symbol，exchange 和 currency 自动推断）

    设计决策（2026-07-10）：
        用户不可手动指定交易所，全部由分类器根据代码决定。
        exchange 和 currency 参数保留为可选，用于覆盖或兼容旧接口。
    """
    # 自动推断 exchange 和 currency
    exchange = data.exchange
    currency = data.currency
    if not exchange:
        result = classify_stock(data.symbol)
        exchange = result.exchange
    if not currency:
        currency = _EXCHANGE_CURRENCY.get(exchange, "USD")

    if not exchange:
        raise HTTPException(
            status_code=400,
            detail=f"无法推断交易所: {data.symbol}",
        )

    # 规范化股票代码（HK 补零到 5 位，防止 01810/1810 重复）
    normalized_symbol = normalize_stock_symbol(exchange, data.symbol)

    existing = db.query(Stock).filter(
        Stock.exchange == exchange,
        Stock.symbol == normalized_symbol
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"该股票已存在：{exchange}/{normalized_symbol}"
        )

    # 名称为空时自动查询
    name = data.name
    if not name:
        try:
            # 复用 lookup 逻辑（通过 Provider 及 TuShare/yfinance 兜底）
            router_p = ProviderRouter()
            provider = router_p.get_provider(exchange)
            fund = provider.get_fundamentals(data.symbol, exchange)
            if fund and fund.name:
                name = fund.name
        except Exception:
            pass

    db_item = Stock(
        id=str(uuid4()),
        exchange=exchange,
        symbol=normalized_symbol,
        name=name or data.symbol,  # 仍无名称则 fallback 到代码
        currency=currency,
        position=0,
        historical_pnl=0,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    background_tasks.add_task(_background_refresh_kline, db_item.id)
    return _to_stock_response(db_item)


# ────────────────────────────────
# 获取个股列表
# ────────────────────────────────

@router.get("", response_model=List[StockResponse])
def list_stocks(db: Session = Depends(get_db)):
    """获取所有个股"""
    items = db.query(Stock).order_by(Stock.created_at.desc()).all()
    return [_to_stock_response(i) for i in items]


# ────────────────────────────────
# 获取单条个股
# ────────────────────────────────

@router.get("/{id}", response_model=StockResponse)
def get_stock(id: str, db: Session = Depends(get_db)):
    """获取单条个股详情"""
    item = db.query(Stock).filter(Stock.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="个股不存在")
    return _to_stock_response(item)


# ────────────────────────────────
# 更新个股
# ────────────────────────────────

@router.put("/{id}", response_model=StockResponse)
def update_stock(id: str, data: StockUpdate, db: Session = Depends(get_db)):
    """更新个股基本信息（exchange + symbol 组合不能与其他记录冲突）"""
    item = db.query(Stock).filter(Stock.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="个股不存在")

    new_exchange = data.exchange if data.exchange is not None else item.exchange
    new_symbol = data.symbol if data.symbol is not None else item.symbol

    # 检查新组合是否与其他记录冲突
    if new_exchange != item.exchange or new_symbol != item.symbol:
        conflict = db.query(Stock).filter(
            Stock.exchange == new_exchange,
            Stock.symbol == new_symbol,
            Stock.id != id
        ).first()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"该股票已存在：{new_exchange}/{new_symbol}"
            )

    if data.exchange is not None:
        item.exchange = data.exchange
    if data.symbol is not None:
        item.symbol = data.symbol
    if data.name is not None:
        item.name = data.name
    if data.currency is not None:
        item.currency = data.currency

    db.commit()
    db.refresh(item)
    return _to_stock_response(item)


# ────────────────────────────────
# 删除个股
# ────────────────────────────────

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stock(id: str, db: Session = Depends(get_db)):
    """删除个股（级联删除关联交易记录）"""
    item = db.query(Stock).filter(Stock.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="个股不存在")
    db.delete(item)
    db.commit()
    return None


# ────────────────────────────────
# 刷新个股基本信息
# ────────────────────────────────

@router.post("/{id}/refresh", response_model=StockResponse)
def refresh_stock(id: str, db: Session = Depends(get_db)):
    """重新拉取股票基本数据并更新数据库

    仅保留股票代码，通过分类器重新推断交易所和货币，
    再从数据源查询正确的股票名称，更新到数据库。

    当添加股票时数据源不可用（如 yfinance 限流）导致信息不准确，
    可用此接口手动触发重新查询并修正。
    """
    item = db.query(Stock).filter(Stock.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="个股不存在")

    # 1. 重新分类：用分类器根据代码推断交易所和货币
    result = classify_stock(item.symbol)
    if result.exchange:
        item.exchange = result.exchange
    item.currency = _EXCHANGE_CURRENCY.get(item.exchange, "USD")

    # 2. 重新查询名称（多源兜底）
    router_p = ProviderRouter()
    name_updated = False
    try:
        provider = router_p.get_provider(item.exchange)
        fund = provider.get_fundamentals(item.symbol, item.exchange)
        if fund and fund.name:
            item.name = fund.name
            name_updated = True
    except Exception:
        pass

    # A 股 TuShare 兜底
    if not name_updated and item.exchange in ("SH", "SZ"):
        try:
            ts_client = TushareClient()
            ts_code = f"{item.symbol}.{item.exchange}"
            basic = ts_client.get_stock_basic(ts_code)
            if basic and basic.get("name"):
                item.name = basic["name"]
                name_updated = True
            if not name_updated:
                fund_info = ts_client.get_fund_basic(ts_code)
                if fund_info and fund_info.get("name"):
                    item.name = fund_info["name"]
                    name_updated = True
        except Exception:
            pass

    # 美股 Finnhub 兜底
    if not name_updated and item.exchange == "US":
        try:
            import finnhub
            from app.config import settings as app_settings
            if app_settings.finnhub_api_key:
                fc = finnhub.Client(api_key=app_settings.finnhub_api_key)
                profile = fc.company_profile2(symbol=item.symbol)
                if profile and profile.get("name"):
                    item.name = profile["name"]
                    name_updated = True
        except Exception:
            pass

    # yfinance 兜底（港股/其他）
    if not name_updated:
        try:
            import yfinance as yf
            if item.exchange == "HK":
                yf_symbol = item.symbol.lstrip("0")
                ticker = yf.Ticker(f"{yf_symbol}.HK")
            else:
                ticker = yf.Ticker(item.symbol)
            info = ticker.info or {}
            name = info.get("longName") or info.get("shortName")
            if name:
                item.name = name
                name_updated = True
        except Exception:
            pass

    db.commit()
    db.refresh(item)
    return _to_stock_response(item)
