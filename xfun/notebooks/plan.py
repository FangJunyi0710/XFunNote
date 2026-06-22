# xfun/notebooks/plan.py — 计划本
"""
plan 本：以月份为分组，管理待办事项 / 目标条目。

"""

from collections import defaultdict
from typing import Any, Dict, List

from future_uuid import uuid7

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
        Column("no",    "TEXT", nullable=False, auto=True),
        Column("seq",    "INTEGER", nullable=False, auto=True),
        Column("month", "TEXT",    nullable=False, index=True),
        Column("done",  "INTEGER", nullable=False, auto=True),
    ]

    # ---- CRUD ----

    def add(self, conn, entries: List[Dict[str, Any]]) -> List[str]:
        """
        批量添加条目，为同一月份内的条目自动分配递增序号 seq。
        seq 从 MAX(seq) + 1 开始，同批次内连续递增。
        """
        # 先计算 seq，再交给 super().add() 处理校验 / 自动填充 / 批量插入
        month_counter: Dict[str, int] = defaultdict(int)
        for entry in entries:
            month = entry["month"]
            if month not in month_counter:
                row = conn.execute(
                    f"SELECT MAX(seq) FROM {self.name} WHERE month = ?", (month,)
                ).fetchone()
                month_counter[month] = row[0] if row[0] is not None else 0
            month_counter[month] += 1
            entry["seq"] = month_counter[month]

        return super().add(conn, entries)

    # ---- 校验 & 自动填充 ----

    def _autofill(self, entry: Dict[str, Any]) -> None:
        """自动填充 id（uuid7）/ done / created_at（seq 在 add 中分配）。"""
        super()._autofill(entry)
        entry["id"] = f"{self.name}-{entry['month']}-{str(uuid7())}"
        entry["no"] = f"{entry['month']}{_seq_to_letter(entry['seq'])}"
        entry.setdefault("done", 0)
