#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
从 URL 下载 IP 列表（每行格式 1.1.1.1:443#DE），
筛选端口为 443 的条目，去掉 #XX 注释，
对剩余 IP:端口 进行 tcping，选出延迟最低的若干个写入 txt 文件。
"""

import socket
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

############################################
# 基本配置（按需修改）
############################################
SOURCE_URL = "https://example.com/ip.txt"   # IP 列表下载地址
OUT_FILE = "best.txt"                        # 结果输出文件
WANT_PORT = 443                              # 只保留此端口
TOP_N = 15                                   # 输出延迟最低的前 N 个
TIMEOUT = 2.0                                # 单次 tcping 超时（秒）
ATTEMPTS = 3                                 # 每个 IP 测试次数，取最优
THREADS = 50                                 # 并发线程数


############################################
# 工具函数
############################################
def download(url):
    """下载文本内容并按行返回。"""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        text = resp.read().decode("utf-8", errors="ignore")
    return text.splitlines()


def parse_lines(lines):
    """解析每行，保留端口为 WANT_PORT 的条目，去掉 #XX 注释。

    返回 [(ip, port), ...]，已去重。
    """
    result = []
    seen = set()
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        # 去掉 #XX 注释部分
        addr = line.split("#", 1)[0].strip()
        if ":" not in addr:
            continue

        ip, _, port = addr.rpartition(":")
        ip = ip.strip()
        port = port.strip()
        if not ip or not port.isdigit():
            continue

        port = int(port)
        if port != WANT_PORT:
            continue

        key = (ip, port)
        if key in seen:
            continue
        seen.add(key)
        result.append(key)

    return result


def tcping(ip, port):
    """对 ip:port 做 TCP 连接测速，返回最低延迟（毫秒），失败返回 None。"""
    best = None
    for _ in range(ATTEMPTS):
        start = time.perf_counter()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        try:
            sock.connect((ip, port))
            elapsed = (time.perf_counter() - start) * 1000
            if best is None or elapsed < best:
                best = elapsed
        except OSError:
            pass
        finally:
            sock.close()
    return best


############################################
# 主流程
############################################
def main():
    print(f"从 {SOURCE_URL} 下载 IP 列表...")
    lines = download(SOURCE_URL)

    targets = parse_lines(lines)
    if not targets:
        raise RuntimeError(f"未解析到端口为 {WANT_PORT} 的 IP")
    print(f"共 {len(targets)} 个端口 {WANT_PORT} 的 IP，开始 tcping 测速...")

    results = []
    with ThreadPoolExecutor(max_workers=THREADS) as pool:
        futures = {pool.submit(tcping, ip, port): (ip, port) for ip, port in targets}
        for fut in as_completed(futures):
            ip, port = futures[fut]
            latency = fut.result()
            if latency is not None:
                results.append((latency, ip, port))

    if not results:
        raise RuntimeError("没有可连通的 IP")

    results.sort(key=lambda x: x[0])
    top = results[:TOP_N]

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        for latency, ip, port in top:
            f.write(f"{ip}\n")

    print(f"测速完成，连通 {len(results)} 个，已写入延迟最低的 {len(top)} 个到 {OUT_FILE}：")
    for latency, ip, port in top:
        print(f"  {ip}:{port}  {latency:.1f} ms")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("执行失败：", e)
        exit(1)
