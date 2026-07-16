"""测试 ScheduleNotebook — 日程本。"""

import pytest

from xfun.core.filter import Condition


class TestScheduleNotebook:
    def test_add_entry(self, registry, db):
        nb = registry["schedule"]
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "schedule", [{
                "content": "开会",
                "start_time": "2026-07-14 10:00:00+08:00",
                "end_time": "2026-07-14 11:00:00+08:00",
                "location": "会议室A",
            }])
        assert len(ids) == 1
        assert ids[0].startswith("schedule-")

    def test_missing_start_time_raises(self, registry, db):
        with db.transaction() as conn:
            with pytest.raises(Exception):
                conn.db.add_entries(conn, "schedule", [{"content": "no start_time"}])

    def test_query_by_start_time(self, registry, db):
        with db.transaction() as conn:
            conn.db.add_entries(conn, "schedule", [
                {"content": "晨会", "start_time": "2026-07-14 09:00:00+08:00"},
                {"content": "评审", "start_time": "2026-07-14 14:00:00+08:00"},
            ])
        with db.transaction() as conn:
            ids = conn.db.list_ids(conn, "schedule", [[Condition("start_time", "2026-07-14 09:00:00+08:00", "=")]])
        assert len(ids) == 1

    def test_location_optional(self, registry, db):
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "schedule", [{
                "content": "冥想",
                "start_time": "2026-07-14 07:00:00+08:00",
            }])
        with db.transaction() as conn:
            row = dict(conn.execute(
                "SELECT * FROM schedule WHERE id = ?", ids
            ).fetchone())
        assert row["location"] is None
        assert row["end_time"] is None

    def test_end_time_optional(self, registry, db):
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "schedule", [{
                "content": "打卡",
                "start_time": "2026-07-14 08:00:00+08:00",
            }])
        with db.transaction() as conn:
            row = dict(conn.execute(
                "SELECT * FROM schedule WHERE id = ?", ids
            ).fetchone())
        assert row["end_time"] is None

    def test_query_by_location(self, registry, db):
        with db.transaction() as conn:
            conn.db.add_entries(conn, "schedule", [
                {"content": "开会", "start_time": "2026-07-14 10:00:00+08:00", "location": "会议室A"},
                {"content": "面试", "start_time": "2026-07-14 14:00:00+08:00", "location": "会议室A"},
                {"content": "健身", "start_time": "2026-07-14 18:00:00+08:00", "location": "健身房"},
            ])
        with db.transaction() as conn:
            ids = conn.db.list_ids(conn, "schedule", [[Condition("location", "会议室A", "=")]])
        assert len(ids) == 2
