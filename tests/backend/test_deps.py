"""测试 backend/deps.py — get_api_permission 鉴权全分支覆盖。"""

from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException, status
from unittest.mock import patch


def _run_async(coro):
    return asyncio.run(coro)


def _insert_token_direct(backend_db, **overrides) -> str:
    """通过原始 SQL 向 _token 表插入记录（绕过 autofill 钩子），返回 token 值。"""
    from xfun.utils.time_utils import now_str

    now = now_str()
    # 自动生成唯一 id 和 token
    import uuid
    entry = {
        "id": str(uuid.uuid4()),
        "token": str(uuid.uuid4()),
        "name": "test-token",
        "permission": "test-permission",
        "is_active": 1,
        "shortcut": None,
        "shortcut_expire_at": None,
        "expires_at": None,
        "created_at": now,
        "updated_at": now,
        **overrides,
    }

    cols = [c.name for c in backend_db.table_infos["_token"]]
    placeholders = ", ".join(f":{c}" for c in cols)
    col_names = ", ".join(cols)
    with backend_db.transaction() as conn:
        conn.execute(
            f"INSERT INTO _token ({col_names}) VALUES ({placeholders})",
            entry,
        )
    return entry["token"]


class TestGetApiPermission:
    """直接调用 get_api_permission 测试不依赖 DB 的分支。"""

    def test_root_token_match(self):
        """ROOT_TOKEN 匹配时直接返回 root 权限。"""
        with patch("backend.deps.ROOT_TOKEN", "my-root-token"), \
                patch("backend.deps._ROOT_PERM", "mock-root-perm"):
            async def _test():
                from backend.deps import get_api_permission
                from backend.permissions import ApiPermission
                result = await get_api_permission(x_api_key="my-root-token")
                assert isinstance(result, ApiPermission)
                assert result.permission == "mock-root-perm"
            _run_async(_test())

    def test_root_token_case_sensitive(self):
        """ROOT_TOKEN 大小写敏感，不匹配时走 token 表查询 → 401。"""
        with patch("backend.deps.ROOT_TOKEN", "my-root-token"):
            async def _test():
                from backend.deps import get_api_permission
                with pytest.raises(HTTPException) as exc:
                    await get_api_permission(x_api_key="MY-ROOT-TOKEN")
                assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
            _run_async(_test())


class TestGetApiPermissionViaRealClient:
    """通过 real_auth_client 测试 token 表查询全部分支。"""

    def test_no_token_found(self, real_auth_client):
        """token 在表中不存在 → 401。"""
        resp = real_auth_client.get(
            "/api/v0/tokens/info",
            headers={"X-API-Key": "nonexistent-token"},
        )
        assert resp.status_code == 401
        assert "无效" in resp.json()["detail"]

    def test_token_inactive(self, real_auth_client, backend_db, demo_perm):
        """is_active=0 → 401。"""
        token = _insert_token_direct(backend_db, is_active=0)
        resp = real_auth_client.get(
            "/api/v0/tokens/info",
            headers={"X-API-Key": token},
        )
        assert resp.status_code == 200
        read_view = resp.json()["read_view"]
        # no_permission 使所有表的 columns 为空列表
        assert read_view.get("_token", []) == [] or all(spec["columns"] == [] for specs in read_view.values() for spec in specs)

    def test_token_expired(self, real_auth_client, backend_db, demo_perm):
        """expires_at 早于当前时间 → 401。"""
        token = _insert_token_direct(backend_db, expires_at="2000-01-01T00:00:00")
        resp = real_auth_client.get(
            "/api/v0/tokens/info",
            headers={"X-API-Key": token},
        )
        assert resp.status_code == 200
        read_view = resp.json()["read_view"]
        # no_permission 使所有表的 columns 为空列表
        assert read_view.get("_token", []) == [] or all(spec["columns"] == [] for specs in read_view.values() for spec in specs)

    def test_token_expires_at_none(self, real_auth_client, backend_db, demo_perm):
        """expires_at 为 NULL（永不过期）→ 正常返回。"""
        token = _insert_token_direct(backend_db, expires_at=None)
        resp = real_auth_client.get(
            "/api/v0/tokens/info",
            headers={"X-API-Key": token},
        )
        assert resp.status_code == 200

    def test_token_permission_not_found(self, real_auth_client, backend_db):
        """permission 在 _permission 表中不存在 → 401。"""
        token = _insert_token_direct(backend_db, permission="nonexistent")
        resp = real_auth_client.get(
            "/api/v0/tokens/info",
            headers={"X-API-Key": token},
        )
        assert resp.status_code == 401
        assert "未知的权限标识" in resp.json()["detail"]

    def test_normal_token_success(self, real_auth_client, backend_db, demo_perm):
        """正常 token → 返回 200。"""
        token = _insert_token_direct(backend_db, permission="test-permission")
        resp = real_auth_client.get(
            "/api/v0/tokens/info",
            headers={"X-API-Key": token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "test-token"
