"""投资备忘模型"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class InvestmentMemo(Base):
    """投资备忘表：记录用户个人投资笔记，可关联个股"""
    __tablename__ = "investment_memo"
    __table_args__ = {"comment": "投资备忘"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="标题"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="正文（Markdown 原文）"
    )
    stock_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("stock.id", ondelete="SET NULL"),
        nullable=True, comment="关联个股"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
