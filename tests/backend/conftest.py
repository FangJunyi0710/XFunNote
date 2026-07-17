"""
Backend 测试共享夹具。

策略：
- 使用 FastAPI TestClient + dependency_overrides 注入 root 权限绕过鉴权
- DB 用临时文件隔离，与 tests/conftest.py 的 db 夹具独立
- 自动初始化系统表（_token、_permission、_view、_filter）
"""

from __future__ import annotations

import os
import tempfile
from typing import Any

import pytest
from fastapi.testclient import TestClient

from xfun import db as _db
from xfun import registry
from xfun.core.db import DB
from xfun.core.view import root_permission
from backend.permissions import ApiPermission
from backend.deps import get_api_permission
from backend.main import app
from backend.routers import manage_db as _manage_db

import xfun as _xfun_module
from xfun.core import ops as _ops
from xfun.core.filter import Condition


# ---- 系统表初始化 ----

_SYSTEM_TABLE_COLS: dict[str, list[dict]] = {
    "_token": [
        {"name": "id", "col_type": "TEXT", "nullable": False, "primary_key": True, "auto": True},
        {"name": "token", "col_type": "TEXT", "nullable": False, "unique": True, "auto": True},
        {"name": "name", "col_type": "TEXT", "nullable": False},
        {"name": "permission", "col_type": "TEXT", "nullable": False},
        {"name": "is_active", "col_type": "INTEGER", "nullable": False, "auto": True},
        {"name": "shortcut", "col_type": "TEXT", "nullable": True, "unique": True},
        {"name": "shortcut_expire_at", "col_type": "TEXT", "nullable": True},
        {"name": "expires_at", "col_type": "TEXT", "nullable": True},
        {"name": "created_at", "col_type": "TEXT", "nullable": False, "auto": True},
        {"name": "updated_at", "col_type": "TEXT", "nullable": False, "auto": True},
    ],
    "_permission": [
        {"name": "id", "col_type": "TEXT", "nullable": False, "primary_key": True, "auto": True},
        {"name": "name", "col_type": "TEXT", "nullable": False, "unique": True},
        {"name": "description", "col_type": "TEXT", "nullable": True},
        {"name": "read_view", "col_type": "TEXT", "nullable": False},
        {"name": "write_view", "col_type": "TEXT", "nullable": False},
        {"name": "created_at", "col_type": "TEXT", "nullable": False, "auto": True},
        {"name": "updated_at", "col_type": "TEXT", "nullable": False, "auto": True},
    ],
    "_view": [
        {"name": "id", "col_type": "TEXT", "nullable": False, "primary_key": True, "auto": True},
        {"name": "name", "col_type": "TEXT", "nullable": False, "unique": True},
        {"name": "data", "col_type": "TEXT", "nullable": False},
        {"name": "created_at", "col_type": "TEXT", "nullable": False, "auto": True},
        {"name": "updated_at", "col_type": "TEXT", "nullable": False, "auto": True},
    ],
    "_filter": [
        {"name": "id", "col_type": "TEXT", "nullable": False, "primary_key": True, "auto": True},
        {"name": "name", "col_type": "TEXT", "nullable": False, "unique": True},
        {"name": "data", "col_type": "TEXT", "nullable": False},
        {"name": "created_at", "col_type": "TEXT", "nullable": False, "auto": True},
        {"name": "updated_at", "col_type": "TEXT", "nullable": False, "auto": True},
    ],
}


@pytest.fixture(scope="session")
def backend_db():
    """session 级临时 DB，初始化所有 notebook 表 + 系统表。"""
    tmpf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmpf.close()
    _db_instance = DB(tmpf.name)

    # 注册 notebook 钩子
    for name, nb in registry.items():
        _db_instance.register_hooks(
            name,
            pre_add=nb._pre_add,
            validate=nb._validate,
            autofill=nb._autofill,
        )

    # 注册系统表钩子
    def _autofill_token(entry: dict) -> None:
        from xfun.utils.token_utils import generate_token
        entry.setdefault("token", generate_token())
        entry.setdefault("is_active", 1)

    _db_instance.register_hooks("_token", autofill=_autofill_token)

    # 初始化 notebook 表
    _db_instance.init({name: nb.columns for name, nb in registry.items()})
    # 初始化系统表
    from xfun.core.db import Column
    system_tables: dict[str, list[Column]] = {}
    for tbl_name, col_dicts in _SYSTEM_TABLE_COLS.items():
        system_tables[tbl_name] = [Column(**c) for c in col_dicts]
    _db_instance.init(system_tables)

    yield _db_instance

    os.unlink(tmpf.name)


@pytest.fixture(autouse=True)
def _clean_tables(backend_db):
    """自动清理所有表数据（函数级隔离），使用 backend_db.transaction() 确保 WAL 可见性。"""
    with backend_db.transaction() as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        existing = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        to_delete = [t for t in list(backend_db.table_infos) if t in existing]
        for table in to_delete:
            conn.execute(f"DELETE FROM {table}")
        # 验证删除效果
        for table in to_delete:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            assert cnt == 0, f"[_clean_tables] FAIL: {table} still has {cnt} rows after DELETE"
    yield


