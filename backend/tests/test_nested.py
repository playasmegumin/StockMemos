"""嵌套资源测试: Reports, TpSlPoints, StockTags"""


def test_create_report(client, sample_stock):
    stock_id = sample_stock["id"]
    analyze = client.get(f"/api/stock-analyze/stock/{stock_id}").json()
    aid = analyze["id"]
    res = client.post(
        f"/api/stock-analyze/{aid}/reports",
        json={
            "generated_at": "2025-07-01T10:00:00",
            "title": "基本面分析报告",
            "content": "这是一份测试报告内容...",
        },
    )
    assert res.status_code == 201
    assert res.json()["title"] == "基本面分析报告"


def test_list_reports(client, sample_stock):
    stock_id = sample_stock["id"]
    aid = client.get(f"/api/stock-analyze/stock/{stock_id}").json()["id"]
    client.post(
        f"/api/stock-analyze/{aid}/reports",
        json={
            "generated_at": "2025-07-01T10:00:00",
            "title": "报告1",
            "content": "内容1",
        },
    )
    client.post(
        f"/api/stock-analyze/{aid}/reports",
        json={
            "generated_at": "2025-07-02T10:00:00",
            "title": "报告2",
            "content": "内容2",
        },
    )
    res = client.get(f"/api/stock-analyze/{aid}/reports")
    assert len(res.json()) == 2


def test_cascade_delete_analyze(client, sample_stock):
    stock_id = sample_stock["id"]
    aid = client.get(f"/api/stock-analyze/stock/{stock_id}").json()["id"]
    client.post(
        f"/api/stock-analyze/{aid}/reports",
        json={
            "generated_at": "2025-07-01T10:00:00",
            "title": "级联测试",
            "content": "删除stock_analyze时应被级联删除",
        },
    )
    client.delete(f"/api/stock-analyze/{aid}")
    res = client.get(f"/api/stock-analyze/{aid}/reports")
    assert res.status_code == 404  # analyze gone


def test_create_tp_sl_point(client, sample_stock):
    stock_id = sample_stock["id"]
    aid = client.get(f"/api/stock-analyze/stock/{stock_id}").json()["id"]
    res = client.post(
        f"/api/stock-analyze/{aid}/tp-sl-points",
        json={"price": 150, "label": "卖出", "notes": "达到目标价"},
    )
    assert res.status_code == 201
    assert res.json()["price"] == 150


def test_list_stock_tags(client, sample_stock):
    stock_id = sample_stock["id"]
    aid = client.get(f"/api/stock-analyze/stock/{stock_id}").json()["id"]
    client.post(f"/api/stock-analyze/{aid}/stock-tags", json={"tag": "成长"})
    client.post(f"/api/stock-analyze/{aid}/stock-tags", json={"tag": "分红"})
    res = client.get(f"/api/stock-analyze/{aid}/stock-tags")
    assert len(res.json()) == 2
    assert res.json()[0]["tag"] in ["成长", "分红"]
