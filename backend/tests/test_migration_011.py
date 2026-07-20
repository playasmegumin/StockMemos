"""Focused migration 011 upgrade test.

Creates a pre-011 table (no currency column), inserts rows, applies the
011 upgrade operations via Alembic's MigrationContext, and verifies all
rows received currency='CNY'.

Uses SQLite in-memory — Alembic's add_column with server_default is
compatible with SQLite.
"""

import sqlalchemy as sa
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, MetaData, Table, Column, String, Numeric, Text, DateTime, func
from sqlalchemy import inspect as sa_inspect


def test_migration_011_adds_currency_column():
    """Simulate upgrading from 010 to 011: currency column added, rows backfilled CNY."""
    engine = create_engine("sqlite://", echo=False)

    # ── Create a pre-011 table schema (no currency column) ─────────
    meta = MetaData()
    Table(
        "historical_adjustment", meta,
        Column("id", String(36), primary_key=True),
        Column("amount", Numeric(18, 4), nullable=False),
        Column("note", Text(), nullable=True),
        Column("created_at", DateTime(), server_default=func.now(), nullable=False),
        Column("updated_at", DateTime(), server_default=func.now(), nullable=False),
    )
    meta.create_all(engine)

    # ── Insert three rows ──────────────────────────────────────────
    with engine.connect() as conn:
        for i in range(1, 4):
            conn.execute(
                sa.text(
                    "INSERT INTO historical_adjustment (id, amount, note) "
                    "VALUES (:id, :amount, :note)"
                ),
                {"id": f"pre-011-{i:03d}", "amount": 100.0 * i, "note": f"row {i}"},
            )
        conn.commit()

    # ── Verify there is NO currency column before migration ────────
    cols_before = {c["name"] for c in sa_inspect(engine).get_columns("historical_adjustment")}
    assert "currency" not in cols_before, "currency column should not exist before 011"

    # ── Apply the 011 upgrade via Alembic Operations API ───────────
    with engine.begin() as connection:
        ctx = MigrationContext.configure(connection)
        op = Operations(ctx)

        # Exact operations from 011_add_currency_to_historical_adjustment.upgrade()
        op.add_column(
            "historical_adjustment",
            Column("currency", String(3), nullable=False, server_default="CNY"),
        )
        op.execute(
            "UPDATE historical_adjustment SET currency = 'CNY' WHERE currency IS NULL"
        )

    # ── Verify currency column exists and rows backfilled ──────────
    cols_after = {c["name"] for c in sa_inspect(engine).get_columns("historical_adjustment")}
    assert "currency" in cols_after, "currency column should exist after 011"

    with engine.connect() as conn:
        rows = conn.execute(
            sa.text("SELECT id, amount, currency FROM historical_adjustment ORDER BY id")
        ).fetchall()
        assert len(rows) == 3, f"expected 3 rows, got {len(rows)}"
        for row in rows:
            row_id, _, ccy = row
            assert ccy == "CNY", f"expected CNY for row {row_id}, got {ccy}"
