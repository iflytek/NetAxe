import json
import urllib
import logging
import hashlib
import threading
import requests,time

logger = logging.getLogger('server')


class nacos:
    def __init__(self,ip="127.0.0.1",port=8848):
        self.ip = ip
        self.port = port
        self.__registerDict = {}
        self.healthy = ""

    def __healthyCheckThreadRun(self):
        while True:
            #检查registerThread
            try:
                time.sleep(5)
                serviceIp = self.__registerDict["serviceIp"]
                servicePort = self.__registerDict["servicePort"]
                serviceName = self.__registerDict["serviceName"]
                namespaceId = self.__registerDict["namespaceId"]
                groupName = self.__registerDict["groupName"]
                clusterName = self.__registerDict["clusterName"]
                ephemeral = self.__registerDict["ephemeral"]
                metadata = self.__registerDict["metadata"]
                weight = self.__registerDict["weight"]
                enabled = self.__registerDict["enabled"]
                self.registerService(serviceIp,servicePort,serviceName,
                                        namespaceId,groupName,clusterName,
                                        ephemeral,metadata,weight,enabled)
            except:
                logging.exception("服务注册心跳进程健康检查失败",exc_info=True)

    def healthyCheck(self):
        t = threading.Thread(target=self.__healthyCheckThreadRun)
        t.start()
        logging.info("健康检查线程已启动")

    def registerService(self,serviceIp,servicePort,serviceName,namespaceId="public",
                        groupName="DEFAULT_GROUP",clusterName="DEFAULT",
                        ephemeral=True,metadata={},weight=1,enabled=True):
        self.__registerDict["serviceIp"] = serviceIp
        self.__registerDict["servicePort"] = servicePort
        self.__registerDict["serviceName"] = serviceName
        self.__registerDict["namespaceId"] = namespaceId
        self.__registerDict["groupName"] = groupName
        self.__registerDict["clusterName"] = clusterName
        self.__registerDict["ephemeral"] = ephemeral
        self.__registerDict["metadata"] = metadata
        self.__registerDict["weight"] = weight
        self.__registerDict["enabled"] = enabled
        self.__registerDict["healthy"] = int(time.time())


        registerUrl = "http://" + self.ip + ":" + str(self.port) + "/nacos/v1/ns/instance"
        params = {
            "ip": serviceIp,
            "port": servicePort,
            "serviceName": serviceName,
            "namespaceId": namespaceId,
            "groupName": groupName,
            "clusterName": clusterName,
            "ephemeral": ephemeral,
            "metadata": json.dumps(metadata),
            "weight": weight,
            "enabled": enabled
        }
        try:
            re = requests.post(registerUrl, params=params)
            if (re.text == "ok"):
                logging.info("服务注册成功。")
            else:
                logging.error("服务注册失败 "+re.text)
        except:
            logging.exception("服务注册失败",exc_info=True)

def fallbackFun():
    return "request Error"
def timeOutFun():
    return "request time out"