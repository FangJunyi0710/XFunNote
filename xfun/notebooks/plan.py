# xfun/notebooks/plan.py — 计划本
"""
plan 本：以月份为分组，管理待办事项 / 目标条目。

"""

from collections import defaultdict
from typing import Any

from xfun.utils.time_utils import validate_yymm

from ..core.errors import EntryInvalidError

from ..core.db import Column
from ..core.notebook import Notebook

# 序号 → 字母映射（A~Ω，共100个，由 A-Z → a-z → 小写希腊 → 大写希腊）
_SEQ_TO_LETTER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzαβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ'


def _seq_to_letter(seq: int) -> str:
    """将 1-based 序号转换为字母编号（A~Ω），超出时使用原数字。"""
    if 0 < seq <= len(_SEQ_TO_LETTER):
        return _SEQ_TO_LETTER[seq - 1]
    return f"[{seq}]"


class PlanNotebook(Notebook):
    name = "plan"
    _extra_columns = [
        Column("no",    "TEXT", auto=True, unique=True),
        Column("seq",    "INTEGER", auto=True),
        Column("month", "TEXT", index=True),
        Column("done",  "INTEGER", default=0),
    ]

    # ---- 钩子 ----

    def _pre_add(self, conn, entries: list[dict[str, Any]]) -> None:
        """
        批量添加条目，为同一月份内的条目自动分配递增序号 seq。
        seq 从 MAX(seq) + 1 开始，同批次内连续递增。
        """
        month_counter: dict[str, int] = defaultdict(int)
        for entry in entries:
            month = entry["month"]
            if month not in month_counter:
                row = conn.execute(
                    f"SELECT MAX(seq) FROM {self.name} WHERE month = ?", (month,)
                ).fetchone()
                month_counter[month] = row[0] if row[0] is not None else 0
            month_counter[month] += 1
            entry["seq"] = month_counter[month]

    def _autofill(self, entry: dict[str, Any]) -> None:
        """自动填充 plan 特有字段：no、done。"""
        super()._autofill(entry)
        entry["no"] = f"{entry['month']}{_seq_to_letter(entry['seq'])}"

    def _validate(self, entry: dict[str, Any]) -> None:
        super()._validate(entry)
        if "month" in entry and entry["month"] is not None:
            if not validate_yymm(str(entry["month"])):
                raise EntryInvalidError("plan", f"month 格式错误，应为 YYMM，实际: {entry['month']}")
        if "done" in entry and entry["done"] is not None:
            if entry["done"] not in (0, 1):
                raise EntryInvalidError("plan", f"done 必须为 0 或 1，实际: {entry['done']}")
