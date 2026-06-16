from datetime import datetime


def now_str() -> str:
    """返回当前时间字符串，格式 "YYYY/MM/DD HH:MM:SS"。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str() -> str:
    """返回今天日期字符串，格式 "YYYY/MM/DD"。"""
    return datetime.now().strftime("%Y-%m-%d")
