#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author:HW
# Filename: xxx
import json
import re

from .netconf_connect import HuaweiyangNetconfConnect, XmlToDict


class HuaweiUSG(HuaweiyangNetconfConnect):
    def __init__(self, *args, **kwargs):
        super(HuaweiUSG, self).__init__(*args, **kwargs)
        self.device_type = kwargs.get("device_type")

    # 查看VRRP状态

    def get_vrrp_info(self):
        data_xml = """
        <filter type="subtree"> 
        <vrrp xmlns="urn:huawei:params:xml:ns:yang:huawei-vrrp"> 
        </vrrp> 
        </filter>
        """
        res = self.netconfig_get_config(data_xml)
        return res['vrrp']['vrrp-instance'] if 'vrrp-instance' in res['vrrp'] else None

    # 查看系统信息
    def get_system_info(self):
        data_xml = '''
                <device-state xmlns="urn:huawei:params:xml:ns:yang:huawei-device">
                </device-state>
                '''
        res = self.netconf_get(data_xml)

        if res:
            return res['device-state']
        else:
            return None

    # 查看双机热备状态
    def get_hrp_state(self):
        data_xml = '''
                <hrp-state xmlns="urn:huawei:params:xml:ns:yang:huawei-hrp"> 
                </hrp-state>
                '''
        res = self.netconf_get(data_xml)
        """
        {'hrp-state': {'@xmlns': 'urn:huawei:params:xml:ns:yang:huawei-hrp', 'hrp-status': 'standby', 
        'peer-status': 'active', 'heartbeat-status': 'running', 'config-master': 'false',
         'hrp-switch-info': {'id': '1', 'time': '2019-02-22T14:54:15+00:00', 
         'description': 'Init switchover to Standby', 'reason': 'HRP is enabled.'}}}
         hrp-status  当前状态  active   standby
         heartbeat-status 心跳状态  running
         config-master 配置主设备  true  false
         hrp-switch-info  历史切换记录
        """
        if res:
            return res['hrp-state']
        else:
            return None

    # 查看安全策略命中计数
    def get_sec_policy_counting(self):
        data_xml = """
        <sec-policy-state xmlns="urn:huawei:params:xml:ns:yang:huawei-security-policy">
        </sec-policy-state>
        """
        _req = self.netconf_get(data_xml)
        if _req:
            return _req['sec-policy-state']
        else:
            return None

    def get_interface_list(self):
        """
        采集interfaces
        请求的XML命令
        """
        data_xml = '''
           <filter type="subtree"> 
            <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces" 
            xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" 
            xmlns:urn1="urn:huawei:params:xml:ns:yang:huawei-interface" 
            xmlns:urn2="urn:huawei:params:xml:ns:yang:huawei-security-zone" 
            xmlns:urn3="urn:ietf:params:xml:ns:yang:ietf-ip" 
            xmlns:urn4="urn:huawei:params:xml:ns:yang:huawei-eth-trunk"> 
            </interfaces> 
            </filter>
        '''
        res = self.netconfig_get_config(data=data_xml)
        # {'vrfName': 'MGMT', 'ipAddr': '10.254.2.1', 'macAddr': '9ce8-95d3-f0e2', 'styleType': 'DynamicArp', 'ifName': 'MEth0/0/0'}
        # {'vrfName': '_public_', 'ipAddr': '100.71.0.98', 'macAddr': '70c7-f2be-9c02', 'styleType': 'InterfaceArp', 'ifName': '40GE1/0/1'} 全局
        return res['interfaces']['interface'] if res else None

    # 安全策略信息
    def get_sec_policy(self):
        data_xml = '''
        <filter type="subtree"> 
            <sec-policy xmlns="urn:huawei:params:xml:ns:yang:huawei-security-policy"> 
            </sec-policy> 
        </filter>
        '''
        res = self.netconfig_get_config(data=data_xml)
        if res:
            return res['sec-policy']['vsys']
        else:
            return None

    # 获取单个安全策略信息
    def get_sec_policy_single(self, rule_name):
        data_xml = '''
        <filter type="subtree"> 
            <sec-policy xmlns="urn:huawei:params:xml:ns:yang:huawei-security-policy"> 
            <vsys>
            <name></name>
            <static-policy>
            <rule>
            <name>{}</name>
            </rule>
            </static-policy>
            </vsys>
            </sec-policy> 
        </filter>
        '''.format(rule_name)
        res = self.netconfig_get_config(data=data_xml)
        if res:
            return res['sec-policy']['vsys']
        else:
            return None

    # NAT策略信息
    def get_nat_policy(self):
        data_xml = '''
        <filter type="subtree"> 
            <nat-policy xmlns="urn:huawei:params:xml:ns:yang:huawei-nat-policy"> 
            </nat-policy> 
        </filter>
        '''
        res = self.netconfig_get_config(data=data_xml)
        if res:
            if isinstance(res['nat-policy']['vsys'], dict):
                return [res['nat-policy']['vsys']]
            elif isinstance(res['nat-policy']['vsys'], list):
                return res['nat-policy']['vsys']
        else:
            return None

    # 获取NAT Server信息 现网主要用这个
    def get_nat_server(self):
        data_xml = '''
                <filter type="subtree"> 
                    <nat-server xmlns="urn:huawei:params:xml:ns:yang:huawei-nat-server">
                    </nat-server> 
                </filter>
                '''
        res = self.netconfig_get_config(data=data_xml)
        if res:
            if isinstance(res['nat-server']['server-mapping'], dict):
                return [res['nat-server']['server-mapping']]
            else:
                return res['nat-server']['server-mapping']
        else:
            return None

    # 获取NAT 地址池信息
    def get_nat_address(self):
        data_xml = '''
                <filter type="subtree"> 
                    <nat-address-group xmlns="urn:huawei:params:xml:ns:yang:huawei-nat-address-group"> 
                    </nat-address-group>
                </filter>
                '''
        res = self.netconfig_get_config(data=data_xml)
        if res and 'nat-address-group' in res['nat-address-group'].keys():
            if isinstance(res['nat-address-group']['nat-address-group'], dict):
                return [res['nat-address-group']['nat-address-group']]
            else:
                return res['nat-address-group']['nat-address-group']
        else:
            return None

    # 获取SLB配置信息
    def get_slb_info(self):
        data_xml = '''
                <filter type="subtree"> 
                    <slb xmlns="urn:huawei:params:xml:ns:yang:huawei-slb" 
                    xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"> 
                    </slb>
                </filter>
                '''
        res = self.netconfig_get_config(data=data_xml)
        """
        slb-pool 实服务组
        slb-loadbalancer 虚服务
        """
        if res:
            if isinstance(res['slb']['slb-pool'], dict):
                return [res['slb']['slb-pool']]
            else:
                return res['slb']['slb-pool']
        else:
            return None

    # 地址集 address-set
    def get_address_set(self):
        data_xml = '''
        <filter type="subtree"> 
        <address-set xmlns="urn:huawei:params:xml:ns:yang:huawei-address-set" 
        xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"> 
        </address-set> 
        </filter>
        '''
        res = self.netconfig_get_config(data=data_xml)
        """
        两个KEY
        addr-object 表示一个地址实例
        addr-group 表示一个地址组实例
        """
        if res:
            if isinstance(res['address-set']['addr-object'], dict):
                try:
                    if isinstance(res['address-set']['addr-object']['elements'], dict):
                        res['address-set']['addr-object']['elements'] = [res['address-set']['addr-object']['elements']]
                except:
                    pass
                return [res['address-set']['addr-object']]
            else:
                for i in res['address-set']['addr-object']:
                    if isinstance(i['elements'], dict):
                        i['elements'] = [i['elements']]
                return res['address-set']['addr-object']
        else:
            return None

    # 服务集 service-set
    def get_service_set(self):
        data_xml = '''
                <filter type="subtree"> 
                <service-set xmlns="urn:huawei:params:xml:ns:yang:huawei-service-set" 
                xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
                </service-set> 
                </filter>
                '''
        res = self.netconfig_get_config(data=data_xml)
        """
        service-object
        """
        if res:
            if isinstance(res['service-set']['service-object'], dict):
                if 'pre-defined-service' in res['service-set'].keys():
                    return [res['service-set']['service-object']] + res['service-set']['pre-defined-service']
                else:
                    return [res['service-set']['service-object']]
            else:
                if 'pre-defined-service' in res['service-set'].keys():
                    return res['service-set']['service-object'] + res['service-set']['pre-defined-service']
                else:
                    return res['service-set']['service-object']
        else:
            return None

    # 查询预定义应用组 不指定查询只返回name， 指定name查询返回明细，后续需要指定查询才用，目前不用
    def get_application(self):
        data_xml = '''
        <application-state xmlns="urn:huawei:params:xml:ns:yang:huawei-application" 
        xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"> 
        <user-defined-application> 
        <vsys> 
        <name>public</name> 
        <applications> 
        <application> 
        <name></name> 
        </application> 
        </applications> 
        </vsys> 
        </user-defined-application> 
        </application-state>
        '''
        res = self.netconf_get(data_xml)

        """
        {'application': {'name': 'BT', 'protocol': ['BT_TCP_Encrypted', 'BT', 'BT_HTTP', 'BT_DHT'], 
        'risk-value': '4', 'label': ['Productivity-Loss', 'Data-Loss', 'Bandwidth-Consuming', 'Evasive', 'Tunneling',
         'P2P-Based'], 'abandon': 'false', 'multichannel': 'true', 'data-model': 'peer-to-peer', 
         'category': 'General_Internet', 'subcategory': 'FileShare_P2P', 
         'description': 'BitTorrent (BT) is a P2P protocol for multi-point downloading and can be used for many 
         different kinds of applications. The client downloads and uploads data at the same time. Example: 
         BitTorrent, BitSpirit and BitComet.'}}
        """
        if res:
            """
            两个key
            user-defined-application  用户自定义应用组
            predefined-application  系统预定义应用组
            """
            return res['application-state']
        else:
            return None

    # 配置安全策略
    def config_sec_policy(self, rule):
        """
        安全策略组名 test
        描述 just for test
        源IP  address-set   或者 address-ipv4
        <source-ip>   增加多个 单IP列表
        <address-ipv4>1.1.1.1/32</address-ipv4>
        <address-ipv4>1.1.1.2/32</address-ipv4>
        </source-ip>
        结束规则 rule5
        使能标志 true
        :param kwargs:
        :return:
        """
        data_xml = """
        <config>
        <sec-policy xmlns="urn:huawei:params:xml:ns:yang:huawei-security-policy" 
        xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" 
        xmlns:yang="urn:ietf:params:xml:ns:yang:1"> 
        <vsys> 
        <name>public</name> 
        <static-policy> 
        <rule nc:operation='create'> 
        <name>test</name> 
        <desc>just for test</desc> 
        <source-zone>trust</source-zone> 
        <destination-zone>untrust</destination-zone> 
        <source-ip> 
        <address-ipv4>1.1.1.1/32</address-ipv4>
        <address-ipv4>1.1.1.2/32</address-ipv4>
        </source-ip> 
        <destination-ip> 
        <address-ipv4>2.2.2.2/32</address-ipv4> 
        </destination-ip> 
        <service> 
        <service-items> 
        <tcp> 
        <source-port>100 200 to 300 600</source-port> 
        <dest-port>700 888 to 999 1023</dest-port> 
        </tcp> 
        </service-items> 
        </service> 
        <action>true</action> 
        </rule> 
        </static-policy> 
        </vsys> 
        </sec-policy> 
        </config>
        """
        dict_data = {
            'config':
                {
                    'sec-policy':
                        {
                            '@xmlns': 'urn:huawei:params:xml:ns:yang:huawei-security-policy',
                            '@xmlns:nc': 'urn:ietf:params:xml:ns:netconf:base:1.0',
                            '@xmlns:yang': 'urn:ietf:params:xml:ns:yang:1',
                            'vsys':
                                {
                                    'name': 'public',
                                    'static-policy': rule
                                }
                        }
                }
        }
        res = XmlToDict().dicttoxml(dict=dict_data)
        data_xml = res.split('\n')[1]
        print(data_xml)
        res = self.edit_config(data_xml)
        if isinstance(res, tuple):
            return res[0], res[1]
        return res, ''

    # 删除安全策略
    def del_sec_policy(self, rule_name):
        res = self.get_sec_policy_single(rule_name=rule_name)
        if res:
            if 'static-policy' in res.keys():
                rule = res['static-policy']['rule']
                rule['@nc:operation'] = 'delete'
                dict_data = {
                    'config':
                        {
                            'sec-policy': {
                                '@xmlns': 'urn:huawei:params:xml:ns:yang:huawei-security-policy',
                                '@xmlns:nc': 'urn:ietf:params:xml:ns:netconf:base:1.0',
                                '@xmlns:yang': 'urn:ietf:params:xml:ns:yang:1',
                                'vsys':
                                    {'name': 'public',
                                     'static-policy':
                                         {'rule': rule}
                                     }
                            }
                        }
                }
                res = XmlToDict().dicttoxml(dict=dict_data)
                data_xml = res.split('\n')[1]
                res = self.edit_config(data_xml)
                if isinstance(res, tuple):
                    return res[0], res[1]
                return res, ''
        return False, '规则不存在'

    # 移动安全策略
    def move_sec_policy(self, **kwargs):
        """
        insert 可以设置为 before/after/first/last（其中 before 代表移动到目标规则之前，after 代表移动到
        目标规则之后，first 代表移动规则至第一条，last 代表移动规则至最后一条）。当 insert 设置为
        before/after 时，必须同时指定目标规则（即指定 key 值）；当 insert 设置为 first/last 时，不能指定
        目标规则。
        :param target_name:
        :param rule_name:
        :return:
        """
        if kwargs.get('rule_name') and kwargs.get('target_name') and kwargs.get('insert'):
            data_xml = """
            <config> 
            <sec-policy xmlns="urn:huawei:params:xml:ns:yang:huawei-security-policy" 
            xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" 
            xmlns:yang="urn:ietf:params:xml:ns:yang:1"> 
            <vsys> 
            <name>public</name> 
            <static-policy> 
            <rule> 
            <name>{target_name}</name> 
            </rule> 
            <rule nc:operation="merge" yang:insert="{insert}" yang:key="[name='{target_name}']"> 
            <name>{rule_name}</name> 
            <action>true</action>
            </rule> 
            </static-policy> 
            </vsys> 
            </sec-policy> 
            </config>
            """.format(rule_name=kwargs['rule_name'], target_name=kwargs['target_name'], insert=kwargs['insert'])
            res = self.edit_config(data_xml)
            return res
        elif kwargs.get('rule_name') and kwargs.get('insert'):
            data_xml = """
            <config> 
            <sec-policy xmlns="urn:huawei:params:xml:ns:yang:huawei-security-policy" 
            xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" 
            xmlns:yang="urn:ietf:params:xml:ns:yang:1"> 
            <vsys> 
            <name>public</name> 
            <static-policy> 
            <rule nc:operation="merge" yang:insert="{insert}" yang:key="[name='{rule_name}']"> 
            <name>{rule_name}</name> 
            <action>true</action>
            </rule> 
            </static-policy> 
            </vsys> 
            </sec-policy> 
            </config>
            """.format(rule_name=kwargs['rule_name'], insert=kwargs['insert'])
            res = self.edit_config(data_xml)
            return res
        return False

    # 查看安全区域
    def get_sec_zone(self, **kwargs):
        data_xml = '''
                <filter type="subtree"> 
                <security-zone xmlns="urn:huawei:params:xml:ns:yang:huawei-security-zone"> 
                </security-zone>
                </filter>
                '''
        res = self.netconfig_get_config(data=data_xml)
        if res:
            if isinstance(res['security-zone']['zone-instance'], list):
                return [res['security-zone']['zone-instance']]
            else:
                return res['security-zone']['zone-instance']
        else:
            return None

    # 配置地址组
    def config_address(self, addr_object):
        """
        :param addr_object:
        {
            '@nc:operation': 'create',
            'vsys': 'public',
            'name': 'test',
            'desc': 'how are you',
            'elements':
                [
                    {
                        'elem-id': '1',
                        'address-ipv4': '192.168.1.0/24'
                    },
                    {
                        'elem-id': '2',
                        'start-ipv4': '192.168.1.1',
                        'end-ipv4': '192.168.1.10'
                    }
                ]
        }
        :return:
        """
        dict_data = {
            'config': {
                'address-set':
                    {
                        '@xmlns': 'urn:huawei:params:xml:ns:yang:huawei-address-set',
                        '@xmlns:nc': 'urn:ietf:params:xml:ns:netconf:base:1.0',
                        'addr-object': addr_object
                    }
            }
        }
        res = XmlToDict().dicttoxml(dict=dict_data)
        data_xml = res.split('\n')[1]
        res = self.edit_config(data_xml)
        if isinstance(res, tuple):
            return res[0], res[1]
        elif isinstance(res, bool):
            return res, ''
        return False, 'netconf未捕获到预期的返回结果'

    # 配置服务对象
    def config_service(self, service_object):
        """
        :param service_object:
        {
            '@nc:operation': 'create',
            'vsys': 'public',
            'name': 'test',
            'desc': 'how are you',
            'elements':
            [
            {
            'id': '0',
            'tcp': {'source-port': {'start': '0', 'end': '65535'},
            'dest-port': {'start': '5938', 'end': '5938'}}
            },
            {
            'id': '1',
            'udp': {'source-port': {'start': '0', 'end': '65535'},
            'dest-port': {'start': '5938', 'end': '5938'}}
            }
            ]
        }
        :return:
        """
        dict_data = {
            'config': {
                'service-set':
                    {
                        '@xmlns': 'urn:huawei:params:xml:ns:yang:huawei-service-set',
                        '@xmlns:nc': 'urn:ietf:params:xml:ns:netconf:base:1.0',
                        'service-object': service_object
                    }
            }
        }
        res = XmlToDict().dicttoxml(dict=dict_data)
        data_xml = res.split('\n')[1]
        res = self.edit_config(data_xml)
        # print(res)
        if isinstance(res, tuple):
            return res[0], res[1]
        elif isinstance(res, bool):
            return res, ''
        return res

    # 创建NAT策略规则 暂不用
    def config_nat_policy(self, policy_obj):
        """
        <config>
        <nat-policy xmlns="urn:huawei:params:xml:ns:yang:huawei-nat-policy"
        xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns:yang="urn:ietf:params:xml:ns:yang:1">
        <vsys>
        <name>public</name>
        <rule nc:operation='create'>
        <name>test</name>
        <description>just for test</description>
        <source-zone>any</source-zone>
        <destination-zone>any</destination-zone>
        <source-ip>
        <address-ipv4>1.1.1.1/32</address-ipv4>
        </source-ip>
        <destination-ip>
        <address-ipv4>2.2.2.2/32</address-ipv4>
        </destination-ip>
        <service>
        <service-items>
        <tcp>
        <source-port>100 200 to 300 600</source-port>
        <dest-port>700 888 to 999 1023</dest-port>
        </tcp>
        </service-items>
        </service>
        <action>no-nat</action>
        </rule>
        </vsys>
        </nat-policy>
        </config>
        {
         'name': 'public', 虚拟系统的名称
         'rule': {
         '@nc:operation': 'create',
         'name': 'test',  # nat规则名称
         'description': 'just for test',
         'source-zone': 'any',
         'destination-zone': 'any',
         'egress-interface' : nat 策略引用的报文出接口名称 和 destination-zone 只能2选1
         'source-ip': {'address-ipv4': '1.1.1.1/32'},
           引用的源地址信息 address-ipv4、address-set address-ipv6 address-ipv4-range:{'start-ipv4': 'end-ipv4':}
           address-set-exclude address-ipv4-exclude address-ipv6-exclude address-ipv4-range-exclude
           address-mac
         'destination-ip': {'address-ipv4': '2.2.2.2/32'}, nat 目的地址信息 节点元素和source-ip一样
         'service': {'service-items': {'tcp': {'source-port': '100 200 to 300 600', 'dest-port': '700 888 to 999 1023'}}},
          引用的服务对象 service-object 和 service-items
         'action': 'no-nat'
         }}
        """
        dict_data = {
            'config': {
                'nat-policy':
                    {
                        '@xmlns': 'urn:huawei:params:xml:ns:yang:huawei-nat-policy',
                        '@xmlns:nc': 'urn:ietf:params:xml:ns:netconf:base:1.0',
                        '@xmlns:yang': 'urn:ietf:params:xml:ns:yang:1',
                        'vsys': policy_obj
                    }
            }
        }
        res = XmlToDict().dicttoxml(dict=dict_data)
        data_xml = res.split('\n')[1]
        res = self.edit_config(data_xml)
        # print(res)
        if isinstance(res, tuple):
            return res[0], res[1]
        elif isinstance(res, bool):
            return res, ''
        return res, ''

    # 配置DNAT规则
    def config_dnat(self, object):
        """
        目前就支持三种，如下
        ICMP——1 (Internet控制报文协议)
        TCP  ——6 (传输控制协议)
        UDP  ——17 (用户数据报协议)
        'server-mapping': {
            '@nc:operation': 'create',
            'name': 'test1234567890',
            'vsys': 'public',
            'global-vpn-name': 'test1',
            'protocol': '6',
            'global': {
                'if-type': 'GigabitEthernet1/0/0'
            },
            'global-port': {
                'start-port': '100',
                'end-port': '200'
            },
            'inside': {
                'start-ip': '1.2.3.4'
            },
            'inside-port': {
                'start-port': '100',
                'end-port': '200'
            },
            'no-reverse': 'true', # True 表示内部服务器无法主动访问外 部，False 表示内部服务器可以主动访问 外部网络。
            'inside-vpn-name': 'test1'
        }
        """

        dict_data = {
            'config': {
                'nat-server':
                    {
                        '@xmlns': 'urn:huawei:params:xml:ns:yang:huawei-nat-server',
                        '@xmlns:nc': 'urn:ietf:params:xml:ns:netconf:base:1.0',
                        'server-mapping': object
                    }
            }
        }
        res = XmlToDict().dicttoxml(dict=dict_data)
        data_xml = res.split('\n')[1]
        res = self.edit_config(data_xml)
        # print(res)
        if isinstance(res, tuple):
            return res[0], res[1]
        elif isinstance(res, bool):
            return res, ''
        return res

    def get_trunk_lacp(self):
        """
               xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"
               xmlns:urn1="urn:huawei:params:xml:ns:yang:huawei-interface"
               xmlns:urn2="urn:huawei:params:xml:ns:yang:huawei-security-zone"
               xmlns:urn3="urn:ietf:params:xml:ns:yang:ietf-ip"
       """
        data_xml = '''
        <filter type="subtree"> 
        <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces" 
        xmlns:urn4="urn:huawei:params:xml:ns:yang:huawei-eth-trunk"> 
        </interfaces> 
        </filter>
        '''

        res = self.netconfig_get_config(data=data_xml)
        if res:
            if isinstance(res['interfaces']['interface'], dict):
                return [res['interfaces']['interface']]
            else:
                return res['interfaces']['interface']
        else:
            return None

    # 以下为巡检需求 CPU
    def get_device_cpu(self):
        data_xml = '''
        <system-state xmlns="urn:ietf:params:xml:ns:yang:ietf-system">
        </system-state>
        '''
        res = self.netconf_get(data_xml)

        res2 = res['system-state']['hw-system:device-resource']
        return res2

    def get_device_ntp(self):
        data_xml = '''
        <filter type="subtree">
          <system xmlns="urn:ietf:params:xml:ns:yang:ietf-system"></system>
        </filter>
        '''
        res = self.netconfig_get_config(data_xml)

        if 'ntp' in res['system'].keys():
            return True
        else:
            return False

    # USG 仅支持静态路由
    def get_device_route(self):
        data_xml = '''
        <filter type="subtree">
        <routing xmlns="urn:ietf:params:xml:ns:yang:ietf-routing">
        </routing>
        </filter>

        '''
        res = self.netconfig_get_config(data_xml)
        res2 = []

        for i in res['routing']['routing-instance']:
            # print(i.keys())
            if 'routing-protocols' in i.keys():
                for j in i['routing-protocols']['routing-protocol']['static-routes']['v4ur:ipv4']['v4ur:route']:
                    tmp = dict()
                    tmp['name'] = i['name']
                    tmp['VRF'] = None
                    tmp['Topology'] = None
                    tmp['Nexthop'] = j['v4ur:next-hop']['v4ur:next-hop-address']
                    tmp['Preference'] = j['hw-v4sr:preference']
                    tmp['Metric'] = '0'
                    tmp['Neighbor'] = 'NotExist'
                    tmp['Ipv4'] = j['v4ur:destination-prefix']
                    tmp['intf'] = 'NotExist'
                    tmp['Protocol'] = 'Static'
                    res2.append(tmp)

        return res2

    @staticmethod
    def get_method():
        return [func for func in dir(HuaweiUSG) if
                callable(getattr(HuaweiUSG, func)) and not func.startswith("__")]


