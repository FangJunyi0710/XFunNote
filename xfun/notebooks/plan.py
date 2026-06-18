# xfun/notebooks/plan.py — 计划本
"""
plan 本：以月份为分组，管理待办事项 / 目标条目。

"""

from typing import Any, Dict, List, Optional

from ..core.db import Column, Filter
from ..core.notebook import Notebook


class PlanNotebook(Notebook):
    name = "plan"
    _extra_columns = [
        Column("no",    "INTEGER", nullable=False),
        Column("month", "TEXT",    nullable=False, index=True),
        Column("done",  "INTEGER", default=0),
    ]

    # 追加自动填充字段（自动合并到基类的 _auto_fields）
    _auto_fields = {"no", "done"}

    # ---- CRUD ----

    def add(self, conn, entry: Dict[str, Any]) -> str:
        self._validate(entry)
        self._autofill(entry, conn)
        conn.execute(self._insert_sql(), entry)
        return entry["id"]

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

    def search(self, conn, query: str, *, limit: int = 50) -> List[Dict[str, Any]]:
        return self.list(
            conn,
            [Filter("content", f"%{query}%", op="LIKE")],
            limit=limit,
        )

    # ---- 校验 & 自动填充 ----

    def _autofill(self, entry: Dict[str, Any], conn) -> None:
        """自动填充 id / no / done / created_at。"""
        super()._autofill(entry, conn)
        month = entry["month"]
        no = self._next_no(month, conn)
        entry["no"] = no
        entry["id"] = f"plan-{month}-{no:03d}"
        entry.setdefault("done", 0)

    def _next_no(self, month: str, conn) -> int:
        """返回指定月份的下一个编号。"""
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM plan WHERE month = :month",
            {"month": month},
        ).fetchone()
        return row["cnt"] + 1

    # ---- 摘要 ----

    def summary(self, conn) -> str:
        """供 AI 使用的计划概览。"""
        rows = conn.execute(
            "SELECT month, COUNT(*) AS total, SUM(done) AS done_cnt "
            "FROM plan GROUP BY month ORDER BY month DESC"
        ).fetchall()
        if not rows:
            return "[plan] 暂无计划"

        lines = ["[plan]"]
        for r in rows:
            lines.append(f"  {r['month']}: {r['done_cnt']}/{r['total']} 已完成")
        return "\n".join(lines)
