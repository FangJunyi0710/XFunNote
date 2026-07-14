"""测试 AccumulationNotebook。"""

import pytest

from xfun.core.filter import Condition


class TestAccumulationNotebook:
    def test_add_accumulation(self, registry, db):
        nb = registry["accumulation"]
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "accumulation", [{
                "content": "Python 列表推导式",
                "source": "官方文档",
                "note": "很实用的语法糖",
            }])
        assert len(ids) == 1
        assert ids[0].startswith("accumulation-")

    def test_query_by_source(self, registry, db):
        nb = registry["accumulation"]
        with db.transaction() as conn:
            conn.db.add_entries(conn, "accumulation", [
                {"content": "Python tip", "source": "博客"},
                {"content": "JS tip", "source": "书籍"},
                {"content": "Python OOP", "source": "博客"},
            ])
        with db.transaction() as conn:
            ids = conn.db.list_ids(conn, "accumulation", [[Condition("source", "博客", "=")]])
        assert len(ids) == 2

    def test_source_and_note_optional(self, registry, db):
        nb = registry["accumulation"]
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "accumulation", [{"content": "just a note"}])
        with db.transaction() as conn:
            row = dict(conn.execute(
                "SELECT * FROM accumulation WHERE id = ?",
                ids,
            ).fetchone())
        assert row["source"] is None
        assert row["note"] is None
