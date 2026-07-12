"""数据库管理、视图管理和权限管理业务逻辑。"""

import json

from xfun import db, init_db
from xfun.utils.time_utils import now_str


def init_database() -> str:
    """初始化数据库：建表/补齐缺失列/建索引。"""
    with db.transaction() as conn:
        init_db(conn)
    return "数据库初始化完成"


def backup_database() -> str:
    """在线热备份数据库。"""
    with db.read_transaction() as conn:
        path = db.backup(conn)
    return f"备份完成: {path}"


def reset_database(backup_first: bool = True) -> str:
    """重置数据库：清空所有表并重新初始化。"""
    with db.read_transaction() as conn:
        if backup_first:
            db.backup(conn)
    with db.transaction() as conn:
        db.reset(conn)
    return "数据库已重置"


# ---- 视图管理（基于数据库 _views 表） ----

def list_views() -> list[dict]:
    """列出所有保存的视图。"""
    with db.read_transaction() as conn:
        rows = conn.execute(
            "SELECT name, created_at, updated_at FROM _views ORDER BY name ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_view(name: str) -> dict | None:
    """读取指定视图。"""
    with db.read_transaction() as conn:
        row = conn.execute(
            "SELECT data FROM _views WHERE name = ?", (name,)
        ).fetchone()
    if row is None:
        return None
    return json.loads(row["data"])


def save_view(name: str, data: dict) -> None:
    """保存/覆盖视图。"""
    now = now_str()
    with db.transaction() as conn:
        conn.execute(
            "INSERT INTO _views (name, data, created_at, updated_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(name) DO UPDATE SET data = ?, updated_at = ?",
            (name, json.dumps(data, ensure_ascii=False), now, now, json.dumps(data, ensure_ascii=False), now),
        )


def delete_view(name: str) -> bool:
    """删除视图。"""
    with db.transaction() as conn:
        cursor = conn.execute("DELETE FROM _views WHERE name = ?", (name,))
    return cursor.rowcount > 0


# ---- 权限管理（基于数据库 _permissions 表） ----

def list_permissions() -> list[dict]:
    """列出所有权限定义。"""
    with db.read_transaction() as conn:
        rows = conn.execute(
            "SELECT id, name, description, can_query, can_add, can_update, "
            "can_delete, can_ai_chat, can_manage_db, can_manage_views, "
            "can_manage_tokens, created_at, updated_at "
            "FROM _permissions ORDER BY id ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_permission(permission_id: str) -> dict | None:
    """获取单个权限定义（完整字段，含 View JSON）。"""
    with db.read_transaction() as conn:
        row = conn.execute(
            "SELECT * FROM _permissions WHERE id = ?", (permission_id,)
        ).fetchone()
    return dict(row) if row else None


def create_permission(permission_id: str, name: str, description: str | None,
                      read_view: dict, write_view: dict,
                      can_query: bool, can_add: bool, can_update: bool,
                      can_delete: bool, can_ai_chat: bool, can_manage_db: bool,
                      can_manage_views: bool, can_manage_tokens: bool) -> dict:
    """创建新的权限定义。"""
    now = now_str()
    with db.transaction() as conn:
        conn.execute(
            "INSERT INTO _permissions "
            "(id, name, description, read_view, write_view, "
            "can_query, can_add, can_update, can_delete, can_ai_chat, "
            "can_manage_db, can_manage_views, can_manage_tokens, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (permission_id, name, description,
             json.dumps(read_view, ensure_ascii=False),
             json.dumps(write_view, ensure_ascii=False),
             1 if can_query else 0,
             1 if can_add else 0,
             1 if can_update else 0,
             1 if can_delete else 0,
             1 if can_ai_chat else 0,
             1 if can_manage_db else 0,
             1 if can_manage_views else 0,
             1 if can_manage_tokens else 0,
             now, now),
        )
    return get_permission(permission_id)


def update_permission(permission_id: str,
                      name: str | None = None,
                      description: str | None = None,
                      read_view: dict | None = None,
                      write_view: dict | None = None,
                      can_query: bool | None = None,
                      can_add: bool | None = None,
                      can_update: bool | None = None,
                      can_delete: bool | None = None,
                      can_ai_chat: bool | None = None,
                      can_manage_db: bool | None = None,
                      can_manage_views: bool | None = None,
                      can_manage_tokens: bool | None = None) -> dict | None:
    """更新权限定义。"""
    now = now_str()
    updates: list[str] = []
    params: list = []

    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if read_view is not None:
        updates.append("read_view = ?")
        params.append(json.dumps(read_view, ensure_ascii=False))
    if write_view is not None:
        updates.append("write_view = ?")
        params.append(json.dumps(write_view, ensure_ascii=False))
    for field in ("can_query", "can_add", "can_update", "can_delete",
                  "can_ai_chat", "can_manage_db", "can_manage_views", "can_manage_tokens"):
        val = locals()[field]
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(1 if val else 0)

    if not updates:
        return get_permission(permission_id)

    updates.append("updated_at = ?")
    params.append(now)
    params.append(permission_id)

    with db.transaction() as conn:
        conn.execute(
            f"UPDATE _permissions SET {', '.join(updates)} WHERE id = ?",
            params,
        )
    return get_permission(permission_id)


def delete_permission(permission_id: str) -> bool:
    """删除权限定义。"""
    with db.transaction() as conn:
        cursor = conn.execute(
            "DELETE FROM _permissions WHERE id = ?", (permission_id,)
        )
    return cursor.rowcount > 0
