"""FastAPI 依赖注入：获取 DB 实例与权限。"""

from xfun import db
from xfun.core.view import Permission, root_permission


def get_root_permission() -> Permission:
    """返回 root 权限（全读全写），当前默认所有 API 使用此权限。"""
    return root_permission(db)
