#!/bin/bash
# 用法：sudo ./update_avahi_hostname.sh
# 从项目根目录的 .env 文件读取 VITE_HOST，并自动去除 .local 后缀作为 Avahi 主机名。

set -euo pipefail

# 获取脚本所在目录（假设脚本位于项目根目录下的 scripts/ 中）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# 检查 .env 是否存在
if [ ! -f "$ENV_FILE" ]; then
    echo "错误：.env 文件不存在于 $ENV_FILE，无法获取主机名。"
    exit 1
fi

# 读取 VITE_HOST，去除首尾空格、引号
VITE_HOST=$(grep -E '^VITE_HOST=' "$ENV_FILE" | head -n1 | sed -E 's/^VITE_HOST=//' | sed -E 's/^["\x27]//;s/["\x27]$//' | sed -E 's/\s*$//')

if [ -z "$VITE_HOST" ]; then
    echo "错误：.env 中未找到 VITE_HOST 变量或值为空。"
    exit 1
fi

# 去掉 .local 后缀（如果存在）
NEW_HOSTNAME="${VITE_HOST%.local}"

if [ -z "$NEW_HOSTNAME" ]; then
    echo "错误：提取的主机名为空。"
    exit 1
fi

echo "从 .env 读取 VITE_HOST=${VITE_HOST}，提取主机名：${NEW_HOSTNAME}"

CONFIG_FILE="/etc/avahi/avahi-daemon.conf"
BACKUP_FILE="${CONFIG_FILE}.bak.$(date +%Y%m%d_%H%M%S)"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "错误：配置文件 $CONFIG_FILE 不存在。"
    exit 1
fi

# 备份原文件
sudo cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "已备份原配置到 $BACKUP_FILE"

# 删除所有 host-name 行（注释或未注释）
sudo sed -i "/^\s*#\?\s*host-name=/d" "$CONFIG_FILE"

# 确保 [server] 段存在
if ! grep -q "^\[server\]" "$CONFIG_FILE"; then
    echo "[server]" | sudo tee -a "$CONFIG_FILE" >/dev/null
fi

# 在 [server] 段后插入新 host-name
sudo sed -i "/^\[server\]/a host-name=${NEW_HOSTNAME}" "$CONFIG_FILE"

echo "已设置 host-name = ${NEW_HOSTNAME}"

# 重启 Avahi 服务
sudo systemctl restart avahi-daemon.service
echo "Avahi 已重启，新的 .local 域名生效：${NEW_HOSTNAME}.local"
