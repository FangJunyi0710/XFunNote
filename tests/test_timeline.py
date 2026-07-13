"""测试 TimelineNotebook — 时间线本。"""

import pytest

from xfun.core.filter import Condition


class TestTimelineNotebook:
    def test_add_entry(self, registry, db):
        nb = registry["timeline"]
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "timeline", [{
                "content": "写代码",
                "start_time": "2026-07-13 09:00:00+08:00",
                "end_time": "2026-07-13 12:00:00+08:00",
                "location": "办公室",
            }])
        assert len(ids) == 1
        assert ids[0].startswith("timeline-")

    def test_missing_start_time_raises(self, registry, db):
        with db.transaction() as conn:
            with pytest.raises(Exception):
                conn.db.add_entries(conn, "timeline", [{"content": "no start_time"}])

    def test_query_by_start_time(self, registry, db):
        with db.transaction() as conn:
            conn.db.add_entries(conn, "timeline", [
                {"content": "晨会", "start_time": "2026-07-13 09:00:00+08:00"},
                {"content": "午休", "start_time": "2026-07-13 12:00:00+08:00"},
            ])
        with db.transaction() as conn:
            ids = conn.db.list_ids(conn, "timeline", [[Condition("start_time", "2026-07-13 09:00:00+08:00", "=")]])
        assert len(ids) == 1

    def test_location_optional(self, registry, db):
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "timeline", [{
                "content": "冥想",
                "start_time": "2026-07-13 07:00:00+08:00",
            }])
        with db.transaction() as conn:
            row = dict(conn.execute(
                "SELECT * FROM timeline WHERE id = ?", ids
            ).fetchone())
        assert row["location"] is None
        assert row["end_time"] is None

    def test_end_time_optional(self, registry, db):
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "timeline", [{
                "content": "打卡",
                "start_time": "2026-07-13 08:00:00+08:00",
            }])
        with db.transaction() as conn:
            row = dict(conn.execute(
                "SELECT * FROM timeline WHERE id = ?", ids
            ).fetchone())
        assert row["end_time"] is None

    def test_query_by_location(self, registry, db):
        with db.transaction() as conn:
            conn.db.add_entries(conn, "timeline", [
                {"content": "写代码", "start_time": "2026-07-13 09:00:00+08:00", "location": "办公室"},
                {"content": "午饭", "start_time": "2026-07-13 12:00:00+08:00", "location": "食堂"},
                {"content": "写代码", "start_time": "2026-07-14 09:00:00+08:00", "location": "办公室"},
            ])
        with db.transaction() as conn:
            ids = conn.db.list_ids(conn, "timeline", [[Condition("location", "办公室", "=")]])
        assert len(ids) == 2
