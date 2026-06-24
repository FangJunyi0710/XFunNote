"""测试 view.py：View 构建、SQL 生成与集合操作。"""

import json
import pytest

from xfun.core.db import DB, Column
from xfun.core.filter import Condition, TRUE_CONDITION
from xfun.core.view import (
    View,
    TableSpec,
    parse_view_json,
    view_to_sql,
    view_to_json,
    view_or,
    view_and,
    view_clean_columns,
    view_clean_filter,
    view_clean_update,
    _TableSpec_and,
    _clean_entry,
)


@pytest.fixture
def db_with_tables(tmp_path):
    """带 plan 和 diary 两个表的数据库。"""
    db = DB(db_path=str(tmp_path / "test_view.db"))
    db.init({
        "plan": [
            Column("id", "TEXT", primary_key=True, nullable=False),
            Column("content", "TEXT", nullable=False),
            Column("month", "TEXT"),
            Column("seq", "INTEGER"),
            Column("done", "INTEGER"),
        ],
        "diary": [
            Column("id", "TEXT", primary_key=True, nullable=False),
            Column("content", "TEXT", nullable=False),
            Column("date", "TEXT"),
            Column("mood", "TEXT"),
        ],
    })
    # 插入样本数据
    with db.transaction() as conn:
        for row in [
            {"id": "p1", "content": "plan A", "month": "2606", "seq": 1, "done": 0},
            {"id": "p2", "content": "plan B", "month": "2606", "seq": 2, "done": 1},
            {"id": "p3", "content": "plan C", "month": "2607", "seq": 1, "done": 0},
        ]:
            conn.execute(db.insert_sql("plan"), row)
        for row in [
            {"id": "d1", "content": "diary X", "date": "2026-06-01", "mood": "happy"},
            {"id": "d2", "content": "diary Y", "date": "2026-06-02", "mood": "sad"},
        ]:
            conn.execute(db.insert_sql("diary"), row)
    return db


# =====================================================================
# parse_view_json
# =====================================================================

class TestParseViewJson:
    def test_single_table_single_spec(self):
        """单个表、单个 TableSpec。"""
        view = parse_view_json("""
        {
            "plan": [
                {"columns": ["content", "month"],
                 "filter": [[{"column": "month", "value": "2606"}]]}
            ]
        }
        """)
        assert list(view) == ["plan"]
        assert len(view["plan"]) == 1
        cols, flt = view["plan"][0]
        assert cols == ["content", "month"]
        # Filter 结构: [[Condition("month","2606")]] → OR((AND(month='2606')))
        assert isinstance(flt, list) and len(flt) == 1
        assert isinstance(flt[0], list) and len(flt[0]) == 1
        assert flt[0][0] == Condition("month", "2606")

    def test_multiple_specs(self):
        """单个表、多个 TableSpec。"""
        view = parse_view_json("""
        {
            "plan": [
                {"columns": ["content", "month"],
                 "filter": [[{"column": "month", "value": "2606"}]]},
                {"columns": ["done"],
                 "filter": [[{"column": "done", "value": 1}]]}
            ]
        }
        """)
        assert len(view["plan"]) == 2
        assert view["plan"][0][0] == ["content", "month"]
        assert view["plan"][1][0] == ["done"]

    def test_multiple_tables(self):
        """多个表。"""
        view = parse_view_json("""
        {
            "plan": [
                {"columns": ["content"], "filter": [[{"column": "month", "value": "2606"}]]}
            ],
            "diary": [
                {"columns": ["date", "mood"], "filter": [[{"column": "date", "value": "2026-06-01"}]]}
            ]
        }
        """)
        assert set(view) == {"plan", "diary"}
        assert len(view["plan"]) == 1
        assert len(view["diary"]) == 1

    def test_empty_dict(self):
        """空 JSON 对象。"""
        view = parse_view_json("{}")
        assert view == {}

    def test_filter_with_negate_tuple(self):
        """Filter 含取反元组。"""
        view = parse_view_json("""
        {
            "plan": [
                {"columns": ["id"],
                 "filter": [[[{"column": "month", "value": "2606"}, true]]]}
            ]
        }
        """)
        _, flt = view["plan"][0]
        # flt = [[(Condition, True)]] 即 NOT(month='2606')
        assert isinstance(flt[0][0], tuple)
        inner, negate = flt[0][0]
        assert negate is True
        assert inner == Condition("month", "2606")

    def test_filter_with_custom_op(self):
        """Filter 含自定义操作符。"""
        view = parse_view_json("""
        {
            "plan": [
                {"columns": ["seq"],
                 "filter": [[{"column": "seq", "op": ">=", "value": 5}]]}
            ]
        }
        """)
        _, flt = view["plan"][0]
        assert flt[0][0] == Condition("seq", 5, ">=")

    def test_filter_and_group(self):
        """Filter 含多个 AND 条件。"""
        view = parse_view_json("""
        {
            "plan": [
                {"columns": ["content"],
                 "filter": [[{"column": "month", "value": "2606"},
                             {"column": "done", "value": 1}]]}
            ]
        }
        """)
        _, flt = view["plan"][0]
        # flt = [[Condition("month","2606"), Condition("done",1)]]
        group = flt[0]
        assert len(group) == 2
        assert group[0] == Condition("month", "2606")
        assert group[1] == Condition("done", 1)

    def test_filter_or_groups(self):
        """Filter 含多个 OR 组。"""
        view = parse_view_json("""
        {
            "plan": [
                {"columns": ["content"],
                 "filter": [[{"column": "month", "value": "2606"}],
                            [{"column": "month", "value": "2607"}]]}
            ]
        }
        """)
        _, flt = view["plan"][0]
        assert len(flt) == 2  # OR of two groups
        assert flt[0][0] == Condition("month", "2606")
        assert flt[1][0] == Condition("month", "2607")

    def test_invalid_json(self):
        """非法 JSON 字符串。"""
        with pytest.raises(json.JSONDecodeError):
            parse_view_json("not json")

    def test_missing_keys(self):
        """spec 缺少 'columns' 或 'filter'。"""
        with pytest.raises(KeyError):
            parse_view_json("""
            {"plan": [{"columns": ["id"]}]}
            """)
        with pytest.raises(KeyError):
            parse_view_json("""
            {"plan": [{"filter": [[{"column": "id", "value": "1"}]]}]}
            """)


