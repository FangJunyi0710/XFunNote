"""测试 WordNotebook：必填字段、ID 去重、可选字段、复习数据默认值。"""

import sqlite3

import pytest
from xfun.core.errors import EntryInvalidError
from xfun.notebooks.word import WordNotebook


@pytest.fixture
def word_nb():
    return WordNotebook()


class TestWordAutofill:
    """word 的核心行为。"""

    def test_add_word(self, db, word_nb):
        """基本写入：单词 + 释义（content）。"""
        db.init({word_nb.name: word_nb.columns})
        with db.transaction() as conn:
            ids = word_nb.add(conn, [
                {"word": "python", "content": "蟒蛇；一种编程语言"},
            ])
        with db.read_transaction() as conn:
            results = word_nb.get_by_id(conn, ids)
        assert results[0]["word"] == "python"
        assert results[0]["content"] == "蟒蛇；一种编程语言"

    def test_id_is_word(self, db, word_nb):
        """id 格式为 word-{word}，可通过 id 查询。"""
        db.init({word_nb.name: word_nb.columns})
        with db.transaction() as conn:
            ids = word_nb.add(conn, [
                {"word": "apple", "content": "苹果"},
            ])
        assert ids[0] == "word-apple"
        with db.read_transaction() as conn:
            result = word_nb.get_by_id(conn, ["word-apple"])
        assert result[0]["word"] == "apple"

    def test_duplicate_word_raises(self, db, word_nb):
        """重复单词因 PRIMARY KEY 约束抛 IntegrityError。"""
        db.init({word_nb.name: word_nb.columns})
        with db.transaction() as conn:
            word_nb.add(conn, [{"word": "apple", "content": "苹果"}])
            with pytest.raises(sqlite3.IntegrityError):
                word_nb.add(conn, [{"word": "apple", "content": "苹果公司"}])

    def test_optional_fields(self, db, word_nb):
        """词性、音标、例句为可选字段。"""
        db.init({word_nb.name: word_nb.columns})
        with db.transaction() as conn:
            ids = word_nb.add(conn, [
                {"word": "hello", "content": "你好", "part_of_speech": "int.",
                 "phonetic": "/həˈloʊ/", "example": "Hello, world!"},
                {"word": "world", "content": "世界"},
            ])
        with db.read_transaction() as conn:
            results = word_nb.get_by_id(conn, ids)
        assert results[0]["part_of_speech"] == "int."
        assert results[0]["phonetic"] == "/həˈloʊ/"
        assert results[0]["example"] == "Hello, world!"
        assert results[1]["part_of_speech"] is None
        assert results[1]["phonetic"] is None
        assert results[1]["example"] is None

    def test_review_defaults(self, db, word_nb):
        """review_count 默认为 0，performance 默认为 0.0。"""
        db.init({word_nb.name: word_nb.columns})
        with db.transaction() as conn:
            ids = word_nb.add(conn, [
                {"word": "apple", "content": "苹果"},
                {"word": "banana", "content": "香蕉", "review_count": 5, "performance": 0.8},
            ])
        with db.read_transaction() as conn:
            results = word_nb.get_by_id(conn, ids)
        assert results[0]["review_count"] == 0
        assert results[0]["performance"] == 0.0
        assert results[1]["review_count"] == 5
        assert results[1]["performance"] == 0.8

    def test_word_missing_raises(self, db, word_nb):
        """word 是必填字段，缺少时抛 EntryInvalidError。"""
        db.init({word_nb.name: word_nb.columns})
        with db.transaction() as conn:
            with pytest.raises(EntryInvalidError, match="word"):
                word_nb.add(conn, [{"content": "没有单词"}])

    def test_content_missing_raises(self, db, word_nb):
        """content（释义）是基类必填字段。"""
        db.init({word_nb.name: word_nb.columns})
        with db.transaction() as conn:
            with pytest.raises(EntryInvalidError, match="content"):
                word_nb.add(conn, [{"word": "test"}])
