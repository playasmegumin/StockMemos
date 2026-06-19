"""世界热点事件节点数据模型"""

from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import String, Date, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class EventNode(Base):
    """世界热点事件节点表：跟踪全球重大事件（如美联储决议、地缘政治冲突）"""
    __tablename__ = "event_node"
    __table_args__ = {"comment": "世界热点事件节点"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    title: Mapped[str] = mapped_column(
        String(300), nullable=False, comment="事件标题，如美联储2024年12月利率决议"
    )
    category: Mapped[str | None] = mapped_column(
        String(50), comment="分类：monetary_policy/geopolitical/macro_data/trade_policy/energy/tech"
    )
    occurred_at: Mapped[date | None] = mapped_column(
        Date, comment="已发生节点日期（空表示尚未发生）"
    )
    description: Mapped[str | None] = mapped_column(
        Text, comment="事件描述"
    )
    source_url: Mapped[str | None] = mapped_column(
        Text, comment="信息来源"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", comment="状态：pending/occurred/materialized"
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
