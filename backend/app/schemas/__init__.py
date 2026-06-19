"""Schema 聚合入口"""

from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioResponse,
    PortfolioWithPnl,
    PortfolioDashboardSummary,
    PortfolioDashboardResponse,
)
from app.schemas.trade_point import TradePointCreate, TradePointResponse
from app.schemas.event import EventCreate, EventResponse
from app.schemas.event_impact import EventImpactCreate, EventImpactResponse
from app.schemas.analysis_report import AnalysisReportCreate, AnalysisReportResponse
from app.schemas.agent_log import AgentLogCreate, AgentLogResponse
from app.schemas.strategy import StrategyCreate, StrategyResponse
from app.schemas.strategy_signal import StrategySignalCreate, StrategySignalResponse

from app.schemas.watchlist import WatchlistCreate, WatchlistResponse
from app.schemas.investment_memo import InvestmentMemoCreate, InvestmentMemoResponse
from app.schemas.memo_event import MemoEventCreate, MemoEventResponse

from app.schemas.event_node import EventNodeCreate, EventNodeResponse
from app.schemas.event_prediction import EventPredictionCreate, EventPredictionResponse

__all__ = [
    "PortfolioCreate",
    "PortfolioResponse",
    "PortfolioWithPnl",
    "PortfolioDashboardSummary",
    "PortfolioDashboardResponse",
    "TradePointCreate",
    "TradePointResponse",
    "EventCreate",
    "EventResponse",
    "EventImpactCreate",
    "EventImpactResponse",
    "AnalysisReportCreate",
    "AnalysisReportResponse",
    "AgentLogCreate",
    "AgentLogResponse",
    "StrategyCreate",
    "StrategyResponse",
    "StrategySignalCreate",
    "StrategySignalResponse",
    "WatchlistCreate",
    "WatchlistResponse",
    "InvestmentMemoCreate",
    "InvestmentMemoResponse",
    "MemoEventCreate",
    "MemoEventResponse",
    "EventNodeCreate",
    "EventNodeResponse",
    "EventPredictionCreate",
    "EventPredictionResponse",
]
