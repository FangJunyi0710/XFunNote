"""Token 自动生成工具。"""

import re
import secrets

def generate_token() -> str:
    """生成 API Token 值（格式: sk-{随机安全字符串}）。"""
    return "sk-" + secrets.token_urlsafe(24)

_TOKEN_PATTERN = re.compile(r"^sk-[-A-Za-z0-9_]{32}$")

def validate_token(token: str) -> bool:
    return _TOKEN_PATTERN.match(token) is not None
