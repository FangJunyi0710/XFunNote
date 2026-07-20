from datetime import date, datetime, timezone
import re


def format_datetime(dt: datetime) -> str:
    """将 datetime 对象格式化为 ISO 字符串，如 "2026-06-16T14:30:00.123Z"。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz=timezone.utc).isoformat(timespec="milliseconds")

def format_date(d: date) -> str:
    """将 date 对象格式化为 ISO 日期字符串，如 "2026-06-18"。"""
    return d.isoformat()


def now_str() -> str:
    """返回当前本地时间字符串。"""
    return format_datetime(datetime.now(timezone.utc))

def today_str() -> str:
    """返回今天日期的字符串，格式 "2026-06-18"。"""
    return format_date(date.today())

def timestamp_str() -> str:
    """返回适合文件名的时间戳，如 "20260625_143000"。"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

_DATETIME_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$')

def validate_datetime(s: str) -> bool:
    """
    判断字符串是否为严格的 ISO 8601 UTC 格式（以 'Z' 结尾），
    例如 "2026-06-16T14:30:00.123Z"
    """
    # 先校验基本格式（正则）
    if not _DATETIME_PATTERN.match(s):
        return False
    # 再尝试解析日期，确保是有效日期时间
    try:
        datetime.fromisoformat(s)   # Python 3.11+ 直接支持带 Z
        return True
    except ValueError:
        return False

_DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')

def validate_date(s: str) -> bool:
    """
    判断字符串是否为有效的 yyyy-mm-dd 日期格式，
    例如 "2026-06-18"。
    """
    if not _DATE_PATTERN.match(s):
        return False
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False

_YYMM_PATTERN = re.compile(r'^\d{2}(0[1-9]|1[0-2])$')

def validate_yymm(s: str) -> bool:
    return bool(_YYMM_PATTERN.match(s))
