"""测试时间工具函数。"""

import re
from datetime import date

from xfun.utils.time_utils import now_str, format_date, format_datetime


class TestTimeUtils:
    def test_now_str_format(self):
        """now_str 应返回包含 UTC 偏移的时间字符串。"""
        s = now_str()
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}", s), f"格式不匹配: {s}"

    def test_today_str_using_format_date(self):
        """使用 format_date(date.today()) 代替已移除的 today_str。"""
        assert format_date(date.today()) == date.today().isoformat()

    def test_now_str_not_empty(self):
        assert now_str() != ""

    def test_format_date(self):
        d = date(2026, 7, 19)
        assert format_date(d) == "2026-07-19"

    def test_format_datetime_naive(self):
        from datetime import datetime
        dt = datetime(2026, 7, 19, 12, 0, 0)
        assert format_datetime(dt).endswith("+00:00")

    def test_format_datetime_aware(self):
        from datetime import datetime, timezone
        dt = datetime(2026, 7, 19, 12, 0, 0, tzinfo=timezone.utc)
        assert format_datetime(dt) == "2026-07-19T12:00:00.000+00:00"
