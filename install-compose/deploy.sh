#! /bin/bash

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

if [ $# -eq 0 ]; then
  # 如果没有传入参数，则使用默认网卡的IP地址
  default_iface=$(ip route show default | awk '/default/ {print $5}')
  iface_ip=$(ip addr show dev $default_iface | awk '/inet / {print $2}' | cut -d '/' -f 1)
else
  # 如果传入了参数，则使用用户输入的IP地址
  iface_ip=$1
fi

echo "开始进行初始化操作，本操作将一次性生成各个配置文件的秘钥"
echo "Using IP: $iface_ip"
echo "Using key: $default_key"
echo "Using nacos_key: $nacos_key"


# 遍历当前目录的所有子目录，查找 config.json 文件并修改其中的 server_ip 字段
find . -type f -name "config.json" -exec sed -i "s|SERVER_IP|${iface_ip}|g" {} \;
find . -type f -name "config.json" -exec sed -i "s|MYSQL_PASSWORD|${default_key}|g" {} \;
find . -type f -name "config.json" -exec sed -i "s|REDIS_PASSWORD|${default_key}|g" {} \;
find . -type f -name "config.json" -exec sed -i "s|MONGO_PASSWORD|${default_key}|g" {} \;
find . -type f -name "config.json" -exec sed -i "s|RABBITMQ_PASSWORD|${default_key}|g" {} \;
find . -type f -name "config.json" -exec sed -i "s|DJANGO_INSECURE|${default_key}|g" {} \;
find . -type f -name "config.json" -exec sed -i "s|NACOS_PASSWORD|${default_key}|g" {} \;
find . -type f -name "config.yaml" -exec sed -i "s|REGIS_PASSWORD|${default_key}|g" {} \;
find . -type f -name "prometheus.yml" -exec sed -i "s|REGIS_PASSWORD|${default_key}|g" {} \;

find ./apisix-compose -type f -name "config.yaml" -exec sed -i "s|APISIX_ADMIN_KEY|${default_key}|g" {} \;
find ./apisix-compose -type f -name "conf.yaml" -exec sed -i "s|APISIX_ADMIN_PASSWORD|${default_key}|g" {} \;
find ./apisix-compose -type f -name "config.yaml" -exec sed -i "s|NACOS_PASSWORD|${default_key}|g" {} \;
find ./redis-compose -type f -name "docker-compose.yml" -exec sed -i "s|REDIS_PASSWORD|${default_key}|g" {} \;
find ./mongo-compose -type f -name "docker-compose.yml" -exec sed -i "s|MONGO_PASSWORD|${default_key}|g" {} \;
find ./rabbitmq-compose -type f -name "docker-compose.yml" -exec sed -i "s|RABBITMQ_PASSWORD|${default_key}|g" {} \;
find ./alertgateway-compose -type f -name "docker-compose.yml" -exec sed -i "s|PROMETHEUS_PASSWORD|${default_key}|g" {} \;


sed -i "s|MYSQL_PASSWORD|${default_key}|g" ./mysql-compose/init/netaxe.sql
sed -i "s|MYSQL_PASSWORD|${default_key}|g" ./mysql-compose/docker-compose.yml
sed -i "s|NACOS_KEY|${nacos_key}|g" ./nacos-compose/docker-compose.yml
sed -i "s|APISIX_ADMIN_KEY|${default_key}|g" ./init.sh
sed -i "s|DJANGO_INSECURE|${default_key}|g" ./init.sh


# 创建docker_netaxe网络
docker network create  --subnet=1.1.38.0/24 --ip-range=1.1.38.0/24 --gateway=1.1.38.254 docker_netaxe


# 安装mysql和mongo
echo "------------------开始mysql和mongo部署------------"
cd $current_path
cd mysql-compose
docker-compose up -d
echo "------------------mysql状态----------------------"
docker-compose ps

cd $current_path
cd mongo-compose
docker-compose up -d
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
# 安装nacos
echo "------------------开始nacos部署-------------------"
cd $current_path
cd nacos-compose
docker-compose up -d
echo "------------------nacos状态----------------------"
docker-compose ps

# 增加延迟，等待 Nacos 启动完成
echo "等待 Nacos 启动完成..."
sleep 30  # 等待 30 秒，可以根据实际情况调整时间

# 部署服务得时候需要注册nacos，需要重置后得密码信息
echo "------------------准备初始化nacos密码完成----------------------"
curl -X POST 'http://127.0.0.1:8848/nacos/v1/auth/users/admin' -d "password=${default_key}"
echo "------------------初始化nacos密码完成----------------------"


## 安装apisix etcd
#echo "------------------开始apisix etcd部署------------------"
#cd $current_path
#cd apisix-compose
#mkdir -m 777 -p etcd_conf/data
#docker-compose up -d
#echo "------------------apisix etcd状态---------------------"
#docker-compose ps


# 安装main和rbac
echo "------------------开始权限中心部署--------------"
cd $current_path
cd abac-compose
docker-compose pull
docker-compose  up -d
echo "------------------权限中心状态------------------"
docker-compose ps
sleep 10

# 安装基础平台
echo "------------------开始管控平台部署--------------"
cd $current_path
cd baseplatform-compose
docker-compose pull
docker-compose  up -d
echo "------------------管控平台状态------------------"
docker-compose ps
sleep 10

# 安装消息网关
echo "------------------开始消息网关部署--------------"
cd $current_path
cd msggateway-compose
docker-compose pull
docker-compose  up -d
echo "------------------消息网关状态------------------"
docker-compose ps
sleep 10

# 安装告警中心
echo "------------------开始告警中心部署--------------"
cd $current_path
cd alertgateway-compose
docker-compose pull
docker-compose  up -d
echo "------------------告警中心状态------------------"
docker-compose  ps
sleep 10

echo "------------------开始前端服务部署--------------"
cd $current_path
cd main-compose
docker-compose pull
docker-compose  up -d
echo "------------------前端服务状态------------------"
docker-compose ps
sleep 10


echo "------------------部署完成------------------------"

echo "请记住初始化密码"
echo "IP: $iface_ip"
echo "密码: $default_key"