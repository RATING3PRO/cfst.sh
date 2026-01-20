#!/usr/bin/env bash
set -euo pipefail

############################################
# 基本配置（修改WORKDIR并下载其他文件）
############################################
WORKDIR="/opt/cfst"
CF_BINARY="$WORKDIR/CloudflareST"
IP_FILE="$WORKDIR/ip.txt"
OUT_FILE="$WORKDIR/best.txt"

cd "$WORKDIR"

############################################
# 检查环境
############################################
if [ ! -x "$CF_BINARY" ]; then
    echo "未找到 CloudflareST 或不可执行"
    exit 1
fi

if [ ! -f "$IP_FILE" ]; then
    echo "未找到 IP 段文件"
    exit 1
fi

############################################
# CloudflareST 低压力测速
############################################
echo "开始测速..."

# 参数说明：
# -n 50   延迟线程数
# -t 6    每个 IP 延迟测试次数
# -dn 10  下载测速 IP 数
# -dt 8   下载测速最长时间
# -sl 0.1 过滤回源 IP
# -tl 250 延迟上限
# -o ""   不生成 result.csv
# -p 10   输出前 10 条

TOP_IPS=$(
    "$CF_BINARY" \
        -f "$IP_FILE" \
        -n 20 \
        -t 6 \
        -dn 10 \
        -dt 8 \
        -sl 0.1 \
        -tl 250 \
        -p 10 \
        -o "" \
    | awk 'NR>2 && $1 ~ /^[0-9]+\./ {print $1}'
)

############################################
# 写入 IP 列表
############################################
if [ -z "$TOP_IPS" ]; then
    echo "未获取到可用 IP"
    exit 2
fi

echo "写入 Top IP 到 best.txt"
printf "%s\n" $TOP_IPS > "$OUT_FILE"

echo "最终 IP 列表："
cat "$OUT_FILE"

############################################
# 调用 Python 更新 DNS （确保有对应py文件）
############################################
echo "开始更新华为云 DNS..."
"$WORKDIR/venv/bin/python" "$WORKDIR/hw_dns_update.py"

echo "任务完成"
