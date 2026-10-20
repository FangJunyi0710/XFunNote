#!/bin/sh
# XFunNote 容器入口：单进程运行 Kotlin/Ktor 服务器。
# 服务器同时托管 API（/api/*）与前端静态文件，无需 nginx。
set -eu

DATA_DIR="${XFUN_DATA_DIR:-/data}"
mkdir -p "$DATA_DIR"

# 首次启动若未提供 ROOT_TOKEN，则生成并写入数据目录 .env（持久化，重启复用）
ENV_FILE="$DATA_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    if [ -z "${ROOT_TOKEN:-}" ]; then
        ROOT_TOKEN="sk-$(head -c 32 /dev/urandom | base64 | tr '+/' '-_' | tr -d '=')"
        echo "==> 未检测到 ROOT_TOKEN，已自动生成并写入 $ENV_FILE"
    fi
    echo "ROOT_TOKEN=\"$ROOT_TOKEN\"" > "$ENV_FILE"
    chmod 600 "$ENV_FILE"
fi

# 加载 .env 中的 ROOT_TOKEN 到当前环境（Kotlin 服务器仅读取环境变量）
. "$ENV_FILE"
export ROOT_TOKEN

echo "==> 启动 XFunNote (Kotlin/Ktor) :${BACKEND_PORT:-80}"
# exec 使 Java 成为 PID 1，直接接收 Docker 的停止信号
exec java $JAVA_OPTS -jar /app/xfunnote-server.jar
