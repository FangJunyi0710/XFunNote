from . import config
from .core.db       import DB
from .core.registry import Registry
from .notebooks.plan import PlanNotebook

db       = DB()
registry = Registry()

# 注册所有 Notebook
registry.register("plan", PlanNotebook())

__all__ = ["db", "registry"]
