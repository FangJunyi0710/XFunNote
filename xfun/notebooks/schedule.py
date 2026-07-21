# xfun/notebooks/schedule.py — 日程本
"""
schedule 本：记录未来计划 / 日程，与 timeline 列定义相同。
前端逻辑不同（规划 vs 记录）。
"""

from typing import Any

from xfun.utils.time_utils import validate_datetime
from ..core.db import Column
from ..core.notebook import Notebook
from ..core.errors import EntryInvalidError


class ScheduleNotebook(Notebook):
    name = "schedule"
    _extra_columns = [
        Column("start_time", "TEXT", index=True),
        Column("end_time",   "TEXT", nullable=True),
        Column("location",   "TEXT", nullable=True),
    ]

    def _validate(self, entry: dict[str, Any]) -> None:
        super()._validate(entry)
        if "start_time" in entry and entry["start_time"] is not None:
            if not validate_datetime(str(entry["start_time"])):
                raise EntryInvalidError("schedule", f"start_time 格式错误，应为 ISO 8601，实际: {entry['start_time']}")
        if "end_time" in entry and entry["end_time"] is not None:
            if not validate_datetime(str(entry["end_time"])):
                raise EntryInvalidError("schedule", f"end_time 格式错误，应为 ISO 8601，实际: {entry['end_time']}")
