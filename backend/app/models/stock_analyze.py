"""个股分析模型"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class StockAnalyze(Base):
    """个股分析表：与 stock 一对一，存储基本面数据和关联子表"""
    __tablename__ = "stock_analyze"
    __table_args__ = (
        UniqueConstraint("stock_id", name="uq_stock_analyze_stock"),
        {"comment": "个股分析"},
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    stock_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("stock.id"), nullable=False, comment="关联个股ID"
    )
    fundamentals_data: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="基本面数据（JSON，如 PE/PB/ROE 等动态指标）"
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

    # 关系
    stock = relationship("Stock")
    reports = relationship(
        "Report", back_populates="stock_analyze", cascade="all, delete-orphan"
    )
    tp_sl_points = relationship(
        "TpSlPoint", back_populates="stock_analyze", cascade="all, delete-orphan"
    )
    stock_tags = relationship(
        "StockTag", back_populates="stock_analyze", cascade="all, delete-orphan"
    )
