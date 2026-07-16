"""测试时间工具函数。"""

import re
from datetime import date

from xfun.utils.time_utils import now_str, today_str


class TestTimeUtils:
    def test_now_str_format(self):
        """now_str 应返回包含 UTC 偏移的时间字符串。"""
        s = now_str()
        # 格式：YYYY-MM-DD HH:MM:SS.mmm±HH:MM
        assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}", s), f"格式不匹配: {s}"

    def test_today_str_format(self):
        """today_str 应返回 ISO 日期字符串。"""
        s = today_str()
        assert re.match(r"\d{4}-\d{2}-\d{2}", s)

    def test_today_str_matches_today(self):
        """today_str 应与 date.today() 一致。"""
        assert today_str() == date.today().isoformat()

    def test_now_str_not_empty(self):
        assert now_str() != ""

    def test_today_str_not_empty(self):
        assert today_str() != ""
