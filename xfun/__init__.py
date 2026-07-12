from .core.db       import DB, Column
from .core.notebook import Notebook
from .notebooks.plan         import PlanNotebook
from .notebooks.diary        import DiaryNotebook
from .notebooks.word         import WordNotebook
from .notebooks.accumulation import AccumulationNotebook
from .notebooks.aimemory     import AIMemoryNotebook

db: DB = DB()
registry: dict[str, Notebook] = {
    "plan":         PlanNotebook(),
    "diary":        DiaryNotebook(),
    "word":         WordNotebook(),
    "accumulation": AccumulationNotebook(),
    "aimemory":     AIMemoryNotebook(),
}

# ---- 系统表定义 ----
_SYSTEM_TABLES: dict[str, list[Column]] = {
    "_tokens": [
        Column("id", "TEXT", primary_key=True, nullable=False),
        Column("token", "TEXT", nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("permission", "TEXT", nullable=False),
        Column("is_active", "INTEGER", nullable=False),
        Column("expires_at", "TEXT", nullable=True),
        Column("created_at", "TEXT", nullable=False),
        Column("updated_at", "TEXT", nullable=False),
    ],
    "_views": [
        Column("name", "TEXT", primary_key=True, nullable=False),
        Column("data", "TEXT", nullable=False),
        Column("created_at", "TEXT", nullable=False),
        Column("updated_at", "TEXT", nullable=False),
    ],
    "_permissions": [
        Column("id", "TEXT", primary_key=True, nullable=False),
        Column("name", "TEXT", nullable=False),
        Column("description", "TEXT", nullable=True),
        Column("read_view", "TEXT", nullable=False),
        Column("write_view", "TEXT", nullable=False),
        Column("can_query", "INTEGER", nullable=False),
        Column("can_add", "INTEGER", nullable=False),
        Column("can_update", "INTEGER", nullable=False),
        Column("can_delete", "INTEGER", nullable=False),
        Column("can_ai_chat", "INTEGER", nullable=False),
        Column("can_manage_db", "INTEGER", nullable=False),
        Column("can_manage_views", "INTEGER", nullable=False),
        Column("can_manage_tokens", "INTEGER", nullable=False),
        Column("created_at", "TEXT", nullable=False),
        Column("updated_at", "TEXT", nullable=False),
    ],
}


def init_db(conn):
    """初始化数据库（用户表 + 系统表 + 种子数据）。"""
    # 注册本子钩子到 DB（CRUD 由 DB 统一管理）
    for name, nb in registry.items():
        db.register_hooks(name, pre_add=nb._pre_add, validate=nb._validate, autofill=nb._autofill)

    db.init(conn, {name: nb.columns for name, nb in registry.items()})
    db.init(conn, _SYSTEM_TABLES)
    # 为 _tokens.token 建唯一索引
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS _tokens_token_idx ON _tokens(token)")
    # 插入默认权限种子数据（INSERT OR IGNORE 防止重复）
    _seed_permissions(conn)


def _seed_permissions(conn):
    """向 _permissions 表插入默认权限（root / readonly / ai）。"""
    import json

    from xfun.utils.time_utils import now_str
    from xfun.core.view import view_to_json, root_permission, full_view, no_view
    from xfun.ai.security import ai_permission

    now = now_str()
    seeds = [
        ("root", "超级管理员", "完全访问权限", root_permission(db),
         True, True, True, True, True, True, True, True),
        ("readonly", "只读", "仅允许查询数据", (full_view(db), no_view(db)),
         True, False, False, False, False, False, False, False),
        ("ai", "AI 助手", "AI 应用读写权限", ai_permission(),
         True, True, True, True, True, False, False, False),
    ]
    for pid, pname, pdesc, (rv, wv), *flags in seeds:
        conn.execute(
            "INSERT OR IGNORE INTO _permissions "
            "(id, name, description, read_view, write_view, "
            "can_query, can_add, can_update, can_delete, can_ai_chat, "
            "can_manage_db, can_manage_views, can_manage_tokens, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (pid, pname, pdesc,
             json.dumps(view_to_json(rv), ensure_ascii=False),
             json.dumps(view_to_json(wv), ensure_ascii=False),
             *flags, now, now),
        )


with db.transaction() as conn:
    init_db(conn)

__all__ = ["db", "registry"]
