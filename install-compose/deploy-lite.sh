#! /bin/bash

# 精简版部署脚本 - 仅部署基础平台、前端和必要的中间件
# 适用于配置较低、内存较小的环境

# 关闭selinux和firewalld
setenforce 0
systemctl stop firewalld
systemctl disable firewalld
systemctl restart docker
current_path=$(pwd)

alias docker-compose='docker compose'

# 检查docker-compose版本以及命令是否安装
docker-compose version
if [ $? -ne 0 ]; then
    echo "请检查docker-compose命令是否安装"
    exit 1
fi

# 默认key设置
default_key=$(openssl rand -hex 8)
nacos_key=$(openssl rand -base64 32) 
x_api_key=$(openssl rand -base64 32)

if [ $# -eq 0 ]; then
  # 如果没有传入参数，则使用默认网卡的IP地址
  default_iface=$(ip route show default | awk '/default/ {print $5}')
  iface_ip=$(ip addr show dev $default_iface | awk '/inet / {print $2}' | cut -d '/' -f 1)
else
  # 如果传入了参数，则使用用户输入的IP地址
  iface_ip=$1
fi

echo "=========================================="
echo "开始精简版部署（仅基础平台和前端）"
echo "=========================================="
echo "Using IP: $iface_ip"
echo "Using key: $default_key"
echo "Using nacos_key: $nacos_key"
echo ""

# 遍历当前目录的所有子目录，查找 config.json 文件并修改其中的 server_ip 字段
find . -type f -name "config.json" -exec sed -i "s|SERVER_IP|${iface_ip}|g" {} \;
find . -type f -name "config.yaml" -exec sed -i "s|SERVER_IP|${iface_ip}|g" {} \;
find . -type f -name "config.json" -exec sed -i "s|X-API-KEY|${x_api_key}|g" {} \;
find . -type f -name "config.yaml" -exec sed -i "s|X-API-KEY|${x_api_key}|g" {} \;
find . -type f -name "config.json" -exec sed -i "s|MYSQL_PASSWD|${default_key}|g" {} \;
find . -type f -name "config.json" -exec sed -i "s|MYSQL_PASSWORD|${default_key}|g" {} \;
find . -type f -name "config.yaml" -exec sed -i "s|MYSQL_PASSWD|${default_key}|g" {} \;
find . -type f -name "config.json" -exec sed -i "s|REDIS_PASSWORD|${default_key}|g" {} \;
find . -type f -name "config.json" -exec sed -i "s|MONGO_PASSWORD|${default_key}|g" {} \;
find . -type f -name "config.json" -exec sed -i "s|RABBITMQ_PASSWORD|${default_key}|g" {} \;
find . -type f -name "config.json" -exec sed -i "s|DJANGO_INSECURE|${default_key}|g" {} \;
find . -type f -name "config.json" -exec sed -i "s|NACOS_PASSWORD|${default_key}|g" {} \;
find . -type f -name "config.yaml" -exec sed -i "s|REGIS_PASSWORD|${default_key}|g" {} \;

# 更新docker-compose文件中的密码
find ./redis-compose -type f -name "docker-compose.yml" -exec sed -i "s|REDIS_PASSWORD|${default_key}|g" {} \;
find ./mongo-compose -type f -name "docker-compose.yml" -exec sed -i "s|MONGO_PASSWORD|${default_key}|g" {} \;
find ./rabbitmq-compose -type f -name "docker-compose.yml" -exec sed -i "s|RABBITMQ_PASSWORD|${default_key}|g" {} \;
find ./alertgateway-compose -type f -name "docker-compose.yml" -exec sed -i "s|PROMETHEUS_PASSWORD|${default_key}|g" {} \;
# 更新mysql相关配置
sed -i "s|MYSQL_PASSWD|${default_key}|g" ./mysql-compose/init/netaxe.sql
sed -i "s|MYSQL_PASSWD|${default_key}|g" ./neteye-compose/config.yaml
sed -i "s|MYSQL_PASSWD|${default_key}|g" ./mysql-compose/docker-compose.yml
sed -i "s|NACOS_PASSWORD|${default_key}|g" ./nacos-compose/docker-compose.yml
sed -i "s|NACOS_KEY|${nacos_key}|g" ./nacos-compose/docker-compose.yml
sed -i "s|APISIX_ADMIN_KEY|${default_key}|g" ./init.sh
sed -i "s|DJANGO_INSECURE|${default_key}|g" ./init.sh
sed -i "s|REGIS_PASSWORD|${default_key}|g" ./prometheus-compose/prometheus.yml
sed -i "s|SERVER_IP|${iface_ip}|g" ./prometheus-compose/prometheus.yml
sed -i "s|REGIS_PASSWORD|${prometheus_password_hash}|g" ./prometheus-compose/prometheus_web.yml

# 创建docker_netaxe网络
echo "------------------创建docker网络------------------"
docker network create --subnet=1.1.38.0/24 --ip-range=1.1.38.0/24 --gateway=1.1.38.254 docker_netaxe 2>/dev/null || echo "网络已存在，跳过创建"

# 安装mysql
echo "------------------开始mysql部署------------"
cd $current_path
cd mysql-compose
docker-compose up -d
sleep 10
echo "------------------mysql状态----------------------"
docker-compose ps

# 安装mongo
echo "------------------开始mongo部署------------"
cd $current_path
cd mongo-compose
docker-compose up -d
sleep 10
echo "------------------mongo状态----------------------"
docker-compose ps

# 安装redis
echo "------------------开始redis部署-----------------"
cd $current_path
cd redis-compose
docker-compose up -d
echo "------------------redis状态------------------"
docker-compose ps

# 安装rabbitmq
echo "------------------开始rabbitmq部署-----------------"
cd $current_path
cd rabbitmq-compose
docker-compose up -d
sleep 10
docker exec rabbitmq /bin/bash /etc/rabbitmq/rabbitmq.sh
echo "------------------rabbitmq状态------------------"
docker-compose ps

# 安装nacos
echo "------------------开始nacos部署-------------------"
cd $current_path
cd nacos-compose
docker-compose up -d
echo "------------------nacos状态----------------------"
docker-compose ps

# 增加延迟，等待 Nacos 启动完成
echo "等待 Nacos 启动完成..."
sleep 30

# 初始化nacos密码
echo "------------------准备初始化nacos密码完成----------------------"
curl -X POST 'http://127.0.0.1:8848/nacos/v1/auth/users/admin' -d "password=${default_key}"
echo "------------------初始化nacos密码完成----------------------"

# 安装权限中心（abac）
echo "------------------开始权限中心部署--------------"
cd $current_path
cd abac-compose
docker-compose pull
docker-compose up -d
echo "------------------权限中心状态------------------"
docker-compose ps
sleep 10

# 安装基础平台
echo "------------------开始管控平台部署--------------"
cd $current_path
cd baseplatform-compose
# 检查是否已存在base-platform目录
if [ ! -d "base-platform" ]; then
    git clone -b dev https://gitee.com/NetAxeClub/base-platform.git
fi
mv config.json base-platform/config/ 2>/dev/null || echo "config.json已存在或已移动"
mkdir -p base-platform/backend/media/device_config/current-configuration
mkdir -p base-platform/backend/media/device_config/startup-configuration
mkdir -p base-platform/backend/plugins/extensibles
docker-compose pull
docker-compose up -d
echo "------------------管控平台状态------------------"
docker-compose ps
sleep 10

# 安装工作台
echo "------------------开始工作台部署--------------"
cd $current_path
cd workbench-compose
docker-compose pull
docker-compose up -d
echo "------------------工作台状态------------------"
docker-compose ps
sleep 10

# 安装前端服务（使用精简版nginx配置）
echo "------------------开始前端服务部署--------------"
cd $current_path
cd main-compose
# 检查精简版nginx配置文件是否存在
if [ ! -f "nginx-lite.conf" ]; then
    echo "错误: nginx-lite.conf 文件不存在，请确保该文件已创建"
    exit 1
fi
# 备份原nginx.conf，使用精简版配置
cp nginx.conf nginx.conf.full 2>/dev/null || echo "原配置已备份或不存在"
cp nginx-lite.conf nginx.conf
docker-compose pull
docker-compose up -d
echo "------------------前端服务状态------------------"
docker-compose ps
sleep 10
echo "------------------刷新权限------------------"
curl "http://127.0.0.1:31104/abac-api/authority/auth_policy/?reload=1"
echo "------------------刷新权限成功------------------"
sleep 10
curl "http://127.0.0.1:31104/abac-api/authority/auth_policy/?reload=1"
echo "------------------刷新权限成功------------------"
echo "=========================================="
echo "精简版部署完成"
echo "=========================================="
echo "请记住初始化密码"
echo "IP: $iface_ip"
echo "密码: $default_key"
echo "注意：此精简版包含基础平台、工作台和前端服务"
echo "如需完整功能，请使用 deploy.sh 进行全量部署"
