"""交易记录 CRUD 及自动重算测试"""


def test_create_transaction(client, sample_stock):
    stock_id = sample_stock["id"]
    res = client.post(
        "/api/transactions",
        json={
            "stock_id": stock_id,
            "quantity": 100,
            "price": 10,
            "gas": 5,
            "traded_at": "2025-06-01",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["quantity"] == 100
    assert data["price"] == 10


def test_transaction_updates_position(client, sample_stock):
    stock_id = sample_stock["id"]
    # buy 100 @ 10, gas=5
    client.post(
        "/api/transactions",
        json={
            "stock_id": stock_id,
            "quantity": 100,
            "price": 10,
            "gas": 5,
            "traded_at": "2025-06-01",
        },
    )
    res = client.get(f"/api/stocks/{stock_id}")
    assert res.json()["position"] == 100  # +100 shares
    assert res.json()["historical_pnl"] == -1005  # -(100*10 + 5)


def test_transaction_full_scenario(client, sample_stock):
    stock_id = sample_stock["id"]
    # buy 100 @ 10, gas=5
    buy = client.post(
        "/api/transactions",
        json={
            "stock_id": stock_id,
            "quantity": 100,
            "price": 10,
            "gas": 5,
            "traded_at": "2025-06-01",
        },
    ).json()
    # sell 50 @ 12, gas=3
    sell = client.post(
        "/api/transactions",
        json={
            "stock_id": stock_id,
            "quantity": -50,
            "price": 12,
            "gas": 3,
            "traded_at": "2025-06-15",
        },
    ).json()
    res = client.get(f"/api/stocks/{stock_id}").json()
    assert res["position"] == 50
    assert res["historical_pnl"] == -408  # -(100*10+5) + -(-50*12+3)
    # update sell: -50 -> -40
    client.put(f"/api/transactions/{sell['id']}", json={"quantity": -40})
    res = client.get(f"/api/stocks/{stock_id}").json()
    assert res["position"] == 60
    # delete buy
    client.delete(f"/api/transactions/{buy['id']}")
    res = client.get(f"/api/stocks/{stock_id}").json()
    assert res["position"] == -40


def test_list_transactions_by_stock(client, sample_stock):
    stock_id = sample_stock["id"]
    client.post(
        "/api/transactions",
        json={
            "stock_id": stock_id,
            "quantity": 100,
            "price": 10,
            "gas": 0,
            "traded_at": "2025-06-01",
        },
    )
    res = client.get(f"/api/transactions/stock/{stock_id}")
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_delete_transaction_recalculates(client, sample_stock):
    stock_id = sample_stock["id"]
    t1 = client.post(
        "/api/transactions",
        json={
            "stock_id": stock_id,
            "quantity": 100,
            "price": 10,
            "gas": 0,
            "traded_at": "2025-06-01",
        },
    ).json()
    t2 = client.post(
        "/api/transactions",
        json={
            "stock_id": stock_id,
            "quantity": 50,
            "price": 12,
            "gas": 0,
            "traded_at": "2025-06-15",
        },
    ).json()
    client.delete(f"/api/transactions/{t1['id']}")
    res = client.get(f"/api/stocks/{stock_id}").json()
    assert res["position"] == 50
