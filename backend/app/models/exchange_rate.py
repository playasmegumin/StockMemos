"""汇率字典模型"""

from datetime import datetime
from sqlalchemy import String, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ExchangeRate(Base):
    """汇率字典表：存储各币种兑人民币汇率"""
    __tablename__ = "exchange_rates"
    __table_args__ = {"comment": "汇率字典"}

    currency: Mapped[str] = mapped_column(
        String(10), primary_key=True, comment="币种代码"
    )
    rate_to_cny: Mapped[float] = mapped_column(
        Numeric(18, 6), nullable=False, comment="1单位本币兑CNY"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="更新时间"
    )
