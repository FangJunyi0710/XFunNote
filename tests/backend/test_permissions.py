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
                "name": "新权限",
                "description": "测试",
                "read_view": json.dumps(self.SAMPLE_VIEW),
                "write_view": json.dumps(self.SAMPLE_VIEW),
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "新权限"

class TestUpdatePermission:
    """PUT /api/v0/permissions/{permission_id}"""
    SAMPLE_VIEW = {"plan": [{"columns": ["content"], "filter": []}]}
    def test_create(self, client):
        resp = client.post(
            "/api/v0/permissions",
            json={
                "name": "新权限",
                "description": "测试",
                "read_view": json.dumps(self.SAMPLE_VIEW),
                "write_view": json.dumps(self.SAMPLE_VIEW),
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "新权限"
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

    def test_update_description(self, client, demo_perm):
        """PUT 更新 description 字段。"""
        resp = client.put(
            f"/api/v0/permissions/{demo_perm['id']}",
            json={"description": "新的描述"},
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "新的描述"

    def test_update_read_view(self, client, demo_perm):
        """PUT 更新 read_view 字段。"""
        new_view = {"plan": [{"columns": ["id"], "filter": []}]}
        resp = client.put(
            f"/api/v0/permissions/{demo_perm['id']}",
            json={"read_view": new_view},
        )
        assert resp.status_code == 200

    def test_update_write_view(self, client, demo_perm):
        """PUT 更新 write_view 字段。"""
        new_view = {"plan": [{"columns": ["id"], "filter": []}]}
        resp = client.put(
            f"/api/v0/permissions/{demo_perm['id']}",
            json={"write_view": new_view},
        )
        assert resp.status_code == 200

    def test_update_no_fields(self, client, demo_perm):
        """PUT 不提供任何更新字段，走查询分支（99-100行）。"""
        resp = client.put(
            f"/api/v0/permissions/{demo_perm['id']}",
            json={},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == demo_perm["name"]


class TestDeletePermission:
    """DELETE /api/v0/permissions/{permission_id}"""

    def test_delete(self, client, demo_perm):
        resp = client.delete(f"/api/v0/permissions/{demo_perm['id']}")
        assert resp.status_code == 200
        assert "已删除" in resp.json()["message"]

    def test_delete_not_found(self, client):
        resp = client.delete("/api/v0/permissions/nonexistent")
        assert resp.status_code == 404
