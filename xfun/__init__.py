from .core.db       import DB, Column
from .core.notebook import Notebook
from .notebooks.plan         import PlanNotebook
from .notebooks.diary        import DiaryNotebook
from .notebooks.word         import WordNotebook
from .notebooks.accumulation import AccumulationNotebook
from .notebooks.aimemory     import AIMemoryNotebook
from .utils.token_utils import generate_token

db: DB = DB()
registry: dict[str, Notebook] = {
    "plan":         PlanNotebook(),
    "diary":        DiaryNotebook(),
    "word":         WordNotebook(),
    "accumulation": AccumulationNotebook(),
    "aimemory":     AIMemoryNotebook(),
}
# TODO 时间线本子
# TODO 日程表本子

# ---- 系统表定义 ----
_SYSTEM_TABLES: dict[str, list[Column]] = {
    "_token": [
        Column("id", "TEXT", primary_key=True, nullable=False, auto=True),
        Column("token", "TEXT", nullable=False, auto=True, index=True),
        Column("name", "TEXT", nullable=False),
        Column("permission", "TEXT", nullable=False),
        Column("is_active", "INTEGER", nullable=False, auto=True),
        Column("expires_at", "TEXT", nullable=True),
        Column("created_at", "TEXT", nullable=False, auto=True),
        Column("updated_at", "TEXT", nullable=False, auto=True),
    ],
    "_view": [
        Column("id", "TEXT", primary_key=True, nullable=False, auto=True),
        Column("name", "TEXT", nullable=False, index=True),
        Column("data", "TEXT", nullable=False),
        Column("created_at", "TEXT", nullable=False, auto=True),
        Column("updated_at", "TEXT", nullable=False, auto=True),
    ],
    "_permission": [
        Column("id", "TEXT", primary_key=True, nullable=False, auto=True),
        Column("name", "TEXT", nullable=False),
        Column("description", "TEXT", nullable=True),
        Column("read_view", "TEXT", nullable=False),
        Column("write_view", "TEXT", nullable=False),
        Column("created_at", "TEXT", nullable=False, auto=True),
        Column("updated_at", "TEXT", nullable=False, auto=True),
    ],
}


def _autofill_token(entry: dict) -> None:
    """_token 自动填充钩子：缺失 token 时自动生成。"""
    entry.setdefault("token", generate_token())
    entry.setdefault("is_active", 1)


def init_db(conn):
    """初始化数据库（用户表 + 系统表 + 种子数据）。"""
    # 注册本子钩子到 DB（CRUD 由 DB 统一管理）
    for name, nb in registry.items():
        db.register_hooks(name, pre_add=nb._pre_add, validate=nb._validate, autofill=nb._autofill)

    # 注册系统表钩子
    db.register_hooks("_token", autofill=_autofill_token)

    db.init(conn, {name: nb.columns for name, nb in registry.items()})
    db.init(conn, _SYSTEM_TABLES)


with db.transaction() as conn:
    init_db(conn)

__all__ = ["db", "registry"]
