import requests,time
import hashlib
import urllib
import json

import logging

LOG_FORMAT = '%(asctime)s -%(name)s- %(threadName)s-%(thread)d - %(levelname)s - %(message)s'
DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
#日志配置
logging.basicConfig(level=logging.INFO,format=LOG_FORMAT,datefmt=DATE_FORMAT)

import threading

class nacos:
    def __init__(self,ip="127.0.0.1",port=8848):
        self.ip = ip
        self.port = port
        self.__threadHealthyDict = {}
        self.__configDict = {}
        self.__registerDict = {}
        self.healthy = ""

    def __healthyCheckThreadRun(self):
        while True:
            time.sleep(3)
            self.healthy = int(time.time())
            #检查configThread
            try:
                for item in self.__configDict:
                    configMsg = item.split("\001")
                    dataId = configMsg[0]
                    group = configMsg[1]
                    tenant = configMsg[2]
                    x = int(time.time()) - self.__threadHealthyDict[dataId + group + tenant]
                    if (x > 20):
                        md5Content = configMsg[3]
                        myConfig = self.__configDict[item]
                        configThread = threading.Thread(target=self.__configListeningThreadRun,
                                                        args=(dataId, group, tenant, md5Content, myConfig))
                        self.__threadHealthyDict[dataId + group + tenant] = int(time.time())
                        configThread.start()
                        logging.info("配置信息监听线程重启成功: dataId=" + dataId + "; group=" + group + "; tenant=" + tenant)
            except:
                logging.exception("配置信息监听线程健康检查错误",exc_info=True)
            #检查registerThread
            try:
                x = int(time.time()) - self.__registerDict["healthy"]
                if (x > 3):
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

    def __configListeningThreadRun(self,dataId,group,tenant,md5Content,myConfig):
        getConfigUrl = "http://" + self.ip + ":" + str(self.port) + "/nacos/v1/cs/configs"
        params = {
            "dataId": dataId,
            "group": group,
            "tenant": tenant
        }

        licenseConfigUrl = "http://" + self.ip + ":" + str(self.port) + "/nacos/v1/cs/configs/listener"
        header = {"Long-Pulling-Timeout": "30000"}
        while True:
            self.__threadHealthyDict[dataId + group + tenant] = int(time.time())
            if (tenant == "public"):
                files = {"Listening-Configs": (None, dataId + "\002" + group + "\002" + md5Content + "\001")}
            else:
                files = {"Listening-Configs": (None, dataId + "\002" + group + "\002" + md5Content + "\002" + tenant + "\001")}
            re = requests.post(licenseConfigUrl, files=files, headers=header)
            if (re.text != ""):
                try:
                    re = requests.get(getConfigUrl, params=params)
                    nacosJson = re.json()
                    md5 = hashlib.md5()
                    md5.update(re.content)
                    md5Content = md5.hexdigest()
                    for item in nacosJson:
                        myConfig[item] = nacosJson[item]
                    logging.info("配置信息更新成功: dataId=" + dataId + "; group=" + group + "; tenant=" + tenant)
                except:
                    logging.exception("配置信息更新失败：dataId=" + dataId + "; group=" + group + "; tenant=" + tenant,
                                      exc_info=True)
                    break

    def config(self,myConfig,dataId,group="DEFAULT_GROUP",tenant="public"):
        logging.info("正在获取配置: dataId="+dataId+"; group="+group+"; tenant="+tenant)
        getConfigUrl = "http://" + self.ip + ":" + str(self.port) + "/nacos/v1/cs/configs"
        params = {
            "dataId": dataId,
            "group": group,
            "tenant": tenant
        }
        try:
            re = requests.get(getConfigUrl, params=params)
            nacosJson = re.json()
            md5 = hashlib.md5()
            md5.update(re.content)
            md5Content = md5.hexdigest()

            self.__configDict[dataId+"\001"+group+"\001"+tenant+"\001"+md5Content] = myConfig

            for item in nacosJson:
                myConfig[item] = nacosJson[item]
            logging.info("配置获取成功：dataId="+dataId+"; group="+group+"; tenant="+tenant)
            configThread = threading.Thread(target=self.__configListeningThreadRun,args=(dataId,group,tenant,md5Content,myConfig))
            self.__threadHealthyDict[dataId+group+tenant] = int(time.time())
            configThread.start()
        except Exception:
            logging.exception("配置获取失败：dataId="+dataId+"; group="+group+"; tenant="+tenant, exc_info=True)

    def __registerBeatThreadRun(self,serviceIp,servicePort,serviceName,
                                groupName,namespaceId,metadata,weight):

        beatUrl = "http://" + self.ip + ":" + str(self.port) + "/nacos/v1/ns/instance/beat?"
        beatJson = {
            "ip": serviceIp,
            "port": servicePort,
            "serviceName": serviceName,
            "metadata": metadata,
#            "scheduled": "true",
            "weight": weight
        }
        params_beat = {
            "serviceName": serviceName,
            "groupName": groupName,
            "namespaceId": namespaceId,
            "beat": urllib.request.quote(json.dumps(beatJson))
        }
        for item in params_beat:
            beatUrl = beatUrl + item + "=" + params_beat[item] + "&"
        while True:
            self.__registerDict["healthy"] = int(time.time())
            try:
                time.sleep(5)
                re = requests.put(beatUrl[:-1])
                if(re.json()['code'] != 10200):
                    self.__registerDict["healthy"] = int(time.time())-10
                    logging.info(re.text)
                    break
                logging.info("发送服务心跳成功")
            except json.JSONDecodeError:
                self.__registerDict["healthy"] = int(time.time()) - 10
                break
            except :
                logging.exception("服务心跳维持失败！",exc_info=True)
                break

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
                beatThread = threading.Thread(target=self.__registerBeatThreadRun,
                                              args=(serviceIp,servicePort,serviceName,
                                              groupName,namespaceId,metadata,weight))
                beatThread.start()
            else:
                logging.error("服务注册失败 "+re.text)
        except:
            logging.exception("服务注册失败",exc_info=True)

