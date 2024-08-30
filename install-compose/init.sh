#! /bin/bash
curl -X POST 'http://127.0.0.1:8848/nacos/v1/auth/users/admin' -d 'password=NACOS_PASSWORD'
echo "------------------初始化nacos密码完成----------------------"

# 初始化消费者
curl http://127.0.0.1:9080/apisix/admin/consumers \
-H 'X-API-KEY: APISIX_ADMIN_KEY' -X PUT -i -d '
{
  "username": "jwt_auth",
  "plugins": {
    "jwt-auth": {
      "_meta": {
        "disable": false
      },
      "exp": 86400,
      "key": "apisix",
      "secret": APISIX_ADMIN_KEY
    }
  }
}'

# 初始化认证
curl http://127.0.0.1:9080/apisix/admin/routes \
-H 'X-API-KEY: APISIX_ADMIN_KEY' -X POST -i -d '
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
-H 'X-API-KEY: APISIX_ADMIN_KEY' -X POST -i -d '
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
-H 'X-API-KEY: APISIX_ADMIN_KEY' -X POST -i -d '
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
-H 'X-API-KEY: APISIX_ADMIN_KEY' -X POST -i -d '
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
-H 'X-API-KEY: APISIX_ADMIN_KEY' -X POST -i -d '
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
-H 'X-API-KEY: APISIX_ADMIN_KEY' -X POST -i -d '
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
-H 'X-API-KEY: APISIX_ADMIN_KEY' -X POST -i -d '
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