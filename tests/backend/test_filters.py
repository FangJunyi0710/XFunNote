"""测试筛选条件管理路由。"""

from __future__ import annotations

import json


class TestListFilters:
    """GET /api/v0/filters"""

    def test_list_empty(self, client):
        resp = client.get("/api/v0/filters")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_data(self, client, demo_filter):
        resp = client.get("/api/v0/filters")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1


class TestGetFilter:
    """GET /api/v0/filters/{name}"""

    def test_get(self, client, demo_filter):
        resp = client.get(f"/api/v0/filters/{demo_filter['name']}")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)

    def test_get_not_found(self, client):
        resp = client.get("/api/v0/filters/nonexistent")
        assert resp.status_code == 404


class TestSaveFilter:
    """PUT /api/v0/filters/{name}"""

    def test_create(self, client):
        resp = client.put(
            "/api/v0/filters/new-filter",
            json={"conditions": [{"field": "content", "op": "contains", "value": "test"}]},
        )
        assert resp.status_code == 200
        assert "已保存" in resp.json()["message"]

    def test_update(self, client, demo_filter):
        resp = client.put(
            f"/api/v0/filters/{demo_filter['name']}",
            json={"conditions": [{"field": "month", "op": "=", "value": "2607"}]},
        )
        assert resp.status_code == 200


class TestDeleteFilter:
    """DELETE /api/v0/filters/{name}"""

    def test_delete(self, client, demo_filter):
        resp = client.delete(f"/api/v0/filters/{demo_filter['name']}")
        assert resp.status_code == 200
        assert "已删除" in resp.json()["message"]

    def test_delete_not_found(self, client):
        resp = client.delete("/api/v0/filters/nonexistent")
        assert resp.status_code == 404
