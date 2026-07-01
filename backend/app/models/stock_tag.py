"""个股标签模型"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class StockTag(Base):
    """个股标签表：stock_analyze 的子表，自由文本标签"""
    __tablename__ = "stock_tag"
    __table_args__ = {"comment": "个股标签"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    stock_analyze_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("stock_analyze.id"), nullable=False, comment="关联个股分析ID"
    )
    tag: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="标签（自由文本，如分红/投机/成长/价值）"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )

    # 关系
    stock_analyze = relationship("StockAnalyze", back_populates="stock_tags")
