from .core.db       import DB
from .core.registry import Registry

db       = DB()
registry = Registry()

__all__ = ["db", "registry"]
