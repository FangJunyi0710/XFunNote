"""Token 自动生成工具。"""

import secrets


def generate_token() -> str:
    """生成 API Token 值（格式: sk-{随机安全字符串}）。"""
    return "sk-" + secrets.token_urlsafe(24)
