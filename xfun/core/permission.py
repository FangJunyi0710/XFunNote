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
            db.insert_sql("_permissions"),
            {
                "id": permission_id,
                "name": name,
                "description": description,
                "read_view": json.dumps(read_view, ensure_ascii=False),
                "write_view": json.dumps(write_view, ensure_ascii=False),
                "can_query": 1 if can_query else 0,
                "can_add": 1 if can_add else 0,
                "can_update": 1 if can_update else 0,
                "can_delete": 1 if can_delete else 0,
                "can_ai_chat": 1 if can_ai_chat else 0,
                "can_manage_db": 1 if can_manage_db else 0,
                "can_manage_views": 1 if can_manage_views else 0,
                "can_manage_tokens": 1 if can_manage_tokens else 0,
                "created_at": now,
                "updated_at": now,
            },
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
    updates: dict = {}
    now = now_str()

    if name is not None:
        updates["name"] = name
    if description is not None:
        updates["description"] = description
    if read_view is not None:
        updates["read_view"] = json.dumps(read_view, ensure_ascii=False)
    if write_view is not None:
        updates["write_view"] = json.dumps(write_view, ensure_ascii=False)
    for field in ("can_query", "can_add", "can_update", "can_delete",
                  "can_ai_chat", "can_manage_db", "can_manage_views", "can_manage_tokens"):
        val = locals()[field]
        if val is not None:
            updates[field] = 1 if val else 0

    if not updates:
        return get_permission(permission_id)

    updates["updated_at"] = now
    updates["id"] = permission_id

    with db.transaction() as conn:
        conn.execute(
            db.update_sql("_permissions", updates) + " WHERE id = :id",
            updates,
        )
    return get_permission(permission_id)


def delete_permission(permission_id: str) -> bool:
    """删除权限定义。"""
    with db.transaction() as conn:
        cursor = conn.execute(
            "DELETE FROM _permissions WHERE id = ?", (permission_id,)
        )
    return cursor.rowcount > 0
