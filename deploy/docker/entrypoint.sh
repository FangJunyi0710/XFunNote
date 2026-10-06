#!/bin/sh
# XFunNote 容器入口：同时运行 uvicorn（内部 8000）与 nginx（对外 80）。
# 任一进程退出即整体退出，交由 Docker 重启策略处理。
set -eu

DATA_DIR="${XFUN_DATA_DIR:-/data}"
mkdir -p "$DATA_DIR"

# 首次启动若未提供 ROOT_TOKEN，则生成并写入数据目录 .env（供后端读取）
ENV_FILE="$DATA_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    if [ -z "${ROOT_TOKEN:-}" ]; then
        ROOT_TOKEN="sk-$(head -c 32 /dev/urandom | base64 | tr '+/' '-_' | tr -d '=')"
        echo "==> 未检测到 ROOT_TOKEN，已自动生成并写入 $ENV_FILE"
    fi
    echo "ROOT_TOKEN=\"$ROOT_TOKEN\"" > "$ENV_FILE"
    chmod 600 "$ENV_FILE"
fi

# 优雅退出：收到终止信号时结束两个子进程
cleanup() {
    kill "${BACKEND_PID:-}" "${NGINX_PID:-}" 2>/dev/null || true
}
trap cleanup TERM INT

# 启动后端（uvicorn，仅监听本地，由 nginx 反代）
echo "==> 启动后端 uvicorn 127.0.0.1:${BACKEND_PORT:-8000}"
uvicorn backend.main:app \
    --host 127.0.0.1 \
    --port "${BACKEND_PORT:-8000}" \
    --workers "${UVICORN_WORKERS:-1}" &
BACKEND_PID=$!

# 启动 nginx（前台运行，作为主进程）
echo "==> 启动 nginx :80"
nginx -g "daemon off;" &
NGINX_PID=$!

# 轮询两个进程，任一退出即整体退出（dash 不支持 wait -n）
while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$NGINX_PID" 2>/dev/null; do
    sleep 2
done

echo "==> 子进程退出，容器即将停止"
cleanup
# 返回仍在运行进程的退出码；若都退出则返回 0
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    wait "$BACKEND_PID" || STATUS=$?
else
    wait "$NGINX_PID" || STATUS=$?
fi
exit "${STATUS:-0}"

