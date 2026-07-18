"""create historical_adjustment table

Revision ID: 010
Revises: 009
Create Date: 2026-07-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "historical_adjustment",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_historical_adjustment"),
        comment="历史盈亏调整记录",
    )
    op.create_index("ix_historical_adjustment_created_at",
                    "historical_adjustment", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_historical_adjustment_created_at",
                  table_name="historical_adjustment")
    op.drop_table("historical_adjustment")
