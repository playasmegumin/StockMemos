"""交易记录模型"""

from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import String, Numeric, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Transaction(Base):
    """交易记录表：存储每条买入/卖出记录"""
    __tablename__ = "transaction"
    __table_args__ = {"comment": "交易记录"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    stock_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("stock.id"), nullable=False, comment="关联个股ID"
    )
    quantity: Mapped[float] = mapped_column(
        Numeric(15, 4), nullable=False, comment="交易数量，正为买入，负为卖出"
    )
    price: Mapped[float] = mapped_column(
        Numeric(12, 4), nullable=False, comment="交易价格"
    )
    gas: Mapped[float] = mapped_column(
        Numeric(12, 4), nullable=False, default=0, comment="手续费"
    )
    traded_at: Mapped[date] = mapped_column(
        Date, nullable=False, comment="交易日期"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="记录创建时间"
    )

    # 关系
    stock = relationship("Stock", back_populates="transactions")
