# xfun/notebooks/accumulation.py — 积累本
"""
accumulation 本：记录知识积累、摘录、灵感等，按分类管理。
"""

from typing import Any, Dict

from future_uuid import uuid7

from ..core.db import Column
from ..core.notebook import Notebook


class AccumulationNotebook(Notebook):
    name = "accumulation"
    _extra_columns = [
        Column("category", "TEXT", nullable=False, index=True),
        Column("source",   "TEXT", nullable=True),
        Column("note",     "TEXT", nullable=True)
    ]

    # ---- 校验 & 自动填充 ----

    def _autofill(self, entry: Dict[str, Any]) -> None:
        """自动填充 id（uuid7）/ created_at。"""
        super()._autofill(entry)
        entry["id"] = f"{self.name}-{str(uuid7())}"
