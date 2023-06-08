## 部署方法
```shell
sh init.sh   && sh  deploy.sh  && sh init_apisix.sh
```


会自动发现你服务器默认路由对应的网卡IP作为服务部署后监听的IP
如果你的服务器涉及到IP映射或者nginx代理，需要改成

```shell
sh init.sh 1.1.1.1   && sh  deploy.sh  && sh init_apisix.sh
```
其中的1.1.1.1 就是你希望服务最终运行的IP

## 工具组件
[redis]
[rabbitmq]
[nacos]
[apisix]
[mongodb]

## 微前端项目
[仓库地址](address)
[镜像地址](address)

## 基础平台(cmdb+基础自动化+拓扑图)
[仓库地址](address)
[镜像地址](address)

## 监控模块
[仓库地址](address)
[镜像地址](address)

## 告警中心
[仓库地址](address)
[镜像地址](address)

## 消息网关
[仓库地址](address)
[镜像地址](address)
