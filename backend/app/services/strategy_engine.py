"""策略规则引擎 — 技术指标计算与信号生成

策略规则 JSON 格式示例：
    {
        "indicators": [
            {"name": "MA5", "type": "sma", "period": 5, "field": "close"},
            {"name": "MA20", "type": "sma", "period": 20, "field": "close"},
            {"name": "RSI", "type": "rsi", "period": 14, "field": "close"}
        ],
        "conditions": [
            {"indicator": "MA5", "operator": ">", "value": "MA20", "value_type": "indicator"},
            {"indicator": "RSI", "operator": "<", "value": 30, "value_type": "number"}
        ],
        "signal_logic": "all",
        "buy_signal": "conditions_met",
        "sell_signal": "conditions_not_met"
    }

支持指标：sma, ema, rsi
支持运算符：>, <, >=, <=, ==, !=
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def _sma(series: pd.Series, period: int) -> pd.Series:
    """简单移动平均"""
    return series.rolling(window=period, min_periods=period).mean()


def _ema(series: pd.Series, period: int) -> pd.Series:
    """指数移动平均"""
    return series.ewm(span=period, adjust=False).mean()


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """相对强弱指标"""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _calculate_indicator(df: pd.DataFrame, indicator: Dict[str, Any]) -> pd.Series:
    """计算单个指标"""
    ind_type = indicator["type"]
    field = indicator.get("field", "close")
    period = indicator.get("period", 14)
    name = indicator["name"]

    if field not in df.columns:
        raise ValueError(f"字段 {field} 不在数据中，可用字段: {list(df.columns)}")

    series = pd.to_numeric(df[field], errors="coerce")

    if ind_type == "sma":
        result = _sma(series, period)
    elif ind_type == "ema":
        result = _ema(series, period)
    elif ind_type == "rsi":
        result = _rsi(series, period)
    else:
        raise ValueError(f"不支持的指标类型: {ind_type}")

    return result


def _evaluate_condition(row: pd.Series, condition: Dict[str, Any]) -> bool:
    """评估单条条件"""
    indicator_name = condition["indicator"]
    operator = condition["operator"]
    value_type = condition.get("value_type", "number")

    left = row.get(indicator_name)
    if left is None or pd.isna(left):
        return False

    if value_type == "indicator":
        right = row.get(condition["value"])
        if right is None or pd.isna(right):
            return False
    else:
        right = float(condition["value"])

    left_f = float(left)
    right_f = float(right)

    ops = {
        ">": lambda a, b: a > b,
        "<": lambda a, b: a < b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }

    if operator not in ops:
        raise ValueError(f"不支持的运算符: {operator}")

    return ops[operator](left_f, right_f)


def run_strategy(df: pd.DataFrame, rules: Dict[str, Any]) -> pd.DataFrame:
    """对 DataFrame 运行策略，返回带信号列的 DataFrame

    Args:
        df: K线数据 DataFrame，需包含 date/close/open/high/low/vol 等列
        rules: 策略规则 JSON

    Returns:
        DataFrame，新增各指标列和 signal 列
    """
    df = df.copy()
    indicators = rules.get("indicators", [])
    conditions = rules.get("conditions", [])
    signal_logic = rules.get("signal_logic", "all")
    buy_signal = rules.get("buy_signal", "conditions_met")
    sell_signal = rules.get("sell_signal", "conditions_not_met")

    # 1. 计算所有指标
    for ind in indicators:
        df[ind["name"]] = _calculate_indicator(df, ind)

    # 2. 逐行评估条件
    def _eval_row(row: pd.Series) -> bool:
        if not conditions:
            return False
        results = [_evaluate_condition(row, c) for c in conditions]
        if signal_logic == "all":
            return all(results)
        return any(results)

    df["conditions_met"] = df.apply(_eval_row, axis=1)

    # 3. 生成信号
    def _signal(row: pd.Series) -> Optional[str]:
        met = row["conditions_met"]
        if buy_signal == "conditions_met" and met:
            return "buy"
        if buy_signal == "conditions_not_met" and not met:
            return "buy"
        if sell_signal == "conditions_met" and met:
            return "sell"
        if sell_signal == "conditions_not_met" and not met:
            return "sell"
        return "hold"

    df["signal"] = df.apply(_signal, axis=1)
    return df


def backtest(df: pd.DataFrame, rules: Dict[str, Any], initial_capital: float = 100000.0) -> Dict[str, Any]:
    """执行回测

    Args:
        df: K线数据 DataFrame
        rules: 策略规则 JSON
        initial_capital: 初始资金

    Returns:
        回测结果字典，包含 trades, equity_curve, total_return, win_rate, max_drawdown
    """
    df = run_strategy(df, rules)

    position = 0  # 0 = 空仓, 1 = 满仓
    cash = initial_capital
    shares = 0.0
    trades = []
    equity = []

    for _, row in df.iterrows():
        price = float(row.get("close", 0))
        signal = row.get("signal", "hold")
        date = row.get("trade_date", "")

        if signal == "buy" and position == 0 and price > 0:
            shares = cash / price
            cash = 0
            position = 1
            trades.append({"date": str(date), "type": "buy", "price": price, "shares": shares})
        elif signal == "sell" and position == 1 and price > 0:
            cash = shares * price
            trades.append({"date": str(date), "type": "sell", "price": price, "shares": shares, "proceeds": cash})
            shares = 0
            position = 0

        current_value = cash + shares * price if price > 0 else cash
        equity.append({"date": str(date), "value": current_value})

    final_value = equity[-1]["value"] if equity else initial_capital
    total_return = (final_value - initial_capital) / initial_capital

    # 胜率
    sell_trades = [t for t in trades if t["type"] == "sell"]
    wins = sum(1 for t in sell_trades if t.get("proceeds", 0) > 0)  # 简化

    # 最大回撤
    peak = initial_capital
    max_dd = 0.0
    for e in equity:
        if e["value"] > peak:
            peak = e["value"]
        dd = (peak - e["value"]) / peak
        if dd > max_dd:
            max_dd = dd

    return {
        "initial_capital": initial_capital,
        "final_value": round(final_value, 2),
        "total_return": round(total_return, 4),
        "total_return_pct": f"{total_return * 100:.2f}%",
        "trade_count": len(trades),
        "win_rate": f"{wins / len(sell_trades) * 100:.1f}%" if sell_trades else "N/A",
        "max_drawdown": round(max_dd, 4),
        "max_drawdown_pct": f"{max_dd * 100:.2f}%",
        "trades": trades,
        "equity_curve": equity,
    }
