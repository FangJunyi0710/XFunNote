"""测试 WordNotebook — 单词复习跟踪。"""

import pytest

from xfun.core.filter import Condition


class TestWordNotebook:
    def test_add_word(self, registry, db):
        nb = registry["word"]
        with db.transaction() as conn:
            ids = nb.add(conn, [{
                "content": "apple",
                "word": "apple",
                "part_of_speech": "noun",
                "phonetic": "/ˈæp.əl/",
            }])
        assert len(ids) == 1
        assert ids[0].startswith("word-")

    def test_review_count_defaults_to_zero(self, registry, db):
        nb = registry["word"]
        with db.transaction() as conn:
            ids = nb.add(conn, [{"content": "run", "word": "run"}])
        with db.transaction() as conn:
            row = nb.get_by_ids(conn, ids)[0]
        assert row["review_count"] == 0

    def test_performance_defaults_to_zero(self, registry, db):
        nb = registry["word"]
        with db.transaction() as conn:
            ids = nb.add(conn, [{"content": "book", "word": "book"}])
        with db.transaction() as conn:
            row = nb.get_by_ids(conn, ids)[0]
        assert row["performance"] == 0.0

    def test_query_by_word(self, registry, db):
        nb = registry["word"]
        with db.transaction() as conn:
            nb.add(conn, [
                {"content": "apple", "word": "apple"},
                {"content": "banana", "word": "banana"},
            ])
        with db.transaction() as conn:
            ids = nb.list_ids(conn, [[Condition("word", "apple", "=")]])
        assert len(ids) == 1

    def test_missing_word_raises(self, registry, db):
        nb = registry["word"]
        with db.transaction() as conn:
            with pytest.raises(Exception):
                nb.add(conn, [{"content": "missing word field"}])

    def test_update_review_count(self, registry, db):
        nb = registry["word"]
        with db.transaction() as conn:
            ids = nb.add(conn, [{"content": "test", "word": "test"}])
        with db.transaction() as conn:
            nb.update(conn, ids, {"review_count": 1, "performance": 0.5})
        with db.transaction() as conn:
            row = nb.get_by_ids(conn, ids)[0]
        assert row["review_count"] == 1
        assert row["performance"] == 0.5
