"""Backend 测试共享夹具 — 适配当前 API。"""
from __future__ import annotations
import os
import tempfile
import uuid
import json
import pytest
from fastapi.testclient import TestClient
from xfun import registry
from xfun.core.db import DB, Column
from xfun.core.view import root_permission, full_view, view_to_json
from xfun.core import ops
from xfun.core.filter import Condition
from backend.deps import get_api_permission, ApiPermission
from backend.main import app
from backend.routers import manage_db as _manage_db
import xfun as _xfun_module
import xfun

# 系统表定义（适配当前列）
_SYSTEM_COLS = {
    "_token": [
        Column("id", "TEXT", primary_key=True, nullable=False, auto=True),
        Column("token", "TEXT", nullable=False, unique=True),
        Column("name", "TEXT", nullable=False),
        Column("permission", "TEXT", nullable=False),
        Column("is_active", "INTEGER", nullable=False),
        Column("shortcut", "TEXT", nullable=True, unique=True),
        Column("shortcut_expire_at", "TEXT", nullable=True),
        Column("expires_at", "TEXT", nullable=True),
        Column("created_at", "TEXT", nullable=False),
        Column("updated_at", "TEXT", nullable=False),
    ],
    "_permission": [
        Column("id", "TEXT", primary_key=True, nullable=False, auto=True),
        Column("uuid", "TEXT", unique=True, nullable=False, auto=True),
        Column("name", "TEXT", nullable=False, unique=True),
        Column("description", "TEXT", nullable=True),
        Column("read_view", "TEXT", nullable=False),
        Column("write_view", "TEXT", nullable=False),
        Column("created_at", "TEXT", nullable=False, auto=True),
        Column("updated_at", "TEXT", nullable=False, auto=True),
    ],
    "_view": [
        Column("id", "TEXT", primary_key=True, nullable=False, auto=True),
        Column("name", "TEXT", nullable=False, unique=True),
        Column("data", "TEXT", nullable=False),
        Column("created_at", "TEXT", nullable=False, auto=True),
        Column("updated_at", "TEXT", nullable=False, auto=True),
    ],
    "_filter": [
        Column("id", "TEXT", primary_key=True, nullable=False, auto=True),
        Column("name", "TEXT", nullable=False, unique=True),
        Column("data", "TEXT", nullable=False),
        Column("created_at", "TEXT", nullable=False, auto=True),
        Column("updated_at", "TEXT", nullable=False, auto=True),
    ],
}

def _autofill_token(entry):
    from xfun.utils.token_utils import generate_token
    entry.setdefault("token", generate_token())
    entry.setdefault("is_active", 1)

def _autofill_permission(entry):
    entry.setdefault("uuid", str(uuid.uuid4()))

@pytest.fixture(scope="session")
def backend_db():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db = DB(tmp.name)
    for name, nb in registry.items():
        db.register_hooks(name, pre_add=nb._pre_add, validate=nb._validate, autofill=nb._autofill)
    db.register_hooks("_token", autofill=_autofill_token)
    db.register_hooks("_permission", autofill=_autofill_permission)
    # 初始化 notebook 表
    db.table_infos.update({name: nb.columns for name, nb in registry.items()})
    db.init()
    # 初始化系统表
    db.table_infos.update(_SYSTEM_COLS)
    db.init()
    yield db
    os.unlink(tmp.name)

def _setup_db(db):
    """设置全局 db 引用。"""
    _xfun_module.db = db
    xfun.db = db
    import sys
    for mod_name, mod in list(sys.modules.items()):
        if mod_name.startswith(('backend.', 'xfun.')):
            for attr in ('db', '_db'):
                if hasattr(mod, attr) and hasattr(getattr(mod, attr), 'db_path'):
                    setattr(mod, attr, db)

@pytest.fixture(autouse=True)
def clean_tables(backend_db):
    with backend_db.transaction() as conn:
        existing = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in list(backend_db.table_infos):
            if table in existing:
                conn.execute(f"DELETE FROM {table}")
    yield

