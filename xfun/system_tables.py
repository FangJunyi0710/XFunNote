import uuid

from xfun.core.db import DB, Column
from xfun.utils.token_utils import generate_token
from xfun.core.errors import EntryInvalidError

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
    from xfun.utils.token_utils import validate_token
    if "token" in entry and entry["token"] is not None:
        if not validate_token(str(entry["token"])):
            raise EntryInvalidError("_token", f"token 格式无效: {entry['token']}")
    if "shortcut" in entry and entry["shortcut"] is not None:
        if validate_token(str(entry["shortcut"])):
            raise EntryInvalidError("_token", f"shortcut 不能以 sk- 开头: {entry['shortcut']}")
    if "is_active" in entry and entry["is_active"] is not None:
        if entry["is_active"] not in (0, 1):
            raise EntryInvalidError("_token", f"is_active 必须为 0 或 1: {entry['is_active']}")

def _validate_permission(entry: dict) -> None:
    import json
    from xfun.core.view import parse_view_json
    from xfun.core.filter import filter_to_sql
    from xfun.core.db import Column
    for key in ("read_view", "write_view"):
        if key in entry and entry[key] is not None:
            try:
                obj = json.loads(str(entry[key]))
                view = parse_view_json(obj)
                for table, specs in view.items():
                    Column.check(table)
                    for cols, flt in specs:
                        for col in cols:
                            Column.check(col)
                        sql, params = filter_to_sql(flt)
            except Exception as e:
                raise EntryInvalidError("_permission", f"{key} 不是有效的 View JSON: {e}")

def _validate_view(entry: dict) -> None:
    import json
    from xfun.core.view import parse_view_json
    from xfun.core.filter import filter_to_sql
    from xfun.core.db import Column
    if "data" in entry and entry["data"] is not None:
        try:
            obj = json.loads(str(entry["data"]))
            view = parse_view_json(obj)
            for table, specs in view.items():
                Column.check(table)
                for cols, flt in specs:
                    for col in cols:
                        Column.check(col)
                    sql, params = filter_to_sql(flt)
        except Exception as e:
            raise EntryInvalidError("_view", f"data 不是有效的 View JSON: {e}")

def _validate_filter(entry: dict) -> None:
    import json
    from xfun.core.filter import parse_filter_json, filter_to_sql
    if "data" in entry and entry["data"] is not None:
        try:
            obj = json.loads(str(entry["data"]))
            flt = parse_filter_json(obj)
            sql, params = filter_to_sql(flt)
        except Exception as e:
            raise EntryInvalidError("_filter", f"data 不是有效的 DNF JSON: {e}")

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
