"""测试 time_utils 工具函数。"""

from datetime import date

from xfun.utils.time_utils import today_str


class TestTodayStr:
    def test_format(self):
        result = today_str()
        expected = date.today().isoformat()
        assert result == expected
        # 验证格式 YYYY-MM-DD
        parts = result.split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 4  # 年
        assert len(parts[1]) == 2  # 月
        assert len(parts[2]) == 2  # 日
