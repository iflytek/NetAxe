#! /bin/bash
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
find . -type f -name "config.json" -exec sed -i "s/NACOS_PASSWORD/$default_key/g" {} \;

find ./apisix-compose -type f -name "config.yaml" -exec sed -i "s/APISIX_ADMIN_KEY/$default_key/g" {} \;
find ./apisix-compose -type f -name "config.yaml" -exec sed -i "s/NACOS_PASSWORD/$default_key/g" {} \;
find ./mysql-compose -type f -name "docker-compose.yml" -exec sed -i "s/MYSQL_PASSWORD/$default_key/g" {} \;
find ./redis-compose -type f -name "docker-compose.yml" -exec sed -i "s/REDIS_PASSWORD/$default_key/g" {} \;
find ./mongo-compose -type f -name "docker-compose.yml" -exec sed -i "s/MONGO_PASSWORD/$default_key/g" {} \;
find ./rabbitmq-compose -type f -name "docker-compose.yml" -exec sed -i "s/RABBITMQ_PASSWORD/$default_key/g" {} \;
find ./nacos-compose -type f -name "docker-compose.yaml" -exec sed -i "s/NACOS_KEY/$default_key/g" {} \;
# find . -type f -name "init_apisix.sh" -exec sed -i "s/DJANGO_INSECURE/$default_key/g" {} \;
# find . -type f -name "init_apisix.sh" -exec sed -i "s/APISIX_ADMIN_KEY/$default_key/g" {} \;
# find . -type f -name "init_apisix.sh" -exec sed -i "s/NACOS_PASSWORD/$default_key/g" {} \;

curl -X POST 'http://127.0.0.1:8848/nacos/v1/auth/users/admin' -d 'password=${default_key}'
echo "------------------初始化nacos密码完成----------------------"

# 初始化消费者
curl http://127.0.0.1:9080/apisix/admin/consumers \
-H 'X-API-KEY: ${default_key}' -X PUT -i -d '
{
  "username": "jwt_auth",
  "plugins": {
    "jwt-auth": {
      "_meta": {
        "disable": false
      },
      "exp": 86400,
      "key": "apisix",
      "secret": ${default_key}
    }
  }
}'

# 初始化认证
curl http://127.0.0.1:9080/apisix/admin/routes \
-H 'X-API-KEY: ${default_key}' -X POST -i -d '
{
  "uri": "/rbac/login/",
  "name": "登录",
  "upstream": {
    "timeout": {
      "connect": 6,
      "send": 6,
      "read": 6
    },
    "type": "roundrobin",
    "scheme": "http",
    "discovery_type": "nacos",
    "discovery_args": {
      "group_name": "default"
    },
    "pass_host": "pass",
    "service_name": "rbac",
    "keepalive_pool": {
      "idle_timeout": 60,
      "requests": 1000,
      "size": 320
    }
  },
  "status": 1
}'

# 初始化权限中心
curl http://127.0.0.1:9080/apisix/admin/routes \
-H 'X-API-KEY: ${default_key}' -X POST -i -d '
{
  "uri": "/rbac/*",
  "name": "权限中心",
  "plugins": {
    "jwt-auth": {
      "_meta": {
        "disable": false
      }
    }
  },
  "upstream": {
    "timeout": {
      "connect": 6,
      "send": 6,
      "read": 6
    },
    "type": "roundrobin",
    "scheme": "http",
    "discovery_type": "nacos",
    "discovery_args": {
      "group_name": "default"
    },
    "pass_host": "pass",
    "service_name": "rbac",
    "keepalive_pool": {
      "idle_timeout": 60,
      "requests": 1000,
      "size": 320
    }
  },
  "status": 1
}'