# =====================================================================
# view_to_sql
# =====================================================================

class TestViewToSql:
    def test_table_not_in_view(self, db_with_tables):
        """表不在 View 中返回空。"""
        view: View = {}
        sql, params = view_to_sql(view, db_with_tables, "plan")
        assert sql == ""
        assert params == []

    def test_table_not_in_db(self, db_with_tables):
        """表不在数据库中返回空。"""
        view: View = {"unknown": [(["id"], [[Condition("id", "1")]])]}
        sql, params = view_to_sql(view, db_with_tables, "unknown")
        assert sql == ""
        assert params == []

    def test_single_spec_contains_expected_keywords(self, db_with_tables):
        """单 TableSpec 生成的 SQL 含有关键字。"""
        view: View = {
            "plan": [(["content", "month"], [[Condition("month", "2606")]])]
        }
        sql, params = view_to_sql(view, db_with_tables, "plan")
        assert "SELECT" in sql
        assert "FROM" in sql
        assert "WHERE" in sql
        assert "UNION ALL" in sql  # 1×WHERE 1=0 + 1×spec → 2 subqueries
        assert "GROUP BY" in sql
        assert "id" in sql
        assert params == ["2606"]

    def test_multiple_specs_produce_union(self, db_with_tables):
        """多 TableSpec 产生 UNION ALL。"""
        view: View = {
            "plan": [
                (["content", "month"], [[Condition("month", "2606")]]),
                (["done"], [[Condition("done", 1)]]),
            ]
        }
        sql, params = view_to_sql(view, db_with_tables, "plan")
        assert "UNION ALL" in sql
        # 1s(WHERE 1=0) + 2 个 specs = 3 个子查询
        assert sql.count("UNION ALL") == 2
        assert len(params) == 2

    def test_sql_executes_returns_rows(self, db_with_tables):
        """生成的 SQL 可执行并返回正确数据。"""
        view: View = {
            "plan": [(["content", "month"], [[Condition("month", "2606")]])]
        }
        sql, params = view_to_sql(view, db_with_tables, "plan")
        with db_with_tables.read_transaction() as conn:
            rows = conn.execute(sql, params).fetchall()
        assert len(rows) == 2  # plan A and plan B
        results = {r["id"]: dict(r) for r in rows}
        assert results["p1"]["content"] == "plan A"
        assert results["p1"]["month"] == "2606"
        assert results["p2"]["content"] == "plan B"
        assert results["p2"]["month"] == "2606"

    def test_sql_executes_with_empty_filter(self, db_with_tables):
        """无条件 Filter 查询所有行。"""
        view: View = {
            "plan": [(["content"], [[Condition("month", "nonexistent")]])]
        }
        sql, params = view_to_sql(view, db_with_tables, "plan")
        with db_with_tables.read_transaction() as conn:
            rows = conn.execute(sql, params).fetchall()
        assert len(rows) == 0

    def test_sql_executes_different_table(self, db_with_tables):
        """在不同表上执行。"""
        view: View = {
            "diary": [(["content", "mood"], [[Condition("mood", "happy")]])]
        }
        sql, params = view_to_sql(view, db_with_tables, "diary")
        with db_with_tables.read_transaction() as conn:
            rows = conn.execute(sql, params).fetchall()
        assert len(rows) == 1
        assert rows[0]["content"] == "diary X"

    def test_sql_empty_specs(self, db_with_tables):
        """TableSpec 列表为空时生成仅含 WHERE 1=0 的 SQL。"""
        view: View = {"plan": []}
        sql, params = view_to_sql(view, db_with_tables, "plan")
        # 不应包含 UNION ALL（只有 1s WHERE 1=0）
        assert "UNION ALL" not in sql
        assert params == []


