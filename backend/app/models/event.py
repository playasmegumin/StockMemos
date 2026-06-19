"""全局事件库数据模型"""

from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import String, Date, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Event(Base):
    """全局事件表：跟踪重大事件（如美联储利率决议、地缘政治事件）"""
    __tablename__ = "event"
    __table_args__ = {"comment": "全局事件库"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="事件名称"
    )
    category: Mapped[str | None] = mapped_column(
        String(50),
        comment="事件类型：monetary_policy/geopolitical/macro_data/company_event",
    )
    expected_date: Mapped[date | None] = mapped_column(
        Date, comment="预期发生日期"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        comment="状态：pending/occurred/materialized",
    )
    source_url: Mapped[str | None] = mapped_column(
        Text, comment="信息来源链接"
    )
    description: Mapped[str | None] = mapped_column(
        Text, comment="事件描述"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
