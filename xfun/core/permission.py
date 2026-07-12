"""权限管理业务逻辑（基于数据库 _permissions 表）。"""

import json

from .. import db
from ..utils.time_utils import now_str


def _permission_exists(permission_id: str) -> bool:
    """检查 _permissions 表中是否存在指定 id。"""
    with db.read_transaction() as conn:
        return conn.execute(
            "SELECT 1 FROM _permissions WHERE id = ?", (permission_id,)
        ).fetchone() is not None


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
