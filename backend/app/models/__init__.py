"""模型聚合入口"""

from app.models.stock import Stock
from app.models.transaction import Transaction
from app.models.stock_analyze import StockAnalyze
from app.models.report import Report
from app.models.tp_sl_point import TpSlPoint
from app.models.stock_tag import StockTag
from app.models.kline_daily import KlineDaily
from app.models.exchange_rate import ExchangeRate
from app.models.capital_flow import CapitalFlow
from app.models.capital_meta import CapitalMeta
from app.models.investment_memo import InvestmentMemo
from app.models.historical_adjustment import HistoricalAdjustment

__all__ = [
    "Stock",
    "Transaction",
    "StockAnalyze",
    "Report",
    "TpSlPoint",
    "StockTag",
    "KlineDaily",
    "ExchangeRate",
    "CapitalFlow",
    "CapitalMeta",
    "InvestmentMemo",
    "HistoricalAdjustment",
]
