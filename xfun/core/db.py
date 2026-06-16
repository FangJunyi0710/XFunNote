from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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
# DB 类（骨架，后续完善）
# ---------------------------------------------------------------------------

class DB:
    """数据库管理器，封装 SQLite 连接与基本操作。"""

    def __init__(self, db_path: str = "data/xfun.db"):
        self.db_path = db_path

    def execute(self, sql: str, params: tuple = ()) -> Any:
        """执行一条 SQL。"""
        raise NotImplementedError

    def init(self) -> None:
        """初始化数据库：建库、建所有表。"""
        raise NotImplementedError
