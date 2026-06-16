"""
所有 Notebook 的公共抽象基类。

每个具体 Notebook（plan / diary / accumulation / ...）必须继承 Notebook，
定义自己的数据库列 schema，并实现核心 CRUD 方法。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .db import Column, Filter


class Notebook(ABC):
    """
    Notebook 基类 —— 定义本子的 schema 与 CRUD 契约。

    子类必须：
    1. 设置 name 属性（本子名称）
    2. 定义 columns 类属性（数据库列 schema）
    3. 实现 add / list / delete / search
    4. （可选）重写 _serialize / _deserialize 控制存取格式
    """

    # ---- 子类必须设定 ----

    name: str = ""                     # 本子名称，如 "plan"
    columns: List[Column] = []         # 数据库列定义

    # ---- 数据库操作 ----

    def init_table(self, db) -> None:
        """
        根据 self.columns 自动建表。

        Parameters
        ----------
        db : DB
            数据库实例，需提供 execute(sql, params) 方法。
        """
        if not self.columns:
            return
        cols_sql = ", ".join(col.sql for col in self.columns)
        sql = f"CREATE TABLE IF NOT EXISTS {self.name} ({cols_sql})"
        db.execute(sql)
        # 建索引
        for col in self.columns:
            if col.index:
                idx_sql = (
                    f"CREATE INDEX IF NOT EXISTS idx_{self.name}_{col.name} "
                    f"ON {self.name}({col.name})"
                )
                db.execute(idx_sql)

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

    # ---- 抽象 CRUD ----

    @abstractmethod
    def add(self, entry: Dict[str, Any]) -> str:
        """
        添加一条条目。

        Parameters
        ----------
        entry : dict
            字段 → 值的映射，必须包含 columns 中定义的所有 NOT NULL 列。

        Returns
        -------
        str
            新条目的 ID。
        """
        ...

    @abstractmethod
    def list(self, filters: List[Filter], *,
             order_by: Optional[str] = None,
             limit: int = 50,
             offset: int = 0) -> List[Dict[str, Any]]:
        """
        按筛选条件列出条目。

        Parameters
        ----------
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

        Raises
        ------
        ValueError
            若 filters 为空。
        """
        ...

    @abstractmethod
    def delete(self, entry_id: str) -> bool:
        """
        删除指定条目。

        Returns
        -------
        bool
            是否删除成功。
        """
        ...

    @abstractmethod
    def search(self, query: str, *, limit: int = 50) -> List[Dict[str, Any]]:
        """
        全文搜索。

        Returns
        -------
        List[Dict[str, Any]]
        """
        ...

    # ---- 可选钩子 ----

    def summary(self) -> str:
        """返回本子的概览摘要，供 AI 日报/周报使用。"""
        return f"[{self.name}] (暂无摘要)"

    # ---- 内置 ----

    def __repr__(self) -> str:
        return f"<Notebook:{self.name}>"

    def __str__(self) -> str:
        return self.name or self.__class__.__name__
