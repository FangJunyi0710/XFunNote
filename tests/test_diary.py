"""测试 DiaryNotebook。"""

import pytest

from xfun.core.filter import Condition


class TestDiaryNotebook:
    def test_add_diary(self, registry, db):
        nb = registry["diary"]
        with db.transaction() as conn:
            ids = nb.add(conn, [{
                "content": "今日心情不错",
                "date": "2026-06-01",
                "mood": "开心",
                "weather": "晴",
            }])
        assert len(ids) == 1
        assert ids[0].startswith("diary-")

    def test_missing_date_raises(self, registry, db):
        nb = registry["diary"]
        with db.transaction() as conn:
            with pytest.raises(Exception):
                nb.add(conn, [{"content": "no date"}])

    def test_query_by_date(self, registry, db):
        nb = registry["diary"]
        with db.transaction() as conn:
            nb.add(conn, [
                {"content": "d1", "date": "2026-06-01"},
                {"content": "d2", "date": "2026-06-02"},
                {"content": "d3", "date": "2026-06-01"},
            ])
        with db.transaction() as conn:
            ids = nb.list_ids(conn, [[Condition("date", "2026-06-01", "=")]])
        assert len(ids) == 2

    def test_mood_and_weather_optional(self, registry, db):
        nb = registry["diary"]
        with db.transaction() as conn:
            ids = nb.add(conn, [{
                "content": "just a note",
                "date": "2026-06-03",
            }])
        with db.transaction() as conn:
            row = nb.get_by_ids(conn, ids)[0]
        assert row["mood"] is None
        assert row["weather"] is None
