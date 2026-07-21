# xfun/notebooks/diary.py — 日记本
"""
diary 本：以日期为分组，记录每日日记。
"""

from typing import Any

from xfun.utils.time_utils import validate_date
from ..core.db import Column
from ..core.notebook import Notebook
from ..core.errors import EntryInvalidError


class DiaryNotebook(Notebook):
    name = "diary"
    _extra_columns = [
        Column("date",    "TEXT", index=True),
        Column("mood",    "TEXT", nullable=True),
        Column("weather", "TEXT", nullable=True),
    ]

    def _validate(self, entry: dict[str, Any]) -> None:
        super()._validate(entry)
        if "date" in entry and entry["date"] is not None:
            if not validate_date(str(entry["date"])):
                raise EntryInvalidError("diary", f"date 格式错误，应为 YYYY-MM-DD，实际: {entry['date']}")
