# -*- coding: utf-8 -*-
# @Time    : 2022/4/14 16:01
# @Author  : jmli12
# @Site    :
# @File    : h3c.py
# @Software: PyCharm
# from apps.automation.utils.auto_main import BatManMain
import json
import math
import re
from typing import Dict, List
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from netmiko import (NetmikoTimeoutException, NetmikoAuthenticationException, ConfigInvalidException)
from apps.asset.models import NetworkDevice
from apps.automation.models import CollectionPlan
from utils.connect_layer.NETCONF.h3c_netconf import H3CinfoCollection
from utils.connect_layer.NETCONF.huawei_netconf import HuaweiCollection, HuaweiUSG
from utils.connect_layer.my_netmiko import my_netmiko

# logging.basicConfig(level=logging.DEBUG)
"""
1. 无特殊情况，默认情况下，连接方式默认用BaseConnection类
2. 特殊设备特殊处理，可以考虑继承BaseConnection类进行功能扩展
"""
device_type_map = {
    "H3C": "hp_comware",
    "Huawei": "huawei",
    "Hillstone": "hillstone",
    "Mellanox": "mellanox",
    "centec": "cisco_ios",
    "Ruijie": "ruijie_os",
    "Maipu": "ruijie_os",
    "Cisco": "cisco_ios",
}
fsm_flag_map = {
    "H3C": "hp_comware",
    "Huawei": "huawei_vrp",
    "Hillstone": "hillstone",
    "Mellanox": "mellanox",
    "centec": "centec",
    "Ruijie": "ruijie",
    "Maipu": "maipu",
    "Cisco": "cisco_ios",
}
netconf_class_map = {
    "huawei_usg": HuaweiUSG,
    "huawei": HuaweiCollection,
    "h3c": H3CinfoCollection,
}


