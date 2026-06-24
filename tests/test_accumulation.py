"""测试 AccumulationNotebook。"""

import pytest

from xfun.core.filter import Condition


class TestAccumulationNotebook:
    def test_add_accumulation(self, registry, db):
        nb = registry["accumulation"]
        with db.transaction() as conn:
            ids = nb.add(conn, [{
                "content": "Python 列表推导式",
                "category": "Python",
                "source": "官方文档",
                "note": "很实用的语法糖",
            }])
        assert len(ids) == 1
        assert ids[0].startswith("accumulation-")

    def test_missing_category_raises(self, registry, db):
        nb = registry["accumulation"]
        with db.transaction() as conn:
            with pytest.raises(Exception):
                nb.add(conn, [{"content": "no category"}])

    def test_query_by_category(self, registry, db):
        nb = registry["accumulation"]
        with db.transaction() as conn:
            nb.add(conn, [
                {"content": "Python tip", "category": "Python"},
                {"content": "JS tip", "category": "JavaScript"},
                {"content": "Python OOP", "category": "Python"},
            ])
        with db.transaction() as conn:
            ids = nb.list_ids(conn, [[Condition("category", "Python", "=")]])
        assert len(ids) == 2

    def test_source_and_note_optional(self, registry, db):
        nb = registry["accumulation"]
        with db.transaction() as conn:
            ids = nb.add(conn, [{"content": "just a note", "category": "misc"}])
        with db.transaction() as conn:
            row = nb.get_by_ids(conn, ids)[0]
        assert row["source"] is None
        assert row["note"] is None
