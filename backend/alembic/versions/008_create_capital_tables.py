"""create capital flow tables + triggers

Revision ID: 008
Revises: 007
Create Date: 2026-07-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── exchange_rates ──────────────────────────────
    op.create_table(
        "exchange_rates",
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("rate_to_cny", sa.Numeric(18, 6), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("currency", name="pk_exchange_rates"),
        comment="汇率字典",
    )

    # ── capital_flow ────────────────────────────────
    op.create_table(
        "capital_flow",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("currency", sa.String(10),
                  nullable=False, server_default="CNY"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_capital_flow"),
        sa.ForeignKeyConstraint(
            ["currency"], ["exchange_rates.currency"],
            name="fk_capital_flow_currency"
        ),
        comment="现金流水",
    )
    op.create_index("ix_capital_flow_created_at",
                    "capital_flow", ["created_at"])

    # ── capital_meta ────────────────────────────────
    op.create_table(
        "capital_meta",
        sa.Column("id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("total_invested_cny", sa.Numeric(18, 4),
                  nullable=False, server_default="0"),
        sa.Column("total_historical_pnl_cny", sa.Numeric(18, 4),
                  nullable=False, server_default="0"),
        sa.Column("total_position_value_cny", sa.Numeric(18, 4),
                  nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id", name="pk_capital_meta"),
        sa.CheckConstraint("id = 1", name="ck_capital_meta_single_row"),
        comment="资金汇总缓存（单行）",
    )

    # ── initial capital_meta row ────────────────────
    op.execute("INSERT INTO capital_meta (id) VALUES (1)")

    # ── trigger: recalc_invested() ──────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION recalc_invested()
        RETURNS trigger AS $$
        BEGIN
            UPDATE capital_meta SET
                total_invested_cny = (
                    SELECT COALESCE(SUM(cf.amount * er.rate_to_cny), 0)
                    FROM capital_flow cf
                    JOIN exchange_rates er ON cf.currency = er.currency
                ),
                updated_at = NOW()
            WHERE id = 1;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_capital_flow_recalc
        AFTER INSERT OR DELETE ON capital_flow
        FOR EACH STATEMENT
        EXECUTE FUNCTION recalc_invested();
    """)

    # ── trigger: recalc_pnl_position() ──────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION recalc_pnl_position()
        RETURNS trigger AS $$
        BEGIN
            UPDATE capital_meta SET
                total_historical_pnl_cny = (
                    SELECT COALESCE(SUM(s.historical_pnl * er.rate_to_cny), 0)
                    FROM stock s
                    JOIN exchange_rates er ON s.currency = er.currency
                ),
                total_position_value_cny = (
                    SELECT COALESCE(SUM(s.position * kd.close * er.rate_to_cny), 0)
                    FROM stock s
                    JOIN exchange_rates er ON s.currency = er.currency
                    LEFT JOIN LATERAL (
                        SELECT close FROM kline_daily
                        WHERE stock_id = s.id
                        ORDER BY trade_date DESC
                        LIMIT 1
                    ) kd ON true
                ),
                updated_at = NOW()
            WHERE id = 1;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_transaction_recalc
        AFTER INSERT OR DELETE OR UPDATE ON transaction
        FOR EACH STATEMENT
        EXECUTE FUNCTION recalc_pnl_position();
    """)

    op.execute("""
        CREATE TRIGGER trg_stock_delete_recalc
        AFTER DELETE ON stock
        FOR EACH STATEMENT
        EXECUTE FUNCTION recalc_pnl_position();
    """)

    # ── trigger: recalc_position_value() ────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION recalc_position_value()
        RETURNS trigger AS $$
        BEGIN
            UPDATE capital_meta SET
                total_position_value_cny = (
                    SELECT COALESCE(SUM(s.position * kd.close * er.rate_to_cny), 0)
                    FROM stock s
                    JOIN exchange_rates er ON s.currency = er.currency
                    LEFT JOIN LATERAL (
                        SELECT close FROM kline_daily
                        WHERE stock_id = s.id
                        ORDER BY trade_date DESC
                        LIMIT 1
                    ) kd ON true
                ),
                updated_at = NOW()
            WHERE id = 1;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_kline_daily_recalc
        AFTER INSERT OR UPDATE ON kline_daily
        FOR EACH STATEMENT
        EXECUTE FUNCTION recalc_position_value();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_kline_daily_recalc ON kline_daily")
    op.execute("DROP TRIGGER IF EXISTS trg_stock_delete_recalc ON stock")
    op.execute("DROP TRIGGER IF EXISTS trg_transaction_recalc ON transaction")
    op.execute("DROP TRIGGER IF EXISTS trg_capital_flow_recalc ON capital_flow")
    op.execute("DROP FUNCTION IF EXISTS recalc_position_value()")
    op.execute("DROP FUNCTION IF EXISTS recalc_pnl_position()")
    op.execute("DROP FUNCTION IF EXISTS recalc_invested()")
    op.drop_table("capital_meta")
    op.drop_table("capital_flow")
    op.drop_table("exchange_rates")
