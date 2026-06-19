"""买卖点数据模型"""

from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import String, Numeric, Date, DateTime, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class TradePoint(Base):
    """买卖点表：记录用户每笔交易操作"""
    __tablename__ = "trade_point"
    __table_args__ = {"comment": "交易操作记录"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    portfolio_id: Mapped[str] = mapped_column(
        ForeignKey("portfolio.id"), nullable=False, comment="关联持仓ID"
    )
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="操作类型：add_position/reduce_position/stop_loss/take_profit",
    )
    price: Mapped[float | None] = mapped_column(
        Numeric(10, 4), comment="交易价格"
    )
    reason: Mapped[str | None] = mapped_column(
        Text, comment="交易理由"
    )
    report_id: Mapped[str | None] = mapped_column(
        ForeignKey("analysis_report.id"), comment="关联分析报告ID"
    )
    trade_date: Mapped[date | None] = mapped_column(
        Date, comment="交易日期"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
