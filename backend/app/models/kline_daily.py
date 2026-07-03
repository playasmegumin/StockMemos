"""日 K 线数据模型"""

from datetime import datetime, date
from sqlalchemy import String, Numeric, Date, DateTime, ForeignKey, func, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class KlineDaily(Base):
    """日 K 线表：存储个股每日交易数据"""
    __tablename__ = "kline_daily"
    __table_args__ = (
        PrimaryKeyConstraint("stock_id", "trade_date", name="pk_kline_daily"),
        {"comment": "日K线数据"},
    )

    stock_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("stock.id", ondelete="CASCADE"), nullable=False,
        comment="关联个股ID",
    )
    trade_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="交易日"
    )
    open: Mapped[float] = mapped_column(
        Numeric(12, 4), nullable=False, comment="开盘价"
    )
    high: Mapped[float] = mapped_column(
        Numeric(12, 4), nullable=False, comment="最高价"
    )
    low: Mapped[float] = mapped_column(
        Numeric(12, 4), nullable=False, comment="最低价"
    )
    close: Mapped[float] = mapped_column(
        Numeric(12, 4), nullable=False, comment="收盘价"
    )
    volume: Mapped[float] = mapped_column(
        Numeric(20, 4), nullable=False, comment="成交量（股数）"
    )
    amount: Mapped[float] = mapped_column(
        Numeric(20, 4), nullable=False, comment="成交额（元/港币/美元）"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )

    # 关系
    stock = relationship("Stock")
