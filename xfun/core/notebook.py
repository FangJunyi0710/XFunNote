"""
所有 Notebook 的公共抽象基类。

每个具体 Notebook（plan / diary / accumulation / ...）必须继承 Notebook，
定义自己的数据库列 schema，并实现核心 CRUD 方法。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .db import Column, Filter
from ..utils.time_utils import now_str


# ---------------------------------------------------------------------------
# 通用基类列定义 —— 所有本子共有的字段
# ---------------------------------------------------------------------------

BASE_COLUMNS = [
    Column("id",         "TEXT", primary_key=True, nullable=False, auto=True),
    Column("content",    "TEXT", nullable=False),
    Column("created_at", "TEXT", nullable=False, auto=True),
    Column("updated_at", "TEXT", nullable=False, auto=True),
    Column("tags",       "TEXT", nullable=True),
    Column("ai_note",    "TEXT", nullable=True),
]


class Notebook(ABC):
    """
    Notebook 基类 —— 定义本子的 schema 与 CRUD 契约。

    子类必须：
    1. 设置 name 属性（本子名称）
    2. 定义 _extra_columns 类属性（本子特有列，不含基类通用列）
    3. 实现 add / list / delete / search
    4. （可选）重写 _serialize / _deserialize 控制存取格式

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

    # ---- 序列化 / 反序列化 ----

    def _serialize(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        写入数据库前的序列化。子类可重写以做转换（如 list→json）。
        默认直接透传。
        """
        return entry

    def _deserialize(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        从数据库读出后的反序列化。子类可重写以做转换（如 json→list）。
        默认直接透传。
        """
        return row

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
        for col in self.columns:
            if col.nullable and col.name not in entry:
                entry[col.name] = None

    # ---- 抽象 CRUD ----

    @abstractmethod
    def add(self, conn, entry: Dict[str, Any]) -> str:
        """
        添加一条条目。

        Parameters
        ----------
        conn : sqlite3.Connection
            事务连接，由上层通过 db.transaction() 提供。
        entry : dict
            字段 → 值的映射，必须包含 columns 中定义的所有 NOT NULL 列。

        Returns
        -------
        str
            新条目的 ID。
        """
        ...

    @abstractmethod
    def list(self, conn, filters: List[Filter], *,
             order_by: Optional[str] = None,
             limit: int = 50,
             offset: int = 0) -> List[Dict[str, Any]]:
        """
        按筛选条件列出条目。

        Parameters
        ----------
        conn : sqlite3.Connection
            事务连接，由上层通过 db.transaction() 提供。
        filters : List[Filter]
            筛选条件列表，不允许为空。
        order_by : str, optional
            排序列名，默认无排序。
        limit : int
            最大返回条数，默认 50。
        offset : int
            偏移量，默认 0。

        Returns
        -------
        List[Dict[str, Any]]
        """
        ...

    @abstractmethod
    def delete(self, conn, entry_id: str) -> bool:
        """
        删除指定条目。

        Parameters
        ----------
        conn : sqlite3.Connection
            事务连接，由上层通过 db.transaction() 提供。
        entry_id : str
            条目 ID。

        Returns
        -------
        bool
            是否删除成功。
        """
        ...

    @abstractmethod
    def search(self, conn, query: str, *, limit: int = 50) -> List[Dict[str, Any]]:
        """
        全文搜索。

        Parameters
        ----------
        conn : sqlite3.Connection
            事务连接，由上层通过 db.transaction() 提供。
        query : str
            搜索关键词。
        limit : int
            最大返回条数，默认 50。

        Returns
        -------
        List[Dict[str, Any]]
        """
        ...

    # ---- 可选钩子 ----

    def summary(self, conn) -> str:
        """返回本子的概览摘要，供 AI 日报/周报使用。"""
        return f"[{self.name}] (暂无摘要)"

    # ---- 内置 ----

    def __repr__(self) -> str:
        return f"<Notebook:{self.name}>"

    def __str__(self) -> str:
        return self.name or self.__class__.__name__
