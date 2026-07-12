"""API Token 管理业务逻辑。"""

from __future__ import annotations

import secrets
import uuid

from .. import db
from .permission import _permission_exists
from ..utils.time_utils import now_str


def list_tokens() -> list[dict]:
    """列出所有 API Token（不暴露完整 token 值）。"""
    with db.read_transaction() as conn:
        rows = conn.execute(
            "SELECT id, name, permission, is_active, expires_at, created_at, updated_at "
            "FROM _tokens ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_token_by_value(token_value: str) -> dict | None:
    """按 token 值查询 Token 信息（含 permission, is_active, expires_at）。"""
    with db.read_transaction() as conn:
        row = conn.execute(
            "SELECT id, name, permission, is_active, expires_at, created_at, updated_at "
            "FROM _tokens WHERE token = ?",
            (token_value,),
        ).fetchone()
    return dict(row) if row else None


def get_token(token_id: str) -> dict | None:
    """获取单个 Token 信息。"""
    with db.read_transaction() as conn:
        row = conn.execute(
            "SELECT id, name, permission, is_active, expires_at, created_at, updated_at "
            "FROM _tokens WHERE id = ?",
            (token_id,),
        ).fetchone()
    return dict(row) if row else None


def create_token(name: str, permission: str) -> dict:
    """创建新 Token，返回包含完整 token 值的对象。

    Parameters
    ----------
    name : str
        Token 可读名称。
    permission : str
        权限标识，对应 _permissions 表中的 id。

    Returns
    -------
    dict
        包含 ``id``, ``token``（仅创建时返回）, ``name``, ``permission``, ``is_active``。
    """
    if not _permission_exists(permission):
        raise ValueError(f"不存在的权限标识: {permission!r}")

    token_value = "sk-" + secrets.token_urlsafe(32)
    now = now_str()
    token_id = str(uuid.uuid4())

    with db.transaction() as conn:
        conn.execute(
            db.insert_sql("_tokens"),
            {
                "id": token_id,
                "token": token_value,
                "name": name,
                "permission": permission,
                "is_active": 1,
                "expires_at": None,
                "created_at": now,
                "updated_at": now,
            },
        )

    return {
        "id": token_id,
        "token": token_value,  # 仅在创建时返回一次
        "name": name,
        "permission": permission,
        "is_active": True,
    }


def update_token(
    token_id: str,
    name: str | None = None,
    permission: str | None = None,
    is_active: bool | None = None,
    expires_at: str | None = None,
) -> dict | None:
    """更新 Token 属性。返回更新后的 Token 信息，不存在返回 None。"""
    updates: dict = {}
    now = now_str()

    if name is not None:
        updates["name"] = name
    if permission is not None:
        if not _permission_exists(permission):
            raise ValueError(f"不存在的权限标识: {permission!r}")
        updates["permission"] = permission
    if is_active is not None:
        updates["is_active"] = 1 if is_active else 0
    if expires_at is not None:
        updates["expires_at"] = expires_at

    if not updates:
        return get_token(token_id)

    updates["updated_at"] = now
    updates["id"] = token_id

    with db.transaction() as conn:
        conn.execute(
            db.update_sql("_tokens", updates) + " WHERE id = :id",
            updates,
        )

    return get_token(token_id)


def delete_token(token_id: str) -> bool:
    """删除 Token。"""
    with db.transaction() as conn:
        cursor = conn.execute("DELETE FROM _tokens WHERE id = ?", (token_id,))
    return cursor.rowcount > 0
