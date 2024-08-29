#!/bin/bash

if [ $# -eq 0 ]; then
  # 如果没有传入参数，则使用默认网卡的IP地址
  default_iface=$(ip route show default | awk '/default/ {print $5}')
  iface_ip=$(ip addr show dev $default_iface | awk '/inet / {print $2}' | cut -d '/' -f 1)
else
  # 如果传入了参数，则使用用户输入的IP地址
  iface_ip=$1
fi

default_key=$(openssl rand -hex 16)

echo "开始进行初始化操作，本操作将一次性生成各个配置文件的秘钥"
echo "Using IP address: $iface_ip"
echo "Using key: $default_key"



# 遍历当前目录的所有子目录，查找 config.json 文件并修改其中的 server_ip 字段
find . -type f -name "config.json" -exec sed -i "s/tmp_server_ip/$iface_ip/g" {} \;
find . -type f -name "config.json" -exec sed -i "s/MYSQL_PASSWORD/$default_key/g" {} \;
find . -type f -name "config.json" -exec sed -i "s/REDIS_PASSWORD/$default_key/g" {} \;
find . -type f -name "config.json" -exec sed -i "s/MONGO_PASSWORD/$default_key/g" {} \;
find . -type f -name "config.json" -exec sed -i "s/RABBITMQ_PASSWORD/$default_key/g" {} \;
find . -type f -name "config.json" -exec sed -i "s/DJANGO_INSECURE/$default_key/g" {} \;

find ./apisix-compose -type f -name "config.yaml" -exec sed -i "s/APISIX_ADMIN_KEY/$default_key/g" {} \;
find ./apisix-compose -type f -name "config.yaml" -exec sed -i "s/NACOS_PASSWORD/$default_key/g" {} \;
find ./mysql-compose -type f -name "docker-compose.yml" -exec sed -i "s/MYSQL_PASSWORD/$default_key/g" {} \;
find ./redis-compose -type f -name "docker-compose.yml" -exec sed -i "s/REDIS_PASSWORD/$default_key/g" {} \;
find ./mongo-compose -type f -name "docker-compose.yml" -exec sed -i "s/MONGO_PASSWORD/$default_key/g" {} \;
find ./rabbitmq-compose -type f -name "docker-compose.yml" -exec sed -i "s/RABBITMQ_PASSWORD/$default_key/g" {} \;
find . -type f -name "init_apisix.sh" -exec sed -i "s/DJANGO_INSECURE/$default_key/g" {} \;
find . -type f -name "init_apisix.sh" -exec sed -i "s/APISIX_ADMIN_KEY/$default_key/g" {} \;
find . -type f -name "init_apisix.sh" -exec sed -i "s/NACOS_PASSWORD/$default_key/g" {} \;

