"""事件-个股影响数据模型"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Integer, Numeric, DateTime, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class EventImpact(Base):
    """事件影响表：记录重大事件对个股的影响评估"""
    __tablename__ = "event_impact"
    __table_args__ = {"comment": "事件对个股影响评估"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    event_id: Mapped[str] = mapped_column(
        ForeignKey("event.id"), nullable=False, comment="关联事件ID"
    )
    stock_code: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="股票代码"
    )
    direction: Mapped[str | None] = mapped_column(
        String(20), comment="影响方向：bullish/bearish/neutral"
    )
    magnitude: Mapped[int | None] = mapped_column(
        Integer, comment="影响程度：1-5"
    )
    confidence: Mapped[float | None] = mapped_column(
        Numeric(3, 2), comment="置信度：0.00-1.00"
    )
    time_window: Mapped[str | None] = mapped_column(
        String(50), comment="时间窗口，如 1-3个月"
    )
    agent_reasoning: Mapped[str | None] = mapped_column(
        Text, comment="Agent推理过程"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
