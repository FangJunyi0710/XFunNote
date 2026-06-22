"""测试 AccumulationNotebook：必填字段、ID 格式、可选字段。"""

import pytest
from xfun.core.errors import EntryInvalidError
from xfun.notebooks.accumulation import AccumulationNotebook


@pytest.fixture
def accum_nb():
    return AccumulationNotebook()


class TestAccumAutofill:
    """accumulation 的核心行为。"""

    def test_add_accum(self, db, accum_nb):
        """基本写入：分类 + 内容。"""
        db.init({accum_nb.name: accum_nb.columns})
        with db.transaction() as conn:
            ids = accum_nb.add(conn, [
                {"category": "tech", "content": "Python 的上下文管理器使用 with 语句。"},
            ])
        with db.read_transaction() as conn:
            results = accum_nb.get_by_id(conn, ids)
        assert results[0]["category"] == "tech"
        assert results[0]["content"] == "Python 的上下文管理器使用 with 语句。"

    def test_id_format(self, db, accum_nb):
        db.init({accum_nb.name: accum_nb.columns})
        with db.transaction() as conn:
            ids = accum_nb.add(conn, [
                {"category": "life", "content": "早睡早起身体好。"},
            ])
        assert ids[0].startswith("accumulation-")

    def test_optional_fields(self, db, accum_nb):
        """source、note 为可选字段。"""
        db.init({accum_nb.name: accum_nb.columns})
        with db.transaction() as conn:
            ids = accum_nb.add(conn, [
                {"category": "book", "content": "活着",
                 "source": "余华《活着》", "note": "经典之作"},
                {"category": "idea", "content": "灵光一闪"},
            ])
        with db.read_transaction() as conn:
            results = accum_nb.get_by_id(conn, ids)
        assert results[0]["source"] == "余华《活着》"
        assert results[0]["note"] == "经典之作"
        assert results[1]["source"] is None
        assert results[1]["note"] is None

    def test_category_missing_raises(self, db, accum_nb):
        """category 是必填字段，缺少时抛 EntryInvalidError。"""
        db.init({accum_nb.name: accum_nb.columns})
        with db.transaction() as conn:
            with pytest.raises(EntryInvalidError, match="category"):
                accum_nb.add(conn, [{"content": "没有分类"}])

    def test_content_missing_raises(self, db, accum_nb):
        """content（正文）是基类必填字段。"""
        db.init({accum_nb.name: accum_nb.columns})
        with db.transaction() as conn:
            with pytest.raises(EntryInvalidError, match="content"):
                accum_nb.add(conn, [{"category": "tech"}])
