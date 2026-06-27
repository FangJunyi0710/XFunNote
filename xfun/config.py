"""
集中管理所有配置，从 .env 和环境变量读取。

其他模块不应直接调用 os.environ.get()，
统一通过此模块获取配置。
"""

import os
from dotenv import load_dotenv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 加载 .env 文件（优先当前目录，其次项目根目录）
load_dotenv(str(PROJECT_ROOT / ".env"))

# ---- 用户 ----

XFUN_USER = os.environ.get("XFUN_USER", "default")


# ---- 数据库 ----
DB_PATH = str(PROJECT_ROOT / "data" / f"{XFUN_USER}.db")


# ---- AI ----

LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL")
LLM_MODEL = os.environ.get("LLM_MODEL")
