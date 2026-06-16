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
