# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      init_nacos
   Description:
   Author:          Lijiamin
   date：           2022/11/4 20:34
-------------------------------------------------
   Change Activity:
                    2022/11/4 20:34
-------------------------------------------------
"""
from utils.custom.nacos import nacos
from netaxe.conf import SERVERIP, SERVERPORT
# 注册服务
nacosServer = nacos(ip=SERVERIP, port=8848)
nacosServer.registerService(
    serviceIp=SERVERIP,
    servicePort=SERVERPORT,
    serviceName="auth",
    groupName="default")
nacosServer.healthyCheck()