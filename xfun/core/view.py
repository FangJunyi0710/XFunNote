from typing import List, Tuple

from .db import Column, DB
from .filter import Filter, convert_filter_object, filter_to_json, filter_to_sql
import json

TableSpec = tuple[list[str], Filter]
# dict[表名, List[(列名列表, 行筛选条件)]]
View = dict[str, List[TableSpec]]

def view_to_sql(view: View, db: DB, table: str) -> Tuple[str, list]:
    """
    将 View 转换为针对指定表的 SELECT 查询。
    """
    if table not in view or table not in db.table_infos:
        return "", []

    Column.check(table)
    subsqls = [f"{db.select_sql(table, [])} WHERE 1=0"]
    params = []

    pks: List[str] = []
    for col in db.table_infos[table]:
        if col.primary_key:
            pks.append(col.name)

    for cols, flt in view[table]:
        # 确保主键列始终被选中（外层 GROUP BY 依赖主键去重）
        spec_cols = list(cols)
        for pk in pks:
            if pk not in spec_cols:
                spec_cols.append(pk)
        sql = db.select_sql(table, spec_cols)
        clause, vals = filter_to_sql(flt)
        if clause:
            sql += f" WHERE {clause}"
        subsqls.append(sql)
        params.extend(vals)

    pieces: List[str] = []
    for col in db.table_infos[table]:
        if col.primary_key:
            pieces.append(col.name)
            continue

        pieces.append(f"MAX({col.name}) AS {col.name}")

    sql = " UNION ALL ".join(subsqls)

    if pks:
        sql = f"SELECT {", ".join(pieces)} FROM ({sql}) AS combined GROUP BY {", ".join(pks)}"

    return sql, params

def view_to_json(view: View) -> dict:
    """将 View 转换为可 JSON 序列化的 Python 对象。"""
    data: dict = {}
    for table_name, specs in view.items():
        spec_list = []
        for columns, flt in specs:
            spec_list.append({
                "columns": list(columns),
                "filter": filter_to_json(flt),
            })
        data[table_name] = spec_list
    return data


def parse_view_json(s: str) -> View:
    """
    将 JSON 筛选条件解析为 View
    """
    data = json.loads(s)
    result: View = {}
    for table_name, specs in data.items():
        table_specs: List[TableSpec] = []
        for spec in specs:
            columns = spec["columns"]
            flt = convert_filter_object(spec["filter"])
            table_specs.append((columns, flt))
        result[table_name] = table_specs
    return result

def view_or(view1: View, view2: View) -> View:
    tables = set(view1) | set(view2)
    merged: View = {}
    for table in tables:
        specs: List[TableSpec] = []
        if table in view1:
            specs.extend(view1[table])
        if table in view2:
            specs.extend(view2[table])
        merged[table] = specs
    return merged

def _TableSpec_and(spec1: TableSpec, spec2: TableSpec) -> TableSpec:
    col1, flt1 = spec1
    col2, flt2 = spec2
    return list(set(col1) & set(col2)), [[flt1, flt2]]

def view_and(view1: View, view2: View) -> View:
    tables = set(view1) & set(view2)
    merged: View = {}
    for table in tables:
        specs: List[TableSpec] = []
        for spec1 in view1[table]:
            for spec2 in view2[table]:
                specs.append(_TableSpec_and(spec1, spec2))
        merged[table] = specs
    return merged

# 暂不需要实现
# def view_diff(view1: View, view2: View) -> View:
#     """
#     差集：返回只在 view1 中出现的，忽略同时在 view2 中出现的。
#     """
#     merged: View = {}
#     for table in view1:
#         if table not in view2:
#             merged[table] = view1[table]
#             continue
#         # 实现差集逻辑
#     return merged

