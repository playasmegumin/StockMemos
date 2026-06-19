"""分析报告数据模型"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AnalysisReport(Base):
    """分析报告表：存储AI生成的个股分析报告"""
    __tablename__ = "analysis_report"
    __table_args__ = {"comment": "AI分析报告"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    stock_code: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="股票代码"
    )
    trigger_type: Mapped[str | None] = mapped_column(
        String(20), comment="触发类型：manual/scheduled"
    )
    final_rating: Mapped[str | None] = mapped_column(
        String(20),
        comment="最终评级：strong_buy/buy/accumulate/neutral/reduce/sell",
    )
    summary: Mapped[str | None] = mapped_column(
        Text, comment="报告摘要"
    )
    valuation_status: Mapped[str | None] = mapped_column(
        String(20), comment="估值状态：overvalued/fair/undervalued"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
