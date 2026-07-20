# xfun/notebooks/timeline.py — 时间线本
"""
timeline 本：记录用户实际做了什么，精确到分钟。
"""

from typing import Any
from ..core.db import Column
from ..core.notebook import Notebook
from ..core.errors import EntryInvalidError

class TimelineNotebook(Notebook):
    name = "timeline"
    _extra_columns = [
        Column("start_time", "TEXT", nullable=False, index=True),
        Column("end_time",   "TEXT", nullable=True),
        Column("location",   "TEXT", nullable=True),
    ]

    def _validate(self, entry: dict[str, Any]) -> None:
        from xfun.utils.time_utils import validate_datetime
        if "start_time" in entry and entry["start_time"] is not None:
            if not validate_datetime(str(entry["start_time"])):
                raise EntryInvalidError("timeline", f"start_time 格式错误，应为 ISO 8601，实际: {entry['start_time']}")
        if "end_time" in entry and entry["end_time"] is not None:
            if not validate_datetime(str(entry["end_time"])):
                raise EntryInvalidError("timeline", f"end_time 格式错误，应为 ISO 8601，实际: {entry['end_time']}")
