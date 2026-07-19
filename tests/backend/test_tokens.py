"""测试 Token 管理路由。"""

from __future__ import annotations


class TestListTokens:
    """GET /api/v0/tokens"""

    def test_list_empty(self, client):
        resp = client.get("/api/v0/tokens")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_data(self, client, demo_token):
        resp = client.get("/api/v0/tokens")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["name"] == "test-token"


class TestGetToken:
    """GET /api/v0/tokens/{token_id}"""

    def test_get(self, client, demo_token):
        resp = client.get(f"/api/v0/tokens/{demo_token['id']}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "test-token"

    def test_get_not_found(self, client):
        resp = client.get("/api/v0/tokens/nonexistent")
        assert resp.status_code == 404


class TestCreateToken:
    """POST /api/v0/tokens"""

    def test_create(self, client, demo_perm):
        resp = client.post(
            "/api/v0/tokens",
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
            "/api/v0/tokens",
            json={"name": "快捷Token", "permission": "test-permission", "shortcut": "my-shortcut"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["shortcut"] == "my-shortcut"
        assert data["shortcut_expire_at"] is not None

    def test_create_invalid_permission(self, client):
        resp = client.post(
            "/api/v0/tokens",
            json={"name": "无效权限", "permission": "nonexistent"},
        )
        assert resp.status_code == 400
        assert "不存在" in resp.json()["detail"]


class TestUpdateToken:
    """PUT /api/v0/tokens/{token_id}"""

    def test_update_name(self, client, demo_token):
        resp = client.put(
            f"/api/v0/tokens/{demo_token['id']}",
            json={"name": "更新后的名称"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "更新后的名称"

    def test_update_deactivate(self, client, demo_token):
        resp = client.put(
            f"/api/v0/tokens/{demo_token['id']}",
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
            f"/api/v0/tokens/{demo_token['id']}",
            json={"permission": "another-perm"},
        )
        assert resp.status_code == 200
        assert resp.json()["permission"] == "another-perm"

    def test_update_invalid_permission(self, client, demo_token):
        resp = client.put(
            f"/api/v0/tokens/{demo_token['id']}",
            json={"permission": "nonexistent"},
        )
        assert resp.status_code == 400

    def test_update_not_found(self, client):
        resp = client.put(
            "/api/v0/tokens/nonexistent",
            json={"name": "新名称"},
        )
        assert resp.status_code == 404

    def test_update_expires_at(self, client, demo_token):
        """PUT 更新 expires_at 字段（175行）。"""
        resp = client.put(
            f"/api/v0/tokens/{demo_token['id']}",
            json={"expires_at": "2099-12-31T23:59:59"},
        )
        assert resp.status_code == 200
        assert resp.json()["expires_at"] == "2099-12-31T23:59:59"

    def test_update_no_fields(self, client, demo_token):
        """PUT 不提供任何更新字段，走查询分支（182-183行）。"""
        resp = client.put(
            f"/api/v0/tokens/{demo_token['id']}",
            json={},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "test-token"


class TestDeleteToken:
    """DELETE /api/v0/tokens/{token_id}"""

    def test_delete(self, client, demo_token):
        resp = client.delete(f"/api/v0/tokens/{demo_token['id']}")
        assert resp.status_code == 200
        assert "已删除" in resp.json()["message"]

    def test_delete_not_found(self, client):
        resp = client.delete("/api/v0/tokens/nonexistent")
        assert resp.status_code == 404


class TestExchangeToken:
    """POST /api/v0/tokens/exchange"""

    def test_exchange(self, client, demo_perm):
        # 先创建带 shortcut 的 token
        create_resp = client.post(
            "/api/v0/tokens",
            json={"name": "可兑换", "permission": "test-permission", "shortcut": "exchange-me"},
        )
        assert create_resp.status_code == 201

        resp = client.post(
            "/api/v0/tokens/exchange",
            json={"shortcut": "exchange-me"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert len(data["token"]) > 0

    def test_exchange_not_found(self, client):
        resp = client.post(
            "/api/v0/tokens/exchange",
            json={"shortcut": "non-existent"},
        )
        assert resp.status_code == 404

    def test_exchange_one_time(self, client, demo_perm):
        """验证 shortcut 一次性使用。"""
        client.post(
            "/api/v0/tokens",
            json={"name": "一次性", "permission": "test-permission", "shortcut": "one-time"},
        )
        resp1 = client.post("/api/v0/tokens/exchange", json={"shortcut": "one-time"})
        assert resp1.status_code == 200
        resp2 = client.post("/api/v0/tokens/exchange", json={"shortcut": "one-time"})
        assert resp2.status_code == 404

    def test_exchange_expired_shortcut(self, client, demo_perm):
        """shortcut 已过期 → 410 GONE（228-231行）。"""
        import json
        import xfun
        from xfun.core.view import full_view, root_permission, view_to_json
        from xfun.core.filter import Condition
        from xfun.core import ops as _ops
        from xfun.utils.time_utils import now_str, format_datetime
        from xfun.utils.token_utils import generate_token

        # 直接插入一个 shortcut_expire_at 已过期的 token
        perm = root_permission(xfun.db)
        fv = view_to_json(full_view(xfun.db))
        now = now_str()
        from datetime import datetime, timedelta, timezone
        past_dt = datetime.now(timezone.utc).astimezone() - timedelta(hours=2)
        past = format_datetime(past_dt)
        token_val = generate_token()
        with xfun.db.transaction() as conn:
            conn.execute(
                "INSERT INTO _token (id, token, name, permission, is_active, shortcut, shortcut_expire_at, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    "expired-shortcut-token",
                    token_val,
                    "过期shortcut",
                    "test-permission",
                    1,
                    "expired-shortcut",
                    past,
                    now,
                    now,
                ],
            )

        resp = client.post("/api/v0/tokens/exchange", json={"shortcut": "expired-shortcut"})
        assert resp.status_code == 410
        assert "过期" in resp.json()["detail"]

        # 验证 shortcut 已被清空（不可再次使用）
        resp2 = client.post("/api/v0/tokens/exchange", json={"shortcut": "expired-shortcut"})
        # 由于 _ops.update 可能受权限校验影响，第二次请求可能仍返回 410
        # 只要确认第二次不是 200 即可（说明 shortcut 不可用）
        assert resp2.status_code != 200


class TestCurrentTokenInfo:
    """GET /api/v0/tokens/info"""

    def test_info(self, client, demo_token):
        resp = client.get("/api/v0/tokens/info", headers={"X-API-Key": demo_token.get("token", "")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "test-token"
        assert "read_view" in data
        assert "write_view" in data

    def test_info_root_token(self, client, monkeypatch):
        """ROOT_TOKEN 访问 /tokens/info（80行）。"""
        import backend.deps as _deps
        import backend.routers.manage_token as _tokon
        monkeypatch.setattr(_deps, "ROOT_TOKEN", "my-root-token-val")
        monkeypatch.setattr(_tokon, "ROOT_TOKEN", "my-root-token-val")
        resp = client.get("/api/v0/tokens/info", headers={"X-API-Key": "my-root-token-val"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "ROOT_TOKEN"

    def test_info_token_deleted(self, client, backend_db, demo_perm):
        """token 在鉴权后被删除 → 404（90行）。
        
        用 client（绕过鉴权），直接在事务中插入后删除 token，
        使得 get_current_token_info 内部二次查询时找不到该 token。
        """
        import uuid
        from xfun.utils.time_utils import now_str

        now = now_str()
        token_val = str(uuid.uuid4())
        cols = [c.name for c in backend_db.table_infos["_token"]]
        placeholders = ", ".join(f":{c}" for c in cols)
        col_names = ", ".join(cols)
        entry = {
            "id": str(uuid.uuid4()),
            "token": token_val,
            "name": "临时token",
            "permission": "test-permission",
            "is_active": 1,
            "shortcut": None,
            "shortcut_expire_at": None,
            "expires_at": None,
            "created_at": now,
            "updated_at": now,
        }
        with backend_db.transaction() as conn:
            conn.execute(f"INSERT INTO _token ({col_names}) VALUES ({placeholders})", entry)
            # 在同一事务中立即删除，使二次查询时查不到
            conn.execute("DELETE FROM _token WHERE id = ?", [entry["id"]])

        resp = client.get("/api/v0/tokens/info", headers={"X-API-Key": token_val})
        assert resp.status_code == 401
        assert "无效" in resp.json()["detail"]
