"""测试 View 系统 — 跨本子查询、并集/交集、安全清洗。"""

import pytest

from xfun.core.view import (
    View,
    view_to_sql,
    view_or,
    view_and,
    view_clean_columns,
    view_clean_filter,
    view_clean_update,
    root_permission,
    no_permission,
    no_view,
    view_to_json,
    parse_view_json,
)
from xfun.core.filter import Condition, TRUE_CONDITION, FALSE_CONDITION
from xfun.core.filter import Condition, TRUE_CONDITION


class TestViewToSQL:
    def test_empty_view(self, db):
        sql, params = view_to_sql({}, db, "plan")
        assert sql == ""
        assert params == []

    def test_nonexistent_table(self, db):
        view: View = {"plan": [(["content"], TRUE_CONDITION)]}
        sql, params = view_to_sql(view, db, "nonexistent")
        assert sql == ""

    def test_single_table_view(self, db):
        view: View = {"plan": [(["content", "month"], TRUE_CONDITION)]}
        sql, params = view_to_sql(view, db, "plan")
        assert "plan" in sql
        assert "MAX" in sql
        assert "GROUP BY" in sql

    def test_entries_appear_in_view(self, registry, db):
        nb = registry["plan"]
        with db.transaction() as conn:
            ids = nb.add(conn, [{"content": "my plan", "month": "2606"}])
        view: View = {"plan": [(["content", "month"], TRUE_CONDITION)]}
        sql, params = view_to_sql(view, db, "plan")
        with db.transaction() as conn:
            rows = conn.execute(sql, params).fetchall()
        assert len(rows) == 1
        assert rows[0]["content"] == "my plan"
        assert rows[0]["month"] == "2606"

    def test_pk_always_selected(self, db):
        view: View = {"plan": [(["content"], TRUE_CONDITION)]}
        sql, params = view_to_sql(view, db, "plan")
        with db.read_transaction() as conn:
            schema = conn.execute("SELECT sql FROM sqlite_master WHERE name='plan'").fetchone()
        assert "id" in sql

    def test_view_results_count(self, registry, db):
        """插入多条数据后，通过 view 查询应返回正确条数。"""
        nb = registry["plan"]
        with db.transaction() as conn:
            nb.add(conn, [
                {"content": "a", "month": "2606"},
                {"content": "b", "month": "2606"},
                {"content": "c", "month": "2607"},
            ])
        view: View = {"plan": [(["content"], Condition("month", "2606", "="))]}
        sql, params = view_to_sql(view, db, "plan")
        with db.transaction() as conn:
            rows = conn.execute(sql, params).fetchall()
        assert len(rows) == 2


class TestViewOr:
    def test_or_same_table(self):
        v1: View = {"plan": [(["content"], TRUE_CONDITION)]}
        v2: View = {"plan": [(["month"], TRUE_CONDITION)]}
        merged = view_or(v1, v2)
        assert "plan" in merged
        assert len(merged["plan"]) == 2

    def test_or_different_tables(self):
        v1: View = {"plan": [(["content"], TRUE_CONDITION)]}
        v2: View = {"diary": [(["date"], TRUE_CONDITION)]}
        merged = view_or(v1, v2)
        assert "plan" in merged
        assert "diary" in merged

    def test_or_overlapping(self):
        v1: View = {"plan": [(["content"], TRUE_CONDITION)]}
        v2: View = {"plan": [(["content"], TRUE_CONDITION)]}
        merged = view_or(v1, v2)
        assert len(merged["plan"]) == 2


class TestViewAnd:
    def test_and_same_table(self):
        v1: View = {"plan": [(["content", "month"], TRUE_CONDITION)]}
        v2: View = {"plan": [(["content", "done"], TRUE_CONDITION)]}
        merged = view_and(v1, v2)
        assert "plan" in merged
        cols, flt = merged["plan"][0]
        assert sorted(cols) == ["content"]

    def test_and_no_common_table(self):
        v1: View = {"plan": [(["content"], TRUE_CONDITION)]}
        v2: View = {"diary": [(["date"], TRUE_CONDITION)]}
        merged = view_and(v1, v2)
        assert merged == {}


class TestViewClean:
    def test_clean_columns_removes_disallowed(self):
        view: View = {"plan": [(["content"], TRUE_CONDITION)]}
        entries = [{"content": "ok", "secret_field": "secret"}]
        cleaned = view_clean_columns(view, "plan", entries)
        assert "content" in cleaned[0]
        assert "secret_field" not in cleaned[0]

    def test_clean_filter_combines_with_view_filter(self):
        view: View = {"plan": [(["content"], Condition("month", "2606", "="))]}
        user_filter = Condition("done", 0, "=")
        combined = view_clean_filter(view, "plan", user_filter)
        assert isinstance(combined, list)

    def test_clean_update(self):
        view: View = {"plan": [(["content", "done"], TRUE_CONDITION)]}
        pairs = view_clean_update(view, "plan", TRUE_CONDITION, {"content": "new", "secret": "x"})
        assert len(pairs) == 1
        combined_filter, cleaned_values = pairs[0]
        assert "content" in cleaned_values
        assert "secret" not in cleaned_values


class TestRootPermission:
    def test_root_permission_covers_all_tables(self, db):
        rv, wv = root_permission(db)
        for table in db.table_infos:
            assert table in rv
            assert table in wv

    def test_root_permission_all_columns(self, db):
        rv, wv = root_permission(db)
        for table, cols in db.table_infos.items():
            spec_cols = rv[table][0][0]
            assert len(spec_cols) == len(cols)


class TestNoView:
    def test_no_view_contains_all_tables(self, db):
        nv = no_view(db)
        for table in db.table_infos:
            assert table in nv

    def test_no_view_empty_columns(self, db):
        nv = no_view(db)
        for table in db.table_infos:
            cols, flt = nv[table][0]
            assert cols == []

    def test_no_view_false_condition(self, db):
        nv = no_view(db)
        for table in db.table_infos:
            _, flt = nv[table][0]
            assert flt == FALSE_CONDITION


class TestNoPermission:
    def test_no_permission_returns_two_views(self, db):
        rv, wv = no_permission(db)
        for table in db.table_infos:
            assert table in rv
            assert table in wv

    def test_no_permission_empty_columns(self, db):
        rv, wv = no_permission(db)
        for table in db.table_infos:
            rcols, _ = rv[table][0]
            wcols, _ = wv[table][0]
            assert rcols == []
            assert wcols == []

    def test_no_permission_query_returns_nothing(self, registry, db):
        nb = registry["plan"]
        with db.transaction() as conn:
            nb.add(conn, [{"content": "secret", "month": "2606"}])
        rv, _ = no_permission(db)
        sql, params = view_to_sql(rv, db, "plan")
        with db.transaction() as conn:
            rows = conn.execute(sql, params).fetchall()
        assert len(rows) == 0


class TestViewSerialization:
    def test_view_to_json_roundtrip(self, db):
        view: View = {"plan": [(["content", "month"], TRUE_CONDITION)]}
        js = view_to_json(view)
        assert "plan" in js
        assert js["plan"][0]["columns"] == ["content", "month"]

    def test_parse_view_json(self):
        s = '{"plan": [{"columns": ["content", "month"], "filter": {"column": "_", "value": null, "op": "TRUE"}}]}'
        view = parse_view_json(s)
        assert "plan" in view
        assert len(view["plan"]) == 1