# 接口格式化类
class InterfaceFormat(object):
    @staticmethod
    def h3c_interface_format(interface):
        if re.search(r'^(GE)', interface):
            return interface.replace('GE', 'GigabitEthernet')

        elif re.search(r'^(BAGG)', interface):
            return interface.replace('BAGG', 'Bridge-Aggregation')

        elif re.search(r'^(RAGG)', interface):
            return interface.replace('RAGG', 'Route-Aggregation')

        elif re.search(r'^(XGE)', interface):
            return interface.replace('XGE', 'Ten-GigabitEthernet')
        elif re.search(r'^(HGE)', interface):
            return interface.replace('XGE', 'HundredGigE')

        elif re.search(r'^(FGE)', interface):
            return interface.replace('FGE', 'FortyGigE')

        elif re.search(r'^(MGE)', interface):
            return interface.replace('MGE', 'M-GigabitEthernet')

        elif re.search(r'^(M-GE)', interface):
            return interface.replace('M-GE', 'M-GigabitEtherne')

        return interface

    @staticmethod
    def huawei_interface_format(interface):
        if re.search(r'^(GE)', interface):
            return interface.replace('GE', 'GigabitEthernet')

        elif re.search(r'^(XGE)', interface):
            return interface.replace('XGE', 'XGigabitEthernet')

        return interface

    @staticmethod
    def maipu_interface_format(interface):
        if re.search(r'^(te)', interface):
            return interface.replace('te', 'tengigabitethernet')

        return interface

    @staticmethod  # 按接口名称速率转换
    def h3c_speed_format(interface):
        if re.search(r'^(GE)', interface) or re.search(
                r'^(GigabitEthernet)', interface):
            return '1G'

        elif re.search(r'^(XGE)', interface) or re.search(r'^(Ten-GigabitEthernet)', interface):
            return '10G'

        elif re.search(r'^(FGE)', interface) or re.search(r'^(FortyGigE)', interface):
            return '40G'

        elif re.search(r'^(Twenty-FiveGigE)', interface):
            return '100G'

        elif re.search(r'^(MGE)', interface) or re.search(r'^(MEth)', interface):
            return '1G'

        elif re.search(r'^(M-GE)', interface):
            return '1G'
        return interface

    @staticmethod  # 按接口名称速率转换
    def ruijie_speed_format(interface):
        if re.search(r'^(GigabitEthernet)', interface):
            return '1G'
        elif re.search(r'^(TenGigabitEthernet)', interface):
            return '10G'
        elif re.search(r'^(TFGigabitEthernet)', interface):
            return '10G'
        elif re.search(r'^(FortyGigabitEthernet)', interface):
            return '40G'
        elif re.search(r'^(HundredGigabitEthernet)', interface):
            return '100G'
        return interface

    @staticmethod  # 按接口名称速率转换
    def cisco_speed_format(interface):
        if re.search(r'^(GigabitEthernet)', interface):
            return '1G'
        elif re.search(r'^(TenGigabitEthernet)', interface):
            return '10G'
        elif re.search(r'^(TFGigabitEthernet)', interface):
            return '10G'
        elif re.search(r'^(FortyGigabitEthernet)', interface):
            return '40G'
        elif re.search(r'^(HundredGigabitEthernet)', interface):
            return '100G'
        return interface


    @staticmethod
    def mathintspeed(value):
        """接口speed单位换算"""
        k = 1000
        try:
            value = int(value) * 1000000
        except:
            return value
        if value == 0:
            return str(value)
        # value = value * 8
        sizes = ['bytes', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
        c = math.floor(math.log(value) / math.log(k))
        value = (value / math.pow(k, c))
        value = '% 6.0f' % value
        value = str(value) + sizes[c]
        return value.strip()


class BaseConn:
    def __init__(self, **kwargs):
        self.hostip = kwargs['manage_ip']
        self.hostname = kwargs['name']
        self.idc_name = kwargs.get('idc__name', '')
        self.vendor_alias = kwargs['vendor__alias']
        self.device_type = device_type_map[self.vendor_alias]
        self.fsm_flag = fsm_flag_map[self.vendor_alias]
        self.auto_enable = kwargs['auto_enable']
        self.soft_version = kwargs['soft_version'] if kwargs['soft_version'] is not None else '',
        self.patch_version = kwargs.get('patch_version', '')
        self.chassis = kwargs['chassis']
        self.slot = kwargs['slot']
        self.serial_num = kwargs.get('serial_num', '')
        self.category__name = kwargs['category__name']
        self.model__name = kwargs.get('model__name', '')
        self.ha_status = kwargs.get('ha_status', '')
        self.bind_ip__ipaddr = kwargs.get('bind_ip__ipaddr', '')
        if 'telnet' in kwargs['protocol']:
            self.device_type += '_telnet'
            self.netmiko_params = {
                'device_type': self.device_type,
                'ip': self.hostip,
                'port': kwargs['telnet']['port'],
                'username': kwargs['telnet']['username'],
                'password': kwargs['telnet']['password'],
                'timeout': 200,  # float，连接超时时间，默认为100
                'session_timeout': 100,  # float，每个请求的超时时间，默认为60
                'conn_timeout': 50,
                'encoding': 'utf-8'
            }
        else:
            self.netmiko_params = {
                'device_type': self.device_type,
                'ip': self.hostip,
                'port': kwargs['ssh']['port'],
                'username': kwargs['ssh']['username'],
                'password': kwargs['ssh']['password'],
                'timeout': 200,  # float，连接超时时间，默认为100
                'session_timeout': 100,  # float，每个请求的超时时间，默认为60
                'conn_timeout': 50,
                'encoding': 'utf-8'
            }
        # print(self.netmiko_params)
        self.collection_plan = kwargs['plan_id']
        self.model = kwargs['model__name'] if kwargs['model__name'] is not None else ''
        self.netconf_params = {}
        if 'netconf' in kwargs['protocol']:
            self.netconf_params = {
                'ip': self.hostip,
                'port': kwargs['netconf']['port'],
                'username': kwargs['netconf']['username'],
                'password': kwargs['netconf']['password'],
                'timeout': 200,  # float，连接超时时间，默认为100
                'session_timeout': 100,  # float，每个请求的超时时间，默认为60
            }
        if self.model.startswith('USG'):
            # 华为防火墙需要从绑定IP访问
            self.netconf_flag = 'huawei_usg'
            self.netconf_params['ip'] = self.bind_ip__ipaddr
            self.fsm_flag = 'huawei_usg'
        elif self.model.startswith('CE'):
            self.netconf_flag = 'huawei'
        elif self.vendor_alias == 'H3C':
            self.netconf_flag = 'h3c'
        elif self.device_type == 'cisco_ios' and self.category__name == '防火墙':
            self.device_type = 'cisco_asa'
        else:
            self.netconf_flag = ''
        self.plan = {}
        self.netconf_class = ''
        if self.collection_plan:
            self.plan = CollectionPlan.objects.filter(id=self.collection_plan).values().first()
            self.netconf_class = self.plan['netconf_class']
        else:
            self.plan = CollectionPlan.objects.filter(
                vendor=self.vendor_alias, category=self.category__name).values().first()
            if self.plan:
                self.netconf_class = self.plan['netconf_class']
                NetworkDevice.objects.filter(
                    manage_ip=self.hostip).update(plan=CollectionPlan.objects.get(id=self.plan['id']))
        # 交换机特性
        self.layer3datas = []

    # 执行命令下发
    def _send_cmd(self, cmds: list) -> List[Dict]:
        paths = []
        try:
            with my_netmiko(**self.netmiko_params) as dev_connection:
                prompt = dev_connection.find_prompt()  # 找出设备的prompt
                quit_cmd = {
                    'H3C': 'quit',
                    'Huawei': 'quit',
                    'Hillstone': 'exit',
                    'Ruijie': 'exit',
                    'centec': 'exit',
                    'Maipu': 'exit',
                }
                if self.vendor_alias in ['H3C', 'Huawei']:
                    # HRP_M<DZ.NET.IN.FW.001>
                    hostname = re.search(r'(<[^)]*>)', prompt).group()
                    if self.hostname != hostname[1:-1]:
                        NetworkDevice.objects.filter(manage_ip=self.hostip).update(name=hostname[1:-1])
                elif self.vendor_alias in ['Hillstone', 'Ruijie', 'centec', 'Maipu', 'Mellanox']:
                    if self.hostname != prompt[:-1]:
                        NetworkDevice.objects.filter(manage_ip=self.hostip).update(name=prompt[:-1])
                # print(prompt)
                for cmd in cmds:
                    content = dev_connection.send_command(cmd)
                    if content:
                        filename = 'automation/' + self.hostip + '/' + '_'.join(cmd.split()) + '.txt'
                        # 判断文件是否已经存在
                        if default_storage.exists(filename):
                            # 删除已经存在的文件重新生成
                            default_storage.delete(filename)
                        path = default_storage.save(filename, ContentFile(content))
                        # automation/10.254.2.55/display_evpn_route_arp.txt
                        paths.append({
                            "path": path,
                            "cmd_file": '_'.join(cmd.split())
                        })
                if self.vendor_alias in quit_cmd.keys():
                    # dev_connection.send_command(quit_cmd[self.vendor_alias])
                    dev_connection.cleanup(command=quit_cmd[self.vendor_alias])
                dev_connection.disconnect()
        except NetmikoAuthenticationException as e:  # 认证失败报错记录
            print('[Error 1] Authentication failed.{}'.format(str(e)))
            raise RuntimeError('[Error 1] Authentication failed.{}'.format(str(e)))
        except NetmikoTimeoutException as e:  # 登录超时报错记录
            print('[Error 2] Connection timed out.{}'.format(str(e)))
            raise RuntimeError('[Error 2] Connection timed out.{}'.format(str(e)))
        except ConfigInvalidException as e:  # 配置项错误
            print('[Error 3] ConfigInvalidException.{}'.format(str(e)))
            raise RuntimeError('[Error 3] ConfigInvalidException.{}'.format(str(e)))
        except Exception as e:
            # 采集失败的记录日志
            print(str(e))
            raise RuntimeError('[Error 4] Exception.{}'.format(str(e)))
        return paths

    # 执行数据解析  这里每个厂商的解析方式不一样，采用类的继承方式实现，父类只做定义
    def _collection_analysis(self, paths: list):
        """
        这里每个厂商的解析方式不一样，采用类的继承方式实现，父类只做定义
        :param paths:
        :return:
        """
        pass

    # 执行netconf的数据解析， 每个厂商的解析方式不一样，父类只做定义，子类继承完善功能
    def _netconf_analysis(self, datas):
        """
        这里每个厂商的解析方式不一样，采用类的继承方式实现，父类只做定义
        :param paths:
        :return:
        """
        pass

    # 按数据采集方案执行数据采集任务 包括commands  和  netconf的下发
    def collection_run(self):
        if self.auto_enable:
            # self.netmiko_params['device_type'] = self.plan['netmiko_flag']
            cmds = json.loads(self.plan['commands'])
            if cmds:
                print('执行命令下发')
                paths = self._send_cmd(cmds)
                self._collection_analysis(paths)
        return

    # 手动运行命令
    def manual_cmd_run(self, *commands):
        if self.auto_enable:
            print('执行命令下发')
            paths = self._send_cmd(cmds=list(commands))
            self._collection_analysis(paths)
        return
