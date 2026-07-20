from xfun.core.db import DB, Column
from xfun.utils.token_utils import generate_token

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
        Column("name", "TEXT", nullable=False, unique=True),
        Column("description", "TEXT", nullable=True),
        Column("read_view", "TEXT", nullable=False),
        Column("write_view", "TEXT", nullable=False),
        Column("created_at", "TEXT", nullable=False, auto=True),
        Column("updated_at", "TEXT", nullable=False, auto=True),
    ],
}
# TODO permission 添加 uuid 列
# TODO token 改为 permission uuid 列表
# TODO permission view 等数据结构应支持 REF 等随引用自动更新



def _autofill_token(entry: dict) -> None:
    """_token 自动填充钩子：自动生成 token。"""
    entry["token"] = generate_token()
    entry.setdefault("is_active", 1)

def register_system_hooks(db: DB) -> None:
    db.register_hooks("_token", autofill=_autofill_token)
