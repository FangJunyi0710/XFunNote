# xfun/notebooks/plan.py — 计划本
"""
plan 本：以月份为分组，管理待办事项 / 目标条目。

"""

from typing import Any, Dict, List, Optional

from future_uuid import uuid7

from ..core.db import Column, Filter
from ..core.notebook import Notebook

class PlanNotebook(Notebook):
    name = "plan"
    _extra_columns = [
        Column("no",    "INTEGER", nullable=False, auto=True),
        Column("month", "TEXT",    nullable=False, index=True),
        Column("done",  "INTEGER", nullable=False, auto=True),
    ]

    # ---- CRUD ----

    def add(self, conn, entries: List[Dict[str, Any]]) -> List[str]:
        for entry in entries:
            self._validate(entry)
            self._autofill(entry, conn)
        conn.executemany(self._insert_sql(), entries)
        return [entry["id"] for entry in entries]

    def list(self, conn, filters: List[Filter], *,
             order_by: Optional[str] = None,
             limit: int = 50,
             offset: int = 0) -> List[Dict[str, Any]]:
        
        where_clauses = []
        params: Dict[str, Any] = {}
        for i, f in enumerate(filters):
            key = f"v_{i}"
            where_clauses.append(f"{f.column} {f.op} :{key}")
            params[key] = f.value

        sql = "SELECT * FROM plan WHERE " + " AND ".join(where_clauses)
        if order_by:
            sql += f" ORDER BY {order_by}"
        sql += " LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset

        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def delete(self, conn, entry_id: str) -> bool:
        cur = conn.execute("DELETE FROM plan WHERE id = :id", {"id": entry_id})
        return cur.rowcount > 0

    # ---- 校验 & 自动填充 ----

    def _autofill(self, entry: Dict[str, Any], conn) -> None:
        """自动填充 id（uuid7）/ no / done / created_at。"""
        super()._autofill(entry, conn)
        entry["id"] = f"plan-{entry["month"]}-{str(uuid7())}"
        entry["no"] = 0       # TODO: 后续完善排序逻辑
        entry.setdefault("done", 0)
