"""视图管理业务逻辑（基于数据库 _views 表）。"""

import json

from xfun import db
from xfun.utils.time_utils import now_str


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
