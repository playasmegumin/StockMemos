"""止盈止损点模型"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Numeric, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TpSlPoint(Base):
    """止盈止损点表：stock_analyze 的子表，存储止盈/止损/目标估值点位"""
    __tablename__ = "tp_sl_point"
    __table_args__ = {"comment": "止盈止损点"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    stock_analyze_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("stock_analyze.id"), nullable=False, comment="关联个股分析ID"
    )
    price: Mapped[float] = mapped_column(
        Numeric(12, 4), nullable=False, comment="股价/目标价"
    )
    label: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="标签：买入/卖出/目标估值"
    )
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="备注"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )

    # 关系
    stock_analyze = relationship("StockAnalyze", back_populates="tp_sl_points")
