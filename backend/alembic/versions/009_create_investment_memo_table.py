"""create investment_memo table

Revision ID: 009
Revises: 008
Create Date: 2026-07-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "investment_memo",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(200), nullable=False, comment="标题"),
        sa.Column("content", sa.Text(), nullable=False, comment="正文（Markdown）"),
        sa.Column("stock_id", sa.String(36), nullable=True, comment="关联个股"),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(),
            nullable=False, comment="创建时间",
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.func.now(),
            nullable=False, comment="更新时间",
        ),
        sa.ForeignKeyConstraint(
            ["stock_id"], ["stock.id"],
            ondelete="SET NULL",
            name="fk_memo_stock",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_investment_memo"),
        comment="投资备忘",
    )
    op.create_index("ix_memo_stock_id", "investment_memo", ["stock_id"])


def downgrade() -> None:
    op.drop_index("ix_memo_stock_id", table_name="investment_memo")
    op.drop_table("investment_memo")
