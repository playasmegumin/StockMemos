"""自选股数据模型"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Watchlist(Base):
    """自选股表：用户关注的股票列表"""
    __tablename__ = "watchlist"
    __table_args__ = {"comment": "自选股列表"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    stock_code: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, comment="股票代码，如 000001.SZ"
    )
    stock_name: Mapped[str | None] = mapped_column(
        String(100), comment="股票名称"
    )
    sector: Mapped[str | None] = mapped_column(
        String(50), comment="所属板块/行业"
    )
    market: Mapped[str | None] = mapped_column(
        String(20), comment="交易所：SH/SZ/HK/US"
    )
    is_watched: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否在关注"
    )
    memo_id: Mapped[str | None] = mapped_column(
        ForeignKey("investment_memo.id"), comment="关联投资备忘录ID"
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
