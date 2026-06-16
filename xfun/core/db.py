import os
import sqlite3
from dataclasses import dataclass
from typing import Any, Optional, Sequence

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
    """
    name: str
    col_type: str
    nullable: bool = True
    default: Any = None
    primary_key: bool = False
    index: bool = False

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
    """数据库管理器，封装 SQLite 连接与基本操作。"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.DB_PATH
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    # ---- 连接管理 ----

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._ensure_data_dir()
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _ensure_data_dir(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ---- 执行 SQL ----

    def execute(self, sql: str, params: Sequence = ()) -> sqlite3.Cursor:
        """执行一条 SQL，返回 cursor。"""
        return self.conn.execute(sql, params)

    def executemany(self, sql: str, seq_of_params: Sequence) -> sqlite3.Cursor:
        """批量执行同一条 SQL。"""
        return self.conn.executemany(sql, seq_of_params)

    def commit(self) -> None:
        self.conn.commit()

    # ---- 初始化 ----

    def init(self, registry) -> None:
        """
        初始化数据库：为 registry 中所有已注册的 notebook 建表。

        Parameters
        ----------
        registry : Registry
            Notebook 注册中心，遍历其中每个 notebook 调用 init_table()。
        """
        for nb in registry:
            nb.init_table(self)
        self.commit()
