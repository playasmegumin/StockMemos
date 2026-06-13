"""持仓数据模型"""

from datetime import datetime, date
from uuid import uuid4
from sqlalchemy import String, Integer, Numeric, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Portfolio(Base):
    """持仓表：用户股票持仓记录"""
    __tablename__ = "portfolio"
    __table_args__ = {"comment": "用户持仓记录"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    stock_code: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="股票代码，如 000001.SZ"
    )
    stock_name: Mapped[str | None] = mapped_column(
        String(100), comment="股票名称"
    )
    quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="持股数量"
    )
    cost_price: Mapped[float] = mapped_column(
        Numeric(10, 4), nullable=False, comment="成本价"
    )
    build_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="建仓日期"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="holding", comment="状态：holding/closed"
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
