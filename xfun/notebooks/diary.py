# xfun/notebooks/diary.py — 日记本
"""
diary 本：以日期为分组，记录每日日记。
"""

from typing import Any, Dict

from future_uuid import uuid7

from ..core.db import Column
from ..core.notebook import Notebook


class DiaryNotebook(Notebook):
    name = "diary"
    _extra_columns = [
        Column("date",    "TEXT", nullable=False, index=True),
        Column("mood",    "TEXT", nullable=True),
        Column("weather", "TEXT", nullable=True),
    ]

    # ---- 校验 & 自动填充 ----

    def _autofill(self, entry: Dict[str, Any]) -> None:
        """自动填充 id（uuid7）/ date / created_at。"""
        super()._autofill(entry)
        entry["id"] = f"{self.name}-{entry['date']}-{str(uuid7())}"
