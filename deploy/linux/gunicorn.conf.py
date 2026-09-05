"""Gunicorn 配置：Linux 生产环境用。"""

import os

bind = "127.0.0.1:8000"
workers = int(os.getenv("GUNICORN_WORKERS", "1"))
worker_class = "sync"
preload_app = True

timeout = 60
keepalive = 5
max_requests = 1000
max_requests_jitter = 50

accesslog = "-"
errorlog = "-"
loglevel = "info"

proc_name = "xfunnote"