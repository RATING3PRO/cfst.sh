#!/usr/bin/env bash
set -euo pipefail

############################################
# 基本配置（修改WORKDIR并下载其他文件）
############################################
WORKDIR="/opt/cfst"
PY_SCRIPT="$WORKDIR/select_best_ip.py"
PYTHON="$WORKDIR/venv/bin/python"
OUT_FILE="$WORKDIR/best.txt"

cd "$WORKDIR"

############################################
# 检查环境
############################################
if [ ! -x "$PYTHON" ]; then
    echo "未找到 Python 解释器或不可执行"
    exit 1
fi

if [ ! -f "$PY_SCRIPT" ]; then
    echo "未找到 select_best_ip.py"
    exit 1
fi

############################################
# 下载并 tcping 测速，选出延迟最低的 IP
############################################
echo "开始下载并测速..."
"$PYTHON" "$PY_SCRIPT"

############################################
# 检查结果
############################################
if [ ! -s "$OUT_FILE" ]; then
    echo "未获取到可用 IP"
    exit 2
fi

echo "最终 IP 列表："
cat "$OUT_FILE"

############################################
# 调用 Python 更新 DNS （确保有对应py文件）
############################################
echo "开始更新华为云 DNS..."
"$PYTHON" "$WORKDIR/hw_dns_update.py"

echo "任务完成"
