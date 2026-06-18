class XFunError(Exception):
    """XFunNote 所有异常的基类。"""
    pass


class NotebookNotFoundError(XFunError):
    """请求的 Notebook 未注册。"""

    def __init__(self, name: str):
        super().__init__(f"Notebook '{name}' 未注册")
        self.name = name


class EntryInvalidError(XFunError):
    """条目数据不合法（缺少必填字段、类型错误等）。"""

    def __init__(self, notebook: str, reason: str):
        super().__init__(f"[{notebook}] 条目无效: {reason}")
        self.notebook = notebook
        self.reason = reason


class InvalidColumnNameError(XFunError):
    """非法列名。"""

    def __init__(self, name: str):
        super().__init__(f"非法列名: {name!r}")
        self.name = name


class InvalidOperatorError(XFunError):
    """不支持的运算符。"""

    def __init__(self, op: str):
        super().__init__(f"非法运算符: {op!r}")
        self.op = op


class InvalidConditionValueError(XFunError):
    """条件值不合法（类型、格式或数量不符）。"""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason
