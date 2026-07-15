"""测试 Registry 初始化和模块导入。"""

import pytest


class TestRegistryInit:
    def test_db_instance_has_tables(self):
        """xfun.db 应包含正确的表信息。"""
        from xfun import db, registry, init_db
        init_db()
        assert set(db.table_infos.keys()) == {"plan", "diary", "word", "accumulation", "aimemory", "timeline", "schedule", "_token", "_view", "_permission"}

    def test_registry_has_all_notebooks(self):
        from xfun import registry
        assert set(registry.keys()) == {"plan", "diary", "word", "accumulation", "aimemory", "timeline", "schedule"}

    def test_notebook_columns_match(self):
        from xfun import registry
        assert len(registry["plan"].columns) == len(registry["plan"]._extra_columns) + 9
        assert len(registry["diary"].columns) == 12  # 9 base + 3 extra
        assert len(registry["word"].columns) == 18  # 9 base + 9 extra
        assert len(registry["accumulation"].columns) == 10  # 9 base + 1 extra
        assert len(registry["aimemory"].columns) == 11  # 9 base + 2 extra
        assert len(registry["timeline"].columns) == 12  # 9 base + 3 extra
        assert len(registry["schedule"].columns) == 12  # 9 base + 3 extra

    def test_db_file_created(self):
        """初始化后数据库文件应存在。"""
        import os
        from xfun import config
        assert os.path.exists(config.DB_PATH)

    def test_notebook_repr(self):
        from xfun import registry
        assert repr(registry["plan"]) == "<Notebook:plan>"
        assert repr(registry["diary"]) == "<Notebook:diary>"

    def test_time_utils_importable(self):
        from xfun.utils.time_utils import now_str, today_str, timestamp_str
        assert now_str() is not None
        assert today_str() is not None
        ts = timestamp_str()
        assert len(ts) == 15, f"timestamp_str 应为15字符, 得到 {ts}"
        assert ts[:8].isdigit() and ts[9:].isdigit(), f"timestamp_str 格式异常: {ts}"
