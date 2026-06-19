"""事件预测结果数据模型"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Numeric, Boolean, DateTime, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class EventPrediction(Base):
    """事件预测结果表：PolyMarket 风格互斥对立预测"""
    __tablename__ = "event_prediction"
    __table_args__ = {"comment": "事件预测结果"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    event_node_id: Mapped[str] = mapped_column(
        ForeignKey("event_node.id"), nullable=False, comment="关联事件节点ID"
    )
    outcome_label: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="结果标签，如加息25bp"
    )
    outcome_description: Mapped[str | None] = mapped_column(
        Text, comment="结果描述"
    )
    probability_estimate: Mapped[float | None] = mapped_column(
        Numeric(3, 2), comment="Agent评估概率 0.00-1.00"
    )
    impact_brief: Mapped[str | None] = mapped_column(
        Text, comment="若此结果发生，后续影响简要解析"
    )
    is_actual_result: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="是否为实际发生结果"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
