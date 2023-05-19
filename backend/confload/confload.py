# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      config.py
   Description:
   Author:          Lijiamin
   date：           2023/3/30 10:09
-------------------------------------------------
   Change Activity:
                    2023/3/30 10:09
-------------------------------------------------
"""
import json
import time
import requests
import logging
import threading
import logging.config
import yaml
from pathlib import Path

log = logging.getLogger(__name__)
# 缺省配置  示例配置
DEFAULTS_FILENAME = "../config/defaults.json"
# 实际运行配置，会覆盖缺省配置
CONFIG_FILENAME = "../config/config.json"
MENU_FILENAME = "../../default_menu.json"
NAMESPACE = "public"

try:
    yaml_loader = yaml.CSafeLoader
except AttributeError:
    yaml_loader = yaml.SafeLoader


# 加载前端默认菜单
def load_memu_files(menu_filename: str = MENU_FILENAME) -> list:
    try:
        with open(menu_filename) as infil:
            return json.load(infil)
    except FileNotFoundError:
        log.warning(f"Couldn't find {menu_filename}")

    return []


# 加载配置文件
def load_config_files() -> dict:
    data = {}
    for fname in (DEFAULTS_FILENAME, CONFIG_FILENAME):
        try:
            with open(fname) as infil:
                data.update(json.load(infil))
        except FileNotFoundError:
            log.warning(f"Couldn't find {fname}")


    if not data:
        raise RuntimeError(
            f"Could not find either {DEFAULTS_FILENAME} or {CONFIG_FILENAME}"
        )

    return data


class Config:
    _instance = None

    def __init__(self):
        self.default_menu = load_memu_files()
        data = load_config_files()
        self.__registerDict = {}
        self.__configDict = {}
        self.healthy = ""
        self.data = data
        self.drivers = data['drivers']
        self.mysql_db = data['mysql_db']
        self.mysql_host = data['mysql_host']
        self.mysql_port = data['mysql_port']
        self.mysql_user = data['mysql_user']
        self.mysql_password = data['mysql_password']
        self.mongodb_host = data['mongodb_host']
        self.mongodb_port = data['mongodb_port']
        self.mongodb_user = data['mongodb_user']
        self.mongodb_password = data['mongodb_password']
        self.nacos = data['nacos']
        self.version = data['version']
        self.local_dev = data['local_dev']
        self.server_ip = data['server_ip']
        self.server_port = data['server_port']
        self.nacos_port = data['nacos_port']
        self.virtual_host = data['virtual_host']
        self.allow_origins = data['allow_origins']
        self.redis_host = data['redis_host']
        self.redis_port = data['redis_port']
        self.redis_pwd = data['redis_pwd']
        self.push_gateway = data['push_gateway']
        self.project_name = data['project_name']
        self.mq_host = data['mq_host']
        self.mq_username = data['mq_username']
        self.mq_password = data['mq_password']
        self.mq_port = data['mq_port']
        self.queue = data['queue']
        self.url_prefix = data['url_prefix']
        self.exchange = data['exchange']
        self.routing_key = data['routing_key']
        self.queue_qos = data['queue_qos']
        self.mongodb_url = data['mongodb_url']
        self.log_config_filename = data["log_config_filename"]
        self.default_webhook_name = data["default_webhook_name"]
        self.default_webhook_headers = data["default_webhook_headers"]
        self.custom_webhooks = data["custom_webhooks"]
        # 微服务 消息网关
        self.msg_gateway = data["msg_gateway"]

    # 单例模式
    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    # 获取项目根目录
    @property
    def get_root_path(self):
        file_path = Path(__file__).resolve()  # 获取当前文件的绝对路径
        root_path = file_path.parent  # 获取当前文件所在目录的路径
        while root_path.name != self.project_name:  # 根据实际情况修改根目录的名称
            root_path = root_path.parent  # 获取上级目录的路径
        return root_path

    def __healthyCheckThreadRun(self):
        while True:
            # 检查registerThread
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
                self.registerService(serviceIp, servicePort, serviceName,
                                     namespaceId, groupName, clusterName,
                                     ephemeral, metadata, weight, enabled)
            except Exception as e:
                logging.exception("服务注册心跳进程健康检查失败:{}".format(str(e)), exc_info=True)

            try:
                # 获取nacos配置并复写
                self.get_config()
            except Exception as e:
                logging.exception("配置更新失败:{}".format(str(e)), exc_info=True)

            try:
                # 获取nacos的prometheus告警规则配置并复写
                self.get_prometheus_rules()
            except Exception as e:
                logging.exception("prometheus告警规则更新失败:{}".format(str(e)), exc_info=True)

    def healthyCheck(self):
        t = threading.Thread(target=self.__healthyCheckThreadRun)
        t.start()
        logging.info("健康检查线程已启动")

    def registerService(self, serviceIp, servicePort, serviceName, namespaceId="public",
                        groupName="default", clusterName="DEFAULT",
                        ephemeral=True, metadata=None, weight=1, enabled=True):
        if metadata is None:
            metadata = {}
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

        registerUrl = "http://" + self.nacos + ":" + str(self.nacos_port) + "/nacos/v1/ns/instance"
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
                logging.error("服务注册失败 " + re.text)
        except:
            logging.exception("服务注册失败", exc_info=True)

    def get_config(self, group="default", tenant="public"):
        logging.info("正在获取配置: dataId=" + self.project_name + "; group=" + group + "; tenant=" + tenant)
        getConfigUrl = "http://" + self.nacos + ":" + str(self.nacos_port) + "/nacos/v1/cs/configs"
        # "dataId": config.project_name,
        params = {
            "dataId": self.project_name,
            "group": group,
            "tenant": tenant
        }
        try:
            res = requests.get(getConfigUrl, params=params)
            # print(res.status_code, res.text)  # 404 config data not exist
            if res.status_code == 200:
                nacos_conf = res.json()
                for k, v in nacos_conf.items():
                    log.info("[nacos ext_config set] key:%s, value:%s" % (k, v))
                    setattr(self, k, v)
        except Exception as e:
            logging.exception("配置获取失败：dataId=" + self.project_name + "; group=" + group + "; tenant=" + tenant,
                              exc_info=True)

    # AlertGatewayPrometheusRules  后期应该改成从Prometheus 的 api 接口获取告警规则会更加灵活，如果有的话
    def get_prometheus_rules(self, group="default", tenant="public"):
        logging.info("正在获取prometheus告警配置: dataId=" + self.project_name + "; group=" + group + "; tenant=" + tenant)
        getConfigUrl = "http://" + self.nacos + ":" + str(self.nacos_port) + "/nacos/v1/cs/configs"
        params = {
            "dataId": "AlertGatewayPrometheusRules",
            "group": group,
            "tenant": tenant
        }
        try:
            res = requests.get(getConfigUrl, params=params)
            if res.status_code == 200:
                self.prometheus_rules = yaml.load(res.text, Loader=yaml_loader)
        except:
            logging.exception("prometheus告警配置获取失败：dataId=" + self.project_name + "; group=" + group + "; tenant=" + tenant,
                              exc_info=True)

    # 发现服务
    def service_dicovery(self, serviceName, groupName='default', namespaceId="public"):
        url = "http://" + self.nacos + ":" + str(self.nacos_port) + "/nacos/v1/ns/instance/list"
        params = {
            "serviceName": serviceName,
            "namespaceId": namespaceId,
            "groupName": groupName,
        }
        res = requests.get(url, params=params)
        if res.status_code == 200:
            return res.json()
        return res


config = Config()


if __name__ == "__main__":
    print(config.custom_webhooks)
