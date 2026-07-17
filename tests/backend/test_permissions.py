"""测试权限管理路由。"""

from __future__ import annotations

import json


class TestListPermissions:
    """GET /api/v0/permissions"""

    def test_list_empty(self, client):
        resp = client.get("/api/v0/permissions")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_data(self, client, demo_perm):
        resp = client.get("/api/v0/permissions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1


class TestGetPermission:
    """GET /api/v0/permissions/{permission_id}"""

    def test_get(self, client, demo_perm):
        resp = client.get(f"/api/v0/permissions/{demo_perm['id']}")
        assert resp.status_code == 200
        assert resp.json()["name"] == demo_perm["name"]

    def test_get_not_found(self, client):
        resp = client.get("/api/v0/permissions/nonexistent")
        assert resp.status_code == 404


class TestCreatePermission:
    """POST /api/v0/permissions"""

    SAMPLE_VIEW = {"plan": [{"columns": ["content"], "filter": []}]}

    def test_create(self, client):
        resp = client.post(
            "/api/v0/permissions",
            json={
                "id": "new-perm",
                "name": "新权限",
                "description": "测试",
                "read_view": self.SAMPLE_VIEW,
                "write_view": self.SAMPLE_VIEW,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        # id 字段 auto=True，会生成带前缀的 id
        assert data["id"].startswith("_permission-") or data["id"] == "new-perm"
        assert data["name"] == "新权限"

class TestUpdatePermission:
    """PUT /api/v0/permissions/{permission_id}"""

    def test_update_name(self, client, demo_perm):
        resp = client.put(
            f"/api/v0/permissions/{demo_perm['id']}",
            json={"name": "新名称"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "新名称"

    def test_update_not_found(self, client):
        resp = client.put(
            "/api/v0/permissions/nonexistent",
            json={"name": "新名称"},
        )
        assert resp.status_code == 404


class TestDeletePermission:
    """DELETE /api/v0/permissions/{permission_id}"""

    def test_delete(self, client, demo_perm):
        resp = client.delete(f"/api/v0/permissions/{demo_perm['id']}")
        assert resp.status_code == 200
        assert "已删除" in resp.json()["message"]

    def test_delete_not_found(self, client):
        resp = client.delete("/api/v0/permissions/nonexistent")
        assert resp.status_code == 404
