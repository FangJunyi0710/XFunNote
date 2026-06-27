from datetime import date, datetime, timezone


def now_str() -> str:
    """返回当前本地时间字符串，包含 UTC 偏移，如 "2026-06-16 14:30:00+08:00"。"""
    return datetime.now(timezone.utc).astimezone().isoformat(sep=" ", timespec="milliseconds")

def today_str() -> str:
    """返回今天日期的字符串，格式 "2026-06-18"。"""
    return date.today().isoformat()

def timestamp_str() -> str:
    """返回适合文件名的时间戳，如 "20260625_143000"。"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
