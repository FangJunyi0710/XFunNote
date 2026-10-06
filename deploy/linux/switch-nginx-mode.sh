#!/bin/bash
# 用法: switch-nginx-mode.sh [http|https] [--cert-path PATH] [--key-path PATH]

set -euo pipefail

HTTP_CONF="/etc/nginx/sites-available/xfunnote-http.conf"
HTTPS_TEMPLATE="/opt/xfunnote/deploy/linux/nginx-https.conf.template"
HTTPS_CONF="/etc/nginx/sites-available/xfunnote-https.conf"
ACTIVE_LINK="/etc/nginx/sites-enabled/xfunnote"

show_usage() {
    echo "用法: $0 [http|https] [--cert-path PATH] [--key-path PATH]"
    echo "  http           切换到 HTTP 模式（仅 80 端口）"
    echo "  https          切换到 HTTPS 模式（需提供证书路径）"
    echo "  --cert-path    证书文件路径（必填）"
    echo "  --key-path     私钥文件路径（必填）"
    echo ""
    current=$(readlink -f "$ACTIVE_LINK" 2>/dev/null | xargs basename || echo "未配置")
    echo "当前模式: $current"
}

if [[ $# -eq 0 ]]; then
    show_usage
    exit 0
fi

MODE="$1"
shift

case "$MODE" in
    http)
        ln -sf "$HTTP_CONF" "$ACTIVE_LINK"
        echo "已切换到 HTTP 模式（端口 80）"
        ;;
    https)
        CERT_PATH=""
        KEY_PATH=""
        while [[ $# -gt 0 ]]; do
            case $1 in
                --cert-path) CERT_PATH="$2"; shift 2 ;;
                --key-path) KEY_PATH="$2"; shift 2 ;;
                *) echo "未知参数: $1"; show_usage; exit 1 ;;
            esac
        done
        [[ -z "$CERT_PATH" || -z "$KEY_PATH" ]] && { echo "错误：HTTPS 模式必须提供 --cert-path 和 --key-path"; show_usage; exit 1; }
        [[ ! -f "$CERT_PATH" || ! -f "$KEY_PATH" ]] && { echo "错误：证书文件不存在"; exit 1; }

        # 从模板读取，替换占位符，写入目标配置
        sed -e "s|__SSL_CERT_PATH__|$CERT_PATH|g" \
            -e "s|__SSL_KEY_PATH__|$KEY_PATH|g" \
            "$HTTPS_TEMPLATE" > "$HTTPS_CONF"

        ln -sf "$HTTPS_CONF" "$ACTIVE_LINK"
        echo "已切换到 HTTPS 模式（端口 80→443）"
        echo "  证书: $CERT_PATH"
        echo "  私钥: $KEY_PATH"
        ;;
    *)
        echo "错误：模式必须是 http 或 https"
        show_usage
        exit 1
        ;;
esac

nginx -t && systemctl reload nginx
echo "Nginx 已重载"