from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .filter import Condition

class XFunError(Exception):
    """XFunNote 所有异常的基类。"""
    pass


class EntryInvalidError(XFunError):
    """条目数据不合法（缺少必填字段、类型错误等）。"""

    def __init__(self, notebook: str, reason: str):
        super().__init__(f"[{notebook}] 条目无效: {reason}")
        self.notebook = notebook
        self.reason = reason


class InvalidSQLError(XFunError):
    """非法SQL片段。"""

    def __init__(self, name: str):
        super().__init__(f"非法SQL片段: {name!r}")
        self.name = name


class InvalidConditionError(XFunError):
    """Condition对象解析失败。"""

    def __init__(self, cond: Condition):
        super().__init__(f"非法Condition对象: {cond!r}")
        self.cond = cond
