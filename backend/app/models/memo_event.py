"""备忘录关联事件数据模型"""

from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import String, Date, DateTime, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class MemoEvent(Base):
    """备忘录事件表：记录对某股票有影响的重要事件"""
    __tablename__ = "memo_event"
    __table_args__ = {"comment": "备忘录关联事件"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    memo_id: Mapped[str] = mapped_column(
        ForeignKey("investment_memo.id"), nullable=False, comment="关联备忘录ID"
    )
    event_name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="事件名称，如 Q3财报发布"
    )
    event_type: Mapped[str | None] = mapped_column(
        String(20), comment="类型：earnings/order/geopolitical/policy/other"
    )
    impact_tag: Mapped[str | None] = mapped_column(
        String(20), comment="影响标签：bullish/bearish/neutral"
    )
    expected_date: Mapped[date | None] = mapped_column(
        Date, comment="预期发生日期"
    )
    actual_date: Mapped[date | None] = mapped_column(
        Date, comment="实际发生日期"
    )
    result_status: Mapped[str] = mapped_column(
        String(20), default="pending", comment="pending/occurred/expired/cancelled"
    )
    result_summary: Mapped[str | None] = mapped_column(
        Text, comment="事件结果摘要"
    )
    source_url: Mapped[str | None] = mapped_column(
        Text, comment="信息来源"
    )
    agent_analysis: Mapped[str | None] = mapped_column(
        Text, comment="Agent分析摘要"
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
