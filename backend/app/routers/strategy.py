"""策略管理 API

Endpoints:
    POST /api/strategies          — 创建策略
    GET  /api/strategies          — 获取策略列表
    PUT  /api/strategies/{id}    — 更新策略
    DELETE /api/strategies/{id}  — 删除策略
    POST /api/strategies/{id}/run — 对某只股票运行策略
    POST /api/backtest            — 执行回测
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import uuid4

from app.database import get_db
from app.models.strategy import Strategy
from app.models.strategy_signal import StrategySignal
from app.schemas.strategy import StrategyCreate, StrategyResponse
from app.services.strategy_engine import run_strategy, backtest
from app.services.tushare_client import TushareClient
import pandas as pd

router = APIRouter()


def _to_strategy_response(item: Strategy) -> StrategyResponse:
    return StrategyResponse(
        id=item.id,
        name=item.name,
        description=item.description,
        rules=item.rules,
        is_active=item.is_active,
        created_at=str(item.created_at) if item.created_at else None,
    )


@router.post("", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
def create_strategy(data: StrategyCreate, db: Session = Depends(get_db)):
    """创建策略"""
    db_item = Strategy(
        id=str(uuid4()),
        name=data.name,
        description=data.description,
        rules=data.rules,
        is_active=data.is_active if data.is_active is not None else True,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return _to_strategy_response(db_item)


@router.get("", response_model=List[StrategyResponse])
def list_strategies(db: Session = Depends(get_db)):
    """获取策略列表"""
    items = db.query(Strategy).order_by(Strategy.created_at.desc()).all()
    return [_to_strategy_response(i) for i in items]


@router.put("/{id}", response_model=StrategyResponse)
def update_strategy(id: str, data: StrategyCreate, db: Session = Depends(get_db)):
    """更新策略"""
    item = db.query(Strategy).filter(Strategy.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="策略不存在")
    item.name = data.name
    item.description = data.description
    item.rules = data.rules
    item.is_active = data.is_active if data.is_active is not None else item.is_active
    db.commit()
    db.refresh(item)
    return _to_strategy_response(item)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy(id: str, db: Session = Depends(get_db)):
    """删除策略"""
    item = db.query(Strategy).filter(Strategy.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="策略不存在")
    db.delete(item)
    db.commit()
    return None


@router.post("/{id}/run", response_model=Dict[str, Any])
def run_strategy_on_stock(id: str, stock_code: str, start_date: str = "20240101", end_date: str = "20241231", db: Session = Depends(get_db)):
    """对某只股票运行策略，返回最新信号"""
    strategy = db.query(Strategy).filter(Strategy.id == id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    tushare = TushareClient()
    kline = tushare.get_daily_kline(stock_code, start_date, end_date)
    if not kline:
        return {"error": "无法获取K线数据", "stock_code": stock_code}

    df = pd.DataFrame(kline)
    df = df.sort_values("trade_date", ascending=True)

    try:
        result_df = run_strategy(df, strategy.rules)
    except Exception as e:
        return {"error": str(e), "stock_code": stock_code}

    latest = result_df.iloc[-1]
    signal = latest.get("signal", "hold")

    # 记录信号
    db_signal = StrategySignal(
        id=str(uuid4()),
        strategy_id=id,
        stock_code=stock_code,
        signal_date=latest["trade_date"],
        signal_type=signal,
        raw_data={
            "indicators": {ind["name"]: float(latest.get(ind["name"], 0)) for ind in strategy.rules.get("indicators", [])},
            "conditions_met": bool(latest.get("conditions_met", False)),
        },
    )
    db.add(db_signal)
    db.commit()

    return {
        "stock_code": stock_code,
        "strategy_id": id,
        "strategy_name": strategy.name,
        "signal": signal,
        "signal_date": str(latest["trade_date"]),
        "indicators": {ind["name"]: float(latest.get(ind["name"], 0)) for ind in strategy.rules.get("indicators", [])},
        "conditions_met": bool(latest.get("conditions_met", False)),
    }


@router.post("/backtest", response_model=Dict[str, Any])
def run_backtest(payload: Dict[str, Any], db: Session = Depends(get_db)):
    """执行回测

    Payload:
        {
            "strategy_id": "...",
            "stock_code": "000001.SZ",
            "start_date": "20240101",
            "end_date": "20241231",
            "initial_capital": 100000
        }
    """
    strategy_id = payload.get("strategy_id")
    stock_code = payload.get("stock_code")
    start_date = payload.get("start_date", "20240101")
    end_date = payload.get("end_date", "20241231")
    initial_capital = payload.get("initial_capital", 100000.0)

    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")

    tushare = TushareClient()
    kline = tushare.get_daily_kline(stock_code, start_date, end_date)
    if not kline:
        return {"error": "无法获取K线数据", "stock_code": stock_code}

    df = pd.DataFrame(kline)
    df = df.sort_values("trade_date", ascending=True)

    try:
        result = backtest(df, strategy.rules, initial_capital=initial_capital)
    except Exception as e:
        return {"error": str(e), "stock_code": stock_code}

    result["strategy_id"] = strategy_id
    result["strategy_name"] = strategy.name
    result["stock_code"] = stock_code
    return result
