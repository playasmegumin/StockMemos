"""分析报告模型"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Report(Base):
    """分析报告表：stock_analyze 的子表，存储每份分析报告"""
    __tablename__ = "report"
    __table_args__ = {"comment": "分析报告"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    stock_analyze_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("stock_analyze.id"), nullable=False, comment="关联个股分析ID"
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, comment="报告生成时间"
    )
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="报告标题"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="报告正文"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )

    # 关系
    stock_analyze = relationship("StockAnalyze", back_populates="reports")
