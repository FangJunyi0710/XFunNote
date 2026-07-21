"""测试 Registry 初始化和模块导入。"""

import pytest


class TestRegistryInit:
    def test_registry_has_all_notebooks(self):
        from xfun import registry
        assert set(registry.keys()) == {"plan", "diary", "word", "accumulation", "aimemory", "timeline", "schedule", "ledger"}

    def test_notebook_columns_match(self):
        from xfun import registry
        assert len(registry["plan"].columns) == len(registry["plan"]._extra_columns) + 9
        assert len(registry["diary"].columns) == 12  # 9 base + 3 extra
        assert len(registry["word"].columns) == 22  # 9 base + 9 extra (已更新)
        assert len(registry["accumulation"].columns) == 10  # 9 base + 1 extra
        assert len(registry["aimemory"].columns) == 11  # 9 base + 2 extra
        assert len(registry["timeline"].columns) == 12  # 9 base + 3 extra
        assert len(registry["schedule"].columns) == 12  # 9 base + 3 extra
        assert len(registry["ledger"].columns) == 12  # 9 base + 9 extra (参考 word)

    def test_db_file_created(self, db):
        """使用 fixture 提供的 db，验证数据库文件存在。"""
        import os
        assert os.path.exists(db.db_path)

    def test_notebook_repr(self):
        from xfun import registry
        assert repr(registry["plan"]) == "<Notebook:plan>"
        assert repr(registry["diary"]) == "<Notebook:diary>"

    def test_time_utils_importable(self):
        from xfun.utils.time_utils import now_str, timestamp_str
        assert now_str() is not None
        ts = timestamp_str()
        assert len(ts) == 15, f"timestamp_str 应为15字符, 得到 {ts}"
        assert ts[:8].isdigit() and ts[9:].isdigit(), f"timestamp_str 格式异常: {ts}"
