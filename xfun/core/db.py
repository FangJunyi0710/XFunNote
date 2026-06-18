import os
import sqlite3
from dataclasses import dataclass
from typing import Any, Optional

from .. import config


# ---------------------------------------------------------------------------
# 列定义
# ---------------------------------------------------------------------------

@dataclass
class Column:
    """
    数据库列定义。

    Attributes
    ----------
    name : str
        列名。
    col_type : str
        SQLite 类型：TEXT / INTEGER / REAL / BLOB。
    nullable : bool
        是否允许 NULL，默认 True。
    default : Any
        默认值，None 表示无默认。
    primary_key : bool
        是否主键，默认 False。
    index : bool
        是否建索引，默认 False。
    auto : bool
        是否由系统自动填充，默认 False。
    """
    name: str
    col_type: str
    nullable: bool = True
    default: Any = None
    primary_key: bool = False
    index: bool = False
    auto: bool = False

    @property
    def sql(self) -> str:
        """生成 CREATE TABLE 用的列定义片段。"""
        parts = [self.name, self.col_type]
        if self.primary_key:
            parts.append("PRIMARY KEY")
        if not self.nullable:
            parts.append("NOT NULL")
        if self.default is not None:
            if isinstance(self.default, str):
                parts.append(f"DEFAULT '{self.default}'")
            else:
                parts.append(f"DEFAULT {self.default}")
        return " ".join(parts)


# ---------------------------------------------------------------------------
# 筛选条件
# ---------------------------------------------------------------------------

@dataclass
class Filter:
    """
    列表筛选条件。

    Attributes
    ----------
    column : str
        筛选的列名。
    value : Any
        筛选值。
    op : str
        比较运算符，默认 "="，支持 ">", "<", ">=", "<=", "!=", "LIKE"。
    """
    column: str
    value: Any
    op: str = "="


# ---------------------------------------------------------------------------
# DB 类
# ---------------------------------------------------------------------------

class DB:
    """数据库管理器，每个事务返回独立的连接，保证隔离。"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.DB_PATH

    def _ensure_data_dir(self) -> None:
        dirname = os.path.dirname(self.db_path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        """建立新连接，统一设置 row_factory 并启用 WAL 模式。"""
        self._ensure_data_dir()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    # ---- 事务 ----

    def transaction(self):
        """
        返回写事务上下文管理器（BEGIN IMMEDIATE）。用于包裹跨多个 Notebook 的写入操作。
        """
        return _TransactionContext(self)

    def read_transaction(self):
        """
        返回只读事务上下文管理器（普通 BEGIN，不阻塞写入者）。
        WAL 模式下读取不阻塞写入，写入不阻塞读取。
        """
        return _ReadTransactionContext(self)

    # ---- 初始化 ----

    def init(self, registry) -> None:
        """
        初始化数据库：为 registry 中所有已注册的 notebook 建表。

        Parameters
        ----------
        registry : Registry
            Notebook 注册中心，遍历其中每个 notebook 调用 init_table()。
        """
        with self.transaction() as conn:
            for nb in registry:
                nb.init_table(conn)


class _TransactionContext:
    """写事务上下文管理器：BEGIN IMMEDIATE，阻塞写入者并发。"""

    def __init__(self, db: DB):
        self.db = db
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> sqlite3.Connection:
        self.conn = self.db._connect()
        self.conn.execute("BEGIN IMMEDIATE") # 主动加写锁，避免高并发下的 SQLITE_BUSY 重试
        return self.conn

    def __exit__(self, exc_type, exc_val, tb) -> None:
        if self.conn is None:
            return
        try:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
        finally:
            self.conn.close()


class _ReadTransactionContext:
    """只读事务上下文管理器：普通 BEGIN，不阻塞写入者（WAL 模式下）。"""

    def __init__(self, db: DB):
        self.db = db
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> sqlite3.Connection:
        self.conn = self.db._connect()
        self.conn.execute("BEGIN")  # 不加 IMMEDIATE，不阻塞写入
        return self.conn

    def __exit__(self, exc_type, exc_val, tb) -> None:
        if self.conn is None:
            return
        try:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
        finally:
            self.conn.close()
