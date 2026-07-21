"""测试视图管理路由。"""

from __future__ import annotations

import json


class TestListViews:
    """GET /api/v0/views"""

    def test_list_empty(self, client):
        resp = client.get("/api/v0/views")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_data(self, client, demo_view):
        resp = client.get("/api/v0/views")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1


class TestGetView:
    """GET /api/v0/views/{name}"""

    def test_get(self, client, demo_view):
        resp = client.get(f"/api/v0/views/{demo_view['name']}")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)

    def test_get_not_found(self, client):
        resp = client.get("/api/v0/views/nonexistent")
        assert resp.status_code == 404


class TestSaveView:
    """PUT /api/v0/views/{name}"""

    def test_create(self, client):
        resp = client.put(
            "/api/v0/views/new-view",
            json={"plan": [{"columns": ["content"], "filter": {"column": "_", "value": None, "op": "TRUE"}}]},
        )
        assert resp.status_code == 200
        assert "已保存" in resp.json()["message"]
    def test_update(self, client, demo_view):
        resp = client.put(
            f"/api/v0/views/{demo_view['name']}",
            json={"plan": [{"columns": ["content", "month"], "filter": []}]},
        )
        assert resp.status_code == 200
        # 验证已更新
        get_resp = client.get(f"/api/v0/views/{demo_view['name']}")
        assert get_resp.json()["plan"][0]["columns"] == ["content", "month"]


class TestDeleteView:
    """DELETE /api/v0/views/{name}"""

    def test_delete(self, client, demo_view):
        resp = client.delete(f"/api/v0/views/{demo_view['name']}")
        assert resp.status_code == 200
        assert "已删除" in resp.json()["message"]

    def test_delete_not_found(self, client):
        resp = client.delete("/api/v0/views/nonexistent")
        assert resp.status_code == 404
