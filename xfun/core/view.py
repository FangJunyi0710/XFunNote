from typing import Any

from .db import Column, DB
from .filter import TRUE_CONDITION, FALSE_CONDITION, Condition, Filter, filter_to_json, filter_to_sql, parse_filter_json
import json

from .. import db as _db

TableSpec = tuple[list[str], Filter]
# dict[表名, list[(列名列表, 行筛选条件)]]
View = dict[str, list[TableSpec]]

def view_to_sql(view: View, db: DB, table: str) -> tuple[str, list]:
    """
    将 View 转换为针对指定表的 SELECT 查询。
    """
    if table not in view or table not in db.table_infos:
        return "", []

    Column.check(table)
    subsqls = [f"{db.select_sql(table, [])} WHERE 1=0"]
    params = []

    pks: list[str] = []
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
        sql += f" WHERE {clause}"
        subsqls.append(sql)
        params.extend(vals)

    pieces: list[str] = []
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


def parse_view_json(obj) -> View:
    """将 JSON 筛选条件解析为 View。传入 json.loads(s)。"""
    result: View = {}
    for table_name, specs in obj.items():
        table_specs: list[TableSpec] = []
        for spec in specs:
            columns = spec["columns"]
            flt = parse_filter_json(spec["filter"])
            table_specs.append((columns, flt))
        result[table_name] = table_specs
    return result

def view_or(view1: View, view2: View) -> View:
    tables = set(view1) | set(view2)
    merged: View = {}
    for table in tables:
        specs: list[TableSpec] = []
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
        specs: list[TableSpec] = []
        for spec1 in view1[table]:
            for spec2 in view2[table]:
                specs.append(_TableSpec_and(spec1, spec2))
        merged[table] = specs
    return merged


def _clean_entry(entry: dict[str, Any], allowed_columns: set[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for col in entry:
        # id 永远不能被 update 或 add
        if col == "id":
            continue
        if col in allowed_columns:
            result[col] = entry[col]
    return result

def view_clean_add(view: View, table: str, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    '''只要 view[table] 中出现了该列，则允许 add 时指定'''
    if table not in view.keys():
        return []
    return [_clean_entry(entry, {col for cols, _ in view[table] for col in cols}) for entry in entries]

def view_clean_delete(view: View, table: str, filter: Filter) -> Filter:
    '''有 id 的修改权限，含义为允许删除'''
    if table not in view.keys():
        return FALSE_CONDITION
    return [[filter, [[flt] for cols, flt in view[table] if "id" in cols]+[[FALSE_CONDITION]]]]

def view_clean_update(view: View, table: str, filter: Filter, values: dict[str, Any]) -> list[tuple[Filter, dict[str, Any]]]:
    if table not in view.keys():
        return []
    result: list[tuple[Filter, dict[str, Any]]] = []
    for cols, flt in view[table]:
        result.append(([[flt, filter]], _clean_entry(values, cols)))
    return result

def full_view(db: DB) -> View:
    full_view: View = {}
    for table_name in db.table_infos:
        full_view[table_name] = [(db.cols(table_name), TRUE_CONDITION)]
    return full_view

def no_view(db: DB) -> View:
    no_view: View = {}
    for table_name in db.table_infos:
        no_view[table_name] = [([], FALSE_CONDITION)]
    return no_view

# 读权限, 写权限
DB_Permission = tuple[View, View]

def root_permission(db: DB) -> DB_Permission:
    return (full_view(db), full_view(db))

def no_permission(db: DB) -> DB_Permission:
    return (no_view(db), no_view(db))
