# xfun/notebooks/plan.py — 计划本
"""
plan 本：以月份为分组，管理待办事项 / 目标条目。

"""

from typing import Any, Dict

from future_uuid import uuid7

from ..core.db import Column
from ..core.notebook import Notebook

class PlanNotebook(Notebook):
    name = "plan"
    _extra_columns = [
        Column("no",    "INTEGER", nullable=False, auto=True),
        Column("month", "TEXT",    nullable=False, index=True),
        Column("done",  "INTEGER", nullable=False, auto=True),
    ]

    # ---- CRUD ----

    # ---- 校验 & 自动填充 ----

    def _autofill(self, entry: Dict[str, Any], conn) -> None:
        """自动填充 id（uuid7）/ no / done / created_at。"""
        super()._autofill(entry, conn)
        entry["id"] = f"plan-{entry["month"]}-{str(uuid7())}"
        entry["no"] = 0       # TODO: 后续完善排序逻辑
        entry.setdefault("done", 0)
