"""历史盈亏调整记录模型"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Numeric, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class HistoricalAdjustment(Base):
    """历史盈亏调整记录（手动记录外部账户盈亏偏移）"""
    __tablename__ = "historical_adjustment"
    __table_args__ = {"comment": "历史盈亏调整记录"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
    )
    amount: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False,
        comment="调整金额（正=盈利，负=亏损）",
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="CNY", server_default="CNY",
        comment="币种代码（CNY/HKD/USD）",
    )
    note: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="备注说明",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(),
        nullable=False, comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(),
        nullable=False, comment="更新时间",
    )
