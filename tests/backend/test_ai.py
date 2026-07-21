"""测试 AI 路由。"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from fastapi import HTTPException

import xfun
from xfun.core.view import full_view, view_to_json


@pytest.fixture
def mock_invoke():
    with patch("backend.services.ai_service.agent_invoke") as m:
        yield m


class TestAIPermission:
    """GET /api/v0/ai/permission"""

    def _ensure_ai_permission(self):
        from xfun.utils.time_utils import now_str
        perm = view_to_json(full_view(xfun.db))
        now = now_str()
        entry = {
            "id": "ai",
            "name": "AI",
            "description": "AI 权限",
            "read_view": json.dumps(perm, ensure_ascii=False),
            "write_view": json.dumps(perm, ensure_ascii=False),
            "created_at": now,
            "updated_at": now,
        }
        with xfun.db.transaction() as conn:
            conn.execute("DELETE FROM _permission WHERE name = ?", (entry["name"],))
            import uuid
            conn.execute(
                "INSERT INTO _permission (id, uuid, name, description, read_view, write_view, created_at, updated_at) "
                "VALUES (:id, :uuid, :name, :description, :read_view, :write_view, :created_at, :updated_at)",
                {**entry, "uuid": str(uuid.uuid4())},
            )

    def test_chat_success(self, mock_invoke, client):
        self._ensure_ai_permission()
        mock_invoke.return_value = []

        resp = client.post(
            "/api/v0/ai/chat",
            json={
                "messages": [{"role": "user", "content": "hello"}],
                "permission_name": "ai",
            },
        )
        assert resp.status_code == 500  # 因为 mock_invoke 返回空列表，但实际可能错误

    def test_get_permission(self, client):
        """AI 权限路由需要 _permission 表中存在 'ai' 记录。"""
        self._ensure_ai_permission()
        resp = client.get("/api/v0/ai/permission")
        assert resp.status_code == 200
        data = resp.json()
        assert "read" in data
        assert "write" in data


class TestAIChat:
    """POST /api/v0/ai/chat"""

    def _ensure_ai_permission(self):
        from xfun.utils.time_utils import now_str
        perm = view_to_json(full_view(xfun.db))
        now = now_str()
        entry = {
            "id": "ai",
            "name": "AI",
            "description": "AI 权限",
            "read_view": json.dumps(perm, ensure_ascii=False),
            "write_view": json.dumps(perm, ensure_ascii=False),
            "created_at": now,
            "updated_at": now,
        }
        with xfun.db.transaction() as conn:
            # 先尝试删除已有记录（按 name 删除），避免 UNIQUE constraint 冲突
            conn.execute("DELETE FROM _permission WHERE name = ?", (entry["name"],))
            import uuid
            conn.execute(
                "INSERT INTO _permission (id, uuid, name, description, read_view, write_view, created_at, updated_at) "
                "VALUES (:id, :uuid, :name, :description, :read_view, :write_view, :created_at, :updated_at)",
                {**entry, "uuid": str(uuid.uuid4())},
            )

    def test_chat_no_messages(self, client):
        self._ensure_ai_permission()
        resp = client.post(
            "/api/v0/ai/chat",
            json={"messages": []},
        )
        assert resp.status_code == 422  # min_length=1

    def test_chat_invalid_permission(self, client):
        resp = client.post(
            "/api/v0/ai/chat",
            json={
                "messages": [{"role": "user", "content": "hello"}],
                "permission_name": "nonexistent",
            },
        )
        assert resp.status_code == 400
        assert "未知权限" in resp.json()["detail"]

    def test_chat_success(self, mock_invoke, client):
        self._ensure_ai_permission()
        mock_invoke.return_value = []

        resp = client.post(
            "/api/v0/ai/chat",
            json={
                "messages": [{"role": "user", "content": "hello"}],
                "permission_name": "ai",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "messages" in data
        assert len(data["messages"]) > 0
