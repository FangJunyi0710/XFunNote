# xfun/notebooks/word.py — 单词本
"""
word 本：管理单词，记录单词、词性、音标、例句、复习数据。
"""

from typing import Any, Dict

from ..core.db import Column
from ..core.notebook import Notebook


class WordNotebook(Notebook):
    name = "word"
    _extra_columns = [
        Column("word",           "TEXT",    nullable=False),
        Column("part_of_speech", "TEXT",    nullable=True),
        Column("phonetic",       "TEXT",    nullable=True),
        Column("example",        "TEXT",    nullable=True),
        Column("review_count",   "INTEGER", nullable=False, auto=True),
        Column("performance",    "REAL",    nullable=False, auto=True),
        Column("next_review",    "TEXT",    nullable=True),
        Column("last_review",    "TEXT",    nullable=True),
        Column("related_words",  "TEXT",    nullable=True),
    ]

    # ---- 校验 & 自动填充 ----

    def _autofill(self, entry: Dict[str, Any]) -> None:
        """自动填充 review_count / performance。
        """
        super()._autofill(entry)
        entry.setdefault("review_count", 0)
        entry.setdefault("performance", 0.0)
