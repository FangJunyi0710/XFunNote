from typing import List, Tuple

from .db import Column, DB
from .filter import Filter, filter_to_sql

Basic_TableSpec = tuple[list[str], Filter]
# dict[表名, List[(列名列表, 行筛选条件)]]
View = dict[str, List[Basic_TableSpec]]

def view_to_sql(view: View, db: DB, table: str) -> Tuple[str, list]:
    """
    将 View 转换为针对指定表的 SELECT 查询。
    """
    if table not in view or table not in db.table_infos:
        return "", []

    Column.check(table)
    subsqls = [f"{db.select_sql(table, [])} WHERE 1=0"]
    params = []

    for cols, flt in view[table]:
        sql = db.select_sql(table, cols)
        clause, vals = filter_to_sql(flt)
        if clause:
            sql += f" WHERE {clause}"
        subsqls.append(f"({sql})")
        params.extend(vals)

    pks: List[str] = []
    pieces: List[str] = []
    for col in db.table_infos[table]:
        if col.primary_key:
            pks.append(col.name)
            pieces.append(col.name)
            continue

        pieces.append(f"MAX({col.name}) AS {col.name}")

    sql = " UNION ALL ".join(subsqls)

    if pks:
        sql = f"SELECT {", ".join(pieces)} FROM ({sql}) AS combined GROUP BY {", ".join(pks)}"

    return sql, params

