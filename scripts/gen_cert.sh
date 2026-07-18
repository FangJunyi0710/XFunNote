#!/bin/bash
# 生成本地自签名证书用于开发/内网测试
# 用法: ./scripts/gen_cert.sh

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
CERT_DIR_ABS="$SCRIPT_DIR/../certs"
mkdir -p "$CERT_DIR_ABS"

if [[ -f "$CERT_DIR_ABS/cert.pem" && -f "$CERT_DIR_ABS/key.pem" ]]; then
    echo "证书已存在，跳过生成。如需重新生成，请先删除 $CERT_DIR_ABS/ 下的文件。"
    echo ""
    echo "rm $CERT_DIR_ABS/cert.pem $CERT_DIR_ABS/key.pem"
    exit 0
fi

# 尝试从 .env 读取 VITE_HOST
ENV_FILE="$SCRIPT_DIR/../.env"
HOSTNAME=""
if [ -f "$ENV_FILE" ]; then
    VITE_HOST=$(grep -E '^VITE_HOST=' "$ENV_FILE" | head -n1 | cut -d '=' -f2- | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
    if [ -n "$VITE_HOST" ]; then
        HOSTNAME="$VITE_HOST"
    fi
fi

# 若未从 .env 获取，则使用系统主机名
if [ -z "$HOSTNAME" ]; then
    HOSTNAME=$(hostname)
fi

# 获取所有非 127.0.0.1 的 IPv4 地址，拼接为 "IP:xxx,IP:yyy" 格式
IP_LIST=$(hostname -I | tr ' ' ',' | sed 's/,$//')
SAN_IPS=""
if [ -n "$IP_LIST" ]; then
    SAN_IPS=$(echo "$IP_LIST" | awk -F',' '{for(i=1;i<=NF;i++) printf "IP:%s,", $i}' | sed 's/,$//')
fi

# 构建 subjectAltName
SAN="DNS:localhost,DNS:*.local,IP:127.0.0.1"
if [ -n "$HOSTNAME" ] && [ "$HOSTNAME" != "localhost" ]; then
    SAN="$SAN,DNS:$HOSTNAME"
fi
if [ -n "$SAN_IPS" ]; then
    SAN="$SAN,$SAN_IPS"
fi

openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout "$CERT_DIR_ABS/key.pem" \
    -out "$CERT_DIR_ABS/cert.pem" \
    -subj "/CN=$HOSTNAME" \
    -addext "subjectAltName = $SAN"

echo "自签名证书已生成到 $CERT_DIR_ABS/"
echo "  cert.pem — 证书文件"
echo "  key.pem  — 私钥文件"
echo ""
echo "在 .env 中配置:"
echo ""
echo "SSL_CERT_PATH=./certs/cert.pem"
echo "SSL_KEY_PATH=./certs/key.pem"