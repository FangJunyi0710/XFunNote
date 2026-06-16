from datetime import datetime, timezone, tzinfo


def now_str() -> str:
    """返回当前时间字符串，包含 UTC 偏移，如 "2026-06-16 14:30:00+08:00"。"""
    return datetime.now(timezone.utc).isoformat(sep=" ", timespec="seconds")
