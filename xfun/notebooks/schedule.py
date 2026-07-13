# xfun/notebooks/schedule.py — 日程本
"""
schedule 本：记录未来计划 / 日程，与 timeline 列定义相同。
前端逻辑不同（规划 vs 记录）。
"""

from ..core.db import Column
from ..core.notebook import Notebook


class ScheduleNotebook(Notebook):
    name = "schedule"
    _extra_columns = [
        Column("start_time", "TEXT", nullable=False, index=True),
        Column("end_time",   "TEXT", nullable=True),
        Column("location",   "TEXT", nullable=True),
    ]
