#! /bin/bash

# 初始化认证
curl http://127.0.0.1:9080/apisix/admin/routes \
-H 'X-API-KEY: edd1c9f034335f136f87ad84b625c8f1' -X POST -i -d '
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
-H 'X-API-KEY: edd1c9f034335f136f87ad84b625c8f1' -X POST -i -d '
{
  "uri": "/rbac/*",
  "name": "权限中心",
  "plugins": {
    "forward-auth": {
      "disable": false,
      "request_headers": [
        "Authorization"
      ],
      "ssl_verify": false,
      "timeout": 10000,
      "upstream_headers": [
        "Authorization"
      ],
      "uri": "http://rbac-nginx:80/rbac/status/"
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
-H 'X-API-KEY: edd1c9f034335f136f87ad84b625c8f1' -X POST -i -d '
{
  "uri": "/api/*",
  "name": "cmdb-api",
  "plugins": {
    "forward-auth": {
      "disable": false,
      "request_headers": [
        "Authorization"
      ],
      "ssl_verify": false,
      "timeout": 10000,
      "upstream_headers": [
        "Authorization"
      ],
      "uri": "http://rbac-nginx:80/rbac/status/"
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
-H 'X-API-KEY: edd1c9f034335f136f87ad84b625c8f1' -X POST -i -d '
{
  "uri": "/ipam/*",
  "name": "cmdb-ipam",
  "plugins": {
    "forward-auth": {
      "disable": false,
      "request_headers": [
        "Authorization"
      ],
      "ssl_verify": false,
      "timeout": 10000,
      "upstream_headers": [
        "Authorization"
      ],
      "uri": "http://rbac-nginx:80/rbac/status/"
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
echo "------------------初始化apisix完成----------------------"