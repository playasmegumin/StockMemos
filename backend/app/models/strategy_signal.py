"""策略信号记录数据模型"""

from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import String, Date, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class StrategySignal(Base):
    """策略信号表：记录策略在某日对某股的判定结果"""
    __tablename__ = "strategy_signal"
    __table_args__ = {"comment": "策略信号记录"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    strategy_id: Mapped[str] = mapped_column(
        ForeignKey("strategy.id"), nullable=False, comment="关联策略ID"
    )
    stock_code: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="股票代码"
    )
    signal_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="信号日期"
    )
    signal_type: Mapped[str | None] = mapped_column(
        String(20), comment="信号类型：buy/sell/hold/overvalued/undervalued"
    )
    raw_data: Mapped[dict | None] = mapped_column(
        JSONB, comment="当日指标原始值(JSON)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
