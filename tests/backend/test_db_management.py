"""测试数据库管理路由。"""

from __future__ import annotations

import pytest
from unittest.mock import patch


class TestDBManagementAuth:
    """数据库管理路由使用 require_root_token，测试 403 拒绝。"""

    def test_init_without_root(self, client):
        """发送错误的 API Key 测试 403。"""
        with patch("backend.services.management_service.init_database") as mock_init:
            mock_init.return_value = "fake"
            resp = client.post("/api/v0/db/init", headers={"X-API-Key": "invalid"})
        assert resp.status_code == 403


class TestDBInit:
    """POST /api/v0/db/init"""

    def test_init(self, client):
        with patch("backend.services.management_service.init_database") as mock_init:
            mock_init.return_value = "fake"
            resp = client.post("/api/v0/db/init", headers={"X-API-Key": "test-root-token"})
        assert resp.status_code == 200
        assert "fake" in resp.json()["message"]


class TestDBBackup:
    """POST /api/v0/db/backup"""

    def test_backup(self, client):
        resp = client.post("/api/v0/db/backup", headers={"X-API-Key": "test-root-token"})
        assert resp.status_code == 200
        assert "备份完成" in resp.json()["message"]


class TestDBReset:
    """POST /api/v0/db/reset"""

    def test_reset(self, client):
        resp = client.post(
            "/api/v0/db/reset",
            json={"backup_first": False},
            headers={"X-API-Key": "test-root-token"},
        )
        assert resp.status_code == 200
        assert "已重置" in resp.json()["message"]

    def test_reset_with_backup(self, client):
        resp = client.post(
            "/api/v0/db/reset",
            json={"backup_first": True},
            headers={"X-API-Key": "test-root-token"},
        )
        assert resp.status_code == 200


class TestDBRestore:
    """POST /api/v0/db/restore"""

    def test_restore_nonexistent(self, client):
        resp = client.post(
            "/api/v0/db/restore",
            json={"backup_path": "/nonexistent/backup.db"},
            headers={"X-API-Key": "test-root-token"},
        )
        # FileNotFoundError -> 应该被转换为 HTTP 404
        assert resp.status_code == 404

    def test_restore_valid(self, client):
        # 先备份获取有效路径
        backup_resp = client.post("/api/v0/db/backup", headers={"X-API-Key": "test-root-token"})
        assert backup_resp.status_code == 200
        backup_path = backup_resp.json()["message"].replace("备份完成: ", "")

        resp = client.post(
            "/api/v0/db/restore",
            json={"backup_path": backup_path},
            headers={"X-API-Key": "test-root-token"},
        )
        assert resp.status_code == 200
        assert "已从备份恢复" in resp.json()["message"]


class TestDBListBackups:
    """GET /api/v0/db/backups"""

    def test_list_backups(self, client):
        # 先创建一个备份
        client.post("/api/v0/db/backup", headers={"X-API-Key": "test-root-token"})

        resp = client.get("/api/v0/db/backups", headers={"X-API-Key": "test-root-token"})
        assert resp.status_code == 200
        data = resp.json()
        assert "backups" in data
        assert len(data["backups"]) >= 1
