"""测试 Token 管理路由。"""

from __future__ import annotations


class TestListTokens:
    """GET /api/v1/tokens"""

    def test_list_empty(self, client):
        resp = client.get("/api/v1/tokens")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_data(self, client, demo_token):
        resp = client.get("/api/v1/tokens")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["name"] == "test-token"


class TestGetToken:
    """GET /api/v1/tokens/{token_id}"""

    def test_get(self, client, demo_token):
        resp = client.get(f"/api/v1/tokens/{demo_token['id']}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "test-token"

    def test_get_not_found(self, client):
        resp = client.get("/api/v1/tokens/nonexistent")
        assert resp.status_code == 404


class TestCreateToken:
    """POST /api/v1/tokens"""

    def test_create(self, client, demo_perm):
        resp = client.post(
            "/api/v1/tokens",
            json={"name": "新Token", "permission": "test-permission"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "新Token"
        assert data["permission"] == "test-permission"
        assert "token" in data
        assert data["is_active"] == 1

    def test_create_with_shortcut(self, client, demo_perm):
        resp = client.post(
            "/api/v1/tokens",
            json={"name": "快捷Token", "permission": "test-permission", "shortcut": "my-shortcut"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["shortcut"] == "my-shortcut"
        assert data["shortcut_expire_at"] is not None

    def test_create_invalid_permission(self, client):
        resp = client.post(
            "/api/v1/tokens",
            json={"name": "无效权限", "permission": "nonexistent"},
        )
        assert resp.status_code == 400
        assert "不存在" in resp.json()["detail"]


class TestUpdateToken:
    """PUT /api/v1/tokens/{token_id}"""

    def test_update_name(self, client, demo_token):
        resp = client.put(
            f"/api/v1/tokens/{demo_token['id']}",
            json={"name": "更新后的名称"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "更新后的名称"

    def test_update_deactivate(self, client, demo_token):
        resp = client.put(
            f"/api/v1/tokens/{demo_token['id']}",
            json={"is_active": False},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] == 0

    def test_update_permission(self, client, demo_token, demo_perm):
        # 创建第二个权限（使用原始 SQL INSERT 避免 id 被自动覆盖）
        import json
        import xfun
        from xfun.core.view import full_view, root_permission, view_to_json
        from xfun.core.filter import Condition
        from xfun.core import ops as _ops

        perm = root_permission(xfun.db)
        fv = view_to_json(full_view(xfun.db))
        with xfun.db.transaction() as conn:
            from xfun.utils.time_utils import now_str
            now = now_str()
            conn.execute(
                "INSERT INTO _permission (id, name, description, read_view, write_view, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    "another-perm",
                    "另一个权限",
                    "",
                    json.dumps(fv, ensure_ascii=False),
                    json.dumps(fv, ensure_ascii=False),
                    now,
                    now,
                ],
            )

        resp = client.put(
            f"/api/v1/tokens/{demo_token['id']}",
            json={"permission": "another-perm"},
        )
        assert resp.status_code == 200
        assert resp.json()["permission"] == "another-perm"

    def test_update_invalid_permission(self, client, demo_token):
        resp = client.put(
            f"/api/v1/tokens/{demo_token['id']}",
            json={"permission": "nonexistent"},
        )
        assert resp.status_code == 400

    def test_update_not_found(self, client):
        resp = client.put(
            "/api/v1/tokens/nonexistent",
            json={"name": "新名称"},
        )
        assert resp.status_code == 404


class TestDeleteToken:
    """DELETE /api/v1/tokens/{token_id}"""

    def test_delete(self, client, demo_token):
        resp = client.delete(f"/api/v1/tokens/{demo_token['id']}")
        assert resp.status_code == 200
        assert "已删除" in resp.json()["message"]

    def test_delete_not_found(self, client):
        resp = client.delete("/api/v1/tokens/nonexistent")
        assert resp.status_code == 404


class TestExchangeToken:
    """POST /api/v1/tokens/exchange"""

    def test_exchange(self, client, demo_perm):
        # 先创建带 shortcut 的 token
        create_resp = client.post(
            "/api/v1/tokens",
            json={"name": "可兑换", "permission": "test-permission", "shortcut": "exchange-me"},
        )
        assert create_resp.status_code == 201

        resp = client.post(
            "/api/v1/tokens/exchange",
            json={"shortcut": "exchange-me"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert len(data["token"]) > 0

    def test_exchange_not_found(self, client):
        resp = client.post(
            "/api/v1/tokens/exchange",
            json={"shortcut": "non-existent"},
        )
        assert resp.status_code == 404

    def test_exchange_one_time(self, client, demo_perm):
        """验证 shortcut 一次性使用。"""
        client.post(
            "/api/v1/tokens",
            json={"name": "一次性", "permission": "test-permission", "shortcut": "one-time"},
        )
        resp1 = client.post("/api/v1/tokens/exchange", json={"shortcut": "one-time"})
        assert resp1.status_code == 200
        resp2 = client.post("/api/v1/tokens/exchange", json={"shortcut": "one-time"})
        assert resp2.status_code == 404


class TestCurrentTokenInfo:
    """GET /api/v1/tokens/info"""

    def test_info(self, client, demo_token):
        resp = client.get("/api/v1/tokens/info", headers={"X-API-Key": demo_token.get("token", "")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "test-token"
        assert "read_view" in data
        assert "write_view" in data
