#!/usr/bin/env python3
"""Seed exchange_rates table with default values.

Runs at container startup to populate the exchange rate dictionary.
Values are kept in sync with frontend/src/config/exchangeRates.ts
"""

import sys
import os

# Add backend dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.exchange_rate import ExchangeRate

DEFAULT_RATES = {
    "CNY": 1.0,
    "HKD": 0.86754,
    "USD": 6.8047,
}


def seed_exchange_rates():
    db = SessionLocal()
    try:
        for currency, rate in DEFAULT_RATES.items():
            existing = db.query(ExchangeRate).filter(
                ExchangeRate.currency == currency
            ).first()
            if existing:
                existing.rate_to_cny = rate
            else:
                db.add(ExchangeRate(currency=currency, rate_to_cny=rate))
        db.commit()
        print(f"[seed] exchange_rates: {len(DEFAULT_RATES)} rows synced")
    except Exception as e:
        print(f"[seed] error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_exchange_rates()
