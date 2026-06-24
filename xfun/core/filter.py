import json
from dataclasses import dataclass
from typing import Any, ClassVar
from collections.abc import Sequence as Seq
from .db import Column
from .errors import InvalidConditionError, InvalidFilterError


# ---------------------------------------------------------------------------
# 筛选条件
# ---------------------------------------------------------------------------

@dataclass
class Condition:
    column: str
    value: Any
    op: str = "="

    _op_registry: ClassVar[dict] = {}

    @classmethod
    def register_op(cls, op_name: str):
        """装饰器：注册自定义运算符的 SQL 生成逻辑。

        Parameters
        ----------
        op_name : str
            自定义运算符名称。

        Returns
        -------
        callable
            装饰器，接收 handler(column, value, op) -> (sql, params)。
        """
        def decorator(func):
            cls._op_registry[op_name] = func
            return func
        return decorator

    def to_sql(self) -> tuple[str, list]:
        """生成该条件的 SQL 片段及参数值列表。

        Returns
        -------
        tuple[str, list]
            (SQL 片段, 参数值列表)。值为 None 时返回空列表，SQL 使用 IS NULL / IS NOT NULL。

        Raises
        ------
        InvalidConditionError
        """
        Column.check(self.column)

        handler = self._op_registry.get(self.op)
        if handler is None:
            raise InvalidConditionError(self)
        
        return handler(self.column, self.value, self.op)
    

@Condition.register_op("=")
@Condition.register_op("!=")
@Condition.register_op(">")
@Condition.register_op("<")
@Condition.register_op(">=")
@Condition.register_op("<=")
@Condition.register_op("LIKE")
@Condition.register_op("NOT LIKE")
@Condition.register_op("IN")
@Condition.register_op("NOT IN")
@Condition.register_op("BETWEEN")
def _builtin_sql(column, value, op) -> tuple[str, list]:
    # --- NULL：只有 = 和 != 可以处理 NULL ---
    if value is None:
        if op == "=":
            return f"{column} IS NULL", []
        if op == "!=":
            return f"{column} IS NOT NULL", []
        raise InvalidConditionError(Condition(column, value, op))

    # --- IN / NOT IN ---
    if op in ("IN", "NOT IN"):
        if not isinstance(value, (list, tuple)):
            raise InvalidConditionError(Condition(column, value, op))
        value = list(dict.fromkeys(value))
        if not value:
            # 空列表：IN → 永假，NOT IN → 永真
            return ("1=0", []) if op == "IN" else ("1=1", [])
        placeholders = ", ".join("?" for _ in value)
        sql = f"{column} {op} ({placeholders})"
        params = list(value)

    # --- BETWEEN ---
    elif op == "BETWEEN":
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise InvalidConditionError(Condition(column, value, op))
        if value[0] is None or value[1] is None:
            # 任意端点为 None → 永假
            return "1=0", []
        sql = f"{column} {op} ? AND ?"
        params = list(value)

    # --- 通用（=, >, <, >=, <=, !=, LIKE, NOT LIKE）---
    else:
        sql = f"{column} {op} ?"
        params = [value]

    return sql, params


Filter = Condition | Seq[Seq["Filter"]] | tuple["Filter", bool]
# 递归结构：外层 OR、内层 AND，元素为子树，直至叶子节点，最外层支持 (... , negate) 元组对整个结果取反。


def filter_to_sql(filter: Filter) -> tuple[str, list]:
    """
    生成 WHERE 子句：外层 OR（取并），内层 AND（取交）。
    最外层可为 (Filter, bool) 元组，bool=True 时对整个结果取反。

    Parameters
    ----------
    filter : Filter
        Filter 结构或 (Filter, bool) 元组。

    Returns
    -------
    tuple[str, list]
        (WHERE 子句 SQL 片段，可能为空，参数值列表)
    """
    if isinstance(filter, Condition):
        return filter.to_sql()

    if isinstance(filter, tuple):
        inner, negate = filter
        clause, vals = filter_to_sql(inner)
        if not clause:
            return "", []
        if negate:
            clause = f"NOT ({clause})"
        return clause, vals

    or_clauses: list[str] = []
    params: list = []
    for group in filter:
        and_clauses: list[str] = []
        for item in group:
            clause, vals = filter_to_sql(item)
            if not clause:
                continue
            and_clauses.append(f"({clause})")
            params.extend(vals)
        if not and_clauses:
            continue
        or_clauses.append("(" + " AND ".join(and_clauses) + ")")

    if not or_clauses:
        return "", []
    
    where_sql = " OR ".join(or_clauses)
    return where_sql, params


def convert_filter_object(obj):
    if isinstance(obj, dict):
        condition = Condition(**obj)
        return condition
    if isinstance(obj, list) and len(obj) == 2 and isinstance(obj[1], bool):
        return (convert_filter_object(obj[0]), obj[1])
    if not isinstance(obj, list):
        raise InvalidFilterError(obj)
    result = []
    for group in obj:
        clause = []
        if not isinstance(group, list):
            raise InvalidFilterError(obj)
        for item in group:
            clause.append(convert_filter_object(item))
        result.append(clause)
    return result

def parse_filter_json(s: str) -> Filter:
    """将 JSON 筛选条件解析为 Filter。"""
    return convert_filter_object(json.loads(s))


def filter_to_json(filter: Filter) -> Any:
    """递归将 Filter 转换为可 JSON 序列化的 Python 对象。

    Parameters
    ----------
    filter : Filter
        Filter 结构或 (Filter, bool) 元组。

    Returns
    -------
    Any
        可序列化的 Python 对象（dict / list）。
    """
    if isinstance(filter, Condition):
        return {"column": filter.column, "value": filter.value, "op": filter.op}
    if isinstance(filter, tuple):
        inner, negate = filter
        return [filter_to_json(inner), negate]
    # Seq[Seq[Filter]]：外层 OR，内层 AND
    return [[filter_to_json(item) for item in group] for group in filter]


from .extras import TRUE_CONDITION, FALSE_CONDITION
