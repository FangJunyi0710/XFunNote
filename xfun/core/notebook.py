"""
Notebook 基类 — 子类只需定义 name 与 _extra_columns，基类自动提供 schema 定义。
CRUD 由 DB 类统一管理，子类通过 _pre_add / _validate / _autofill 钩子定制行为。
"""

from typing import Any

from .db import Column


# ---------------------------------------------------------------------------
# 通用基类列定义 —— 所有本子共有的字段
# ---------------------------------------------------------------------------

BASE_COLUMNS = [
    Column("id",         "TEXT",    primary_key=True, nullable=False, auto=True),
    Column("content",    "TEXT",    nullable=False),
    Column("created_at", "TEXT",    nullable=False, auto=True),
    Column("updated_at", "TEXT",    nullable=False, auto=True),
    Column("tags",       "TEXT",    nullable=True),
    Column("is_ai_gen",  "INTEGER", nullable=False, auto=True),
    Column("ai_tags",    "TEXT",    nullable=True),
    Column("ai_note",    "TEXT",    nullable=True),
]

_AUTOFILL_DEFAULTS = {
    "is_ai_gen": 0,
}


class Notebook:
    """
    Notebook 基类 —— 定义本子的 schema 与行为契约。

    子类只需：
    1. 设置 name 属性（本子名称）
    2. 定义 _extra_columns 类属性（本子特有列，不含基类通用列）

    可选：重写钩子方法以定制行为：
    - ``_pre_add(conn, entries)`` — 添加前批量修改（如分配序号）
    - ``_validate(entry)`` — 本子特有字段校验
    - ``_autofill(entry)`` — 本子特有字段自动填充

    columns 属性由 BASE_COLUMNS + _extra_columns 自动合并。
    """

    # ---- 子类必须设定 ----

    name: str = ""
    _extra_columns: list[Column] = []

    # ---- 合并列 ----

    @property
    def columns(self) -> list[Column]:
        """合并基类通用列 + 子类特有列"""
        return BASE_COLUMNS + self._extra_columns

    # ---- 钩子方法（子类可重写） ----

    def _pre_add(self, conn, entries: list[dict]) -> None:
        """预添加钩子：在 validate/autofill 前批量修改条目。"""
        pass

    def _validate(self, entry: dict[str, Any]) -> None:
        """校验钩子：本子特有的校验逻辑。"""
        pass

    def _autofill(self, entry: dict[str, Any]) -> None:
        """自动填充钩子：填充本子特有字段（基类通用字段由 DB 统一填充）。"""
        cols = {c.name for c in self.columns}
        for field, default in _AUTOFILL_DEFAULTS.items():
            if field in cols and field not in entry:
                entry[field] = default

    # ---- 内置 ----

    def __repr__(self) -> str:
        return f"<Notebook:{self.name}>"

    def __str__(self) -> str:
        return self.name or self.__class__.__name__
