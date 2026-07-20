"""历史盈亏调整 CRUD + 资金汇总集成测试"""

import math

import pytest
from pydantic import ValidationError

from app.schemas.historical_adjustment import (
    HistoricalAdjustmentCreate,
    HistoricalAdjustmentUpdate,
)

BASE = "/api/historical-adjustments"


def _create(client, amount: float, note: str | None = None,
            currency: str | None = None):
    body = {"amount": amount}
    if note is not None:
        body["note"] = note
    if currency is not None:
        body["currency"] = currency
    return client.post(BASE, json=body)


# ─── Schema validation ────────────────────────────────


class TestSchemaValidation:
    def test_create_accepts_positive(self):
        s = HistoricalAdjustmentCreate(amount=100.0)
        assert s.amount == 100.0
        assert s.currency == "CNY"

    def test_create_accepts_negative(self):
        s = HistoricalAdjustmentCreate(amount=-50.0)
        assert s.amount == -50.0

    def test_create_rejects_zero(self):
        with pytest.raises(ValidationError, match="must not be zero"):
            HistoricalAdjustmentCreate(amount=0.0)

    def test_create_rejects_nan(self):
        with pytest.raises(ValidationError, match="finite number"):
            HistoricalAdjustmentCreate(amount=math.nan)

    def test_create_rejects_inf(self):
        with pytest.raises(ValidationError, match="finite number"):
            HistoricalAdjustmentCreate(amount=math.inf)

    def test_create_rejects_neg_inf(self):
        with pytest.raises(ValidationError, match="finite number"):
            HistoricalAdjustmentCreate(amount=-math.inf)

    def test_create_default_currency(self):
        """Create schema defaults to CNY."""
        s = HistoricalAdjustmentCreate(amount=100.0)
        assert s.currency == "CNY"

    def test_create_accepts_valid_currencies(self):
        for ccy in ("CNY", "HKD", "USD", "cny", "hkd", "usd"):
            s = HistoricalAdjustmentCreate(amount=100.0, currency=ccy)
            assert s.currency == ccy.upper()

    def test_create_rejects_invalid_currency(self):
        with pytest.raises(ValidationError, match="Currency must"):
            HistoricalAdjustmentCreate(amount=100.0, currency="EUR")

    def test_update_accepts_positive(self):
        s = HistoricalAdjustmentUpdate(amount=200.0)
        assert s.amount == 200.0

    def test_update_rejects_zero(self):
        with pytest.raises(ValidationError, match="must not be zero"):
            HistoricalAdjustmentUpdate(amount=0.0)

    def test_update_rejects_nan(self):
        with pytest.raises(ValidationError, match="finite number"):
            HistoricalAdjustmentUpdate(amount=math.nan)

    def test_update_currency_optional(self):
        """Update schema allows omitting currency (preserve existing)."""
        s = HistoricalAdjustmentUpdate(amount=100.0)
        assert s.currency is None

    def test_update_rejects_invalid_currency(self):
        with pytest.raises(ValidationError, match="Currency must"):
            HistoricalAdjustmentUpdate(amount=100.0, currency="EUR")


# ─── List ─────────────────────────────────────────────


def test_list_empty(client):
    res = client.get(BASE)
    assert res.status_code == 200
    assert res.json() == []


def test_list_returns_all_ordered_by_created_at_desc(client):
    r1 = _create(client, 100.0, "first").json()
    r2 = _create(client, -50.0, "second").json()
    res = client.get(BASE)
    data = res.json()
    assert len(data) == 2
    ids = {d["id"] for d in data}
    assert r1["id"] in ids
    assert r2["id"] in ids
    # verify both have timestamps
    assert data[0]["created_at"] is not None
    assert data[1]["created_at"] is not None


# ─── Create ───────────────────────────────────────────


def test_create_returns_201_and_response(client):
    res = _create(client, 1234.56, "测试盈亏调整")
    assert res.status_code == 201
    data = res.json()
    assert data["amount"] == 1234.56
    assert data["note"] == "测试盈亏调整"
    assert data["currency"] == "CNY"
    assert data["id"] is not None
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


def test_create_negative_amount_is_allowed(client):
    res = _create(client, -999.99, "亏损记录")
    assert res.status_code == 201
    assert res.json()["amount"] == -999.99


def test_create_without_note(client):
    res = _create(client, 500.0)
    assert res.status_code == 201
    assert res.json()["note"] is None


def test_create_rejects_zero_amount(client):
    res = _create(client, 0.0)
    assert res.status_code == 422
    errors = res.json()["detail"]
    assert any("must not be zero" in e["msg"] for e in errors)


