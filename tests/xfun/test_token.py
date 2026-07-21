"""测试 Token 工具函数和系统表自动填充。"""

import pytest

from xfun.utils.token_utils import generate_token
from xfun.system_tables import _autofill_token


class TestGenerateToken:
    def test_token_starts_with_sk(self):
        token = generate_token()
        assert token.startswith("sk-")

    def test_token_length(self):
        token = generate_token()
        assert len(token) > 32

    def test_token_is_unique(self):
        tokens = {generate_token() for _ in range(100)}
        assert len(tokens) == 100

    def test_token_contains_only_urlsafe_chars(self):
        token = generate_token()
        prefix, _, rest = token.partition("-")
        assert prefix == "sk"
        assert rest.isascii()
        import string
        allowed = set(string.ascii_letters + string.digits + "-_")
        assert all(c in allowed for c in rest)


class TestSystemTableToken:
    def test_autofill_adds_token(self):
        entry = {"name": "test", "permission": "admin"}
        _autofill_token(entry)
        assert entry["name"] == "test"
        assert entry["token"].startswith("sk-")

    def test_autofill_sets_token_if_missing(self):
        entry = {"name": "test2", "permission": "admin"}
        _autofill_token(entry)
        assert "token" in entry
        assert entry["token"].startswith("sk-")
