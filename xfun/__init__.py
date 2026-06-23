from . import config
from .core.db       import DB
from .core.registry import Registry
from .notebooks.plan         import PlanNotebook
from .notebooks.diary        import DiaryNotebook
from .notebooks.word         import WordNotebook
from .notebooks.accumulation import AccumulationNotebook
from .notebooks.aimemory     import AIMemoryNotebook

db       = DB()
registry = Registry()

# 注册所有 Notebook
registry.register("plan",  PlanNotebook())
registry.register("diary", DiaryNotebook())
registry.register("word",  WordNotebook())
registry.register("accumulation", AccumulationNotebook())
registry.register("aimemory",     AIMemoryNotebook())

db.init({nb.name: nb.columns for nb in registry})

__all__ = ["db", "registry"]