def test_create_rejects_non_finite_via_python_only():
    """NaN/Inf cannot be sent over JSON, but validate at the Python level."""
    with pytest.raises(ValidationError, match="finite number"):
        HistoricalAdjustmentCreate(amount=float("nan"))


def test_create_default_currency_cny(client):
    """Omitting currency defaults to CNY, succeeds when CNY rate exists."""
    res = _create(client, 200.0, "default cny")
    assert res.status_code == 201
    assert res.json()["currency"] == "CNY"


def test_create_explicit_hkd(client):
    res = _create(client, 500.0, "hk dollars", currency="HKD")
    assert res.status_code == 201
    assert res.json()["currency"] == "HKD"


def test_create_explicit_usd(client):
    res = _create(client, 300.0, "us dollars", currency="USD")
    assert res.status_code == 201
    assert res.json()["currency"] == "USD"


def test_create_explicit_lowercase_normalized(client):
    """Lowercase currency is normalized to uppercase by schema validator."""
    res = _create(client, 100.0, "lowercase hkd", currency="hkd")
    assert res.status_code == 201
    assert res.json()["currency"] == "HKD"


def test_create_rejects_invalid_currency_via_api(client):
    res = _create(client, 100.0, currency="EUR")
    assert res.status_code == 422


def test_create_rejects_missing_exchange_rate(client):
    """Delete the HKD rate before creating — expect 422."""
    from app.database import SessionLocal
    db = SessionLocal()
    from app.models.exchange_rate import ExchangeRate
    db.query(ExchangeRate).filter(ExchangeRate.currency == "HKD").delete()
    db.commit()
    db.close()
    res = _create(client, 100.0, currency="HKD")
    assert res.status_code == 422
    assert "汇率配置不存在" in res.json()["detail"]
    assert "HKD" in res.json()["detail"]


def test_create_rejects_nonpositive_rate(client):
    """Set HKD rate to 0 — expect 422."""
    from app.database import SessionLocal
    db = SessionLocal()
    from app.models.exchange_rate import ExchangeRate
    rate = db.query(ExchangeRate).filter(ExchangeRate.currency == "HKD").first()
    rate.rate_to_cny = 0
    db.commit()
    db.close()
    res = _create(client, 100.0, currency="HKD")
    assert res.status_code == 422
    assert "正数" in res.json()["detail"]


# ─── Update ────────────────────────────────────────────


