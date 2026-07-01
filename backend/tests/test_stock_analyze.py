"""个股分析 CRUD 及基本面数据更新测试"""


def test_get_or_create_analyze(client, sample_stock):
    stock_id = sample_stock["id"]
    res = client.get(f"/api/stock-analyze/stock/{stock_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["stock_id"] == stock_id
    assert data["fundamentals_data"] is None


def test_get_or_create_is_idempotent(client, sample_stock):
    stock_id = sample_stock["id"]
    r1 = client.get(f"/api/stock-analyze/stock/{stock_id}").json()
    r2 = client.get(f"/api/stock-analyze/stock/{stock_id}").json()
    assert r1["id"] == r2["id"]  # same record, 1:1


def test_update_fundamentals(client, sample_stock):
    stock_id = sample_stock["id"]
    analyze = client.get(f"/api/stock-analyze/stock/{stock_id}").json()
    res = client.put(
        f"/api/stock-analyze/{analyze['id']}",
        json={"fundamentals_data": {"pe_ttm": 25.5, "pb": 6.2, "roe": 0.18}},
    )
    assert res.status_code == 200
    assert res.json()["fundamentals_data"]["pe_ttm"] == 25.5


def test_stock_analyze_404(client):
    res = client.get("/api/stock-analyze/stock/nonexistent")
    assert res.status_code == 404
