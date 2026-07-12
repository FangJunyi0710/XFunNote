"""API Token 管理业务逻辑。"""

from __future__ import annotations

import secrets
import uuid

from xfun import db
from xfun.permission_service import _permission_exists
from xfun.utils.time_utils import now_str


def list_tokens() -> list[dict]:
    """列出所有 API Token（不暴露完整 token 值）。"""
    with db.read_transaction() as conn:
        rows = conn.execute(
            "SELECT id, name, permission, is_active, expires_at, created_at, updated_at "
            "FROM _tokens ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


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
            "INSERT INTO _tokens (id, token, name, permission, is_active, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 1, ?, ?)",
            (token_id, token_value, name, permission, now, now),
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
    now = now_str()
    updates: list[str] = []
    params: list = []

    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if permission is not None:
        if not _permission_exists(permission):
            raise ValueError(f"不存在的权限标识: {permission!r}")
        updates.append("permission = ?")
        params.append(permission)
    if is_active is not None:
        updates.append("is_active = ?")
        params.append(1 if is_active else 0)
    if expires_at is not None:
        updates.append("expires_at = ?")
        params.append(expires_at)

    if not updates:
        return get_token(token_id)

    updates.append("updated_at = ?")
    params.append(now)
    params.append(token_id)

    with db.transaction() as conn:
        conn.execute(
            f"UPDATE _tokens SET {', '.join(updates)} WHERE id = ?",
            params,
        )

    return get_token(token_id)


def delete_token(token_id: str) -> bool:
    """删除 Token。"""
    with db.transaction() as conn:
        cursor = conn.execute("DELETE FROM _tokens WHERE id = ?", (token_id,))
    return cursor.rowcount > 0