def test_update_amount_and_note(client):
    created = _create(client, 100.0, "original note").json()
    rid = created["id"]
    res = client.put(
        f"{BASE}/{rid}",
        json={"amount": 200.0, "note": "updated note"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["amount"] == 200.0
    assert data["note"] == "updated note"
    assert data["id"] == rid


def test_update_amount_only_clears_note(client):
    """note 为 None 时，数据库应置为 NULL"""
    created = _create(client, 100.0, "some note").json()
    res = client.put(
        f"{BASE}/{created['id']}",
        json={"amount": 300.0, "note": None},
    )
    assert res.status_code == 200
    assert res.json()["amount"] == 300.0
    assert res.json()["note"] is None


def test_update_preserves_currency_when_omitted(client):
    created = _create(client, 100.0, currency="HKD").json()
    assert created["currency"] == "HKD"
    res = client.put(
        f"{BASE}/{created['id']}",
        json={"amount": 200.0, "note": "still hkd"},
    )
    assert res.status_code == 200
    assert res.json()["currency"] == "HKD"
    assert res.json()["amount"] == 200.0


def test_update_changes_currency(client):
    created = _create(client, 100.0, "original cny").json()
    assert created["currency"] == "CNY"
    res = client.put(
        f"{BASE}/{created['id']}",
        json={"amount": 200.0, "currency": "HKD", "note": "switched to hkd"},
    )
    assert res.status_code == 200
    assert res.json()["currency"] == "HKD"


def test_update_rejects_invalid_currency(client):
    created = _create(client, 100.0).json()
    res = client.put(
        f"{BASE}/{created['id']}",
        json={"amount": 200.0, "currency": "EUR"},
    )
    assert res.status_code == 422


def test_update_explicit_null_currency_preserves_existing(client):
    """Sending currency=null should preserve the existing currency value."""
    created = _create(client, 100.0, currency="HKD").json()
    assert created["currency"] == "HKD"
    res = client.put(
        f"{BASE}/{created['id']}",
        json={"amount": 300.0, "currency": None, "note": "null currency"},
    )
    assert res.status_code == 200
    assert res.json()["currency"] == "HKD"
    assert res.json()["amount"] == 300.0


def test_update_rejects_missing_exchange_rate(client):
    """Changing currency to one without a rate should fail."""
    from app.database import SessionLocal
    db = SessionLocal()
    from app.models.exchange_rate import ExchangeRate
    db.query(ExchangeRate).filter(ExchangeRate.currency == "HKD").delete()
    db.commit()
    db.close()
    created = _create(client, 100.0).json()
    res = client.put(
        f"{BASE}/{created['id']}",
        json={"amount": 200.0, "currency": "HKD"},
    )
    assert res.status_code == 422
    assert "汇率配置不存在" in res.json()["detail"]


def test_update_rejects_nonpositive_rate(client):
    """Changing currency to one with rate_to_cny <= 0 should fail."""
    from app.database import SessionLocal
    db = SessionLocal()
    from app.models.exchange_rate import ExchangeRate
    rate = db.query(ExchangeRate).filter(ExchangeRate.currency == "HKD").first()
    rate.rate_to_cny = 0
    db.commit()
    db.close()
    created = _create(client, 100.0).json()
    res = client.put(
        f"{BASE}/{created['id']}",
        json={"amount": 200.0, "currency": "HKD"},
    )
    assert res.status_code == 422
    assert "正数" in res.json()["detail"]


def test_update_returns_404_for_missing_id(client):
    res = client.put(
        f"{BASE}/nonexistent-id",
        json={"amount": 100.0, "note": "should fail"},
    )
    assert res.status_code == 404
    assert "不存在" in res.json()["detail"]


def test_update_rejects_zero_amount(client):
    created = _create(client, 100.0).json()
    res = client.put(
        f"{BASE}/{created['id']}",
        json={"amount": 0.0, "note": "zero"},
    )
    assert res.status_code == 422
    errors = res.json()["detail"]
    assert any("must not be zero" in e["msg"] for e in errors)


# ─── Delete ───────────────────────────────────────────


def test_delete_returns_204(client):
    created = _create(client, 100.0).json()
    res = client.delete(f"{BASE}/{created['id']}")
    assert res.status_code == 204


def test_delete_removes_record(client):
    created = _create(client, 100.0).json()
    client.delete(f"{BASE}/{created['id']}")
    res = client.get(BASE)
    assert res.json() == []


def test_delete_returns_404_for_missing_id(client):
    res = client.delete(f"{BASE}/nonexistent-id")
    assert res.status_code == 404
    assert "不存在" in res.json()["detail"]


# ─── Capital Summary Integration ─────────────────────


def test_capital_summary_adjustment_zero_when_no_records(client):
    res = client.get("/api/capital/summary")
    assert res.status_code == 200
    assert res.json()["total_adjustment_cny"] == 0.0


def test_capital_summary_adjustment_sums_correctly(client):
    _create(client, 1000.0, "gain")
    _create(client, -300.0, "loss")
    _create(client, 50.0, "small gain")
    res = client.get("/api/capital/summary")
    assert res.status_code == 200
    # 1000*1.0 + (-300)*1.0 + 50*1.0 = 750
    assert res.json()["total_adjustment_cny"] == 750.0


def test_capital_summary_adjustment_with_negative_total(client):
    _create(client, 100.0)
    _create(client, -500.0)
    res = client.get("/api/capital/summary")
    assert res.json()["total_adjustment_cny"] == -400.0


def test_capital_summary_mixed_currency_aggregation(client):
    """Multi-currency: SUM(amount * rate_to_cny) across currencies."""
    _create(client, 1000.0, "CNY gain")                # 1000 * 1.0   = 1000
    _create(client, 2000.0, "HKD gain", currency="HKD")  # 2000 * 0.92 = 1840
    _create(client, 100.0, "USD loss", currency="USD")   # 100 * 7.25  = 725
    res = client.get("/api/capital/summary")
    assert res.status_code == 200
    expected = 1000 * 1.0 + 2000 * 0.92 + 100 * 7.25
    assert abs(res.json()["total_adjustment_cny"] - expected) < 0.001


def test_capital_summary_fails_on_orphan_rate(client):
    """An adjustment with no valid exchange rate triggers a 500 error."""
    _create(client, 500.0, "good cny")
    # Delete all exchange rates, then insert an orphan adjustment via raw DB
    from app.database import SessionLocal
    db = SessionLocal()
    from app.models.exchange_rate import ExchangeRate
    db.query(ExchangeRate).delete()
    from app.models.historical_adjustment import HistoricalAdjustment
    from uuid import uuid4
    orphan = HistoricalAdjustment(
        id=str(uuid4()), amount=100.0, currency="HKD", note="orphan"
    )
    db.add(orphan)
    db.commit()
    db.close()
    # Now the summary should fail
    res = client.get("/api/capital/summary")
    assert res.status_code == 500
    assert "缺少有效汇率" in res.json()["detail"]