@pytest.fixture
def root_perm(backend_db) -> ApiPermission:
    """root 权限对象。"""
    return ApiPermission(root_permission(backend_db))


@pytest.fixture
def client(backend_db) -> TestClient:
    """FastAPI TestClient，注入 root 权限绕过鉴权。"""
    _setup_test_db(backend_db)
    app.dependency_overrides[get_api_permission] = lambda: ApiPermission(
        root_permission(backend_db)
    )

    # 设置 manage_db 路由的 ROOT_TOKEN，使 require_root_token 通过
    _manage_db.ROOT_TOKEN = "test-root-token"

    yield TestClient(app)
    app.dependency_overrides.clear()
    _manage_db.ROOT_TOKEN = ""


def _setup_test_db(backend_db):
    """替换模块级 db 为测试实例。"""
    _xfun_module.db = backend_db
    import sys
    for mod_name, mod in list(sys.modules.items()):
        if mod_name.startswith(('backend.', 'xfun.')):
            for attr in ('db', '_db'):
                if hasattr(mod, attr) and hasattr(getattr(mod, attr), 'db_path'):
                    setattr(mod, attr, backend_db)


@pytest.fixture
def real_auth_client(backend_db) -> TestClient:
    """FastAPI TestClient，不覆盖 get_api_permission，使用真实鉴权。"""
    _setup_test_db(backend_db)
    _manage_db.ROOT_TOKEN = "test-root-token"
    yield TestClient(app)
    _manage_db.ROOT_TOKEN = ""


@pytest.fixture
def demo_perm(backend_db) -> dict:
    """创建一个预置权限，返回完整行。"""
    from xfun.core.view import full_view, view_to_json
    from xfun.core.db import Column
    from xfun.utils.time_utils import now_str

    read_view = full_view(backend_db)
    write_view = full_view(backend_db)

    import json
    now = now_str()
    entry = {
        "id": "test-permission",
        "name": "测试权限",
        "description": "测试用",
        "read_view": json.dumps(view_to_json(read_view), ensure_ascii=False),
        "write_view": json.dumps(view_to_json(write_view), ensure_ascii=False),
        "created_at": now,
        "updated_at": now,
    }
    with backend_db.transaction() as conn:
        conn.execute(
            "INSERT INTO _permission (id, name, description, read_view, write_view, created_at, updated_at) "
            "VALUES (:id, :name, :description, :read_view, :write_view, :created_at, :updated_at)",
            entry,
        )

    return entry


@pytest.fixture
def demo_token(backend_db, demo_perm) -> dict:
    """创建一个预置 Token，返回完整行（含明文 token）。"""
    perm = root_permission(backend_db)
    entry = {
        "name": "test-token",
        "permission": "test-permission",
    }
    with backend_db.transaction() as conn:
        ids = conn.db.add_entries(conn, "_token", [entry])
        # 查询完整的行
        from xfun.core.db import Column
        cols = [c.name for c in backend_db.table_infos["_token"]]
        results = _ops.query(
            conn, perm, "_token",
            {"_token": [(cols, Condition("id", ids[0], "="))]},
            limit=1,
        )
    return dict(results[0]) if results else {}


@pytest.fixture
def demo_view(backend_db) -> dict:
    """创建一个预置视图（包含 id 字段）。"""
    perm = root_permission(backend_db)
    import json
    data = json.dumps({"plan": [{"columns": ["content"], "filter": []}]}, ensure_ascii=False)
    entry = {"id": "test-view", "name": "test-view", "data": data}
    with backend_db.transaction() as conn:
        ids = conn.db.add_entries(conn, "_view", [entry])
        from xfun.core.db import Column
        cols = [c.name for c in backend_db.table_infos["_view"]]
        results = _ops.query(
            conn, perm, "_view",
            {"_view": [(cols, Condition("id", ids[0], "="))]},
            limit=1,
        )
    return dict(results[0]) if results else {}


@pytest.fixture
def demo_filter(backend_db) -> dict:
    """创建一个预置筛选条件（包含 id 字段）。"""
    perm = root_permission(backend_db)
    import json
    data = json.dumps({"conditions": []}, ensure_ascii=False)
    entry = {"id": "test-filter", "name": "test-filter", "data": data}
    with backend_db.transaction() as conn:
        ids = conn.db.add_entries(conn, "_filter", [entry])
        from xfun.core.db import Column
        cols = [c.name for c in backend_db.table_infos["_filter"]]
        results = _ops.query(
            conn, perm, "_filter",
            {"_filter": [(cols, Condition("id", ids[0], "="))]},
            limit=1,
        )
    return dict(results[0]) if results else {}
