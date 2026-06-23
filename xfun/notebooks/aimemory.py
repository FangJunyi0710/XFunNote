# xfun/notebooks/aimemory.py — AI 记忆本
"""
aimemory 本：专用于存储 AI 生成的结构化记忆。

与 accumulation 的区别：
- accumulation 是通用积累，用户手动或 AI 均可写入
- aimemory 专用于 AI 的记忆沉淀（标题 + 来源 + 备注），由 `save_memory` 工具写入
"""

from typing import Any, Dict

from future_uuid import uuid7

from ..core.db import Column
from ..core.notebook import Notebook


class AIMemoryNotebook(Notebook):
    name = "aimemory"
    _extra_columns = [
        Column("title",     "TEXT", nullable=False, index=True),
        Column("source",    "TEXT", nullable=True),
        Column("note",      "TEXT", nullable=True),
    ]

    # ---- 校验 & 自动填充 ----

    def _autofill(self, entry: Dict[str, Any]) -> None:
        """自动填充 id（uuid7）/ created_at / is_ai_gen=1。"""
        super()._autofill(entry)
        entry["id"] = f"{self.name}-{str(uuid7())}"
        entry["is_ai_gen"] = 1
