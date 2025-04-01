#! /bin/bash
current_path=$(pwd)
alias docker-compose='docker compose'
# 检查docker-compose版本以及命令是否安装
docker-compose version
if [ $? -ne 0 ]; then
    echo "请检查docker-compose命令是否安装"
    exit 1
fi


# 更新main和abac
echo "------------------开始abac更新--------------"
cd $current_path
cd abac-compose
docker-compose down -v && docker-compose pull && docker-compose up -d
echo "------------------abac状态------------------"
docker-compose ps
sleep 10

echo "------------------开始web main更新--------------"
cd $current_path
cd main-compose
docker-compose down -v && docker-compose pull && docker-compose up -d
echo "------------------web main状态------------------"
docker-compose ps
sleep 10

# 更新基础平台
echo "------------------开始基础平台更新--------------"
cd $current_path
cd baseplatform-compose
docker-compose down -v && docker-compose pull && docker-compose up -d
echo "------------------基础平台状态------------------"
docker-compose ps
sleep 10

# 更新消息网关
echo "------------------开始消息网关更新--------------"
cd $current_path
cd msggateway-compose
docker-compose down -v && docker-compose pull && docker-compose up -d
echo "------------------消息网关状态------------------"
docker-compose ps
sleep 10

# 更新告警中心
echo "------------------开始告警中心更新--------------"
cd $current_path
cd alertgateway-compose
docker-compose down -v && docker-compose pull && docker-compose up -d
echo "------------------告警中心状态------------------"
docker-compose  ps

# 更新IPAM
echo "------------------开始IPAM更新--------------"
cd $current_path
cd ipam-compose
docker-compose down -v && docker-compose pull && docker-compose up -d
echo "------------------IPAM状态------------------"
docker-compose  ps

echo "------------------更新完成------------------------"


