#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
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
IP_FILE = "yes.txt"

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


def delete_old_records(zone_id):
    req = ListRecordSetsWithLineRequest(zone_id=zone_id, type="A")
    resp = client.list_record_sets_with_line(req)
    target = RECORD_NAME + "."

    for r in resp.recordsets or []:
        if r.name == target and r.line == LINE:
            print(f"删除旧记录：{r.id}")
            client.delete_record_set(DeleteRecordSetRequest(
                zone_id=zone_id,
                recordset_id=r.id
            ))


def create_records(zone_id, ips):
    total = len(ips)
    batches = (total + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(batches):
        batch = ips[i * BATCH_SIZE:(i + 1) * BATCH_SIZE]
        body = CreateRecordSetWithLineRequestBody(
            name=RECORD_NAME + ".",
            type="A",
            ttl=TTL,
            line=LINE,
            records=batch
        )
        req = CreateRecordSetWithLineRequest(zone_id=zone_id, body=body)
        client.create_record_set_with_line(req)
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