# =====================================================================
# view_or
# =====================================================================

class TestViewOr:
    def test_disjoint_tables(self):
        """不同表的 View 合并。"""
        v1: View = {"plan": [(["content"], [[Condition("month", "2606")]])]}
        v2: View = {"diary": [(["date"], [[Condition("date", "2026-06-01")]])]}
        merged = view_or(v1, v2)
        assert set(merged) == {"plan", "diary"}
        assert len(merged["plan"]) == 1
        assert len(merged["diary"]) == 1

    def test_same_table(self):
        """相同表的 TableSpec 合并。"""
        spec1 = (["content"], [[Condition("month", "2606")]])
        spec2 = (["done"], [[Condition("done", 1)]])
        v1: View = {"plan": [spec1]}
        v2: View = {"plan": [spec2]}
        merged = view_or(v1, v2)
        assert list(merged) == ["plan"]
        assert len(merged["plan"]) == 2
        assert merged["plan"][0] == spec1
        assert merged["plan"][1] == spec2

    def test_empty_view(self):
        """与空 View 合并。"""
        v1: View = {"plan": [(["content"], [[Condition("month", "2606")]])]}
        merged = view_or(v1, {})
        assert merged == v1

    def test_both_empty(self):
        """两个空 View 合并。"""
        assert view_or({}, {}) == {}


# =====================================================================
# view_and
# =====================================================================

class TestViewAnd:
    def test_no_shared_table(self):
        """没有共同表 → 空 View。"""
        v1: View = {"plan": [(["content"], [[Condition("month", "2606")]])]}
        v2: View = {"diary": [(["date"], [[Condition("date", "2026-06-01")]])]}
        assert view_and(v1, v2) == {}

    def test_shared_table_single_spec(self):
        """共同表各一个 TableSpec。"""
        v1: View = {"plan": [(["content", "month"], [[Condition("month", "2606")]])]}
        v2: View = {"plan": [(["content", "done"], [[Condition("done", 1)]])]}
        merged = view_and(v1, v2)
        assert list(merged) == ["plan"]
        assert len(merged["plan"]) == 1
        cols, flt = merged["plan"][0]
        # 列取交集
        assert set(cols) == {"content"}
        # Filter AND 组合: [[Condition("month","2606"), Condition("done",1)]]
        assert len(flt) == 1
        assert len(flt[0]) == 2

    def test_shared_table_cartesian_product(self):
        """共同表多个 TableSpec 时做笛卡尔积。"""
        v1: View = {"plan": [
            (["content", "month"], [[Condition("month", "2606")]]),
            (["content", "month"], [[Condition("month", "2607")]]),
        ]}
        v2: View = {"plan": [
            (["content", "done"], [[Condition("done", 1)]]),
        ]}
        merged = view_and(v1, v2)
        assert len(merged["plan"]) == 2


# =====================================================================
# _TableSpec_and
# =====================================================================

class TestTableSpecAnd:
    def test_columns_intersection(self):
        """列名取交集。"""
        spec1: TableSpec = (["a", "b", "c"], [[Condition("a", 1)]])
        spec2: TableSpec = (["b", "c", "d"], [[Condition("b", 2)]])
        cols, flt = _TableSpec_and(spec1, spec2)
        assert set(cols) == {"b", "c"}

    def test_no_shared_columns(self):
        """没有共同列 → 空列列表。"""
        spec1: TableSpec = (["a"], [[Condition("a", 1)]])
        spec2: TableSpec = (["b"], [[Condition("b", 2)]])
        cols, flt = _TableSpec_and(spec1, spec2)
        assert cols == []

    def test_filter_combined_as_and(self):
        """两个 Filter 以 AND 组合。"""
        flt1 = [[Condition("a", 1)]]
        flt2 = [[Condition("b", 2)]]
        spec1: TableSpec = (["a"], flt1)
        spec2: TableSpec = (["b"], flt2)
        _, flt = _TableSpec_and(spec1, spec2)
        # AND 组合: [[f1, f2]] → OR((AND(f1, f2)))
        assert flt == [[flt1, flt2]]


