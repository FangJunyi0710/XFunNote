# xfun/notebooks/ledger.py — 账本
"""
ledger 本：记录收支流水，每笔包含日期和金额。
分类与备注复用基类的 tags 和 note 字段。
"""

from typing import Any

from xfun.utils.time_utils import validate_date
from ..core.db import Column
from ..core.notebook import Notebook
from ..core.errors import EntryInvalidError


class LedgerNotebook(Notebook):
    name = "ledger"
    _extra_columns = [
        Column("date", "TEXT", index=True),
        Column("amount_cents", "INTEGER"),
        Column("account", "TEXT", nullable=True),
    ]

    def _validate(self, entry: dict[str, Any]) -> None:
        super()._validate(entry)
        if "date" in entry and entry["date"] is not None:
            if not validate_date(str(entry["date"])):
                raise EntryInvalidError("ledger", f"date 格式错误，应为 YYYY-MM-DD，实际: {entry['date']}")
        if "amount_cents" in entry and entry["amount_cents"] is not None:
            try:
                amount_cents = int(entry["amount_cents"])
                if amount_cents == 0:
                    raise EntryInvalidError("ledger", "amount_cents 不能为 0")
            except (ValueError, TypeError):
                raise EntryInvalidError("ledger", f"amount_cents 必须为数字，实际: {entry['amount_cents']}")
