"""add currency column to historical_adjustment

Revision ID: 011
Revises: 010
Create Date: 2026-07-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "historical_adjustment",
        sa.Column("currency", sa.String(3),
                  nullable=False, server_default="CNY"),
    )
    # Existing rows already get "CNY" via server_default on add_column;
    # explicitly backfill for clarity.
    op.execute("UPDATE historical_adjustment SET currency = 'CNY' WHERE currency IS NULL")


def downgrade() -> None:
    op.drop_column("historical_adjustment", "currency")
