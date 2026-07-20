# xfun/notebooks/word.py — 单词本
"""
word 本：管理单词，记录单词、词性、音标、例句、复习数据。
"""

from typing import Any
from fsrs import Card, Rating, Scheduler
from datetime import datetime
scheduler = Scheduler()

from ..utils.time_utils import format_datetime, now_str
from ..core.db import Column
from ..core.notebook import Notebook
from ..core.errors import EntryInvalidError

class WordNotebook(Notebook):
    name = "word"
    _extra_columns = [
        Column("word",           "TEXT",    nullable=False, unique=True),
        Column("part_of_speech", "TEXT",    nullable=True),
        Column("phonetic",       "TEXT",    nullable=True),
        Column("example",        "TEXT",    nullable=True),
        Column("related_words",  "TEXT",    nullable=True),

        # ---- FSRS 核心状态字段 ----
        Column("stability",      "REAL",    nullable=False, auto=True),   # 稳定性（天）
        Column("difficulty",     "REAL",    nullable=False, auto=True),   # 难度
        Column("state",          "INTEGER", nullable=False, auto=True),     # 卡片状态: 0=新, 1=学习中, 2=复习中, 3=重新学习
        Column("lapses",         "INTEGER", nullable=False, auto=True),     # 遗忘次数
        Column("step",           "INTEGER", nullable=False, auto=True),     # 学习/重学步骤索引

        # ---- 复习记录 ----
        Column("review_count",   "INTEGER", nullable=False, auto=True),     # 总复习次数（对应 FSRS 的 reps）
        Column("next_review",    "TEXT",    nullable=False, auto=True),     # 下次复习时间（ISO 8601 字符串）
        Column("last_review",    "TEXT",    nullable=True),                 # 上次复习时间
    ]

    # ---- 校验 & 自动填充 ----
    def _autofill(self, entry: dict[str, Any]) -> None:
        super()._autofill(entry)
        entry.setdefault("review_count", 0)
        entry.setdefault("stability", 2.5)      # FSRS 默认初始稳定性
        entry.setdefault("difficulty", 5.0)     # 中等难度
        entry.setdefault("state", 0)            # 新卡片
        entry.setdefault("lapses", 0)
        entry.setdefault("step", 0)
        entry.setdefault("next_review", now_str())

    def _validate(self, entry: dict[str, Any]) -> None:
        """校验 word 特有字段（仅校验已存在的字段）。"""
        from ..utils.time_utils import validate_datetime

        # ---- FSRS 核心状态字段 ----
        if "stability" in entry and entry["stability"] is not None:
            try:
                val = float(entry["stability"])
                if val <= 0:
                    raise EntryInvalidError("word", f"stability 必须大于 0，实际: {val}")
            except (ValueError, TypeError):
                raise EntryInvalidError("word", f"stability 必须为数字，实际: {entry['stability']}")

        if "difficulty" in entry and entry["difficulty"] is not None:
            try:
                val = float(entry["difficulty"])
                if val < 1.0 or val > 10.0:
                    raise EntryInvalidError("word", f"difficulty 必须在 1.0 ~ 10.0 之间，实际: {val}")
            except (ValueError, TypeError):
                raise EntryInvalidError("word", f"difficulty 必须为数字，实际: {entry['difficulty']}")

        if "state" in entry and entry["state"] is not None:
            try:
                val = int(entry["state"])
                if val not in (0, 1, 2, 3):
                    raise EntryInvalidError("word", f"state 必须为 0/1/2/3，实际: {val}")
            except (ValueError, TypeError):
                raise EntryInvalidError("word", f"state 必须为整数，实际: {entry['state']}")

        if "lapses" in entry and entry["lapses"] is not None:
            try:
                val = int(entry["lapses"])
                if val < 0:
                    raise EntryInvalidError("word", f"lapses 必须 >= 0，实际: {val}")
            except (ValueError, TypeError):
                raise EntryInvalidError("word", f"lapses 必须为整数，实际: {entry['lapses']}")

        if "step" in entry and entry["step"] is not None:
            try:
                val = int(entry["step"])
                if val < 0:
                    raise EntryInvalidError("word", f"step 必须 >= 0，实际: {val}")
            except (ValueError, TypeError):
                raise EntryInvalidError("word", f"step 必须为整数，实际: {entry['step']}")

        if "review_count" in entry and entry["review_count"] is not None:
            try:
                val = int(entry["review_count"])
                if val < 0:
                    raise EntryInvalidError("word", f"review_count 必须 >= 0，实际: {val}")
            except (ValueError, TypeError):
                raise EntryInvalidError("word", f"review_count 必须为整数，实际: {entry['review_count']}")

        # ---- 时间字段 ----
        if "next_review" in entry and entry["next_review"] is not None:
            if not validate_datetime(str(entry["next_review"])):
                raise EntryInvalidError("word", f"next_review 格式错误，应为 ISO 8601 Z，实际: {entry['next_review']}")

        if "last_review" in entry and entry["last_review"] is not None:
            if not validate_datetime(str(entry["last_review"])):
                raise EntryInvalidError("word", f"last_review 格式错误，应为 ISO 8601 Z，实际: {entry['last_review']}")

def review_word(word_entry: dict, rating: Rating) -> dict:
    """
    复习一个单词并更新其调度信息。

    Args:
        notebook: WordNotebook 实例
        word_entry: 单词条目字典
        rating: FSRS 评分 (Rating.Again, Hard, Good, Easy)
    """
    # 1. 将数据库记录转换为 FSRS Card 对象
    card = Card(
        card_id=word_entry['id'],
        stability=word_entry['stability'],
        difficulty=word_entry['difficulty'],
        state=word_entry['state'],
        lapses=word_entry['lapses'],
        reps=word_entry['review_count'],  # reps 对应 review_count
        step=word_entry.get('step', 0),
        due=datetime.fromisoformat(word_entry['next_review']),
        last_review=datetime.fromisoformat(word_entry['last_review']) if word_entry.get('last_review') else None
    )

    # 2. 使用调度器进行复习，得到更新后的 Card 和本次复习日志
    updated_card, review_log = scheduler.review_card(card, rating)

    # 3. 将更新后的数据写回 word_entry
    word_entry['stability'] = updated_card.stability
    word_entry['difficulty'] = updated_card.difficulty
    word_entry['state'] = updated_card.state
    word_entry['lapses'] = updated_card.lapses
    word_entry['review_count'] = updated_card.reps
    word_entry['next_review'] = format_datetime(updated_card.due)
    word_entry['last_review'] = now_str()
    word_entry['step'] = updated_card.step

    return word_entry
