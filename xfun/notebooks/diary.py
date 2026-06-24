# xfun/notebooks/diary.py — 日记本
"""
diary 本：以日期为分组，记录每日日记。
"""

from ..core.db import Column
from ..core.notebook import Notebook


class DiaryNotebook(Notebook):
    name = "diary"
    _extra_columns = [
        Column("date",    "TEXT", nullable=False, index=True),
        Column("mood",    "TEXT", nullable=True),
        Column("weather", "TEXT", nullable=True),
    ]
