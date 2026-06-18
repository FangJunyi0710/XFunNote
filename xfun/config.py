"""
集中管理所有配置，从 .env 和环境变量读取。

其他模块不应直接调用 os.environ.get()，
统一通过此模块获取配置。
"""

import os
from dotenv import load_dotenv

# 加载 .env 文件（优先当前目录，其次项目根目录）
load_dotenv()


# ---- 用户 ----

XFUN_USER = os.environ.get("XFUN_USER", "default")


# ---- 数据库 ----

DB_PATH = f"data/{XFUN_USER}.db"


# ---- AI ----

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL")
