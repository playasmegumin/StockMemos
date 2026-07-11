"""资金汇总缓存模型"""

from datetime import datetime
from sqlalchemy import Integer, Numeric, DateTime, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CapitalMeta(Base):
    """资金汇总缓存表（单行）：由 DB 触发器自动维护"""
    __tablename__ = "capital_meta"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_capital_meta_single_row"),
        {"comment": "资金汇总缓存（单行）"},
    )

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, server_default="1"
    )
    total_invested_cny: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, server_default="0",
        comment="总投入金额(CNY)"
    )
    total_historical_pnl_cny: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, server_default="0",
        comment="历史总盈亏(CNY)"
    )
    total_position_value_cny: Mapped[float] = mapped_column(
        Numeric(18, 4), nullable=False, server_default="0",
        comment="总持仓金额(CNY)"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="更新时间"
    )
