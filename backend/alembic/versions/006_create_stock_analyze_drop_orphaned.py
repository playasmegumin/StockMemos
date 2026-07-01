"""create stock_analyze/report/tp_sl_point/stock_tag, drop orphaned tables

Revision ID: 006
Revises: 005
Create Date: 2025-07-01 16:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 创建新表 ──
    op.create_table(
        "stock_analyze",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("stock_id", sa.String(36), nullable=False),
        sa.Column("fundamentals_data", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["stock_id"], ["stock.id"]),
        sa.UniqueConstraint("stock_id", name="uq_stock_analyze_stock"),
        comment="个股分析",
    )
    op.create_table(
        "report",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("stock_analyze_id", sa.String(36), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["stock_analyze_id"], ["stock_analyze.id"]),
        comment="分析报告",
    )
    op.create_table(
        "tp_sl_point",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("stock_analyze_id", sa.String(36), nullable=False),
        sa.Column("price", sa.Numeric(12, 4), nullable=False),
        sa.Column("label", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["stock_analyze_id"], ["stock_analyze.id"]),
        comment="止盈止损点",
    )
    op.create_table(
        "stock_tag",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("stock_analyze_id", sa.String(36), nullable=False),
        sa.Column("tag", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["stock_analyze_id"], ["stock_analyze.id"]),
        comment="个股标签",
    )

    # ── 删除废弃表（注意 FK 依赖顺序）──
    op.drop_table("memo_event")
    op.drop_table("event_prediction")
    op.drop_table("strategy_signal")
    op.drop_table("watchlist")
    op.drop_table("investment_memo")
    op.drop_table("event_node")
    op.drop_table("strategy")
    op.drop_table("agent_log")
    op.drop_table("analysis_report")
    op.drop_table("event_impact")
    op.drop_table("event")


def downgrade() -> None:
    # 恢复废弃表（简化处理，只建核心结构）
    op.create_table(
        "event",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("expected_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        comment="全局事件库",
    )
    op.create_table(
        "event_impact",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("event_id", sa.String(36), nullable=False),
        sa.Column("stock_code", sa.String(20), nullable=False),
        sa.Column("direction", sa.String(20), nullable=True),
        sa.Column("magnitude", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column("time_window", sa.String(50), nullable=True),
        sa.Column("agent_reasoning", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"]),
        comment="事件对个股影响评估",
    )
    op.create_table(
        "analysis_report",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("stock_code", sa.String(20), nullable=False),
        sa.Column("trigger_type", sa.String(20), nullable=True),
        sa.Column("final_rating", sa.String(20), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("valuation_status", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        comment="AI分析报告",
    )
    op.create_table(
        "agent_log",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("report_id", sa.String(36), nullable=False),
        sa.Column("agent_name", sa.String(50), nullable=False),
        sa.Column("agent_role", sa.String(50), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("conclusion", sa.Text(), nullable=True),
        sa.Column("meta_data", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["report_id"], ["analysis_report.id"]),
        comment="Agent推理过程日志",
    )

    # 删除新表（逆序，先删有 FK 的子表）
    op.drop_table("stock_tag")
    op.drop_table("tp_sl_point")
    op.drop_table("report")
    op.drop_table("stock_analyze")
