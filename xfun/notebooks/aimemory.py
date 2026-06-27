# xfun/notebooks/aimemory.py — AI 记忆本
"""
aimemory 本：专用于存储 AI 生成的结构化记忆。

与 accumulation 的区别：
- accumulation 是通用积累，用户手动或 AI 均可写入
- aimemory 专用于 AI 的记忆沉淀（标题 + 来源 + 备注），由 `add_entries(notetype="aimemory", ...)` 工具写入
"""

from ..core.db import Column
from ..core.notebook import Notebook


class AIMemoryNotebook(Notebook):
    name = "aimemory"
    _extra_columns = [
        Column("title",     "TEXT", nullable=False, index=True),
        Column("source",    "TEXT", nullable=True),
    ]
