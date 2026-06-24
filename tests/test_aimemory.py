"""测试 AIMemoryNotebook：标题必填、ID 格式、可选字段。"""

import pytest
from xfun.core.errors import EntryInvalidError
from xfun.notebooks.aimemory import AIMemoryNotebook


@pytest.fixture
def aimem_nb():
    return AIMemoryNotebook()


class TestAIMemoryAutofill:
    """aimemory 的核心行为。"""

    def test_add_aimemory(self, db, aimem_nb):
        """基本写入：标题 + 内容。"""
        db.init({aimem_nb.name: aimem_nb.columns})
        with db.transaction() as conn:
            ids = aimem_nb.add(conn, [
                {"title": "Python 最佳实践", "content": "使用 with 语句管理资源。"},
            ])
        with db.read_transaction() as conn:
            results = aimem_nb.get_by_ids(conn, ids)
        assert results[0]["title"] == "Python 最佳实践"
        assert results[0]["content"] == "使用 with 语句管理资源。"

    def test_id_format(self, db, aimem_nb):
        db.init({aimem_nb.name: aimem_nb.columns})
        with db.transaction() as conn:
            ids = aimem_nb.add(conn, [
                {"title": "记忆示例", "content": "早睡早起。"},
            ])
        assert ids[0].startswith("aimemory-")

    def test_optional_fields(self, db, aimem_nb):
        """source、note 为可选字段。"""
        db.init({aimem_nb.name: aimem_nb.columns})
        with db.transaction() as conn:
            ids = aimem_nb.add(conn, [
                {"title": "读书笔记", "content": "活着",
                 "source": "chat"},
                {"title": "灵感", "content": "灵光一闪"},
            ])
        with db.read_transaction() as conn:
            results = aimem_nb.get_by_ids(conn, ids)
        assert results[0]["source"] == "chat"
        assert results[1]["source"] is None

    def test_title_missing_raises(self, db, aimem_nb):
        """title 是必填字段，缺少时抛 EntryInvalidError。"""
        db.init({aimem_nb.name: aimem_nb.columns})
        with db.transaction() as conn:
            with pytest.raises(EntryInvalidError, match="title"):
                aimem_nb.add(conn, [{"content": "没有标题"}])

    def test_content_missing_raises(self, db, aimem_nb):
        """content（正文）是基类必填字段。"""
        db.init({aimem_nb.name: aimem_nb.columns})
        with db.transaction() as conn:
            with pytest.raises(EntryInvalidError, match="content"):
                aimem_nb.add(conn, [{"title": "只有标题"}])
