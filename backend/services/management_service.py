"""数据库管理业务逻辑（初始化/备份/重置）。"""

from xfun import init_db
from xfun.core.db import DB


def init_database(db: DB) -> str:
    """初始化数据库：建表/补齐缺失列/建索引。"""
    init_db()
    db.init()
    return "数据库初始化完成"


def backup_database(db: DB) -> str:
    """在线热备份数据库。"""
    path = db.backup()
    return f"备份完成: {path}"


def reset_database(db: DB, backup_first: bool = True) -> str:
    """重置数据库：清空所有表并重新初始化。"""
    if backup_first:
        db.backup()
    db.reset()
    return "数据库已重置"


def restore_database(db: DB, backup_path: str) -> str:
    """从备份文件恢复数据库（恢复前自动备份当前数据库做安全网）。"""
    pre_path = db.backup()
    path = db.restore(backup_path)
    return f"已从备份恢复: {path}（恢复前自动备份: {pre_path}）"
