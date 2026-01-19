#!/usr/bin/env python3
from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkdns.v2 import DnsClient
from huaweicloudsdkdns.v2.region.dns_region import DnsRegion
from huaweicloudsdkdns.v2.model import *
from huaweicloudsdkcore.exceptions import exceptions

# ========= 必填配置 =========
AK = "你的AccessKey"
SK = "你的SecretKey"
REGION = "AP_SOUTHEAST_1"   #替换为你的区域，例如 CN_NORTH_1等 默认：AP_SOUTHEAST_1）
ZONE_NAME = "run.254301.xyz."   #替换为你的域名（根）     
RECORD_NAME = "run.254301.xyz."  #替换为你希望的子域名或根域名     
TEST_IP = "1.1.1.1"  #可随意替换
LINE_NAME = "Yidong" #查看 https://support.huaweicloud.com/api-dns/zh-cn_topic_0085546214.html             
TTL = 300 #可按需替换

# ========= 创建客户端 =========
credentials = BasicCredentials(AK, SK)
client = DnsClient.new_builder() \
    .with_credentials(credentials) \
    .with_region(DnsRegion.value_of(REGION)) \
    .build()

def get_zone_id():
    request = ListPublicZonesRequest(name=ZONE_NAME)
    response = client.list_public_zones(request)
    if not response.zones:
        raise RuntimeError("未找到 Zone，请确认域名是否在该账号下")
    return response.zones[0].id

def main():
    try:
        zone_id = get_zone_id()
        print(f"Zone ID: {zone_id}")

        request = CreateRecordSetWithLineRequest()
        request.zone_id = zone_id
        request.body = CreateRecordSetWithLineRequestBody(
            name=RECORD_NAME,
            type="A",
            ttl=TTL,
            line=LINE_NAME,
            records=[TEST_IP]
        )

        resp = client.create_record_set_with_line(request)
        print("DNS 记录创建成功")
        print(resp)

    except exceptions.ClientRequestException as e:
        print("华为云 API 错误")
        print("status:", e.status_code)
        print("error_code:", e.error_code)
        print("message:", e.error_msg)

if __name__ == "__main__":
    main()
