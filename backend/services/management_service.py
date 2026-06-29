"""数据库管理和视图文件管理业务逻辑。"""

import json
from pathlib import Path

from xfun import db, init_db


def init_database() -> str:
    """初始化数据库：建表/补齐缺失列/建索引。"""
    with db.transaction() as conn:
        init_db(conn)
    return "数据库初始化完成"


def backup_database() -> str:
    """在线热备份数据库。"""
    with db.read_transaction() as conn:
        path = db.backup(conn)
    return f"备份完成: {path}"


def reset_database(backup_first: bool = True) -> str:
    """重置数据库：清空所有表并重新初始化。"""
    with db.read_transaction() as conn:
        if backup_first:
            db.backup(conn)
    with db.transaction() as conn:
        db.reset(conn)
    return "数据库已重置"


# ---- 视图文件管理 ----

_VIEWS_DIR = Path(__file__).resolve().parent.parent.parent / "input"


def _ensure_views_dir() -> None:
    _VIEWS_DIR.mkdir(parents=True, exist_ok=True)
    (_VIEWS_DIR / ".gitkeep").touch(exist_ok=True)


def list_views() -> list[dict]:
    """列出所有保存的视图文件。"""
    _ensure_views_dir()
    views = []
    for f in sorted(_VIEWS_DIR.glob("*.json")):
        views.append({"name": f.stem, "path": str(f.name)})
    return views


def get_view(name: str) -> dict | None:
    """读取指定视图文件。"""
    _ensure_views_dir()
    path = _VIEWS_DIR / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_view(name: str, data: dict) -> None:
    """保存/覆盖视图文件。"""
    _ensure_views_dir()
    path = _VIEWS_DIR / f"{name}.json"
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def delete_view(name: str) -> bool:
    """删除视图文件。"""
    _ensure_views_dir()
    path = _VIEWS_DIR / f"{name}.json"
    if path.exists():
        path.unlink()
        return True
    return False
