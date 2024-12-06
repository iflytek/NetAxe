#! /bin/bash
current_path=$(pwd)
alias docker-compose='docker compose'

# 检查docker-compose版本以及命令是否安装
docker-compose version
if [ $? -ne 0 ]; then
    echo "请检查docker-compose命令是否安装"
    exit 1
fi

# 卸载mysql和mongo
echo "------------------开始mysql和mongo卸载------------"
cd $current_path
cd mysql-compose
docker-compose down -v
echo "------------------mysql状态----------------------"
docker-compose ps
cd $current_path
cd mongo-compose
docker-compose down -v
echo "------------------mongo状态----------------------"
docker-compose ps


# 卸载redis
echo "------------------开始redis卸载-----------------"
cd $current_path
cd redis-compose
docker-compose down -v
echo "------------------redis状态------------------"
docker-compose ps


# 卸载rabbitmq
echo "------------------开始rabbitmq卸载-----------------"
cd $current_path
cd rabbitmq-compose
docker-compose down -v
sleep 10
docker exec rabbitmq /bin/bash /etc/rabbitmq/rabbitmq.sh
echo "------------------rabbitmq状态------------------"
docker-compose ps


# 卸载nacos
echo "------------------开始nacos卸载-------------------"
cd $current_path
cd nacos-compose
docker-compose down -v
echo "------------------nacos状态----------------------"
docker-compose ps



# 卸载apisix etcd
echo "------------------开始apisix etcd卸载------------------"
cd $current_path
cd apisix-compose
mkdir -m 777 -p etcd_conf/data
docker-compose down -v
rm -rf etcd_conf/data
echo "------------------apisix etcd状态---------------------"
docker-compose ps


# 卸载prometheus
echo "------------------开始prometheus卸载------------------"
cd $current_path
cd prometheus-compose
chmod 777 prometheus-vata/
docker-compose  down -v
echo "------------------prometheus状态---------------------"
docker-compose ps
sleep 10

# 卸载main和rbac
echo "------------------开始权限中心卸载--------------"
cd $current_path
cd abac-compose
docker-compose  down -v
echo "------------------权限中心状态------------------"
docker-compose ps
sleep 10

echo "------------------开始web main卸载--------------"
cd $current_path
cd main-compose
docker-compose  down -v
echo "------------------web main状态------------------"
docker-compose ps
sleep 10

# 卸载基础平台
echo "------------------开始管控平台卸载--------------"
cd $current_path
cd baseplatform-compose
docker-compose  down -v
echo "------------------管控平台状态------------------"
docker-compose ps
sleep 10

# 卸载消息网关
echo "------------------开始消息网关卸载--------------"
cd $current_path
cd msggateway-compose
docker-compose  down -v
echo "------------------消息网关状态------------------"
docker-compose ps
sleep 10

# 卸载告警中心
echo "------------------开始告警中心卸载--------------"
cd $current_path
cd alertgateway-compose
docker-compose  down -v
echo "------------------告警中心状态------------------"
docker-compose  ps

# 卸载IPAM
echo "------------------开始IPAM卸载--------------"
cd $current_path
cd ipam-compose
docker-compose  down -v
echo "------------------IPAM状态------------------"
docker-compose  ps

echo "------------------卸载完成------------------------"
# stop停止所有容器
#docker stop $(docker ps -a -q)

# remove删除所有容器
#docker rm $(docker ps -a -q)

# 删除所有镜像
#docker rmi $(docker images -q)

# 卸载docker_netaxe网络
docker network inspect docker_netaxe
if [ $? -eq 0 ]; then
    docker network rm docker_netaxe
fi

echo "------------------卸载完成---------------------------"