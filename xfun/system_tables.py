import uuid

from xfun.core.db import DB, Column
from xfun.utils.time_utils import validate_datetime
from xfun.utils.token_utils import generate_token, validate_token
from xfun.core.errors import EntryInvalidError
from xfun.core.view import validate_view
from xfun.core.filter import validate_filter

# ---- 系统表定义 ----
SYSTEM_TABLES: dict[str, list[Column]] = {
    "_token": [
        Column("id", "TEXT", primary_key=True, nullable=False, auto=True),
        Column("token", "TEXT", nullable=False, auto=True, unique=True),
        Column("name", "TEXT", nullable=False),
        Column("permission", "TEXT", nullable=False),
        Column("is_active", "INTEGER", nullable=False, auto=True),
        Column("shortcut", "TEXT", nullable=True, unique=True),
        Column("shortcut_expire_at", "TEXT", nullable=True),
        Column("expires_at", "TEXT", nullable=True),
        Column("created_at", "TEXT", nullable=False, auto=True),
        Column("updated_at", "TEXT", nullable=False, auto=True),
    ],
    "_view": [
        Column("id", "TEXT", primary_key=True, nullable=False, auto=True),
        Column("name", "TEXT", nullable=False, unique=True),
        Column("data", "TEXT", nullable=False),
        Column("created_at", "TEXT", nullable=False, auto=True),
        Column("updated_at", "TEXT", nullable=False, auto=True),
    ],
    "_filter": [
        Column("id", "TEXT", primary_key=True, nullable=False, auto=True),
        Column("name", "TEXT", nullable=False, unique=True),
        Column("data", "TEXT", nullable=False),
        Column("created_at", "TEXT", nullable=False, auto=True),
        Column("updated_at", "TEXT", nullable=False, auto=True),
    ],
    "_permission": [
        Column("id", "TEXT", primary_key=True, nullable=False, auto=True),
        Column("uuid", "TEXT", nullable=False, auto=True, unique=True),
        Column("name", "TEXT", nullable=False, unique=True),
        Column("description", "TEXT", nullable=True),
        Column("read_view", "TEXT", nullable=False),
        Column("write_view", "TEXT", nullable=False),
        Column("created_at", "TEXT", nullable=False, auto=True),
        Column("updated_at", "TEXT", nullable=False, auto=True),
    ],
}
# TODO token 改为 permission uuid 列表
# TODO permission view 等数据结构应支持 REF 等随引用自动更新

def _validate_token(entry: dict) -> None:
    if "token" in entry and entry["token"] is not None:
        if not validate_token(str(entry["token"])):
            raise EntryInvalidError("_token", f"token 格式无效: {entry['token']}")
    if "shortcut" in entry and entry["shortcut"] is not None:
        if validate_token(str(entry["shortcut"])):
            raise EntryInvalidError("_token", f"shortcut 不能符合 token 格式: {entry['shortcut']}")
    if "is_active" in entry and entry["is_active"] is not None:
        if entry["is_active"] not in (0, 1):
            raise EntryInvalidError("_token", f"is_active 必须为 0 或 1: {entry['is_active']}")
    if "expires_at" in entry and entry["expires_at"] is not None:
        if not validate_datetime(str(entry["expires_at"])):
            raise EntryInvalidError("_token", f"expires_at 不是有效的 ISO UTC 时间: {entry['expires_at']}")
    if "shortcut_expire_at" in entry and entry["shortcut_expire_at"] is not None:
        if not validate_datetime(str(entry["shortcut_expire_at"])):
            raise EntryInvalidError("_token", f"shortcut_expire_at 不是有效的 ISO UTC 时间: {entry['shortcut_expire_at']}")

def _validate_permission(entry: dict) -> None:
    for key in ("read_view", "write_view"):
        if key in entry and entry[key] is not None:
            validate_view(entry[key])

def _validate_view(entry: dict) -> None:
    if "data" in entry and entry["data"] is not None:
        validate_view(entry["data"])

def _validate_filter(entry: dict) -> None:
    if "data" in entry and entry["data"] is not None:
        validate_filter(entry["data"])

def _autofill_token(entry: dict) -> None:
    """_token 自动填充钩子：自动生成 token。"""
    entry["token"] = generate_token()
    entry.setdefault("is_active", 1)

def _autofill_permission(entry: dict) -> None:
    entry["uuid"] = uuid.uuid4()

def register_system_hooks(db: DB) -> None:
    db.register_hooks("_token", autofill=_autofill_token, validate=_validate_token)
    db.register_hooks("_permission", validate=_validate_permission, autofill=_autofill_permission)
    db.register_hooks("_view", validate=_validate_view)
    db.register_hooks("_filter", validate=_validate_filter)
