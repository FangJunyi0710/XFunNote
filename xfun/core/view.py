"""视图定义：表级视图的 Filter 描述。"""

from typing import Tuple

from .db import Column, Filter, filter_to_sql

Basic_TableSpec = tuple[list[str], Filter]
# dict[表名, (列名列表, 行筛选条件)]
Basic_View = dict[str, Basic_TableSpec]


def basic_view_to_sql(view: Basic_View, table: str) -> Tuple[str, list]:
    """将 Basic_View 转换为针对指定表的 SELECT 查询。

    Parameters
    ----------
    view : Basic_View
        视图定义，dict[表名, (列名列表, 行筛选条件)]。
    table : str
        要查询的表名，作为键从 view 中查找。

    Returns
    -------
    Tuple[str, list]
        (SQL 语句, 参数值列表)。若 table 不在 view 中则返回 ("", [])。
    """
    if table not in view:
        return "", []

    Column.check(table)
    cols, filter = view[table]
    for col in cols:
        Column.check(col)
    select_cols = ", ".join(f"{table}.{col}" for col in cols)

    sql = f"SELECT {select_cols} FROM {table}"

    clause, params = filter_to_sql(filter)
    if clause:
        sql += f" WHERE {clause}"

    return sql, params

