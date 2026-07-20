from datetime import date, datetime, timezone


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
