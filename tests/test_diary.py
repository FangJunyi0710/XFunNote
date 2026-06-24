"""测试 DiaryNotebook：_autofill、ID 格式、date 必填。"""

import pytest
from xfun.core.errors import EntryInvalidError
from xfun.notebooks.diary import DiaryNotebook


@pytest.fixture
def diary_nb():
    return DiaryNotebook()


class TestDiaryAutofill:
    """diary _autofill 的核心行为。"""

    def test_explicit_date(self, db, diary_nb):
        db.init({diary_nb.name: diary_nb.columns})
        with db.transaction() as conn:
            ids = diary_nb.add(conn, [
                {"date": "2026-06-18", "content": "今天学习了Python"},
            ])
        with db.read_transaction() as conn:
            results = diary_nb.get_by_ids(conn, ids)
        assert results[0]["date"] == "2026-06-18"
        assert results[0]["content"] == "今天学习了Python"

    def test_id_format(self, db, diary_nb):
        db.init({diary_nb.name: diary_nb.columns})
        with db.transaction() as conn:
            ids = diary_nb.add(conn, [
                {"date": "2026-07-01", "content": "暑假第一天"},
            ])
        with db.read_transaction() as conn:
            results = diary_nb.get_by_ids(conn, ids)
        assert ids[0].startswith("diary-")
        assert results[0]["date"] == "2026-07-01"

    def test_optional_fields(self, db, diary_nb):
        """mood、weather 为可选字段，提供时入库、不提供时为 None。"""
        db.init({diary_nb.name: diary_nb.columns})
        with db.transaction() as conn:
            ids = diary_nb.add(conn, [
                {"date": "2026-06-18", "content": "今日无事", "mood": "平静", "weather": "阴"},
                {"date": "2026-06-19", "content": "只有内容"},
            ])
        with db.read_transaction() as conn:
            results = diary_nb.get_by_ids(conn, ids)
        assert results[0]["mood"] == "平静"
        assert results[0]["weather"] == "阴"
        assert results[1]["mood"] is None
        assert results[1]["weather"] is None

    def test_date_missing_raises(self, db, diary_nb):
        """date 是必填字段，缺少时抛 EntryInvalidError。"""
        db.init({diary_nb.name: diary_nb.columns})
        with db.transaction() as conn:
            with pytest.raises(EntryInvalidError, match="date"):
                diary_nb.add(conn, [{"content": "没有日期"}])
