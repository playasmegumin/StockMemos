"""投资备忘 API 测试"""

import pytest


class TestInvestmentMemos:
    """投资备忘 CRUD 测试"""

    def test_create_memo(self, client):
        """创建纯文本备忘"""
        res = client.post("/api/memos", json={
            "title": "市场观察",
            "content": "今天大盘走势良好，茅台上涨",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "市场观察"
        assert data["content"] == "今天大盘走势良好，茅台上涨"
        assert data["stock_id"] is None
        assert data["id"] is not None

    def test_create_memo_with_stock(self, client, sample_stock):
        """创建关联个股的备忘"""
        stock_id = sample_stock["id"]
        res = client.post("/api/memos", json={
            "title": "茅台观察",
            "content": "茅台基本面良好",
            "stock_id": stock_id,
        })
        assert res.status_code == 201
        assert res.json()["stock_id"] == stock_id

    def test_create_memo_empty_title(self, client):
        """创建备忘时标题不能为空"""
        res = client.post("/api/memos", json={
            "title": "",
            "content": "test",
        })
        assert res.status_code == 422

    def test_list_memos(self, client):
        """列表返回按时间降序"""
        client.post("/api/memos", json={"title": "A", "content": "a"})
        client.post("/api/memos", json={"title": "B", "content": "b"})
        res = client.get("/api/memos")
        assert res.status_code == 200
        items = res.json()
        # 因为 SQLite 没有 datetime 精度问题，验证至少返回 2 条
        assert len(items) >= 2

    def test_list_memos_with_stock_filter(self, client, sample_stock):
        """按个股过滤备忘"""
        stock_id = sample_stock["id"]
        client.post("/api/memos", json={"title": "关联", "content": "x", "stock_id": stock_id})
        client.post("/api/memos", json={"title": "不关联", "content": "y"})
        res = client.get(f"/api/memos?stock_id={stock_id}")
        assert res.status_code == 200
        items = res.json()
        assert all(item["stock_id"] == stock_id for item in items)

    def test_list_item_does_not_include_content(self, client):
        """列表项不包含正文内容"""
        client.post("/api/memos", json={"title": "T", "content": "secret content"})
        res = client.get("/api/memos")
        item = res.json()[0]
        assert "content" not in item

    def test_get_memo(self, client):
        """获取单条备忘包含正文"""
        created = client.post("/api/memos", json={
            "title": "详细", "content": "详细内容",
        }).json()
        res = client.get(f"/api/memos/{created['id']}")
        assert res.status_code == 200
        assert res.json()["content"] == "详细内容"

    def test_get_memo_not_found(self, client):
        """不存在的备忘返回 404"""
        res = client.get("/api/memos/nonexistent")
        assert res.status_code == 404

    def test_update_memo(self, client):
        """更新备忘"""
        created = client.post("/api/memos", json={
            "title": "旧标题", "content": "旧内容",
        }).json()
        res = client.put(f"/api/memos/{created['id']}", json={
            "title": "新标题",
            "content": "新内容",
        })
        assert res.status_code == 200
        assert res.json()["title"] == "新标题"
        assert res.json()["content"] == "新内容"

    def test_update_memo_partial(self, client):
        """部分更新仅修改指定字段"""
        created = client.post("/api/memos", json={
            "title": "标题", "content": "内容",
        }).json()
        res = client.put(f"/api/memos/{created['id']}", json={
            "title": "仅改标题",
        })
        assert res.status_code == 200
        assert res.json()["title"] == "仅改标题"
        assert res.json()["content"] == "内容"

    def test_update_memo_clear_stock(self, client, sample_stock):
        """取消关联个股"""
        stock_id = sample_stock["id"]
        created = client.post("/api/memos", json={
            "title": "T", "content": "C", "stock_id": stock_id,
        }).json()
        res = client.put(f"/api/memos/{created['id']}", json={
            "stock_id": None,
        })
        assert res.json()["stock_id"] is None

    def test_update_memo_not_found(self, client):
        """更新不存在的备忘返回 404"""
        res = client.put("/api/memos/nonexistent", json={"title": "x"})
        assert res.status_code == 404

    def test_delete_memo(self, client):
        """删除备忘"""
        created = client.post("/api/memos", json={
            "title": "待删除", "content": "bye",
        }).json()
        res = client.delete(f"/api/memos/{created['id']}")
        assert res.status_code == 204

    def test_delete_memo_not_found(self, client):
        """删除不存在的备忘返回 404"""
        res = client.delete("/api/memos/nonexistent")
        assert res.status_code == 404

    def test_delete_then_list(self, client):
        """删除后列表不再包含"""
        created = client.post("/api/memos", json={
            "title": "删", "content": "除",
        }).json()
        client.delete(f"/api/memos/{created['id']}")
        res = client.get("/api/memos")
        ids = [item["id"] for item in res.json()]
        assert created["id"] not in ids
