"""Schema 聚合入口"""

from app.schemas.stock import StockCreate, StockUpdate, StockResponse
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionResponse
from app.schemas.stock_analyze import StockAnalyzeCreate, StockAnalyzeResponse
from app.schemas.report import ReportCreate, ReportUpdate, ReportResponse
from app.schemas.tp_sl_point import TpSlPointCreate, TpSlPointUpdate, TpSlPointResponse
from app.schemas.stock_tag import StockTagCreate, StockTagUpdate, StockTagResponse

__all__ = [
    "StockCreate",
    "StockUpdate",
    "StockResponse",
    "TransactionCreate",
    "TransactionUpdate",
    "TransactionResponse",
    "StockAnalyzeCreate",
    "StockAnalyzeResponse",
    "ReportCreate",
    "ReportUpdate",
    "ReportResponse",
    "TpSlPointCreate",
    "TpSlPointUpdate",
    "TpSlPointResponse",
    "StockTagCreate",
    "StockTagUpdate",
    "StockTagResponse",
]
