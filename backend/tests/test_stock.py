"""个股 CRUD 测试"""


def test_create_stock(client):
    res = client.post(
        "/api/stocks",
        json={
            "exchange": "SH",
            "symbol": "600519",
            "name": "贵州茅台",
            "currency": "CNY",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["exchange"] == "SH"
    assert data["symbol"] == "600519"
    assert data["name"] == "贵州茅台"
    assert data["position"] == 0.0
    assert data["historical_pnl"] == 0.0
    assert "id" in data


def test_create_stock_duplicate(client):
    client.post(
        "/api/stocks",
        json={
            "exchange": "SH",
            "symbol": "600519",
            "name": "贵州茅台",
            "currency": "CNY",
        },
    )
    res = client.post(
        "/api/stocks",
        json={
            "exchange": "SH",
            "symbol": "600519",
            "name": "Duplicate",
            "currency": "CNY",
        },
    )
    assert res.status_code == 409


def test_list_stocks(client, sample_stock):
    res = client.get("/api/stocks")
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_get_stock(client, sample_stock):
    res = client.get(f"/api/stocks/{sample_stock['id']}")
    assert res.status_code == 200
    assert res.json()["name"] == "贵州茅台"


def test_update_stock(client, sample_stock):
    res = client.put(
        f"/api/stocks/{sample_stock['id']}", json={"name": "茅台更新"}
    )
    assert res.status_code == 200
    assert res.json()["name"] == "茅台更新"


def test_delete_stock(client, sample_stock):
    res = client.delete(f"/api/stocks/{sample_stock['id']}")
    assert res.status_code == 204
    # verify deleted
    res = client.get(f"/api/stocks/{sample_stock['id']}")
    assert res.status_code == 404
