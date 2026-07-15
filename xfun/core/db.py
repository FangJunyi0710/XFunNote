from __future__ import annotations

from pathlib import Path
import re
import sqlite3
from dataclasses import dataclass
from typing import Any

from future_uuid import uuid7

from .. import config
from ..utils.time_utils import now_str, timestamp_str
from .errors import EntryInvalidError, InvalidSQLError


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
    unique: bool = False
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
        InvalidSQLError
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
        if self.unique:
            parts.append("UNIQUE")
        if not self.nullable:
            parts.append("NOT NULL")

        return " ".join(parts)

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
    if col.unique:
        raise InvalidSQLError(
            f"新增列 {col.name} 为 UNIQUE：ALTER TABLE ADD COLUMN 不支持添加 UNIQUE 约束列"
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
    # UNIQUE 约束无法通过 PRAGMA table_info 获取，不做兼容性检查


# ---------------------------------------------------------------------------
# DB 类
# ---------------------------------------------------------------------------

class DB:
    """数据库管理器，每个事务返回独立的连接，保证隔离。"""

    def __init__(self, db_path: str = ""):
        self.db_path = db_path or config.DB_PATH
        self.table_infos: dict[str, list[Column]] = {}
        # {table_name: {"pre_add": callable, "validate": callable, "autofill": callable}}
        self.hooks: dict[str, dict[str, Any]] = {}

    def register_hooks(self, table_name: str, *, pre_add=None, validate=None, autofill=None) -> None:
        """注册本子钩子函数。

        Parameters
        ----------
        table_name : str
            表名。
        pre_add : callable, optional
            添加前钩子，签名 ``(conn, entries: list[dict]) -> None``，用于批量修改条目。
        validate : callable, optional
            校验钩子，签名 ``(entry: dict) -> None``，用于本子特有校验。
        autofill : callable, optional
            自动填充钩子，签名 ``(entry: dict) -> None``，用于填充本子特有字段。
        """
        self.hooks[table_name] = {
            "pre_add": pre_add,
            "validate": validate,
            "autofill": autofill,
        }

    def cols(self, table: str) -> list[str]:
        """返回指定表的所有列名。"""
        return [c.name for c in self.table_infos[table]]

    def _connect(self) -> sqlite3.Connection:
        """建立新连接，统一设置 row_factory 并启用 WAL 模式。"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
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

    @staticmethod
    def _table_exists(conn: _ConnWrapper, table_name: str) -> bool:
        """检查表是否存在。"""
        return conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        ).fetchone() is not None

    @staticmethod
    def _create_table(conn: _ConnWrapper, table_name: str, cols: list[Column]) -> None:
        """创建新表。"""
        cols_sql = ", ".join(col.sql for col in cols)
        # 只会被 init 调用，其已检查表名
        conn.execute(f"CREATE TABLE {table_name} ({cols_sql})")
    
    @staticmethod
    def _sync_existing_table(conn: _ConnWrapper, table_name: str, desired_cols: list[Column]) -> None:
        """补齐缺失列并检查已有列的一致性。

        双向检查：
        - 代码中有但数据库中无 → ALTER TABLE ADD COLUMN 补齐
        - 代码中有且数据库中有 → 检查类型/可空性/主键一致性
        - 数据库中有但代码中无 → 报错，防止残留列导致 NOT NULL 约束冲突
        """
        # 只会被 init 调用，其已检查表名
        existing_cols = {
            row["name"]: row
            for row in conn.execute(f"PRAGMA table_info({table_name})")
        }
        desired_names = {col.name for col in desired_cols}

        # 反向检查：数据库中有但代码中无的多余列
        for existing_name in existing_cols:
            if existing_name not in desired_names:
                raise InvalidSQLError(
                    f"表 {table_name} 存在代码未定义的列 {existing_name!r}："
                    f"请手动删除该列或重置数据库"
                )

        for col in desired_cols:
            existing_info = existing_cols.get(col.name)
            if existing_info is None:
                _check_addition_column(col)
                conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {col.sql}")
            else:
                _check_existing_column(col, existing_info, table_name)

    @staticmethod
    def _create_indexes(conn: _ConnWrapper, table_name: str, cols: list[Column]) -> None:
        """为指定列建索引。"""
        # 只会被 init 调用，其已检查表名
        for col in cols:
            if not col.index:
                continue
            # UNIQUE 约束会自动创建索引，无需重复创建
            if col.unique:
                continue
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_{col.name} "
                f"ON {table_name}({col.name})"
            )

    def init(self, conn, table_infos: dict[str, list[Column]]) -> None:
        """
        根据表信息初始化数据库。

        若表已存在：
        - 缺失的列通过 ``ALTER TABLE ADD COLUMN`` 自动补齐（不可空或主键列抛出异常）。
        - 已有列与代码定义不一致时抛出异常，不自动修改已有表结构。
        """
        for table_name, desired_cols in table_infos.items():
            if not desired_cols:
                continue
            Column.check(table_name)
            for col in desired_cols:
                Column.check(col.name)

            if DB._table_exists(conn, table_name):
                DB._sync_existing_table(conn, table_name, desired_cols)
            else:
                DB._create_table(conn, table_name, desired_cols)

            DB._create_indexes(conn, table_name, desired_cols)

        self.table_infos.update(table_infos)

    # ---- 备份与重置 ----

    def backup(self) -> str:
        """
        在线热备份数据库到 ``data/backups/{basename}.backup.{timestamp}``。
        内部使用无事务连接，调用方无需传连接。
        """
        dst = Path(self.db_path).parent / "backups" / f"{Path(self.db_path).stem}.backup.{timestamp_str()}"
        src_conn = self._connect()
        dest_conn = DB(str(dst))._connect()
        try:
            src_conn.backup(dest_conn)
        finally:
            src_conn.close()
            dest_conn.close()
        return str(dst)

    def restore(self, backup_path: str) -> str:
        """
        使用 SQLite 在线备份 API 从物理备份文件恢复数据库。
        对称于 :meth:`backup`，内部使用无事务连接。

        恢复前自动清理 ``-wal`` / ``-shm`` 残留文件。

        Parameters
        ----------
        backup_path : str
            备份文件路径。

        Returns
        -------
        str
            恢复来源的备份文件路径。

        Raises
        ------
        FileNotFoundError
            备份文件不存在。
        """
        src = Path(backup_path)
        if not src.exists():
            raise FileNotFoundError(f"备份文件不存在: {backup_path}")

        # 清理 -wal / -shm 残留，避免新旧页混用
        name = Path(self.db_path).name
        parent = Path(self.db_path).parent
        for ext in ('-wal', '-shm'):
            f = parent / f"{name}{ext}"
            f.unlink(missing_ok=True)

        # 反向备份 API：备份文件 → 当前数据库
        dest_conn = self._connect()
        src_conn = DB(str(src))._connect()
        try:
            src_conn.backup(dest_conn)
        finally:
            src_conn.close()
            dest_conn.close()

        return str(src)

    def reset(self, conn) -> None:
        """
        清空所有表并重新初始化。
        """
        # 查出数据库中所有用户表（排除 sqlite_% 系统表）
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        for (table_name,) in rows:
            conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        self.init(conn, self.table_infos)
# TODO init/reset 消除 conn 改为自管理事务

    # ---- 自动生成 INSERT SQL ----

    def insert_sql(self, table_name: str) -> str:
        """根据 表名 自动生成 INSERT 语句。"""
        col_names = [c.name for c in self.table_infos[table_name]]
        cols = ", ".join(col_names)
        vals = ", ".join(f":{n}" for n in col_names)
        return f"INSERT INTO {table_name} ({cols}) VALUES ({vals})"

    # ---- SELECT 语句 ----

    def select_sql(self, table_name: str, cols: list[str]) -> str:
        """
        生成完整 SELECT 语句。

        在 *cols* 中的列输出为 ``table_name.col``，
        不在 *cols* 中的表已有列输出为 ``NULL AS col``，
        保证结果集包含该表的所有列，未选中列值为 NULL。

        Parameters
        ----------
        table_name : str
            表名，须在 table_infos 中。
        cols : list[str]
            要选择的列名列表。

        Returns
        -------
        str
            完整 SELECT 查询语句，例如
            ``"SELECT plan.id, NULL AS content, plan.month, NULL AS seq FROM plan"``。
        """
        all_col_names = [c.name for c in self.table_infos[table_name]]
        pieces: list[str] = []
        for col in all_col_names:
            if col in cols:
                pieces.append(f"{table_name}.{col}")
            else:
                pieces.append(f"NULL AS {col}")
        return f"SELECT {', '.join(pieces)} FROM {table_name}"
    
    # ---- 钩子驱动的 CRUD ----

    def _validate_entry(self, table_name: str, entry: dict) -> None:
        """基础校验：检查非空非自动字段是否存在。"""
        for col in self.table_infos[table_name]:
            if not col.nullable and not col.auto:
                if col.name not in entry:
                    raise EntryInvalidError(
                        table_name, f"缺少必填字段 '{col.name}'"
                    )

    def _autofill_entry(self, table_name: str, entry: dict) -> None:
        """基础自动填充：按表实际列填充 id、时间戳、可空列补 None。"""
        cols = {c.name for c in self.table_infos[table_name]}

        if "id" in cols:
            entry["id"] = f"{table_name}-{str(uuid7())}"
        if "created_at" in cols:
            entry["created_at"] = now_str()
        if "updated_at" in cols:
            entry["updated_at"] = now_str()

        for col in self.table_infos[table_name]:
            if col.nullable and col.name not in entry:
                entry[col.name] = None

    def add_entries(self, conn, table_name: str, entries: list[dict]) -> list[str]:
        """批量添加条目（钩子驱动）。

        流程：pre_add(conn, entries) → 基础校验 → 本子校验 → 基础自动填充 → 本子自动填充 → INSERT。
        """
        hooks = self.hooks.get(table_name, {})
        pre_add = hooks.get("pre_add")
        validate = hooks.get("validate")
        autofill = hooks.get("autofill")

        if pre_add:
            pre_add(conn, entries)

        for entry in entries:
            self._validate_entry(table_name, entry)
            if validate:
                validate(entry)
            self._autofill_entry(table_name, entry)
            if autofill:
                autofill(entry)

        conn.executemany(self.insert_sql(table_name), entries)
        return [entry["id"] for entry in entries]

    def list_ids(self, conn, table_name: str, filter, *, order_by: str = "", limit: int = -1, offset: int = 0) -> list[str]:
        """按筛选条件列出 ID。"""
        from .filter import filter_to_sql

        where_sql, params = filter_to_sql(filter)
        sql = f"SELECT id FROM {table_name}"
        if where_sql:
            sql += f" WHERE {where_sql}"
        if order_by:
            Column.check_order_by(order_by)
            sql += f" ORDER BY {order_by}"
        sql += f" LIMIT {limit} OFFSET {offset}"
        rows = conn.execute(sql, params).fetchall()
        return [row["id"] for row in rows]
# TODO 消除 string +=

    def update_entries(self, conn, table_name: str, entry_ids: list[str], entry: dict) -> None:
        """批量更新条目。"""
        if not entry_ids:
            return
        for k in entry:
            Column.check(k)
        entry["updated_at"] = now_str()
        set_clause = ", ".join(f"{k} = :{k}" for k in entry)
        params = [{**entry, "id": eid} for eid in entry_ids]
        conn.executemany(
            f"UPDATE {table_name} SET {set_clause} WHERE id = :id", params
        )

    def delete_entries(self, conn, table_name: str, entry_ids: list[str]) -> None:
        """批量删除条目。"""
        if not entry_ids:
            return
        conn.executemany(
            f"DELETE FROM {table_name} WHERE id = :id",
            [{"id": eid} for eid in entry_ids],
        )



class _ConnWrapper:
    """轻量包装，使 conn.db 可在所有 Python 版本下工作。"""
    __slots__ = ('_conn', 'db')

    def __init__(self, conn: sqlite3.Connection, db: DB):
        self._conn = conn
        self.db = db

    def __getattr__(self, name: str):
        return getattr(self._conn, name)

class _TransactionContext:
    """写事务上下文管理器：BEGIN IMMEDIATE，阻塞写入者并发。"""

    def __init__(self, db: DB):
        self.db = db
        self.conn: sqlite3.Connection | None = None

    def __enter__(self) -> _ConnWrapper:
        self.conn = self.db._connect()
        self.conn.execute("BEGIN IMMEDIATE") # 主动加写锁，避免高并发下的 SQLITE_BUSY 重试
        return _ConnWrapper(self.conn, self.db)

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
        self.conn: sqlite3.Connection | None = None

    def __enter__(self) -> _ConnWrapper:
        self.conn = self.db._connect()
        self.conn.execute("BEGIN")  # 不加 IMMEDIATE，不阻塞写入
        return _ConnWrapper(self.conn, self.db)

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
