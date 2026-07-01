"""个股基本信息模型"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Numeric, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Stock(Base):
    """个股表：存储个股基本信息及动态计算的持仓、历史盈亏"""
    __tablename__ = "stock"
    __table_args__ = (
        UniqueConstraint("exchange", "symbol", name="uq_stock_exchange_symbol"),
        {"comment": "个股基本信息"},
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    exchange: Mapped[str] = mapped_column(
        String(8), nullable=False, comment="交易所类型，如 SH、SZ、HK、US"
    )
    symbol: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="个股标识，如 600519 或 AAPL"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="个股名称"
    )
    currency: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="交易货币，如 CNY、USD、HKD"
    )
    position: Mapped[float] = mapped_column(
        Numeric(15, 4), nullable=False, default=0, comment="当前持仓数量（Σ 交易记录数量）"
    )
    historical_pnl: Mapped[float] = mapped_column(
        Numeric(15, 4), nullable=False, default=0, comment="历史盈亏（-Σ(数量×价格+手续费)）"
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

    # 关系：级联删除交易记录
    transactions = relationship(
        "Transaction", back_populates="stock", cascade="all, delete-orphan"
    )
