from .core.db       import DB
from .core.notebook import Notebook
from .system_tables import SYSTEM_TABLES, register_system_hooks
from .notebooks.plan         import PlanNotebook
from .notebooks.diary        import DiaryNotebook
from .notebooks.word         import WordNotebook
from .notebooks.accumulation import AccumulationNotebook
from .notebooks.aimemory     import AIMemoryNotebook
from .notebooks.timeline     import TimelineNotebook
from .notebooks.schedule     import ScheduleNotebook
from .notebooks.ledger       import LedgerNotebook

registry: dict[str, Notebook] = {
    "plan":         PlanNotebook(),
    "diary":        DiaryNotebook(),
    "word":         WordNotebook(),
    "accumulation": AccumulationNotebook(),
    "aimemory":     AIMemoryNotebook(),
    "timeline":     TimelineNotebook(),
    "schedule":     ScheduleNotebook(),
    "ledger":       LedgerNotebook(),
}

def init_db(db: DB):
    """初始化数据库（注册钩子 + 建用户表 + 建系统表）。"""
    # 注册本子钩子到 DB（CRUD 由 DB 统一管理）
    for name, nb in registry.items():
        db.register_hooks(name, pre_add=nb._pre_add, validate=nb._validate, autofill=nb._autofill)

    # 注册系统表钩子
    register_system_hooks(db)

    # 注册钩子后才初始化表（init 内部自管理事务）
    db.table_infos.update({name: nb.columns for name, nb in registry.items()})
    db.table_infos.update(SYSTEM_TABLES)
