"""投资备忘录数据模型"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Numeric, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class InvestmentMemo(Base):
    """投资备忘录表：每只自选股的投研笔记"""
    __tablename__ = "investment_memo"
    __table_args__ = {"comment": "投资备忘录"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    stock_code: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="股票代码"
    )
    target_price: Mapped[float | None] = mapped_column(
        Numeric(10, 4), comment="目标股价（估值）"
    )
    valuation_method: Mapped[str | None] = mapped_column(
        String(50), comment="估值方法：PE/DCF/可比公司"
    )
    business_scope: Mapped[str | None] = mapped_column(
        Text, comment="业务范围/供需关系/产业链生态位"
    )
    short_trend: Mapped[str | None] = mapped_column(
        String(20), comment="短线趋势：up/down/sideways"
    )
    mid_trend: Mapped[str | None] = mapped_column(
        String(20), comment="中线趋势：up/down/sideways"
    )
    long_trend: Mapped[str | None] = mapped_column(
        String(20), comment="长期趋势：up/down/sideways"
    )
    trend_logic: Mapped[str | None] = mapped_column(
        Text, comment="趋势预测核心逻辑"
    )
    notes: Mapped[str | None] = mapped_column(
        Text, comment="用户自定义备注"
    )
    last_updated_by: Mapped[str | None] = mapped_column(
        String(50), comment="最后更新来源：user/fundamental_agent/news_agent/technical_agent"
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