class HuaweiCollection(HuaweiyangNetconfConnect):

    def __init__(self, *args, **kwargs):
        super(HuaweiCollection, self).__init__(*args, **kwargs)
        self.device_type = kwargs.get("device_type")

    @staticmethod
    def get_method():
        return [func for func in dir(HuaweiCollection) if
                callable(getattr(HuaweiCollection, func)) and not func.startswith("__")]

    def colleciton_system_info(self):
        data_xml = '''
        <system xmlns="http://www.huawei.com/netconf/vrp/huawei-system">
          <systemInfo>
          </systemInfo>
        </system>
        '''
        res = self.netconf_get(data_xml)
        return res['system']['systemInfo'] if res else None

    def colleciton_stack(self):
        data_xml = '''
         <stack xmlns="http://www.huawei.com/netconf/vrp/huawei-stack">
            <stackMemberInfos>
              <stackMemberInfo>
                <memberID></memberID>
                <nextMemberID></nextMemberID>
                <deviceType></deviceType>
                <sysoid></sysoid>
                <role></role>
                <mac></mac>
                <priority></priority>
                <nextPriority></nextPriority>
                <domain></domain>
                <nextDomain></nextDomain>
                <stackPort1State></stackPort1State>
                <stackPort2State></stackPort2State>
                <uplinkPort></uplinkPort>
                <nextUplinkPort></nextUplinkPort>
                <switchMode></switchMode>
                <nextSwitchMode></nextSwitchMode>
              </stackMemberInfo>
            </stackMemberInfos>
          </stack>
        '''
        backup_xml = '''
         <stack xmlns="http://www.huawei.com/netconf/vrp/huawei-stack">
            <stackMemberInfos>
              <stackMemberInfo>
                <memberID></memberID>
                <nextMemberID></nextMemberID>
                <deviceType></deviceType>
                <sysoid></sysoid>
                <role></role>
                <mac></mac>
                <priority></priority>
                <nextPriority></nextPriority>
                <domain></domain>
                <nextDomain></nextDomain>
                <stackPort1State></stackPort1State>
              </stackMemberInfo>
            </stackMemberInfos>
          </stack>
        '''
        try:
            res = self.netconf_get(data_xml)
        except:
            res = self.netconf_get(backup_xml)
        return res['stack']['stackMemberInfos']['stackMemberInfo'] if res else None

    def get_phyentitys(self):
        """
        采集实体硬件信息
        请求的XML命令
        """
        obtain_xml = '''
        <devm xmlns="http://www.huawei.com/netconf/vrp/huawei-devm">
        <phyEntitys>
          <phyEntity>
          <entClass>mpuModule</entClass>
          </phyEntity>
        </phyEntitys>
        </devm>
        '''
        request = self.netconf_get(obtain_xml)
        return request['devm']['phyEntitys']['phyEntity']

    def get_master_board(self):
        """
        采集主控板信息
        请求的XML命令
        """
        obtain_xml = '''
        <devm xmlns="http://www.huawei.com/netconf/vrp/huawei-devm">
            <mpuBoards>
              <mpuBoard>
                <position></position>
                <entIndex></entIndex>
                <boardType></boardType>
              </mpuBoard>
            </mpuBoards>
          </devm>
           '''
        request = self.netconf_get(obtain_xml)
        # print(request)
        return request['devm']['mpuBoards']['mpuBoard']

    # 根据序列号区分slot编号
    def colleciton_moduleinfo(self):
        """
        采集colleciton_moduleinfo
        请求的XML命令
        <devm xmlns="http://www.huawei.com/netconf/vrp/huawei-devm">
                <rUModuleInfos>
                  <rUModuleInfo>
                    <entClass>mpuModule</entClass>
                    <position></position>
                     <entSerialNo></entSerialNo>
                   </rUModuleInfo>
                 </rUModuleInfos>
         </devm>
        """
        obtain_xml = '''
           <devm xmlns="http://www.huawei.com/netconf/vrp/huawei-devm">
                 <rUModuleInfos>
                   <rUModuleInfo>
                     <entClass>chassis</entClass>
                    <position></position>
                    <entSerialNo></entSerialNo>
                    <entSerialNum></entSerialNum>
                 </rUModuleInfo>
                </rUModuleInfos>
              </devm>
           '''
        back_xml = '''
        <devm xmlns="http://www.huawei.com/netconf/vrp/huawei-devm">
                 <rUModuleInfos>
                   <rUModuleInfo>
                     <entClass>mpuModule</entClass>
                    <position></position>
                    <entSerialNo></entSerialNo>
                    <entSerialNum></entSerialNum>
                 </rUModuleInfo>
                </rUModuleInfos>
              </devm>
        '''
        req = self.netconf_get(obtain_xml)
        if req:
            # 10.254.3.5 没有 chassis  只有 mpuModule
            # 10.254.6.8 有 chassis
            # 先查询 chassis  没有 chassis 则获取 mpuModule
            res = req['devm']['rUModuleInfos']['rUModuleInfo']
            if isinstance(res, dict):
                if res['entSerialNum'] == 'NA':
                    req = self.netconf_get(back_xml)
                    return req['devm']['rUModuleInfos']['rUModuleInfo']
            return res
        # {'ifName': 'Eth-Trunk127', 'TrunkMemberIfs': {'TrunkMemberIf': [{'memberIfName': '40GE1/0/5', 'weight': '1', 'memberIfState': 'Up'}, {'memberIfName': '40GE1/0/6', 'weight': '1', 'memberIfState': 'Up'}]}}
        # {'ifName': 'Eth-Trunk1', 'TrunkMemberIfs': {'TrunkMemberIf': {'memberIfName': '10GE1/0/1', 'weight': '1', 'memberIfState': 'Up'}}}

    def colleciton_trunk_lacp(self):
        """
        采集聚合口
        请求的XML命令
        """
        obtain_xml = '''
         <ifmtrunk xmlns="http://www.huawei.com/netconf/vrp/huawei-ifmtrunk">
            <TrunkIfs>
              <TrunkIf>
                <ifName></ifName>
                <TrunkMemberIfs>
                  <TrunkMemberIf>
                    <memberIfName></memberIfName>
                    <weight></weight>
                    <memberIfState></memberIfState>
                  </TrunkMemberIf>
                </TrunkMemberIfs>
              </TrunkIf>
            </TrunkIfs>
          </ifmtrunk>
           '''
        request = self.netconf_get(obtain_xml)
        # {'ifName': 'Eth-Trunk127', 'TrunkMemberIfs': {'TrunkMemberIf': [{'memberIfName': '40GE1/0/5', 'weight': '1', 'memberIfState': 'Up'}, {'memberIfName': '40GE1/0/6', 'weight': '1', 'memberIfState': 'Up'}]}}
        # {'ifName': 'Eth-Trunk1', 'TrunkMemberIfs': {'TrunkMemberIf': {'memberIfName': '10GE1/0/1', 'weight': '1', 'memberIfState': 'Up'}}}
        if request:
            lacp_res = request['ifmtrunk']['TrunkIfs']['TrunkIf']
            if isinstance(lacp_res, dict):
                return [lacp_res]
            elif isinstance(lacp_res, list):
                return lacp_res
            else:
                return []
        else:
            return []

    def colleciton_arp_list(self):
        """
        采集ARP信息
        请求的XML命令
        <vni></vni>
        """
        data_xml = '''
           <arp xmlns="http://www.huawei.com/netconf/vrp/huawei-arp">
            <arpTables>
              <arpTable>
                <vrfName></vrfName>
                <ipAddr></ipAddr>
                <macAddr></macAddr>
                <styleType></styleType>
                <ifName></ifName>
                <expireTime></expireTime>
                <peVid></peVid>
                <ceVid></ceVid>
                <pvc></pvc>
                <peerAddr></peerAddr>
              </arpTable>
            </arpTables>
          </arp>
        '''
        res = self.netconf_get(data_xml)
        # {'vrfName': 'MGMT', 'ipAddr': '10.254.2.1', 'macAddr': '9ce8-95d3-f0e2', 'styleType': 'DynamicArp', 'ifName': 'MEth0/0/0'}
        # {'vrfName': '_public_', 'ipAddr': '100.71.0.98', 'macAddr': '70c7-f2be-9c02', 'styleType': 'InterfaceArp', 'ifName': '40GE1/0/1'} 全局
        return res['arp']['arpTables']['arpTable'] if res else []

    # MAC 转发表项
    def collection_mac_table(self):
        xml_dict = {'mac': {
            '@xmlns': 'http://www.huawei.com/netconf/vrp/huawei-mac',
            'vlanFdbDynamics': {
                'vlanFdbDynamic': {
                    'slotId': None,
                    'vlanId': None,
                    'macAddress': None,
                    'macType': None,
                    'outIfName': None}
            },
            'vlanFdbs': {
                'vlanFdb': {
                    'slotId': None,
                    'vlanId': None,
                    'macAddress': None,
                    'macType': None,
                    'outIfName': None
                }
            }
        }}
        regex = re.compile(r'(vlanFdbDynamics|vlanFdbs)')
        tmp_xml = XmlToDict().dicttoxml(dict=xml_dict)
        flag, res = self._netconf_get(tmp_xml)
        # {'slotId': '0', 'vlanId': '4', 'macAddress': '082e-5ff0-2981',
        # 'macType': 'dynamic', 'outIfName': '10GE1/3/0/47'}
        # return res['mac']['vlanFdbDynamics']['vlanFdbDynamic'] if res else None
        if not flag:
            regex_commpile = re.search(regex, res)
            if regex_commpile is not None:
                regex_res = regex_commpile.group()
                xml_dict['mac'].pop(str(regex_res))
                tmp_xml = XmlToDict().dicttoxml(dict=xml_dict)
                flag, res = self._netconf_get(tmp_xml)
        if res:
            mac_res = []
            # if 'bdFdbs' in res['mac']:
            #     if isinstance(res['mac']['bdFdbs']['bdFdb'], list):
            #         mac_res += res['mac']['bdFdbs']['bdFdb']
            #     else:
            #         mac_res += [res['mac']['bdFdbs']['bdFdb']]
            if 'vlanFdbs' in res['mac']:
                if isinstance(res['mac']['vlanFdbs']['vlanFdb'], list):
                    mac_res += res['mac']['vlanFdbs']['vlanFdb']
                else:
                    mac_res += [res['mac']['vlanFdbs']['vlanFdb']]
            if 'vlanFdbDynamics' in res['mac']:
                if isinstance(res['mac']['vlanFdbDynamics']['vlanFdbDynamic'], list):
                    mac_res += res['mac']['vlanFdbDynamics']['vlanFdbDynamic']
                else:
                    mac_res += [res['mac']['vlanFdbDynamics']['vlanFdbDynamic']]
            return mac_res
        else:
            return []

    # BD动态转发表项
    def collection_mac_bd(self):
        """
        :return:
        """
        data_xml = '''
      <mac xmlns="http://www.huawei.com/netconf/vrp/huawei-mac">
            <bdFdbs>
              <bdFdb>
                <slotId></slotId>
                <macAddress></macAddress>
                <macType></macType>
                <outIfName></outIfName>
                <bdId></bdId>
                <vid></vid>
              </bdFdb>
            </bdFdbs>
          </mac>
        '''
        flag, res = self._netconf_get(data_xml)
        # {'slotId': '0', 'macAddress': '00e0-ed73-81e0', 'bdId': '11003', 'macType': 'dynamic', 'outIfName': 'Eth-Trunk24.1'}
        if flag:
            return res['mac']['bdFdbs']['bdFdb'] if res else []
        return []

    # vxlan 转发表项
    def collection_mac_vxlan(self):
        data_xml = '''
        <mac xmlns="http://www.huawei.com/netconf/vrp/huawei-mac">
                <vxlanFdbs>
                  <vxlanFdb>
                    <slotId></slotId>
                    <macAddress></macAddress>
                    <bdId></bdId>
                    <macType></macType>
                    <sourceIP></sourceIP>
                    <peerIP></peerIP>
                    <vnId></vnId>
                  </vxlanFdb>
                </vxlanFdbs>
              </mac>
        '''
        res = self.netconf_get(data_xml)
        # {'slotId': '0', 'macAddress': '00e0-ed7a-5f38', 'bdId': '11003', 'macType': 'evn', 'tunnelType': 'IPv4'}
        return res['mac']['vxlanFdbs']['vxlanFdb'] if res else []

    # VXLAN动态控制平面转发表项
    def collection_mac_vxlan_control(self):
        data_xml = '''
         <mac xmlns="http://www.huawei.com/netconf/vrp/huawei-mac">
        <vxlanControls>
          <vxlanControl>
            <slotId></slotId>
            <macAddress></macAddress>
            <bdId></bdId>
            <macType></macType>
            <tunnelType></tunnelType>
            <sourceIpv6></sourceIpv6>
            <peerIpv6></peerIpv6>
            <vnId></vnId>
          </vxlanControl>
        </vxlanControls>
      </mac>
        '''
        res = self.netconf_get(data_xml)
        # {'slotId': '0', 'macAddress': '00e0-ed7a-5f38', 'bdId': '11003', 'macType': 'evn', 'tunnelType': 'IPv4'}
        return res['mac']['vxlanControls']['vxlanControl'] if res else None

    # LLDP 邻居
    def collection_lldp_ip(self):
        data_xml = '''
          <lldp xmlns="http://www.huawei.com/netconf/vrp/huawei-lldp">
                <lldpInterfaces>
                  <lldpInterface>
                    <ifName></ifName>
                    <lldpNeighbors>
                      <lldpNeighbor>
                        <nbIndex></nbIndex>
                         <managementAddresss>
                          <managementAddress>
                            <manAddrSubtype></manAddrSubtype>
                            <manAddr></manAddr>
                            <manAddrLen></manAddrLen>
                          </managementAddress>
                        </managementAddresss>
                        <chassisIdSubtype></chassisIdSubtype>
                        <chassisId></chassisId>
                        <portIdSubtype></portIdSubtype>
                        <portId></portId>
                        <portDescription></portDescription>
                        <systemName></systemName>
                      </lldpNeighbor>
                    </lldpNeighbors>
                  </lldpInterface>
                </lldpInterfaces>
              </lldp>
        '''
        res = self.netconf_get(data_xml)
        return res['lldp']['lldpInterfaces']['lldpInterface'] if res else None

    # 接口动态信息和 IPV4、IPV6信息
    def collection_intf_ipv4v6(self):
        data_xml = '''
       <ifm xmlns="http://www.huawei.com/netconf/vrp/huawei-ifm">
         <interfaces>
           <interface>
             <ifName></ifName>
             <ipv6Oper>
                  <ipv6Addrs>
                    <ipv6Addr>
                      <ifIp6Addr></ifIp6Addr>
                      <addrType6></addrType6>
                    </ipv6Addr>
                  </ipv6Addrs>
                </ipv6Oper>
             <ipv4Oper>
               <ipv4Addrs>
                 <ipv4Addr>
                   <ifIpAddr/>
                   <subnetMask/>
                   <addrType/>
                 </ipv4Addr>
               </ipv4Addrs>
             </ipv4Oper>
             <ifDynamicInfo>
              <ifOperStatus></ifOperStatus>
              <ifPhyStatus></ifPhyStatus>
              <ifLinkStatus></ifLinkStatus>
              <ifOpertMTU></ifOpertMTU>
              <ifOperSpeed></ifOperSpeed>
              <ifV4State></ifV4State>
              <ifV6State></ifV6State>
              <ifCtrlFlapDamp></ifCtrlFlapDamp>
              <ifOperMac></ifOperMac>
            </ifDynamicInfo>
           </interface>
         </interfaces>
       </ifm>
        '''
        res = self.netconf_get(data_xml)
        # {'ifIndex': '74', 'ifName': 'Stack-Port2/2'}
        # {'ifIndex': '75', 'ifName': 'Eth-Trunk1', 'ipv4Oper': {'ipv4Addrs': {'ipv4Addr': {'ifIpAddr': '100.72.10.2', 'subnetMask': '255.255.255.252', 'addrType': 'main'}}}}
        if res:
            for i in res['ifm']['interfaces']['interface']:
                if 'ifDynamicInfo' in i.keys():
                    if 'ifOperSpeed' in i['ifDynamicInfo'].keys():
                        i['ifDynamicInfo']['ifOperSpeed'] = str(int(int(i['ifDynamicInfo']['ifOperSpeed']) / 1000000))
            return res['ifm']['interfaces']['interface']
        # return res['ifm']['interfaces']['interface'] if res else None
        return []

    # MLAG配置信息
    def collection_mlag(self):
        xml = '''
        <mlag xmlns="http://www.huawei.com/netconf/vrp/huawei-mlag">
        <mlagInstances>
          <mlagInstance>
            <dfsgroupId></dfsgroupId>
            <mlagId></mlagId>
            <localMlagPort></localMlagPort>
            <localMlagState></localMlagState>
            <peerMlagPort></peerMlagPort>
            <peerMlagState></peerMlagState>
          </mlagInstance>
        </mlagInstances>
         <localDfsInfos>
          <localDfsInfo>
            <dfsgroupId></dfsgroupId>
            <localPriority></localPriority>
            <srcIpAddress></srcIpAddress>
            <srcVpnName></srcVpnName>
            <localState></localState>
            <localHeartState></localHeartState>
            <localSystemID></localSystemID>
            <localSystemName></localSystemName>
            <localSoftVersion></localSoftVersion>
            <localDevType></localDevType>
            <localCausation></localCausation>
          </localDfsInfo>
        </localDfsInfos>
        </mlag>
        '''
        res = self.netconf_get(xml)
        return res['mlag']['mlagInstances']['mlagInstance'] if res else None

    # 以下为巡检内容
    # CPU
    def colleciton_device_cpu(self):
        xml = '''
      <devm xmlns="http://www.huawei.com/netconf/vrp/huawei-devm">
        <cpuInfos>
          <cpuInfo>
            <position></position>
            <entIndex></entIndex>
            <systemCpuUsage></systemCpuUsage>
            <ovloadThreshold></ovloadThreshold>
            <unovloadThreshold></unovloadThreshold>
          </cpuInfo>
        </cpuInfos>
      </devm>
        '''
        try:
            data = self.netconf_get(xml)  # 存在不支持情况
        except Exception as e:
            return 'device do not suport netconf about cpu'

        res = data['devm']['cpuInfos']['cpuInfo']
        return res

    # memory
    def colleciton_device_memory(self):
        xml = '''
      <devm xmlns="http://www.huawei.com/netconf/vrp/huawei-devm">
        <memoryInfos>
          <memoryInfo>
            <position></position>
            <osMemoryTotal></osMemoryTotal>
            <osMemoryUse></osMemoryUse>
            <osMemoryFree></osMemoryFree>
            <osMemoryUsage></osMemoryUsage>
            <ovloadThreshold></ovloadThreshold>
            <unovloadThreshold></unovloadThreshold>
          </memoryInfo>
        </memoryInfos>
      </devm>
        '''
        try:
            data = self.netconf_get(xml)  # 存在不支持情况
        except Exception as e:
            return 'device do not suport netconf about memory'

        # print(data)

        res = data['devm']['memoryInfos']['memoryInfo']
        return res

    # 堆叠 get_stack()

    # LACP colleciton_trunk_lacp
    def collection_aggregation(self):
        trunkIfs_xml = '''
      <ifmtrunk xmlns="http://www.huawei.com/netconf/vrp/huawei-ifmtrunk">
        <TrunkIfs>
          <TrunkIf>
            <ifName></ifName>
            <trunkType></trunkType>
          </TrunkIf>
        </TrunkIfs>
      </ifmtrunk>
        '''

        trunkMemberIfs_xml0 = '''
        <ifmtrunk xmlns="http://www.huawei.com/netconf/vrp/huawei-ifmtrunk">
        <TrunkIfs>
        '''
        trunkMemberIfs_xml1 = '''
        <TrunkIf>
        <ifName>{}</ifName>
        <TrunkMemberIfs>
        <TrunkMemberIf>
        <memberIfName></memberIfName>
        <memberIfState></memberIfState>
        </TrunkMemberIf>
        </TrunkMemberIfs>
        </TrunkIf>
        '''
        trunkMemberIfs_xml2 = '''
        </TrunkIfs>
        </ifmtrunk>
        '''
        try:
            trunkIfs_data = self.netconf_get(trunkIfs_xml)  # 存在不支持情况

        except Exception as e:
            print(e)
            return 'device do not suport netconf about aggregation'
        if isinstance(trunkIfs_data['ifmtrunk']['TrunkIfs']['TrunkIf'], list):
            for i in trunkIfs_data['ifmtrunk']['TrunkIfs']['TrunkIf']:
                tmp_xml = trunkMemberIfs_xml1.format(i['ifName'])
                trunkMemberIfs_xml0 = trunkMemberIfs_xml0 + tmp_xml
            trunkMemberIfs_xml = trunkMemberIfs_xml0 + trunkMemberIfs_xml2
            trunkMemberIfs_data = self.netconf_get(trunkMemberIfs_xml)
        else:
            return

        res = trunkMemberIfs_data['ifmtrunk']['TrunkIfs']['TrunkIf']
        return res

    # interface status
    def collection_intf_status(self):
        data_xml1 = '''
        <ifm xmlns="http://www.huawei.com/netconf/vrp/huawei-ifm">
        <interfaces>
        <interface>
        <ifName></ifName>
        <ifDynamicInfo>
        <ifOperStatus></ifOperStatus>
        <ifPhyStatus></ifPhyStatus>
        <ifLinkStatus></ifLinkStatus>
        <ifOpertMTU></ifOpertMTU>
        <ifOperSpeed></ifOperSpeed>
        <ifV4State></ifV4State>
        <ifV6State></ifV6State>
        </ifDynamicInfo>
        </interface>
        </interfaces>
        </ifm>
         '''
        r1 = self.netconf_get(data_xml1)
        # print({1:r1})
        data_st = '''
        <devm xmlns="http://www.huawei.com/netconf/vrp/huawei-devm">
        <ports>'''
        data_end = '''</ports></devm>'''
        if r1:
            for i in r1['ifm']['interfaces']['interface']:
                if any(i["ifName"].startswith(str_) for str_ in
                       ["Tunnel", "Port", "MEth", "Vbdif", "Vlanif", "Sip", "LoopBack", "NULL0", "Stack-Port",
                        "Eth-Trunk"]):
                    continue
                elif i["ifName"].find('.') != -1:
                    continue
                else:
                    # print(i["ifName"])
                    tmp_data = '''<port>
                                <position>{}</position>
                                <ethernetPort>
                                <duplex/>
                                </ethernetPort>
                                </port>'''.format(i["ifName"])
                    data_st += tmp_data
        data_xml2 = data_st + data_end
        r2 = self.netconf_get(data_xml2)
        r2_res = dict()
        for i in r2['devm']['ports']['port']:
            r2_res[i['position']] = i['ethernetPort']['duplex']
        datas = list()
        for i in r1['ifm']['interfaces']['interface']:
            if any(i["ifName"].startswith(str_) for str_ in
                   ["Tunnel", "Port", "MEth", "Vbdif", "Vlanif", "Sip", "LoopBack", "NULL0", "Stack-Port",
                    "Eth-Trunk"]):
                continue
            elif i["ifName"].find('.') != -1:
                continue
            if 'ifDynamicInfo' in i.keys() and not i['ifName'].startswith('Eth-Trunk'):
                if 'ifOperSpeed' in i['ifDynamicInfo'].keys():
                    data = dict(
                        interface=i['ifName'],
                        status=i['ifDynamicInfo']['ifOperStatus'],
                        speed=i['ifDynamicInfo']['ifOperSpeed'],
                        duplex=r2_res[i['ifName']],
                        description='')
                    datas.append(data)
        return datas

    # OSPF 没找到
    def collection_ospf_peer(self):
        return False

    # BGP (对等体信息)
    def collection_bgp_peer(self):
        xml = '''
      <bgp xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>_public_</vrfName>
              <bgpVrfAFs>
                <bgpVrfAF>
                  <afType></afType>
                  <peerAFs>
                    <peerAF>
                      <remoteAddress></remoteAddress>
                      <peerInfo>
                        <peerType></peerType>
                        <remoteRouterId></remoteRouterId>
                        <bgpCurState></bgpCurState>
                      </peerInfo>
                    </peerAF>
                  </peerAFs>
                </bgpVrfAF>
              </bgpVrfAFs>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>



        '''
        try:
            data = self.netconf_get(xml)  # 存在不支持情况
        except Exception as e:
            return 'device do not suport netconf about bgp_peer'

        # print(data)
        res = []
        res1 = data['bgp']['bgpcomm']['bgpVrfs']['bgpVrf']['bgpVrfAFs']['bgpVrfAF']
        # print(dict(aa = res1))
        if isinstance(res1, list):
            for i in res1:
                if isinstance(i['peerAFs']['peerAF'], list):
                    for j in i['peerAFs']['peerAF']:
                        tmp = dict(
                            Name=None,
                            VRF=None,
                            AF=i.get('afType', 'NotExist'),
                        )
                        tmp['IpAddress'] = j.get('remoteAddress', 'NotExist')
                        tmp['ASNumber'] = 'NotExist'
                        tmp['State'] = j['peerInfo']['bgpCurState']

                        res.append(tmp)
                else:
                    j = i['peerAFs']['peerAF']
                    tmp = dict(
                        Name=None,
                        VRF=None,
                        AF=i.get('afType', 'NotExist'),
                    )
                    tmp['IpAddress'] = j.get('remoteAddress', 'NotExist')
                    tmp['ASNumber'] = 'NotExist'
                    tmp['State'] = j['peerInfo']['bgpCurState']

                    res.append(tmp)

        return res

    # BGP (对等体日志信息)
    def collection_bgp_error(self):
        xml = '''
      <bgp xmlns="http://www.huawei.com/netconf/vrp/huawei-bgp">
        <bgpcomm>
          <bgpVrfs>
            <bgpVrf>
              <vrfName>_public_</vrfName>
              <bgpPeers>
                <bgpPeer>
                  <peerAddr></peerAddr>
                  <peerLogInfos>
                    <peerLogInfo>
                      <logIndex></logIndex>
                      <stateEvent></stateEvent>
                      <errorCode></errorCode>
                      <notification></notification>
                      <logDateTime></logDateTime>
                    </peerLogInfo>
                  </peerLogInfos>
                </bgpPeer>
              </bgpPeers>
            </bgpVrf>
          </bgpVrfs>
        </bgpcomm>
      </bgp>
        '''
        try:
            data = self.netconf_get(xml)  # 存在不支持情况
        except Exception as e:
            return 'device do not suport netconf about bgp_peer'

        print(data)

        # res = data['devm']['memoryInfos']['memoryInfo']
        # return res

    # ntp status
    def collection_ntp_status(self):
        xml = '''
      <ntp xmlns="http://www.huawei.com/netconf/vrp/huawei-ntp">
        <ntpStatus>
          <clockStatus></clockStatus>
          <clockStratum></clockStratum>
          <clockSrc></clockSrc>
        </ntpStatus>
      </ntp>
        '''
        try:
            data = self.netconf_get(xml)  # 存在不支持情况
        except Exception as e:
            return 'device do not suport netconf about ntp status'

        # print(data)

        res = data['ntp']['ntpStatus']
        return res

    # ip_routing_table
    def collection_ip_routing_table(self):
        xml = '''
        <rm xmlns="http://www.huawei.com/netconf/vrp/huawei-rm">
        <rmbase>
          <uniAfs>
            <uniAf>
              <vrfName>_public_</vrfName>
              <afType>ipv4unicast</afType>
              <topologys>
                <topology>
                  <topologyName>base</topologyName>
                  <routes>
                    <route>
                      <prefix></prefix>
                      <maskLength></maskLength>
                      <protocolId></protocolId>
                      <ifName></ifName>
                      <processId></processId>
                      <directNexthop></directNexthop>
                    </route>
                  </routes>
                </topology>
              </topologys>
            </uniAf>
          </uniAfs>
        </rmbase>
        </rm>
        '''
        try:
            data = self.netconf_get(xml)  # 存在不支持情况
        except Exception as e:
            return 'device do not suport netconf about ip_routing_table'

        res = data['rm']['rmbase']['uniAfs']['uniAf']['topologys']['topology']['routes']['route']
        return res

    # mac-move
    def collection_mac_flap(self):
        xml = '''
        <mac xmlns="http://www.huawei.com/netconf/vrp/huawei-mac">
          <macflpDetectRecords>
            <macflpDetectRecord>
              <broadcastDomainType></broadcastDomainType>
              <broadcastDomainName></broadcastDomainName>
              <slotId></slotId>
              <macAddress></macAddress>
              <moveNum></moveNum>
              <startTime></startTime>
              <endTime></endTime>
              <originalPorts>
                <originalPort>
                  <orgPortType></orgPortType>
                  <orgPort></orgPort>
                </originalPort>
              </originalPorts>
              <movePorts>
                <movePort>
                  <movePortType></movePortType>
                  <moveSequence></moveSequence>
                  <movePort></movePort>
                </movePort>
              </movePorts>
            </macflpDetectRecord>
          </macflpDetectRecords>
        </mac>
          '''
        try:
            data = self.netconf_get(xml)  # 存在不支持情况
        except Exception as e:
            return 'device do not suport netconf about mac-move'

        res = data['mac']['macflpDetectRecords']['macflpDetectRecord']
        return res

    def collection_foo(self):
        xml = '''
      <mac xmlns="http://www.huawei.com/netconf/vrp/huawei-mac">
        <macflpDetectRecords>
          <macflpDetectRecord>
            <broadcastDomainType></broadcastDomainType>
            <broadcastDomainName></broadcastDomainName>
            <slotId></slotId>
            <macAddress></macAddress>
            <moveNum></moveNum>
            <startTime></startTime>
            <endTime></endTime>
            <originalPorts>
              <originalPort>
                <orgPortType></orgPortType>
                <orgPort></orgPort>
              </originalPort>
            </originalPorts>
            <movePorts>
              <movePort>
                <movePortType></movePortType>
                <moveSequence></moveSequence>
                <movePort></movePort>
              </movePort>
            </movePorts>
          </macflpDetectRecord>
        </macflpDetectRecords>
      </mac>
        '''
        try:
            data = self.netconf_get(xml)  # 存在不支持情况
        except Exception as e:
            print(e)
            return 'device do not suport netconf about foo'

        print(data)
        #
        # res = data['devm']['memoryInfos']['memoryInfo']
        return data


if __name__ == '__main__':
    pass