import os
import re
import json
import sqlite3
from dataclasses import dataclass
from typing import Any, ClassVar, List, Optional, Sequence as Seq, Tuple, Union

from .. import config
from .errors import InvalidSQLError, InvalidConditionError


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
    primary_key: bool = False
    index: bool = False
    auto: bool = False

    # 所有拼接到sql中的列名需满足此
    _COLUMN_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*$")

    @classmethod
    def check(cls, name: str) -> None:
        if not cls._COLUMN_PATTERN.match(name):
            raise InvalidSQLError(name)

    @classmethod
    def check_order_by(cls, order_by: str) -> None:
        """校验 ORDER BY 子句中的列名，支持逗号分隔的多列及 ASC/DESC 后缀。

        Parameters
        ----------
        order_by : str
            ORDER BY 子句，例如 ``"month ASC, seq DESC"``。

        Raises
        ------
        InvalidColumnNameError
        """
        for part in order_by.split(","):
            part = part.strip().split(None, 1)
            cls.check(part[0])
            if len(part) > 1 and part[1] not in ("ASC", "DESC"):
                raise InvalidSQLError(part[1])

    @property
    def sql(self) -> str:
        """生成 CREATE TABLE 用的列定义片段。"""
        self.check(self.name)
        parts = [self.name, self.col_type]
        if self.primary_key:
            parts.append("PRIMARY KEY")
        if not self.nullable:
            parts.append("NOT NULL")

        return " ".join(parts)


# ---------------------------------------------------------------------------
# 筛选条件
# ---------------------------------------------------------------------------

@dataclass
class Condition:
    column: str
    value: Any
    op: str = "="

    _op_registry: ClassVar[dict] = {}

    @classmethod
    def register_op(cls, op_name: str):
        """装饰器：注册自定义运算符的 SQL 生成逻辑。

        Parameters
        ----------
        op_name : str
            自定义运算符名称。

        Returns
        -------
        callable
            装饰器，接收 handler(column, value, op) -> (sql, params)。
        """
        def decorator(func):
            cls._op_registry[op_name] = func
            return func
        return decorator

    def to_sql(self) -> Tuple[str, list]:
        """生成该条件的 SQL 片段及参数值列表。

        Returns
        -------
        tuple[str, list]
            (SQL 片段, 参数值列表)。值为 None 时返回空列表，SQL 使用 IS NULL / IS NOT NULL。

        Raises
        ------
        InvalidColumnNameError
        InvalidOperatorError
        InvalidConditionValueError
        """
        Column.check(self.column)

        handler = self._op_registry.get(self.op)
        if handler is None:
            raise InvalidConditionError(self)
        
        return handler(self.column, self.value, self.op)
    
@Condition.register_op("=")
@Condition.register_op("!=")
@Condition.register_op(">")
@Condition.register_op("<")
@Condition.register_op(">=")
@Condition.register_op("<=")
@Condition.register_op("LIKE")
@Condition.register_op("NOT LIKE")
@Condition.register_op("IN")
@Condition.register_op("NOT IN")
@Condition.register_op("BETWEEN")
def _builtin_sql(column, value, op) -> Tuple[str, list]:
    # --- NULL：只有 = 和 != 可以处理 NULL ---
    if value is None:
        if op == "=":
            return f"{column} IS NULL", []
        if op == "!=":
            return f"{column} IS NOT NULL", []
        raise InvalidConditionError(Condition(column, value, op))

    # --- IN / NOT IN ---
    if op in ("IN", "NOT IN"):
        if not isinstance(value, (list, tuple)):
            raise InvalidConditionError(Condition(column, value, op))
        if not value:
            # 空列表：IN → 永假，NOT IN → 永真
            return ("1=0", []) if op == "IN" else ("1=1", [])
        placeholders = ", ".join("?" for _ in value)
        sql = f"{column} {op} ({placeholders})"
        params = list(value)

    # --- BETWEEN ---
    elif op == "BETWEEN":
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise InvalidConditionError(Condition(column, value, op))
        if value[0] is None or value[1] is None:
            # 任意端点为 None → 永假
            return "1=0", []
        sql = f"{column} {op} ? AND ?"
        params = list(value)

    # --- 通用（=, >, <, >=, <=, !=, LIKE, NOT LIKE）---
    else:
        sql = f"{column} {op} ?"
        params = [value]

    return sql, params


Filter = Union[Condition, Seq[Seq["Filter"]], Tuple["Filter", bool]]
# 递归结构：外层 OR、内层 AND，元素可为子 Filter 或 Condition。
# 最外层支持 (Filter, negate) 元组对整个结果取反。

def filter_to_sql(filter: Filter) -> Tuple[str, list]:
    """
    生成 WHERE 子句：外层 OR（取并），内层 AND（取交）。
    最外层可为 (Filter, bool) 元组，bool=True 时对整个结果取反。

    Parameters
    ----------
    filter : Filter
        Filter 结构或 (Filter, bool) 元组。

    Returns
    -------
    tuple[str, list]
        (WHERE 子句 SQL 片段，可能为空，参数值列表)
    """
    if isinstance(filter, Condition):
        return filter.to_sql()

    if isinstance(filter, tuple):
        inner, negate = filter
        clause, vals = filter_to_sql(inner)
        if not clause:
            return "", []
        if negate:
            clause = f"NOT ({clause})"
        return clause, vals

    or_clauses: List[str] = []
    params: list = []
    for group in filter:
        and_clauses: List[str] = []
        for item in group:
            clause, vals = filter_to_sql(item)
            if not clause:
                continue
            and_clauses.append(f"({clause})")
            params.extend(vals)
        if not and_clauses:
            continue
        or_clauses.append("(" + " AND ".join(and_clauses) + ")")

    if not or_clauses:
        return "", []
    
    where_sql = " OR ".join(or_clauses)
    return where_sql, params

