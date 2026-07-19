import re

from xfun.config import PROJECT_ROOT
from xfun.core.errors import UsernameInvalidError


def get_db_path(user: str) -> str:
    _USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9\-_]{1,64}$")
    if not _USERNAME_PATTERN.match(user):
        raise UsernameInvalidError(user)
    return str(PROJECT_ROOT / "data" / f"{user}.db")
