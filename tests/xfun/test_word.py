"""测试 word 本子。"""

import pytest
from xfun.core.errors import EntryInvalidError


class TestWordNotebook:
    def test_add_word(self, db, registry):
        entry = {"content": "apple", "word": "apple", "part_of_speech": "noun"}
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "word", [entry])
        assert len(ids) == 1
        with db.read_transaction() as conn:
            row = conn.execute("SELECT word, part_of_speech FROM word WHERE id = ?", (ids[0],)).fetchone()
        assert row["word"] == "apple"
        assert row["part_of_speech"] == "noun"

    def test_review_count_defaults_to_zero(self, db, registry):
        entry = {"content": "run", "word": "run", "part_of_speech": "verb"}
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "word", [entry])
        with db.read_transaction() as conn:
            row = conn.execute("SELECT review_count FROM word WHERE id = ?", (ids[0],)).fetchone()
        assert row["review_count"] == 0

    def test_query_by_word(self, db, registry):
        entry = {"content": "apple", "word": "apple", "part_of_speech": "noun"}
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "word", [entry])
        with db.read_transaction() as conn:
            rows = conn.execute("SELECT * FROM word WHERE word = 'apple'").fetchall()
        assert len(rows) == 1
        assert rows[0]["part_of_speech"] == "noun"

    def test_missing_word_raises(self, db, registry):
        entry = {"content": "test"}
        with pytest.raises(EntryInvalidError, match="缺少必填字段 'word'"):
            with db.transaction() as conn:
                conn.db.add_entries(conn, "word", [entry])