def parse_filter_json(s: str) -> Filter:
    """将 JSON 筛选条件解析为 Filter。"""
    data = json.loads(s)

    def _convert(obj):
        if isinstance(obj, dict):
            condition = Condition(**obj)
            return condition
        if isinstance(obj, list) and len(obj) == 2 and isinstance(obj[1], bool):
            return (_convert(obj[0]), obj[1])
        if not isinstance(obj, list):
            raise ValueError(f"无法识别的 filter JSON 格式: {s}")
        result = []
        for group in obj:
            clause = []
            if not isinstance(group, list):
                raise ValueError(f"无法识别的 filter JSON 格式: {s}")
            for item in group:
                clause.append(_convert(item))
            result.append(clause)
        return result

    return _convert(data)

# ---------------------------------------------------------------------------
# 列兼容性检查
# ---------------------------------------------------------------------------

def _check_addition_column(col: Column):
    """检查新加列的属性是否可行

    Raises
    ------
    InvalidSQLError
        列不可空或为主键时抛出，因为 SQLite 的 ADD COLUMN 不支持这些约束。
    """
    Column.check(col.name)
    if not col.nullable:
        raise InvalidSQLError(
            f"新增列 {col.name} 不可为 NULL：ALTER TABLE ADD COLUMN "
            f"要求列必须可空，否则无法为已有数据行填充值"
        )
    if col.primary_key:
        raise InvalidSQLError(
            f"新增列 {col.name} 为主键：ALTER TABLE ADD COLUMN 不支持添加主键列"
        )


def _check_existing_column(col: Column, existing: sqlite3.Row, table_name: str) -> None:
    """检查已有列与代码定义是否一致，不一致时抛出异常。"""
    if col.col_type.upper() != existing["type"].upper():
        raise InvalidSQLError(
            f"表 {table_name} 列 {col.name} 类型冲突："
            f"代码定义 {col.col_type}，数据库中为 {existing['type']}"
        )
    existing_not_null = bool(existing["notnull"])
    if (not col.nullable) != existing_not_null:
        raise InvalidSQLError(
            f"表 {table_name} 列 {col.name} 约束冲突："
            f"代码定义 nullable={col.nullable}，数据库中 "
            f"{'NOT NULL' if existing_not_null else 'NULLABLE'}"
        )
    col_pk = 1 if col.primary_key else 0
    if col_pk != existing["pk"]:
        raise InvalidSQLError(
            f"表 {table_name} 列 {col.name} 主键属性冲突："
            f"代码定义 primary_key={col.primary_key}，数据库中 "
            f"{'是主键' if existing['pk'] else '非主键'}"
        )


# ---------------------------------------------------------------------------
# DB 类
# ---------------------------------------------------------------------------

class DB:
    """数据库管理器，每个事务返回独立的连接，保证隔离。"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or config.DB_PATH
        self.table_infos = {}

    def _connect(self) -> sqlite3.Connection:
        """建立新连接，统一设置 row_factory 并启用 WAL 模式。"""
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

    def init(self, table_infos: dict[str, List[Column]]) -> None:
        """
        根据表信息初始化数据库。

        若表已存在：
        - 缺失的列通过 ``ALTER TABLE ADD COLUMN`` 自动补齐（不可空或主键列抛出异常）。
        - 已有列与代码定义不一致时抛出异常，不自动修改已有表结构。
        """
        with self.transaction() as conn:
            for table_name, desired_cols in table_infos.items():
                if not desired_cols:
                    continue
                Column.check(table_name)
                for col in desired_cols:
                    Column.check(col.name)

                existing = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,)
                ).fetchone()

                if existing is None:
                    # ---- 表不存在：直接创建 ----
                    cols_sql = ", ".join(col.sql for col in desired_cols)
                    conn.execute(f"CREATE TABLE {table_name} ({cols_sql})")
                else:
                    # ---- 表已存在：补齐新列，检查已有列 ----
                    existing_cols = {
                        row["name"]: row for row in conn.execute(f"PRAGMA table_info({table_name})")
                    }
                    for col in desired_cols:
                        existing_info = existing_cols.get(col.name)
                        if existing_info is None:
                            _check_addition_column(col)
                            conn.execute(
                                f"ALTER TABLE {table_name} "
                                f"ADD COLUMN {col.sql}"
                            )
                        else:
                            _check_existing_column(col, existing_info, table_name)

                # 建索引
                for col in desired_cols:
                    if not col.index:
                        continue
                    idx_sql = (
                        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_{col.name} "
                        f"ON {table_name}({col.name})"
                    )
                    conn.execute(idx_sql)
            self.table_infos.update(table_infos)

    # ---- 自动生成 INSERT SQL ----

    def insert_sql(self, table_name: str) -> str:
        """根据 表名 自动生成 INSERT 语句。"""
        col_names = [c.name for c in self.table_infos[table_name]]
        cols = ", ".join(col_names)
        vals = ", ".join(f":{n}" for n in col_names)
        return f"INSERT INTO {table_name} ({cols}) VALUES ({vals})"
    

class _TransactionContext:
    """写事务上下文管理器：BEGIN IMMEDIATE，阻塞写入者并发。"""

    def __init__(self, db: DB):
        self.db = db
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> sqlite3.Connection:
        self.conn = self.db._connect()
        self.conn.db = self.db
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
        self.conn.db = self.db
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
