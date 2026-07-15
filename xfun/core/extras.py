from .filter import Condition


# ---------------------------------------------------------------------------
# 文本模糊搜索
# ---------------------------------------------------------------------------


@Condition.register_op("TEXT_SEARCH")
def _text_search(column: str, value, op: str):
    """
    文本模糊搜索 — LIKE 的语义别名，自动包裹 ``%``。

    用法::

        Condition("content", "关键字", "TEXT_SEARCH")

    SQL 生成::

        content LIKE '%关键字%'

    相对于直接使用 LIKE 的好处是语义更清晰，调用方无需手动拼接 ``%``。
    """
    return f"{column} LIKE ?", [f"%{value}%"]

@Condition.register_op("TRUE")
def _true(column: str, value, op: str):
    """
    恒真条件，忽略列名和值。

    用法::

        Condition("_", None, "TRUE")

    SQL 生成::

        1=1

    常用于构造 always-true 的默认筛选条件，或与其他条件做布尔组合。
    ``column`` 参数会被 ``Condition.to_sql()`` 校验但不会被使用，
    传入任意合法标识符即可（如 ``"_"``）。
    """
    return "1=1", []


@Condition.register_op("FALSE")
def _false(column: str, value, op: str):
    """
    恒假条件，忽略列名和值。

    用法::

        Condition("_", None, "FALSE")

    SQL 生成::

        1=0

    常用于构造永假条件以阻断查询，或逻辑禁用某个筛选分支。
    """
    return "1=0", []

# TODO 正则表达式匹配