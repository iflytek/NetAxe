#! /bin/bash

# 关闭selinux和firewalld
setenforce 0
systemctl stop firewalld
current_path=$(pwd)



# 检查docker-compose版本以及命令是否安装
docker-compose --version
if [ $? -ne 0 ]; then
    echo "请检查docker-compose命令是否安装"
    exit 1
fi
if which docker compose version  >/dev/null; then
    alias docker-compose='docker compose'
fi

# 创建docker_netaxe网络
docker network inspect docker_netaxe
if [ $? -ne 0 ]; then
    docker network create  --subnet=1.1.38.0/24 \
    --ip-range=1.1.38.0/24 \
    --gateway=1.1.38.254 \
    docker_netaxe
fi

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
echo "------------------开始nacos部署-------------------"
cd $current_path
cd nacos-compose
docker-compose up -d
echo "------------------nacos状态----------------------"
docker-compose ps



# 安装apisix
echo "------------------开始apisix部署------------------"
cd $current_path
cd apisix-compose
mkdir -m 777 -p etcd_conf/data
docker-compose up -d
echo "------------------apisix状态---------------------"
docker-compose ps


# 安装prometheus
echo "------------------开始prometheus部署------------------"
cd $current_path
cd prometheus-compose
docker-compose  up -d
echo "------------------prometheus状态---------------------"
docker-compose ps
sleep 10

# 安装main和rbac
echo "------------------开始rbac部署--------------"
cd $current_path
cd rbac-compose
docker-compose  up -d
echo "------------------rbac状态------------------"
docker-compose ps
sleep 10

echo "------------------开始web main部署--------------"
cd $current_path
cd main-compose
docker-compose  up -d
echo "------------------web main状态------------------"
docker-compose ps
sleep 10

# 安装基础平台
echo "------------------开始基础平台部署--------------"
cd $current_path
cd baseplatform-compose
docker-compose  up -d
echo "------------------基础平台状态------------------"
docker-compose ps
sleep 10

# 安装消息网关
echo "------------------开始消息网关部署--------------"
cd $current_path
cd msggateway-compose
docker-compose  up -d
echo "------------------消息网关状态------------------"
docker-compose ps
sleep 10

# 安装告警中心
echo "------------------开始告警中心部署--------------"
cd $current_path
cd alertgateway-compose
docker-compose  up -d
echo "------------------告警中心状态------------------"
docker-compose  ps


echo "------------------部署完成------------------------"
