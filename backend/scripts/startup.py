#!/usr/bin/env python3
"""Application startup script — runs before uvicorn.

Steps:
  1. Create all ORM tables (models must be imported so SQLAlchemy can see them)
  2. Stamp alembic to head (skip broken old migrations, schema managed by ORM)
  3. Create DB triggers (not handled by SQLAlchemy ORM)
  4. Seed exchange_rates table
  5. Start uvicorn
"""

import sys
import os
import subprocess

# Ensure backend directory (parent of scripts/) is on the path
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _backend_dir)

# Step 1: import ALL models so SQLAlchemy knows about them
from app.database import Base, engine
import app.models  # noqa — registers all ORM tables

Base.metadata.create_all(bind=engine)
print("[startup] ORM tables created/verified")

# Step 2: stamp alembic to head (schema managed by ORM, migrations for drift detection)
subprocess.run(["alembic", "stamp", "head"], check=True)
print("[startup] alembic stamped to head")

# Step 3: create DB triggers (SQLAlchemy ORM does not manage triggers)
triggers_sql = """
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

DROP TRIGGER IF EXISTS trg_capital_flow_recalc ON capital_flow;
CREATE TRIGGER trg_capital_flow_recalc
AFTER INSERT OR DELETE ON capital_flow
FOR EACH STATEMENT
EXECUTE FUNCTION recalc_invested();

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

DROP TRIGGER IF EXISTS trg_transaction_recalc ON transaction;
CREATE TRIGGER trg_transaction_recalc
AFTER INSERT OR DELETE OR UPDATE ON transaction
FOR EACH STATEMENT
EXECUTE FUNCTION recalc_pnl_position();

DROP TRIGGER IF EXISTS trg_stock_delete_recalc ON stock;
CREATE TRIGGER trg_stock_delete_recalc
AFTER DELETE ON stock
FOR EACH STATEMENT
EXECUTE FUNCTION recalc_pnl_position();

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

DROP TRIGGER IF EXISTS trg_kline_daily_recalc ON kline_daily;
CREATE TRIGGER trg_kline_daily_recalc
AFTER INSERT OR UPDATE ON kline_daily
FOR EACH STATEMENT
EXECUTE FUNCTION recalc_position_value();
"""

with engine.connect() as conn:
    conn.execute(__import__("sqlalchemy").text(triggers_sql))
    conn.commit()
print("[startup] DB triggers created")

# Step 4: seed exchange_rates (ensure capital_meta row exists too)
from scripts.seed_exchange_rates import seed_exchange_rates
seed_exchange_rates()

# Also ensure capital_meta row exists
with engine.connect() as conn:
    conn.execute(__import__("sqlalchemy").text(
        "INSERT INTO capital_meta (id) VALUES (1) ON CONFLICT (id) DO NOTHING"
    ))
    conn.commit()
print("[startup] exchange_rates seeded + capital_meta row")

# Step 5: start uvicorn
print("[startup] starting uvicorn...")
os.execvp("uvicorn", ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"])
