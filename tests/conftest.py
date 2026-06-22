"""pytest 共享 fixtures。"""

import pytest
from xfun.core.db import DB
from xfun.core.registry import Registry
from xfun.core.notebook import Notebook, Column
from xfun.notebooks.plan import PlanNotebook


class _TestNotebook(Notebook):
    """最小化测试用 Notebook，只用于测试基类。"""
    name = "test_nb"
    _extra_columns = [
        Column("title", "TEXT", nullable=False),
        Column("count", "INTEGER"),
    ]

    def _autofill(self, entry):
        from future_uuid import uuid7
        super()._autofill(entry)
        entry.setdefault("id", str(uuid7()))


@pytest.fixture
def db(tmp_path):
    """临时文件 SQLite 数据库（跨连接持久化）。"""
    return DB(db_path=str(tmp_path / "test.db"))


@pytest.fixture
def test_nb():
    return _TestNotebook()


@pytest.fixture
def plan_nb():
    return PlanNotebook()


@pytest.fixture
def registry():
    reg = Registry()
    reg.register("plan", PlanNotebook())
    return reg
