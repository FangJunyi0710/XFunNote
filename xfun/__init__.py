from .core.db       import DB
from .core.notebook import Notebook
from .notebooks.plan         import PlanNotebook
from .notebooks.diary        import DiaryNotebook
from .notebooks.word         import WordNotebook
from .notebooks.accumulation import AccumulationNotebook
from .notebooks.aimemory     import AIMemoryNotebook

db: DB = DB()
registry: dict[str, Notebook] = {
    "plan":         PlanNotebook(),
    "diary":        DiaryNotebook(),
    "word":         WordNotebook(),
    "accumulation": AccumulationNotebook(),
    "aimemory":     AIMemoryNotebook(),
}

def init_db(conn):
    db.init(conn, {name: nb.columns for name, nb in registry.items()})

with db.transaction() as conn:
    init_db(conn)

__all__ = ["db", "registry"]
