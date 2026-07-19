from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .filter import Condition

class XFunError(Exception):
    """XFunNote 所有异常的基类。"""
    pass


class UsernameInvalidError(XFunError):
    """用户名不合法。"""
    def __init__(self, username: str):
        super().__init__(f"非法用户名：{username}")


class EntryInvalidError(XFunError):
    """条目数据不合法（缺少必填字段、类型错误等）。"""
    def __init__(self, notebook: str, reason: str):
        super().__init__(f"[{notebook}] 条目无效: {reason}")
        self.notebook = notebook
        self.reason = reason


class SQLInvalidError(XFunError):
    """非法SQL片段。"""
    def __init__(self, name: str):
        super().__init__(f"非法SQL片段: {name!r}")
        self.name = name


class FilterInvalidError(XFunError):
    """Filter 对象解析失败。"""
    def __init__(self, obj):
        super().__init__(f"非法 Filter 对象: {obj!r}")
        self.obj = obj


class AIError(XFunError):
    """AI 相关异常的基类。"""
    pass

class PromptError(AIError):
    """Prompt 内部字段定义校验失败。"""
    def __init__(self, msg: str):
        super().__init__(msg)


class ToolError(AIError):
    """工具执行时因输入或数据状态导致的业务错误。"""
    def __init__(self, msg: str):
        super().__init__(msg)
