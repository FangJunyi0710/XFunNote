# xfun/notebooks/plan.py — 计划本
"""
plan 本：以月份为分组，管理待办事项 / 目标条目。

每条记录包含：
- id        : 主键，自动生成  plan-{month}-{no}
- no        : 月份内编号，自动递增
- month     : 所属月份，如 "2606"
- content   : 事项内容
- done      : 是否完成，默认 0
- created_at: 创建时间，自动填充
"""

from typing import Any, Dict, List, Optional

from ..core.db import Column, Filter
from ..core.notebook import Notebook
from ..core.errors import EntryInvalidError
from ..utils.time_utils import now_str


class PlanNotebook(Notebook):
    name    = "plan"
    columns = [
        Column("id",         "TEXT",    primary_key=True),
        Column("no",         "INTEGER", nullable=False),
        Column("month",      "TEXT",    nullable=False, index=True),
        Column("content",    "TEXT",    nullable=False),
        Column("done",       "INTEGER", default=0),
        Column("created_at", "TEXT",    nullable=False),
    ]

    # ---- 自动填充字段（用户不需要提供） ----
    _auto_fields = {"id", "no", "done", "created_at"}

    # ---- CRUD ----

    def add(self, entry: Dict[str, Any]) -> str:
        # 用户只需提供 month, content
        self._validate(entry)
        self._autofill(entry)
        self.db.execute(
            "INSERT INTO plan (id, no, month, content, done, created_at) "
            "VALUES (:id, :no, :month, :content, :done, :created_at)",
            entry,
        )
        self.db.commit()
        return entry["id"]

    def list(self, filters: List[Filter], *,
             order_by: Optional[str] = None,
             limit: int = 50,
             offset: int = 0) -> List[Dict[str, Any]]:
        if not filters:
            raise ValueError("filters 不能为空")

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

        rows = self.db.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def delete(self, entry_id: str) -> bool:
        cur = self.db.execute("DELETE FROM plan WHERE id = :id", {"id": entry_id})
        self.db.commit()
        return cur.rowcount > 0

    def search(self, query: str, *, limit: int = 50) -> List[Dict[str, Any]]:
        return self.list(
            [Filter("content", f"%{query}%", op="LIKE")],
            limit=limit,
        )

    # ---- 校验 & 自动填充 ----

    def _validate(self, entry: Dict[str, Any]) -> None:
        """校验用户提供的必填字段（排除自动填充字段）。"""
        for col in self.columns:
            if not col.nullable and col.name not in self._auto_fields:
                if col.name not in entry:
                    raise EntryInvalidError(
                        self.name, f"缺少必填字段 '{col.name}'"
                    )

    def _autofill(self, entry: Dict[str, Any]) -> None:
        """自动填充 id / no / done / created_at。"""
        month = entry["month"]
        # 计算月份内编号：当前月份已有条目数 + 1
        no = self._next_no(month)
        entry["no"] = no
        entry["id"] = f"plan-{month}-{no:03d}"
        entry.setdefault("done", 0)
        entry["created_at"] = now_str()

    def _next_no(self, month: str) -> int:
        """返回指定月份的下一个编号。"""
        row = self.db.execute(
            "SELECT COUNT(*) AS cnt FROM plan WHERE month = :month",
            {"month": month},
        ).fetchone()
        return row["cnt"] + 1

    # ---- 摘要 ----

    def summary(self) -> str:
        """供 AI 使用的计划概览。"""
        rows = self.db.execute(
            "SELECT month, COUNT(*) AS total, SUM(done) AS done_cnt "
            "FROM plan GROUP BY month ORDER BY month DESC"
        ).fetchall()
        if not rows:
            return "[plan] 暂无计划"

        lines = ["[plan]"]
        for r in rows:
            lines.append(f"  {r['month']}: {r['done_cnt']}/{r['total']} 已完成")
        return "\n".join(lines)
