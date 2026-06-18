from . import config
from .core.db       import DB
from .core.registry import Registry
from .notebooks.plan  import PlanNotebook
from .notebooks.diary import DiaryNotebook
from .notebooks.word  import WordNotebook

db       = DB()
registry = Registry()

# 注册所有 Notebook
registry.register("plan",  PlanNotebook())
registry.register("diary", DiaryNotebook())
registry.register("word",  WordNotebook())

__all__ = ["db", "registry"]
