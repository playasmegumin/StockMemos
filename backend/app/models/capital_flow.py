"""现金流水模型"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Numeric, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CapitalFlow(Base):
    """现金流水表：记录资金存入/取出/手续费"""
    __tablename__ = "capital_flow"
    __table_args__ = {"comment": "现金流水"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="操作类型: deposit/withdraw/fee"
    )
    amount: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, comment="金额(正负号按type转换)"
    )
    currency: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="CNY",
        comment="币种"
    )
    note: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="备注"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
