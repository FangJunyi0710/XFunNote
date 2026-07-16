"""测试 AI 路由。"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

import xfun
from xfun.core.view import full_view, view_to_json


class TestAIPermission:
    """GET /api/v1/ai/permission"""

    def test_get_permission(self, client):
        """AI 权限路由需要 _permission 表中存在 'ai' 记录。"""
        from xfun.utils.time_utils import now_str
        # 创建 ai 权限（使用 raw SQL INSERT 手动指定 id）
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
            conn.execute("DELETE FROM _permission WHERE id = ?", (entry["id"],))
            conn.execute(
                "INSERT INTO _permission (id, name, description, read_view, write_view, created_at, updated_at) "
                "VALUES (:id, :name, :description, :read_view, :write_view, :created_at, :updated_at)",
                entry,
            )

        resp = client.get("/api/v1/ai/permission")
        assert resp.status_code == 200
        data = resp.json()
        assert "read" in data
        assert "write" in data


class TestAIChat:
    """POST /api/v1/ai/chat"""

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
            # 先尝试删除已有记录（按 name 删除，因为 UNIQUE 约束在 name 列），避免 UNIQUE constraint 冲突
            conn.execute("DELETE FROM _permission WHERE name = ?", (entry["name"],))
            conn.execute(
                "INSERT INTO _permission (id, name, description, read_view, write_view, created_at, updated_at) "
                "VALUES (:id, :name, :description, :read_view, :write_view, :created_at, :updated_at)",
                entry,
            )

    def test_chat_no_messages(self, client):
        self._ensure_ai_permission()
        resp = client.post(
            "/api/v1/ai/chat",
            json={"messages": []},
        )
        assert resp.status_code == 422  # min_length=1

    def test_chat_invalid_permission(self, client):
        resp = client.post(
            "/api/v1/ai/chat",
            json={
                "messages": [{"role": "user", "content": "hello"}],
                "permission_name": "nonexistent",
            },
        )
        assert resp.status_code == 400
        assert "未知权限" in resp.json()["detail"]

    @patch("backend.services.ai_service.agent_invoke")
    def test_chat_success(self, mock_invoke, client):
        self._ensure_ai_permission()
        mock_invoke.return_value = []

        resp = client.post(
            "/api/v1/ai/chat",
            json={
                "messages": [{"role": "user", "content": "hello"}],
                "permission_name": "ai",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "messages" in data
        assert len(data["messages"]) > 0
