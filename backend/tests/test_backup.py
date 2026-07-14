"""Tests for backup export/import endpoints"""

import io
import json
import zipfile

from fastapi.testclient import TestClient


class TestBackup:
    """Backup API tests"""

    def test_export_empty_types_returns_422(self, client: TestClient):
        resp = client.post("/api/backup/export", json={"types": []})
        assert resp.status_code == 422

    def test_export_invalid_types_returns_422(self, client: TestClient):
        resp = client.post("/api/backup/export", json={"types": ["invalid"]})
        assert resp.status_code == 422

    def test_export_stocks_only(self, client: TestClient):
        resp = client.post("/api/backup/export", json={"types": ["stocks"]})
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            assert "stocks.json" in zf.namelist()

    def test_export_full_includes_all_files(self, client: TestClient):
        resp = client.post("/api/backup/export", json={"types": ["stocks", "transactions", "memos", "kline"]})
        assert resp.status_code == 200
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            names = zf.namelist()
            assert "stocks.json" in names
            assert "transactions.json" in names
            assert "memos.json" in names

    def test_import_skip_existing_stocks(self, client: TestClient):
        client.post("/api/stocks", json={
            "exchange": "US", "symbol": "SKIPSTK", "name": "Skip Test"
        })
        resp = client.post("/api/backup/export", json={"types": ["stocks"]})
        assert resp.status_code == 200
        resp = client.post("/api/backup/import", files={"file": ("test.zip", resp.content, "application/zip")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"]["stocks"] == 0
        assert len(data["skipped"]["stocks"]) > 0

    def test_import_new_stock(self, client: TestClient):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("stocks.json", json.dumps({
                "version": "1", "exported_at": "2026-07-13T00:00:00Z",
                "stocks": [{"exchange": "US", "symbol": "TESTBK2", "name": "Test Corp", "tags": ["tech"]}]
            }))
            zf.writestr("transactions.json", json.dumps({
                "version": "1", "exported_at": "2026-07-13T00:00:00Z", "transactions": []
            }))
            zf.writestr("memos.json", json.dumps({
                "version": "1", "exported_at": "2026-07-13T00:00:00Z", "memos": []
            }))
        buf.seek(0)
        resp = client.post("/api/backup/import", files={"file": ("test.zip", buf.getvalue(), "application/zip")})
        assert resp.status_code == 200
        assert resp.json()["imported"]["stocks"] == 1

    def test_import_tx_unknown_stock(self, client: TestClient):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("stocks.json", json.dumps({
                "version": "1", "exported_at": "2026-07-13T00:00:00Z", "stocks": []
            }))
            zf.writestr("transactions.json", json.dumps({
                "version": "1", "exported_at": "2026-07-13T00:00:00Z",
                "transactions": [{"exchange": "ZZ", "symbol": "NONEXIST", "quantity": 100, "price": 10, "gas": 0, "traded_at": "2026-01-15"}]
            }))
            zf.writestr("memos.json", json.dumps({
                "version": "1", "exported_at": "2026-07-13T00:00:00Z", "memos": []
            }))
        buf.seek(0)
        resp = client.post("/api/backup/import", files={"file": ("test.zip", buf.getvalue(), "application/zip")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"]["transactions"] == 0
