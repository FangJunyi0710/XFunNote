"""测试自定义运算符（JSON_CONTAINS / TEXT_SEARCH / TRUE / FALSE）。"""

from xfun.core.filter import Condition, filter_to_sql, TRUE_CONDITION, FALSE_CONDITION


class TestJsonContains:
    def test_json_contains(self):
        cond = Condition("tags", "Python", "JSON_CONTAINS")
        sql, params = cond.to_sql()
        assert "json_each(tags)" in sql
        assert params == ["Python"]

    def test_json_not_contains(self):
        cond = Condition("tags", "私密", "JSON_NOT_CONTAINS")
        sql, params = cond.to_sql()
        assert "NOT EXISTS" in sql
        assert "json_each(tags)" in sql
        assert params == ["私密"]


class TestTextSearch:
    def test_text_search(self):
        cond = Condition("content", "关键字", "TEXT_SEARCH")
        sql, params = cond.to_sql()
        assert sql == "content LIKE ?"
        assert params == ["%关键字%"]


class TestTrueFalse:
    def test_true_condition(self):
        sql, params = TRUE_CONDITION.to_sql()
        assert sql == "1=1"
        assert params == []

    def test_false_condition(self):
        sql, params = FALSE_CONDITION.to_sql()
        assert sql == "1=0"
        assert params == []

    def test_true_in_filter(self):
        sql, params = filter_to_sql([[TRUE_CONDITION]])
        # filter_to_sql([[TRUE_CONDITION]]) → ((1=1))
        assert "(1=1)" in sql

    def test_false_in_filter(self):
        sql, params = filter_to_sql([[FALSE_CONDITION]])
        assert "(1=0)" in sql

    def test_true_with_other_condition(self):
        sql, params = filter_to_sql([[Condition("a", 1), TRUE_CONDITION]])
        assert "(a = ?) AND (1=1)" in sql
        assert params == [1]

    def test_false_with_other_condition(self):
        sql, params = filter_to_sql([[Condition("a", 1), FALSE_CONDITION]])
        assert "(a = ?) AND (1=0)" in sql
        assert params == [1]

    def test_true_condition_direct_to_sql(self):
        sql, params = TRUE_CONDITION.to_sql()
        assert sql == "1=1"
        assert params == []

    def test_false_condition_direct_to_sql(self):
        sql, params = FALSE_CONDITION.to_sql()
        assert sql == "1=0"
        assert params == []
