"""
所有 Notebook 的公共抽象基类。

每个具体 Notebook（plan / diary / accumulation / ...）必须继承 Notebook，
定义自己的数据库列 schema，并实现核心 CRUD 方法。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .db import Column, Filter, build_where
from ..utils.time_utils import now_str


# ---------------------------------------------------------------------------
# 通用基类列定义 —— 所有本子共有的字段
# ---------------------------------------------------------------------------

BASE_COLUMNS = [
    Column("id",         "TEXT",    primary_key=True, nullable=False, auto=True),
    Column("content",    "TEXT",    nullable=False),
    Column("created_at", "TEXT",    nullable=False, auto=True),
    Column("updated_at", "TEXT",    nullable=False, auto=True),
    Column("tags",       "TEXT",    nullable=False, auto=True), # json 数组：list[str]
    Column("is_ai_gen",  "INTEGER", nullable=False, auto=True),
    Column("ai_tags",    "TEXT",    nullable=False, auto=True),
    Column("ai_note",    "TEXT",    nullable=True),
]


class Notebook(ABC):
    """
    Notebook 基类 —— 定义本子的 schema 与 CRUD 契约。

    子类必须：
    1. 设置 name 属性（本子名称）
    2. 定义 _extra_columns 类属性（本子特有列，不含基类通用列）
    3. 实现 list 抽象方法

    add / delete 已有基类默认实现（通过 _validate / _autofill 多态扩展）。
    columns 属性由 BASE_COLUMNS + _extra_columns 自动合并。
    """

    # ---- 子类必须设定 ----

    name: str = ""
    _extra_columns: List[Column] = []

    # ---- 合并列 ----

    @property
    def columns(self) -> List[Column]:
        """合并基类通用列 + 子类特有列"""
        return BASE_COLUMNS + self._extra_columns

    # ---- 通用查询方法 ----

    def get_by_id(self, conn, entry_ids: List[str]) -> List[Dict[str, Any]]:
        """根据 ID 列表批量查询，返回结果保持传入顺序，不存在的 ID 被跳过。"""
        if not entry_ids:
            return []
        placeholders = ", ".join(f":id_{i}" for i in range(len(entry_ids)))
        params = {f"id_{i}": eid for i, eid in enumerate(entry_ids)}
        rows = conn.execute(
            f"SELECT * FROM {self.name} WHERE id IN ({placeholders})",
            params,
        ).fetchall()
        result = {r["id"]: dict(r) for r in rows}
        return [result[eid] for eid in entry_ids if eid in result]

    # ---- 自动生成 INSERT SQL ----

    def _insert_sql(self) -> str:
        """根据 self.columns 自动生成 INSERT 语句。"""
        col_names = [c.name for c in self.columns]
        cols = ", ".join(col_names)
        vals = ", ".join(f":{n}" for n in col_names)
        return f"INSERT INTO {self.name} ({cols}) VALUES ({vals})"

    # ---- 数据库操作 ----

    def init_table(self, conn) -> None:
        """
        根据 self.columns 自动建表。

        Parameters
        ----------
        conn : sqlite3.Connection
            事务连接，由 db.init() 或 db.transaction() 提供。
        """
        if not self.columns:
            return
        cols_sql = ", ".join(col.sql for col in self.columns)
        sql = f"CREATE TABLE IF NOT EXISTS {self.name} ({cols_sql})"
        conn.execute(sql)
        # 建索引
        for col in self.columns:
            if col.index:
                idx_sql = (
                    f"CREATE INDEX IF NOT EXISTS idx_{self.name}_{col.name} "
                    f"ON {self.name}({col.name})"
                )
                conn.execute(idx_sql)

    # ---- 校验 & 自动填充（通用） ----

    def _validate(self, entry: Dict[str, Any]) -> None:
        """校验用户提供的必填字段（排除自动填充字段）。"""
        for col in self.columns:
            if not col.nullable and not col.auto:
                if col.name not in entry:
                    from .errors import EntryInvalidError
                    raise EntryInvalidError(
                        self.name, f"缺少必填字段 '{col.name}'"
                    )

    def _autofill(self, entry: Dict[str, Any], conn) -> None:
        """自动填充通用字段：时间戳、可空列补 None。子类可重写以补充自有逻辑。"""
        entry["created_at"] = now_str()
        entry["updated_at"] = now_str()
        entry.setdefault("tags","[]")
        entry.setdefault("ai_tags","[]")
        entry.setdefault("is_ai_gen", 0)
        for col in self.columns:
            if col.nullable and col.name not in entry:
                entry[col.name] = None

    # ---- CRUD ----

    def add(self, conn, entries: List[Dict[str, Any]]) -> List[str]:
        """
        批量添加条目。

        Parameters
        ----------
        conn : sqlite3.Connection
            事务连接，由上层通过 db.transaction() 提供。
        entries : list[dict]
            条目列表，每个 dict 为字段 → 值的映射。

        Returns
        -------
        list[str]
            新条目的 ID 列表。
        """
        for entry in entries:
            self._validate(entry)
            self._autofill(entry, conn)
        conn.executemany(self._insert_sql(), entries)
        return [entry["id"] for entry in entries]

    def list(self, conn, filter: Filter, *,
             order_by: Optional[str] = None,
             limit: int = -1,
             offset: int = 0) -> List[str]:
        """
        按筛选条件列出条目。

        Parameters
        ----------
        conn : sqlite3.Connection
            事务连接，由上层通过 db.transaction() 提供。
        filter : Filter
            筛选条件列表。
        order_by : str, optional
            排序列名，默认无排序。
        limit : int
            最大返回条数，默认 50。
        offset : int
            偏移量，默认 0。

        Returns
        -------
        List[str]
            ID 列表。
        """
        where_sql, params = build_where(filter)
        sql = f"SELECT id FROM {self.name}"
        if where_sql:
            sql += f" WHERE {where_sql}"
        if order_by:
            Column.check_order_by(order_by)
            sql += f" ORDER BY {order_by}"
        sql += f" LIMIT {limit} OFFSET {offset}"
        rows = conn.execute(sql, params).fetchall()
        return [row["id"] for row in rows]

    def delete(self, conn, entry_ids: List[str]) -> None:
        """
        批量删除条目。使用 executemany 逐条执行 DELETE。

        Parameters
        ----------
        conn : sqlite3.Connection
            事务连接，由上层通过 db.transaction() 提供。
        entry_ids : list[str]
            要删除的条目 ID 列表。
        """
        if not entry_ids:
            return
        conn.executemany(
            f"DELETE FROM {self.name} WHERE id = :id",
            [{"id": eid} for eid in entry_ids]
        )

    def update(self, conn, entry_ids: List[str], entry: Dict[str, Any]) -> None:
        """
        批量更新条目。

        Parameters
        ----------
        conn : sqlite3.Connection
            事务连接，由上层通过 db.transaction() 提供。
        entry_ids : list[str]
            要更新的条目 ID 列表。
        entry : dict
            要更新的字段映射，只包含需要修改的列。
        """
        if not entry_ids:
            return
        for k in entry:
            Column.check(k)
        set_clause = ", ".join(f"{k} = :{k}" for k in entry)
        entry["updated_at"] = now_str()
        set_clause += ", updated_at = :updated_at"

        params = [{**entry, "id": eid} for eid in entry_ids]
        conn.executemany(
            f"UPDATE {self.name} SET {set_clause} WHERE id = :id",
            params
        )

    # ---- 内置 ----

    def __repr__(self) -> str:
        return f"<Notebook:{self.name}>"

    def __str__(self) -> str:
        return self.name or self.__class__.__name__
