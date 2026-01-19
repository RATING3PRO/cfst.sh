# Cloudflare Speed Test & Huawei Cloud DNS Updater

本项目用于自动测试 Cloudflare 节点速度，并将优选 IP 更新到华为云 DNS 解析记录中。

## 功能特性

- 集成 [CloudflareST](https://github.com/XIU2/CloudflareSpeedTest) 进行测速
- 自动筛选低延迟、高带宽的 IP
- 自动更新华为云 DNS 解析记录
- 支持运营商线路区分（如移动、联通、电信）

## 文件说明

- `cfst.sh`: 主控 Shell 脚本，负责调用测速工具和 Python 更新脚本，可配置在cron或systemd timer中。
- `hw_dns_update.py`: Python 脚本，用于调用华为云 API 更新 DNS 记录。
- `test_huawei_dns.py`: 单据测试脚本，用于验证华为云 API 配置是否正确。
- `ip.txt`: Cloudflare IP 地址段文件（需自行下载或生成）。

## 环境要求

- Linux 系统 (CentOS/Ubuntu/Debian)
- Python 3.6+
- `CloudflareST` 可执行文件

## 部署步骤

### 1. 准备目录与文件

建议部署在 `/opt/cfst` 目录下（其他目录需更改cfst.sh中的WORKDIR）：

```bash
mkdir -p /opt/cfst
cd /opt/cfst
# 将本项目所有文件上传至此目录
chmod +x cfst.sh
```

### 2. 安装 CloudflareST

下载并解压 CloudflareST 到 `/opt/cfst` 目录，确保二进制文件名为 `CloudflareST` 且有执行权限。

```bash
# 示例（请根据架构下载对应版本）
wget -N https://github.com/XIU2/CloudflareSpeedTest/releases/download/v2.2.5/CloudflareST_linux_amd64.tar.gz
tar -zxf CloudflareST_linux_amd64.tar.gz
mv CloudflareST /opt/cfst/CloudflareST
chmod +x /opt/cfst/CloudflareST
```

确保存在 `ip.txt` 文件，如果 CloudflareST 压缩包中包含该文件，直接使用即可。

### 3. 配置 Python 环境

建议使用虚拟环境运行 Python 脚本：

```bash
cd /opt/cfst
python3 -m venv venv
source venv/bin/activate

# 安装华为云 SDK
pip install huaweicloudsdkcore huaweicloudsdkdns
```

### 4. 修改配置

#### 修改 `hw_dns_update.py`

编辑 `hw_dns_update.py`，填入你的华为云 Access Key 和域名信息：

```python
# 华为云账号信息
ACCESS_KEY_ID = "你的AccessKeyId"
ACCESS_KEY_SECRET = "你的AccessKeySecret"

# DNS 配置
REGION = "ap-southeast-1"      # 区域 ID
ZONE_NAME = "example.com"      # 主域名
RECORD_NAME = "cf.example.com" # 子域名
LINE = "Yidong"                # 线路（默认移动，查看hw_dns_update.py中的注释）
```

#### 修改 `cfst.sh` (可选)

如果你的安装目录不是 `/opt/cfst`，请修改 `cfst.sh` 中的 `WORKDIR` 变量。

```bash
WORKDIR="/opt/cfst"
```

## 使用方法

### 手动运行

```bash
sudo ./cfst.sh
```

运行成功后，脚本会生成 `best.txt` 并自动更新 DNS 记录。

## 注意事项

1. **安全提示**：请勿将包含 AK/SK 的代码上传到公开仓库。
2. **区域 ID**：华为云区域 ID 通常为小写（如 `cn-north-4`, `ap-southeast-1`），请参考华为云官方文档。

