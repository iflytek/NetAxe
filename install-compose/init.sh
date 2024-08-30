#! /bin/bash

curl -X PUT 'http://127.0.0.1:8848/nacos/v1/auth/users?username=nacos&newPassword=netaxenacos'
echo "------------------初始化nacos密码完成----------------------"

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