# 初始化cmdb-api
curl http://127.0.0.1:9080/apisix/admin/routes \
-H 'X-API-KEY: ${default_key}' -X POST -i -d '
{
  "uri": "/api/*",
  "name": "cmdb-api",
  "plugins": {
    "jwt-auth": {
      "_meta": {
        "disable": false
      }
    }
  },
  "upstream": {
    "timeout": {
      "connect": 6,
      "send": 6,
      "read": 6
    },
    "type": "roundrobin",
    "scheme": "http",
    "discovery_type": "nacos",
    "discovery_args": {
      "group_name": "default"
    },
    "pass_host": "pass",
    "service_name": "cmdb",
    "keepalive_pool": {
      "idle_timeout": 60,
      "requests": 1000,
      "size": 320
    }
  },
  "status": 1
}'
# 初始化cmdb-ipam
curl http://127.0.0.1:9080/apisix/admin/routes \
-H 'X-API-KEY: ${default_key}' -X POST -i -d '
{
  "uri": "/ipam/*",
  "name": "cmdb-ipam",
  "plugins": {
    "jwt-auth": {
      "_meta": {
        "disable": false
      }
    }
  },
  "upstream": {
    "timeout": {
      "connect": 6,
      "send": 6,
      "read": 6
    },
    "type": "roundrobin",
    "scheme": "http",
    "discovery_type": "nacos",
    "discovery_args": {
      "group_name": "default"
    },
    "pass_host": "pass",
    "service_name": "ipam",
    "keepalive_pool": {
      "idle_timeout": 60,
      "requests": 1000,
      "size": 320
    }
  },
  "status": 1
}'

# 初始化cmdb-base_platform
curl http://127.0.0.1:9080/apisix/admin/routes \
-H 'X-API-KEY: ${default_key}' -X POST -i -d '
{
  "uri": "/base_platform/*",
  "name": "cmdb-base_platform",
  "plugins": {
    "jwt-auth": {
      "_meta": {
        "disable": false
      }
    }
  },
  "upstream": {
    "timeout": {
      "connect": 6,
      "send": 6,
      "read": 6
    },
    "type": "roundrobin",
    "scheme": "http",
    "discovery_type": "nacos",
    "discovery_args": {
      "group_name": "default"
    },
    "pass_host": "pass",
    "service_name": "base_platform",
    "keepalive_pool": {
      "idle_timeout": 60,
      "requests": 1000,
      "size": 320
    }
  },
  "status": 1
}'
# 初始化alert-gateway
curl http://127.0.0.1:9080/apisix/admin/routes \
-H 'X-API-KEY: ${default_key}' -X POST -i -d '
{
  "uri": "/alert_gateway/*",
  "name": "alert_gateway",
  "plugins": {
    "jwt-auth": {
      "_meta": {
        "disable": false
      }
    }
  },
  "upstream": {
    "timeout": {
      "connect": 6,
      "send": 6,
      "read": 6
    },
    "type": "roundrobin",
    "scheme": "http",
    "discovery_type": "nacos",
    "discovery_args": {
      "group_name": "default"
    },
    "pass_host": "pass",
    "service_name": "alert_gateway",
    "keepalive_pool": {
      "idle_timeout": 60,
      "requests": 1000,
      "size": 320
    }
  },
  "status": 1
}'
# 初始化message-gateway
curl http://127.0.0.1:9080/apisix/admin/routes \
-H 'X-API-KEY: ${default_key}' -X POST -i -d '
{
  "uri": "/msg_gateway/*",
  "name": "msg_gateway",
  "plugins": {
    "jwt-auth": {
      "_meta": {
        "disable": false
      }
    }
  },
  "upstream": {
    "timeout": {
      "connect": 6,
      "send": 6,
      "read": 6
    },
    "type": "roundrobin",
    "scheme": "http",
    "discovery_type": "nacos",
    "discovery_args": {
      "group_name": "default"
    },
    "pass_host": "pass",
    "service_name": "msg_gateway",
    "keepalive_pool": {
      "idle_timeout": 60,
      "requests": 1000,
      "size": 320
    }
  },
  "status": 1
}'
echo "------------------初始化apisix完成----------------------"