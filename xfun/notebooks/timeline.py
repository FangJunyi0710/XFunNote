# xfun/notebooks/timeline.py — 时间线本
"""
timeline 本：记录用户实际做了什么，精确到分钟。
"""

from ..core.db import Column
from ..core.notebook import Notebook


class TimelineNotebook(Notebook):
    name = "timeline"
    _extra_columns = [
        Column("start_time", "TEXT", nullable=False, index=True),
        Column("end_time",   "TEXT", nullable=True),
        Column("location",   "TEXT", nullable=True),
    ]
