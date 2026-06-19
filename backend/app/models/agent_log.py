"""Agent思考过程日志数据模型"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, DateTime, Text, func, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AgentLog(Base):
    """Agent日志表：记录每个Agent的完整推理过程"""
    __tablename__ = "agent_log"
    __table_args__ = {"comment": "Agent推理过程日志"}

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    report_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_report.id"), nullable=False, comment="关联报告ID"
    )
    agent_name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Agent名称，如 bull_agent"
    )
    agent_role: Mapped[str | None] = mapped_column(
        String(50),
        comment="角色：intelligence/event_analysis/bull/bear/referee/valuation/reporter",
    )
    reasoning: Mapped[str | None] = mapped_column(
        Text, comment="完整思考文本"
    )
    conclusion: Mapped[str | None] = mapped_column(
        Text, comment="结论摘要"
    )
    meta_data: Mapped[dict | None] = mapped_column(
        JSONB, comment="结构化输出(JSON)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
