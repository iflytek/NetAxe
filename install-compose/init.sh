#!/bin/bash

if [ $# -eq 0 ]; then
  # 如果没有传入参数，则使用默认网卡的IP地址
  default_iface=$(ip route show default | awk '/default/ {print $5}')
  iface_ip=$(ip addr show dev $default_iface | awk '/inet / {print $2}' | cut -d '/' -f 1)
else
  # 如果传入了参数，则使用用户输入的IP地址
  iface_ip=$1
fi

echo "Using IP address: $iface_ip"

# 遍历当前目录的所有子目录，查找 config.json 文件并修改其中的 server_ip 字段
#find . -type f -name "config.json" -exec sed -i "s/\"server_ip\": \"[^\"]*\"/\"server_ip\": \"$iface_ip\"/g" {} \;
find . -type f -name "config.json" -exec sed -i "s/tmp_server_ip/'$iface_ip'/g" {} \;