# =====================================================================
# view_to_json
# =====================================================================

class TestViewToJson:
    def test_single_table(self):
        """单表 View 序列化为 dict。"""
        view: View = {"plan": [(["content", "month"], [[Condition("month", "2606")]])]}
        result = view_to_json(view)
        assert "plan" in result
        assert len(result["plan"]) == 1
        spec = result["plan"][0]
        assert spec["columns"] == ["content", "month"]
        assert spec["filter"] == [[{"column": "month", "value": "2606", "op": "="}]]

    def test_multiple_tables(self):
        """多表 View 序列化。"""
        view: View = {
            "plan": [(["content"], [[Condition("month", "2606")]])],
            "diary": [(["date"], [[Condition("date", "2026-06-01")]])],
        }
        result = view_to_json(view)
        assert set(result) == {"plan", "diary"}

    def test_multiple_specs(self):
        """多 TableSpec 序列化。"""
        view: View = {
            "plan": [
                (["content"], [[Condition("month", "2606")]]),
                (["done"], [[Condition("done", 1)]]),
            ]
        }
        result = view_to_json(view)
        assert len(result["plan"]) == 2

    def test_empty_view(self):
        """空 View。"""
        assert view_to_json({}) == {}

    def test_true_condition(self):
        """TRUE_CONDITION 序列化。"""
        view: View = {"plan": [(["content"], TRUE_CONDITION)]}
        result = view_to_json(view)
        assert result["plan"][0]["filter"] == {"column": "_", "value": None, "op": "TRUE"}

    def test_json_serializable(self):
        """返回的 dict 可被 json.dumps 正常处理。"""
        view: View = {"plan": [(["content"], [[Condition("month", "2606"), Condition("done", 1)]])]}
        raw = view_to_json(view)
        dumped = json.dumps(raw, ensure_ascii=False)
        assert isinstance(dumped, str)
        assert "month" in dumped
        assert "2606" in dumped


# =====================================================================
# _clean_entry / view_add / view_delete / view_update
# =====================================================================

def make_view() -> View:
    return {
        "plan": [
            (["content", "month"], [[Condition("month", "2606")]]),
            (["content", "done"], [[Condition("done", 1)]]),
        ]
    }

class TestCleanEntry:
    def test_keep_allowed(self):
        """仅保留允许的列。"""
        entry = {"content": "hello", "month": "2606", "done": 1, "extra": "x"}
        result = _clean_entry(entry, {"content", "month"})
        assert result == {"content": "hello", "month": "2606"}

    def test_empty_allowed(self):
        """允许列为空 → 空 dict。"""
        assert _clean_entry({"a": 1}, set()) == {}


class TestViewAdd:
    def test_clean_against_view(self):
        """entries 按视图列白名单（所有 spec 的并集）清洗。"""
        cleaned = view_clean_columns(make_view(), "plan", [
            {"content": "A", "month": "2606", "done": 1, "extra": "x"},
            {"content": "B", "done": 0},
        ])
        assert len(cleaned) == 2
        # 白名单 = {"content", "month", "done"}（所有 spec 列的并集）
        assert cleaned[0] == {"content": "A", "month": "2606", "done": 1}
        assert cleaned[1] == {"content": "B", "done": 0}


class TestViewDelete:
    def test_merge_filters(self):
        """view_delete 将用户 filter 与视图 filter AND 组合。"""
        merged = view_clean_filter(make_view(), "plan", [[Condition("content", "A", "LIKE")]])
        # 结果: [[user_filter, [[spec1_filter], [spec2_filter]]]]
        assert len(merged) == 1
        assert merged[0][0] == [[Condition("content", "A", "LIKE")]]
        assert len(merged[0][1]) == 2


class TestViewUpdate:
    def test_expand_per_spec(self):
        """view_update 按每个 spec 展开为 (filter, values) 对。"""
        results = view_clean_update(make_view(), "plan", [[Condition("done", 1)]], {"content": "updated", "extra": "x"})
        assert len(results) == 2  # 两个 spec，各产生一组 (filter, values)
        # spec 1: 列白名单 {"content", "month"} + filter = AND(原 filter, 用户 filter)
        flt1, vals1 = results[0]
        assert vals1 == {"content": "updated"}
        # spec 2: 列白名单 {"content", "done"} + filter = AND(原 filter, 用户 filter)
        flt2, vals2 = results[1]
        assert vals2 == {"content": "updated"}
        # 两个 filter 都应包含用户传入的 Condition
        for flt, _ in results:
            assert isinstance(flt, list)
            # flt 结构: AND(原 spec filter, 用户 filter)
            spec_filters = flt[0]
            assert len(spec_filters) == 2
