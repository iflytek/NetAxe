#! /bin/bash

# 检查docker-compose版本以及命令是否安装
docker-compose --version
if [ $? -ne 0 ]; then
    echo "请检查docker-compose命令是否安装"
    exit 1
fi

# stop停止所有容器
docker stop $(docker ps -a -q)

# remove删除所有容器
docker rm $(docker ps -a -q)

# 删除所有镜像
#docker rmi $(docker images -q)

# 卸载docker_netaxe网络
docker network inspect docker_netaxe
if [ $? -eq 0 ]; then
    docker network rm docker_netaxe
fi

echo "------------------卸载完成---------------------------"