def fallbackFun():
    return "request Error"
def timeOutFun():
    return "request time out"

class nacosBalanceClient:
    def __init__(self,ip="127.0.0.1",port=8848,serviceName="",
                      group="DEFAULT_GROUP",namespaceId="public",timeout=6,
                      fallbackFun=fallbackFun, timeOutFun=timeOutFun):
        self.ip = ip
        self.port = port
        self.serviceName = serviceName
        self.group = group
        self.namespaceId = namespaceId
        self.__LoadBalanceDict = {}
        self.timeout = timeout
        self.fallbackFun = fallbackFun
        self.timeOutFun  = timeOutFun

    def __doRequest(self,method,url,requestParamJson,*args,**kwargs) :
        if method == "GET" or method == "get":
            url = url + "/"
            for item in args:
                url = url + str(item) + "/"
            url = url[:-1]
            if kwargs.__len__() != 0:
                url = url + "?"
                for item in kwargs:
                    url = url + str(item) + "=" + str(kwargs[item]) + "&"
                url = url[:-1]
            return requests.get(url, timeout=self.timeout).text
        if method == "POST" or method == "post":
            if requestParamJson:
                header = {"Content-type": "application/json;charset=utf-8"}
                data = None
                for item in args:
                    data = item
                return requests.post(url,headers=header,data=json.dumps(data,ensure_ascii=False).encode("utf-8"), timeout=self.timeout).text
            else:
                files = {}
                for map in args:
                    for key in map:
                        files[key] = (None,map[key])
                return requests.post(url,files=files, timeout=self.timeout).text

    def __getAddress(self,serviceName,group,namespaceId):
        getProviderUrl = "http://" + self.ip + ":" + str(self.port) + "/nacos/v1/ns/instance/list"
        params = {
            "serviceName": serviceName,
            "groupName": group,
            "namespaceId": namespaceId
        }
        re = requests.get(getProviderUrl, params=params)
        try:
            msg = re.json()['hosts']
        except json.JSONDecodeError:
            msg = []
        hosts = []
        for item in msg:
            hosts.append({
                'ip': item['ip'],
                'port': item['port'],
                'healthy': item['healthy']
            })
        md5 = hashlib.md5()
        md5.update(json.dumps(hosts,ensure_ascii=False).encode("utf-8"))
        md5Content = md5.hexdigest()
        try:
            oldMd5 = self.__LoadBalanceDict[serviceName + group + namespaceId + "md5"]
        except KeyError:
            self.__LoadBalanceDict[serviceName + group + namespaceId + "md5"] = md5Content
            oldMd5 = ""
        if oldMd5 != md5Content:
            healthyHosts = []
            for host in msg:
                if host['healthy'] == True:
                    healthyHosts.append(host)
            self.__LoadBalanceDict[serviceName + group + namespaceId] = healthyHosts
            self.__LoadBalanceDict[serviceName + group + namespaceId + "index"] = 0

    def __loadBalanceClient(self,serviceName,group,namespaceId):
        try:
            x = int(time.time()) - self.__LoadBalanceDict[serviceName + group + namespaceId + "time"]
        except KeyError:
            x = 11
        if x > 10:
            self.__getAddress(serviceName,group,namespaceId)
            self.__LoadBalanceDict[serviceName + group + namespaceId + "time"] = int(time.time())

        index = self.__LoadBalanceDict[serviceName + group + namespaceId + "index"]
        l = len(self.__LoadBalanceDict[serviceName + group + namespaceId])
        if l == 0:
            logging.error("无可用服务 serviceName: "+serviceName+";group: "+group+";namespaceId: "+namespaceId)
            return ""
        if index >= l:
            self.__LoadBalanceDict[serviceName + group + namespaceId + "index"] = 1
            return self.__LoadBalanceDict[serviceName + group + namespaceId][0]['ip']+":"+str(self.__LoadBalanceDict[serviceName + group + namespaceId][0]['port'])
        else:
            self.__LoadBalanceDict[serviceName + group + namespaceId + "index"] = index + 1
            return  self.__LoadBalanceDict[serviceName + group + namespaceId][index]['ip'] + ":" + str(self.__LoadBalanceDict[serviceName + group + namespaceId][index]['port'])

    def customRequestClient(self,method,url,
                            requestParamJson=False,https=False):
        def requestPro(f):
            def mainPro(*args, **kwargs):
                address = self.__loadBalanceClient(self.serviceName, self.group, self.namespaceId)
                if address == "":
                    return
                else:
                    if https:
                        requestUrl = "https://" + address + url
                    else:
                        requestUrl = "http://" + address + url
                    try:
                        return self.__doRequest(method, requestUrl, requestParamJson, *args, **kwargs)
                    except requests.ConnectTimeout:
                        logging.exception("链接超时   ",exc_info=True)
                        return self.timeOutFun(self.serviceName,self.group,self.namespaceId,method,url)
                    except Exception as ex:
                        logging.exception("链接失败   ", exc_info=True)
                        return self.fallbackFun(self.serviceName,self.group,self.namespaceId,method,url,ex)
            mainPro.__name__ = f.__name__
            return mainPro
        return requestPro

