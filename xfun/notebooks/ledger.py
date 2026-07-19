# xfun/notebooks/ledger.py — 账本
"""
ledger 本：记录收支流水，每笔包含日期和金额。
分类与备注复用基类的 tags 和 note 字段。
"""

from ..core.db import Column
from ..core.notebook import Notebook


class LedgerNotebook(Notebook):
    name = "ledger"
    _extra_columns = [
        Column("date", "TEXT", nullable=False, index=True),
        Column("amount", "REAL", nullable=False),
        Column("account", "TEXT", nullable=True),
    ]