@pytest.fixture
def root_perm(backend_db):
    return ApiPermission("root", backend_db, root_permission(backend_db))

@pytest.fixture
def client(backend_db):
    _setup_db(backend_db)
    import xfun.config
    import backend.deps; backend.deps.ROOT_TOKEN = "test-root-token"
    xfun.config.ROOT_TOKEN = "test-root-token"
    _manage_db.ROOT_TOKEN = "test-root-token"
    app.dependency_overrides[get_api_permission] = lambda: ApiPermission("test-root-token", backend_db, root_permission(backend_db))
    yield TestClient(app)
    app.dependency_overrides.clear()
    xfun.config.ROOT_TOKEN = ""
    _manage_db.ROOT_TOKEN = ""

@pytest.fixture
def real_auth_client(backend_db):
    _setup_db(backend_db)
    import xfun.config
    import backend.deps; backend.deps.ROOT_TOKEN = "test-root-token"
    xfun.config.ROOT_TOKEN = "test-root-token"
    _manage_db.ROOT_TOKEN = "test-root-token"
    yield TestClient(app)
    xfun.config.ROOT_TOKEN = ""
    _manage_db.ROOT_TOKEN = ""

@pytest.fixture
def demo_perm(backend_db):
    now = _xfun_module.utils.time_utils.now_str()
    fv = json.dumps(view_to_json(full_view(backend_db)))
    entry = {
        "name": "测试权限",
        "description": "测试",
        "read_view": fv,
        "write_view": fv,
        "created_at": now,
        "updated_at": now,
    }
    with backend_db.transaction() as conn:
        ids = ops.add(conn, root_permission(backend_db), "_permission", [entry])
    with backend_db.read_transaction() as conn:
        cols = [c.name for c in backend_db.table_infos["_permission"]]
        rows = ops.query(conn, root_permission(backend_db), "_permission",
                         {"_permission": [(cols, Condition("id", ids[0]["id"], "="))]})
    return dict(rows[0]) if rows else {}

@pytest.fixture
def demo_token(backend_db, demo_perm):
    from xfun.utils.token_utils import generate_token
    entry = {"name": "test-token", "permission": demo_perm["name"], "token": generate_token()}
    with backend_db.transaction() as conn:
        ids = ops.add(conn, root_permission(backend_db), "_token", [entry])
    with backend_db.read_transaction() as conn:
        cols = [c.name for c in backend_db.table_infos["_token"]]
        rows = ops.query(conn, root_permission(backend_db), "_token",
                         {"_token": [(cols, Condition("id", ids[0]["id"], "="))]})
    return dict(rows[0]) if rows else {}

@pytest.fixture
def demo_view(backend_db):
    data = json.dumps({"plan": [{"columns": ["content"], "filter": []}]})
    entry = {"name": "test-view", "data": data}
    with backend_db.transaction() as conn:
        ids = ops.add(conn, root_permission(backend_db), "_view", [entry])
    with backend_db.read_transaction() as conn:
        cols = [c.name for c in backend_db.table_infos["_view"]]
        rows = ops.query(conn, root_permission(backend_db), "_view",
                         {"_view": [(cols, Condition("id", ids[0]["id"], "="))]})
    return dict(rows[0]) if rows else {}

@pytest.fixture
def demo_filter(backend_db):
    data = json.dumps({"conditions": []})
    entry = {"name": "test-filter", "data": data}
    with backend_db.transaction() as conn:
        ids = ops.add(conn, root_permission(backend_db), "_filter", [entry])
    with backend_db.read_transaction() as conn:
        cols = [c.name for c in backend_db.table_infos["_filter"]]
        rows = ops.query(conn, root_permission(backend_db), "_filter",
                         {"_filter": [(cols, Condition("id", ids[0]["id"], "="))]})
    return dict(rows[0]) if rows else {}
