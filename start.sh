#!/usr/bin/env bash
# 视频号下载器 - 一键启动 (macOS / Linux)

set -e

cd "$(dirname "$0")"

BIN_NAME="wx-dl"
if [ "$(uname -s)" = "Darwin" ] && [ "$(uname -m)" = "arm64" ]; then
    BIN_NAME="wx-dl-arm64"
fi

if [ ! -f "bin/$BIN_NAME" ]; then
    echo "[ERROR] 找不到 bin/$BIN_NAME"
    echo "请先编译: cd scribe-studio/backend/core && go build -o ../../../scribe-transcribe/bin/$BIN_NAME ."
    exit 1
fi

echo "========================================"
echo "  视频号下载器 - 一键启动"
echo "========================================"
echo ""
echo "[INFO] 启动视频号代理服务..."
echo "[INFO] API 地址: http://127.0.0.1:2022"
echo "[INFO] 代理端口: 2023"
echo ""
echo "请在手机 WiFi 中配置 HTTP 代理:"
echo "  服务器: $(ipconfig getifaddr en0 2>/dev/null || hostname -I | awk '{print $1}')"
echo "  端口:   2023"
echo ""

exec "./bin/$BIN_NAME" --hostname 127.0.0.1 --port 2023
