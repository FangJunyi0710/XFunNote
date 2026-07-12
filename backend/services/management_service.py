"""数据库管理业务逻辑（初始化/备份/重置）。"""

from xfun import db, init_db


def init_database() -> str:
    """初始化数据库：建表/补齐缺失列/建索引。"""
    with db.transaction() as conn:
        init_db(conn)
    return "数据库初始化完成"


def backup_database() -> str:
    """在线热备份数据库。"""
    with db.read_transaction() as conn:
        path = db.backup(conn)
    return f"备份完成: {path}"


def reset_database(backup_first: bool = True) -> str:
    """重置数据库：清空所有表并重新初始化。"""
    with db.read_transaction() as conn:
        if backup_first:
            db.backup(conn)
    with db.transaction() as conn:
        db.reset(conn)
    return "数据库已重置"
