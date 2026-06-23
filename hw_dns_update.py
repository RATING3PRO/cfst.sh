#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkdns.v2 import DnsClient
from huaweicloudsdkdns.v2.region.dns_region import DnsRegion
from huaweicloudsdkdns.v2.model import (
    ListPublicZonesRequest,
    ListRecordSetsWithLineRequest,
    DeleteRecordSetRequest,
    CreateRecordSetWithLineRequest,
    CreateRecordSetWithLineRequestBody,
)
from huaweicloudsdkcore.exceptions import exceptions

############################################
# 华为云账号信息（必须填写）
############################################
ACCESS_KEY_ID = "YOUR_ACCESS_KEY_ID"
ACCESS_KEY_SECRET = "YOUR_ACCESS_KEY_SECRET"

############################################
# DNS 配置 （替换为自己的管辖区和域名）
############################################
REGION = "ap-southeast-1"
ZONE_NAME = "run.254301.xyz"
RECORD_NAME = "run.254301.xyz"

LINE = "Yidong"   # 运营商线路（https://support.huaweicloud.com/api-dns/zh-cn_topic_0085546214.html）
TTL = 60
BATCH_SIZE = 50
IP_FILE = "best.txt"
CREATE_MAX_RETRIES = 5
CREATE_RETRY_BASE_DELAY = 1.0  # 秒，指数退避基数

############################################
# 初始化客户端
############################################
credentials = BasicCredentials(
    ACCESS_KEY_ID,
    ACCESS_KEY_SECRET
)

client = DnsClient.new_builder() \
    .with_credentials(credentials) \
    .with_region(DnsRegion.value_of(REGION)) \
    .build()

############################################
# 工具函数
############################################
def get_zone_id():
    req = ListPublicZonesRequest(name=ZONE_NAME)
    resp = client.list_public_zones(req)
    if not resp.zones:
        raise RuntimeError("未找到 Zone")
    return resp.zones[0].id


def read_ips():
    if not os.path.exists(IP_FILE):
        raise RuntimeError("IP 文件不存在")

    with open(IP_FILE) as f:
        ips = [i.strip() for i in f if i.strip()]

    if not ips:
        raise RuntimeError("IP 列表为空")
    return ips


def list_target_records(zone_id, target):
    page_limit = 500
    offset = 0
    while True:
        req = ListRecordSetsWithLineRequest(
            zone_id=zone_id,
            type="A",
            name=target,
            limit=page_limit,
            offset=offset,
        )
        resp = client.list_record_sets_with_line(req)
        page = resp.recordsets or []
        for r in page:
            if r.name == target and r.line == LINE:
                yield r
        if len(page) < page_limit:
            return
        offset += page_limit


def delete_old_records(zone_id):
    target = RECORD_NAME.rstrip(".") + "."
    failures = []

    for r in list_target_records(zone_id, target):
        print(f"删除旧记录：{r.id}")
        try:
            client.delete_record_set(DeleteRecordSetRequest(
                zone_id=zone_id,
                recordset_id=r.id
            ))
        except exceptions.ClientRequestException as e:
            if e.status_code == 404:
                print(f"警告：记录 {r.id} 已不存在，跳过")
            else:
                print(f"错误：删除 {r.id} 失败（status={e.status_code}）：{e.error_msg}")
                failures.append((r.id, e))

    if failures:
        raise RuntimeError(f"删除旧记录失败 {len(failures)} 条，已停止以避免重复创建")


def _is_transient_create_error(e):
    # 删除后传播延迟常见错误码：同名冲突 / 配额抢占 / 5xx
    if e.status_code in (409, 429, 500, 502, 503, 504):
        return True
    if e.status_code == 400 and e.error_code in ("DNS.0312", "DNS.0102"):
        # 0312: record set already exists; 0102: 资源繁忙
        return True
    return False


def create_records(zone_id, ips):
    total = len(ips)
    batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
    target = RECORD_NAME.rstrip(".") + "."

    for i in range(batches):
        batch = ips[i * BATCH_SIZE:(i + 1) * BATCH_SIZE]
        body = CreateRecordSetWithLineRequestBody(
            name=target,
            type="A",
            ttl=TTL,
            line=LINE,
            records=batch
        )
        req = CreateRecordSetWithLineRequest(zone_id=zone_id, body=body)

        for attempt in range(CREATE_MAX_RETRIES):
            try:
                client.create_record_set_with_line(req)
                break
            except exceptions.ClientRequestException as e:
                if attempt < CREATE_MAX_RETRIES - 1 and _is_transient_create_error(e):
                    delay = CREATE_RETRY_BASE_DELAY * (2 ** attempt)
                    print(f"创建记录集 {i+1}/{batches} 第 {attempt+1} 次失败"
                          f"（status={e.status_code} code={e.error_code}），{delay:.1f}s 后重试")
                    time.sleep(delay)
                    continue
                raise
        print(f"创建记录集 {i+1}/{batches}，IP 数 {len(batch)}")

############################################
# 主流程
############################################
def main():
    print("开始华为云 DNS 更新")
    zone_id = get_zone_id()
    ips = read_ips()
    delete_old_records(zone_id)
    create_records(zone_id, ips)
    print("DNS 更新完成")

if __name__ == "__main__":
    try:
        main()
    except exceptions.ClientRequestException as e:
        print("华为云 API 错误：", e.error_msg)
        exit(1)
    except Exception as e:
        print("执行失败：", e)
        exit(2)

