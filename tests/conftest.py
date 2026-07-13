"""
pytest 共享夹具（fixtures）。

所有测试用例共享的：
- ``db``：session 级共享 SQLite DB（临时文件），函数级清表隔离。
- ``registry``：Notebook 实例字典，与 xfun.__init__.registry 结构一致。
- ``conn``：写事务连接（自动回滚/提交）。
- ``read_conn``：只读事务连接。
"""

import os
import tempfile
from typing import Any

import pytest

from xfun.core.db import DB
from xfun.core.notebook import Notebook
from xfun.notebooks.plan import PlanNotebook
from xfun.notebooks.diary import DiaryNotebook
from xfun.notebooks.word import WordNotebook
from xfun.notebooks.accumulation import AccumulationNotebook
from xfun.notebooks.aimemory import AIMemoryNotebook
from xfun.notebooks.timeline import TimelineNotebook
from xfun.notebooks.schedule import ScheduleNotebook

# ---------------------------------------------------------------------------
# 夹具
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def notebook_classes() -> dict[str, type[Notebook]]:
    return {
        "plan":         PlanNotebook,
        "diary":        DiaryNotebook,
        "word":         WordNotebook,
        "accumulation": AccumulationNotebook,
        "aimemory":     AIMemoryNotebook,
        "timeline":     TimelineNotebook,
        "schedule":     ScheduleNotebook,
    }


@pytest.fixture(scope="session")
def registry() -> dict[str, Notebook]:
    return {
        "plan":         PlanNotebook(),
        "diary":        DiaryNotebook(),
        "word":         WordNotebook(),
        "accumulation": AccumulationNotebook(),
        "aimemory":     AIMemoryNotebook(),
        "timeline":     TimelineNotebook(),
        "schedule":     ScheduleNotebook(),
    }


# ---- session 级：一次性创建 + 初始化 DB ----

@pytest.fixture(scope="session")
def _shared_db(registry):
    """session 级共享 DB：初始化一次，所有测试函数复用。"""
    tmpf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmpf.close()
    _db = DB(tmpf.name)
    with _db.transaction() as conn:
        for name, nb in registry.items():
            _db.register_hooks(
                name, pre_add=nb._pre_add, validate=nb._validate, autofill=nb._autofill,
            )
        _db.init(conn, {name: nb.columns for name, nb in registry.items()})
    yield _db
    os.unlink(tmpf.name)


# ---- function 级：清表隔离 ----

@pytest.fixture(scope="function")
def db(_shared_db) -> DB:
    """函数级：清除所有实际存在的表数据，确保隔离。"""
    _db = _shared_db
    with _db.transaction() as conn:
        existing = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        for table in list(_db.table_infos):
            if table in existing:
                conn.execute(f"DELETE FROM {table}")
    return _db


@pytest.fixture
def conn(db):
    """写事务连接。"""
    with db.transaction() as conn:
        yield conn


@pytest.fixture
def read_conn(db):
    """只读事务连接。"""
    with db.read_transaction() as read_conn:
        yield read_conn


@pytest.fixture
def demo_entries(registry) -> dict[str, list[dict[str, Any]]]:
    """为每个 Notebook 预置的样本数据。"""
    return {
        "plan": [
            {"content": "计划A", "month": "2606"},
            {"content": "计划B", "month": "2606"},
            {"content": "计划C", "month": "2607"},
        ],
        "diary": [
            {"content": "日记 1", "date": "2026-06-01", "mood": "开心", "weather": "晴"},
            {"content": "日记 2", "date": "2026-06-02", "mood": "平静", "weather": "多云"},
        ],
        "word": [
            {"content": "apple", "word": "apple", "part_of_speech": "noun", "example": "An apple a day."},
            {"content": "run", "word": "run", "part_of_speech": "verb"},
        ],
        "accumulation": [
            {"content": "Python 技巧", "category": "编程", "source": "博客"},
            {"content": "经济学原理", "category": "经济", "source": "书籍"},
        ],
        "aimemory": [
            {"content": "用户叫小方", "title": "[事实]姓名"},
            {"content": "喜欢简洁风格", "title": "[策略]UI偏好"},
        ],
        "timeline": [
            {"content": "写代码", "start_time": "2026-07-13 09:00:00+08:00", "end_time": "2026-07-13 12:00:00+08:00", "location": "办公室"},
            {"content": "午饭", "start_time": "2026-07-13 12:00:00+08:00", "end_time": "2026-07-13 13:00:00+08:00", "location": "食堂"},
        ],
        "schedule": [
            {"content": "开会", "start_time": "2026-07-14 10:00:00+08:00", "end_time": "2026-07-14 11:00:00+08:00", "location": "会议室A"},
            {"content": "健身", "start_time": "2026-07-14 18:00:00+08:00", "end_time": "2026-07-14 19:00:00+08:00", "location": "健身房"},
        ],
    }


@pytest.fixture
def populated_db(db, registry, demo_entries):
    """预先填充了样本数据的 DB 和对应的条目 ID 字典。"""
    ids: dict[str, list[str]] = {}
    with db.transaction() as conn:
        for nb_name, entries in demo_entries.items():
            ids[nb_name] = conn.db.add_entries(conn, nb_name, entries)
    return db, ids
