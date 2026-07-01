"""drop portfolio and trade_point tables (replaced by stock + transaction)

Revision ID: 005
Revises: 004
Create Date: 2025-07-01 16:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # trade_point 有 FK → portfolio.id，必须先删 trade_point
    op.drop_table("trade_point")
    op.drop_table("portfolio")


def downgrade() -> None:
    # 恢复 portfolio 表
    op.create_table(
        "portfolio",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("stock_code", sa.String(20), nullable=False),
        sa.Column("stock_name", sa.String(100), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("cost_price", sa.Numeric(10, 4), nullable=False),
        sa.Column("build_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), server_default="holding"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        comment="用户持仓记录",
    )
    # 恢复 trade_point 表
    op.create_table(
        "trade_point",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("portfolio_id", sa.String(36), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("price", sa.Numeric(10, 4), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("report_id", sa.String(36), nullable=True),
        sa.Column("trade_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolio.id"]),
        comment="买卖点记录",
    )
