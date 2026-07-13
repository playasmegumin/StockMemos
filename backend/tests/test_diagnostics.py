"""Tests for diagnostics endpoint"""

from fastapi.testclient import TestClient


class TestDiagnostics:
    """Diagnostics endpoint tests"""

    def test_diagnostics_endpoint_returns_200(self, client: TestClient):
        """GET /api/diagnostics should return 200"""
        resp = client.get("/api/diagnostics")
        assert resp.status_code == 200

    def test_diagnostics_response_structure(self, client: TestClient):
        """Response should have services, versions, total_latency_ms, checked_at"""
        resp = client.get("/api/diagnostics")
        data = resp.json()
        assert "services" in data
        assert "versions" in data
        assert "total_latency_ms" in data
        assert "checked_at" in data

    def test_services_is_list(self, client: TestClient):
        """services should be a list of service checks"""
        resp = client.get("/api/diagnostics")
        data = resp.json()
        assert isinstance(data["services"], list)
        assert len(data["services"]) > 0

    def test_each_service_has_required_fields(self, client: TestClient):
        """Each service should have name, category, status, latency_ms, error, checked_at"""
        resp = client.get("/api/diagnostics")
        data = resp.json()
        for svc in data["services"]:
            assert "name" in svc
            assert svc["status"] in ("ok", "error", "skipped")
            assert "latency_ms" in svc
            assert "error" in svc or svc["error"] is None
            assert "checked_at" in svc

    def test_each_service_has_category(self, client: TestClient):
        """Each service should have a category field (datasource or llm)"""
        resp = client.get("/api/diagnostics")
        data = resp.json()
        for svc in data["services"]:
            assert svc["category"] in ("datasource", "llm")

    def test_versions_has_project_and_db(self, client: TestClient):
        """versions should include project_version and db_version"""
        resp = client.get("/api/diagnostics")
        data = resp.json()
        v = data["versions"]
        assert "project_version" in v
        assert "db_version" in v

    def test_datasource_scope(self, client: TestClient):
        """scope=datasource should only return datasource services"""
        resp = client.get("/api/diagnostics?scope=datasource")
        data = resp.json()
        for svc in data["services"]:
            assert svc["category"] == "datasource"
        names = [s["name"] for s in data["services"]]
        assert "TuShare" in names
        assert "AKShare" in names
        assert "DeepSeek" not in names

    def test_llm_scope(self, client: TestClient):
        """scope=llm should only return LLM services"""
        resp = client.get("/api/diagnostics?scope=llm")
        data = resp.json()
        for svc in data["services"]:
            assert svc["category"] == "llm"
        names = [s["name"] for s in data["services"]]
        assert "DeepSeek" in names
        assert "TuShare" not in names

    def test_tushare_is_in_services(self, client: TestClient):
        """TuShare should be one of the services"""
        resp = client.get("/api/diagnostics")
        data = resp.json()
        names = [s["name"] for s in data["services"]]
        assert "TuShare" in names

    def test_yfinance_us_is_in_services(self, client: TestClient):
        """Yahoo Finance (US) should be one of the services"""
        resp = client.get("/api/diagnostics")
        data = resp.json()
        names = [s["name"] for s in data["services"]]
        assert "Yahoo Finance (US)" in names

    def test_yfinance_hk_is_in_services(self, client: TestClient):
        """Yahoo Finance (HK) should be one of the services"""
        resp = client.get("/api/diagnostics")
        data = resp.json()
        names = [s["name"] for s in data["services"]]
        assert "Yahoo Finance (HK)" in names

    def test_skipped_services_have_latency_zero(self, client: TestClient):
        """Skipped services should have latency_ms = 0"""
        resp = client.get("/api/diagnostics")
        data = resp.json()
        for svc in data["services"]:
            if svc["status"] == "skipped":
                assert svc["latency_ms"] == 0

    def test_services_endpoint_returns_metadata(self, client: TestClient):
        """GET /api/diagnostics/services should return static metadata"""
        resp = client.get("/api/diagnostics/services")
        assert resp.status_code == 200
        data = resp.json()
        assert "services" in data
        assert isinstance(data["services"], list)
        assert len(data["services"]) == 8  # 5 datasource + 3 llm
        for svc in data["services"]:
            assert "name" in svc
            assert "category" in svc
            assert "usage" in svc
            assert "registration_type" in svc
            assert svc["category"] in ("datasource", "llm")
            # Verify dynamic fields
            if svc["name"] == "TuShare":
                assert "A 股" in svc["usage"]
            if svc["name"] == "DeepSeek":
                assert svc["usage"] in ("已启用", "未配置")
