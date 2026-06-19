"""策略定义数据模型"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Boolean, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Strategy(Base):
    """策略表：用户自定义的技术指标策略组合"""
    __tablename__ = "strategy"
    __table_args__ = {"comment": "策略定义"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="策略名称"
    )
    description: Mapped[str | None] = mapped_column(
        Text, comment="策略描述"
    )
    rules: Mapped[dict] = mapped_column(
        JSONB, nullable=False, comment="指标组合规则(JSON)"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否启用"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
