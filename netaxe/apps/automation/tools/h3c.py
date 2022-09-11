# -*- coding: utf-8 -*-
# @Time    : 2022/4/14 16:01
# @Author  : jmli12
# @Site    :
# @File    : h3c.py
# @Software: PyCharm
import json
import math
import re
import time
from datetime import datetime

from django.core.cache import cache
from ncclient.transport.errors import SessionCloseError
from netaddr import IPNetwork, IPAddress

from apps.asset.models import NetworkDevice, Model, Vendor
from utils.connect_layer.auto_main import BatManMain
from utils.connect_layer.NETCONF.h3c_netconf import H3CinfoCollection, H3CSecPath
from utils.db.mongo_ops import MongoNetOps, MongoOps
from utils.wechat_api import send_msg_netops
from .base_connection import BaseConn


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
        return interface.replace('HGE', 'HundredGigE')

    elif re.search(r'^(FGE)', interface):
        return interface.replace('FGE', 'FortyGigE')

    elif re.search(r'^(MGE)', interface):
        return interface.replace('MGE', 'M-GigabitEthernet')

    elif re.search(r'^(M-GE)', interface):
        return interface.replace('M-GE', 'M-GigabitEtherne')

    return interface


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

    elif re.search(r'^(HGE)', interface):
        return '100G'

    elif re.search(r'^(MGE)', interface) or re.search(r'^(MEth)', interface):
        return '1G'

    elif re.search(r'^(M-GE)', interface):
        return '1G'
    return interface


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


class H3cProc(BaseConn):
    """
    display ip interface
    display arp
    display mac-address
    display link-aggregation verbose
    display interface brief
    display lldp neighbor-information verbose
    """

    def __init__(self, **kwargs):
        super(H3cProc, self).__init__(**kwargs)
        self.ser_map = {}
        self.addr_map = {}
        self.dnat_data = []
        self.snat_data = []
        self.nat_addr_groups = {}
        self.addr_set = {}

    # 华三防火墙安全策略处理
    def h3c_secpath_sec_policy(self, datas):
        """
        Type: '1',
        ID: '0',
        Action: '2',
        SrcZoneList: {
            SrcZoneItem: 'taibao'
        },
        DestZoneList: {
            DestZoneItem: 'iflytek'
        },
        DestAddrList: {
            DestAddrItem: 'Server-AIaaS'
        },
        ServGrpList: {
            ServGrpItem: 'Services-AIaaS'
        },
        Enable: 'true',
        Log: 'false',
        Counting: 'true',
        Count: '27349857740',
        Byte: '36160694587021',
        SessAgingTimeSw: 'false',
        SessPersistAgingTimeSw: 'false',
        AllRulesCount: '3',
        hostip: '10.254.12.70'
        :param host:
        :param datas:
        :return:
        """
        my_mongo = MongoOps(db='Automation', coll='sec_policy')
        my_mongo.delete_many(query=dict(hostip=self.hostip))
        address_mongo = MongoOps(db='NETCONF', coll='h3c_address_set')
        results = []
        for i in datas:
            # print(i)
            tmp = dict()
            tmp['src_ip_split'] = []
            tmp['dst_ip_split'] = []
            service = []
            if i.get('ServGrpList'):
                if isinstance(i['ServGrpList']['ServGrpItem'], str):
                    service.append(
                        dict(
                            object=i['ServGrpList']['ServGrpItem']))
                elif isinstance(i['ServGrpList']['ServGrpItem'], list):
                    service += [{'object': x}
                                for x in i['ServGrpList']['ServGrpItem']]
            if i.get('ServObjList'):
                type_map = {
                    "0": "tcp",
                    "1": "udp",
                    "2": "icmp"
                }
                if isinstance(i['ServObjList']['ServObjItem'], str):
                    item = json.loads(i['ServObjList']['ServObjItem'])
                    item['Type'] = type_map[item['Type']]
                    service.append(dict(item=item))
                elif isinstance(i['ServObjList']['ServObjItem'], list):
                    for x in i['ServObjList']['ServObjItem']:
                        _tmp = json.loads(x)
                        _tmp['Type'] = type_map[_tmp['Type']]
                        service.append(dict(item=_tmp))
                    # service += [{'item': json.loads(x)} for x in i['ServObjList']['ServObjItem']]
            # 'ServObjList': {'ServObjItem': '{ "Type": "0", "StartSrcPort": "0", "EndSrcPort": "65535", "StartDestPort": "80", "EndDestPort": "80" }'},
            # 子网IP匹配正则
            ipaddr_regex = re.compile('^\\d+.\\d+.\\d+.\\d+/\\d+$')
            # 主机IP地址匹配正则
            host_ip_regex = re.compile('^\\d+.\\d+.\\d+.\\d+$')
            src_addr = []
            # 源地址对象组
            if i.get('SrcAddrList'):
                if isinstance(i['SrcAddrList']['SrcAddrItem'], list):
                    for src_item in i['SrcAddrList']['SrcAddrItem']:
                        src_addr.append(dict(object=src_item))
                        src_addr_res = address_mongo.find(
                            query_dict=dict(hostip=self.hostip, Name=src_item),
                            fileds={'_id': 0, 'elements': 1})
                        if src_addr_res:
                            for _src_addr in src_addr_res:
                                if 'elements' not in _src_addr.keys():
                                    continue
                                for _sub_addr in _src_addr['elements']:
                                    # 子网
                                    if _sub_addr['Type'] == 'subnet':
                                        if all(k in _sub_addr for k in (
                                                "SubnetIPv4Address", "IPv4Mask")):
                                            _tmp_subnet = _sub_addr['SubnetIPv4Address'] + \
                                                          '/' + _sub_addr['IPv4Mask']
                                            tmp['src_ip_split'].append(
                                                dict(start=IPNetwork(_tmp_subnet).first,
                                                     end=IPNetwork(_tmp_subnet).last))
                                    # 范围
                                    if _sub_addr['Type'] == 'range':
                                        if all(k in _sub_addr for k in (
                                                "StartIPv4Address", "EndIPv4Address")):
                                            start_ip = _sub_addr['StartIPv4Address']
                                            end_ip = _sub_addr['EndIPv4Address']
                                            tmp['src_ip_split'].append(dict(start=IPAddress(start_ip).value,
                                                                            end=IPAddress(end_ip).value))
                                    # 主机地址
                                    if _sub_addr['Type'] == 'ip' and _src_addr.get(
                                            'HostIPv4Address'):
                                        start_ip = _sub_addr['HostIPv4Address']
                                        end_ip = _sub_addr['HostIPv4Address']
                                        tmp['src_ip_split'].append(dict(start=IPAddress(start_ip).value,
                                                                        end=IPAddress(end_ip).value))
                        elif ipaddr_regex.search(src_item):
                            tmp['src_ip_split'].append(
                                dict(start=IPNetwork(src_item).first,
                                     end=IPNetwork(src_item).last))
                elif isinstance(i['SrcAddrList']['SrcAddrItem'], str):
                    src_addr.append(
                        dict(object=i['SrcAddrList']['SrcAddrItem']))
                    src_addr_res = address_mongo.find(
                        query_dict=dict(
                            hostip=self.hostip, Name=i['SrcAddrList']['SrcAddrItem']),
                        fileds={'_id': 0, 'elements': 1})
                    if src_addr_res:
                        for _src_addr in src_addr_res:
                            if 'elements' not in _src_addr.keys():
                                continue
                            for _sub_addr in _src_addr['elements']:
                                # 子网
                                if _sub_addr['Type'] == 'subnet':
                                    if all(k in _sub_addr for k in (
                                            "SubnetIPv4Address", "IPv4Mask")):
                                        _tmp_subnet = _sub_addr['SubnetIPv4Address'] + \
                                                      '/' + _sub_addr['IPv4Mask']
                                        tmp['src_ip_split'].append(
                                            dict(start=IPNetwork(_tmp_subnet).first,
                                                 end=IPNetwork(_tmp_subnet).last))
                                # 范围
                                if _sub_addr['Type'] == 'range':
                                    if all(k in _sub_addr for k in (
                                            "StartIPv4Address", "EndIPv4Address")):
                                        start_ip = _sub_addr['StartIPv4Address']
                                        end_ip = _sub_addr['EndIPv4Address']
                                        tmp['src_ip_split'].append(dict(start=IPAddress(start_ip).value,
                                                                        end=IPAddress(end_ip).value))
                                # 主机地址
                                if _sub_addr['Type'] == 'ip' and _src_addr.get(
                                        'HostIPv4Address'):
                                    start_ip = _sub_addr['HostIPv4Address']
                                    end_ip = _sub_addr['HostIPv4Address']
                                    tmp['src_ip_split'].append(dict(start=IPAddress(start_ip).value,
                                                                    end=IPAddress(end_ip).value))
                    elif ipaddr_regex.search(i['SrcAddrList']['SrcAddrItem']):
                        tmp['src_ip_split'].append(
                            dict(start=IPNetwork(i['SrcAddrList']['SrcAddrItem']).first,
                                 end=IPNetwork(i['SrcAddrList']['SrcAddrItem']).last))
            dst_addr = []
            # 目的地址对象组
            if i.get('DestAddrList'):
                if isinstance(i['DestAddrList']['DestAddrItem'], list):
                    for dst_item in i['DestAddrList']['DestAddrItem']:
                        dst_addr.append(dict(object=dst_item))
                        dst_addr_res = address_mongo.find(
                            query_dict=dict(hostip=self.hostip, Name=dst_item),
                            fileds={'_id': 0, 'elements': 1})
                        if dst_addr_res:
                            for _dst_addr in dst_addr_res:
                                if 'elements' not in _dst_addr.keys():
                                    continue
                                for _sub_addr in _dst_addr['elements']:
                                    # 子网
                                    if _sub_addr['Type'] == 'subnet':
                                        if all(k in _sub_addr for k in (
                                                "SubnetIPv4Address", "IPv4Mask")):
                                            _tmp_subnet = _sub_addr['SubnetIPv4Address'] + \
                                                          '/' + _sub_addr['IPv4Mask']
                                            tmp['dst_ip_split'].append(
                                                dict(start=IPNetwork(_tmp_subnet).first,
                                                     end=IPNetwork(_tmp_subnet).last))
                                    # 范围
                                    if _sub_addr['Type'] == 'range':
                                        if all(k in _sub_addr for k in (
                                                "StartIPv4Address", "EndIPv4Address")):
                                            start_ip = _sub_addr['StartIPv4Address']
                                            end_ip = _sub_addr['EndIPv4Address']
                                            tmp['dst_ip_split'].append(dict(start=IPAddress(start_ip).value,
                                                                            end=IPAddress(end_ip).value))
                                    # 主机地址
                                    if _sub_addr['Type'] == 'ip' and _sub_addr.get(
                                            'HostIPv4Address'):
                                        start_ip = _sub_addr['HostIPv4Address']
                                        end_ip = _sub_addr['HostIPv4Address']
                                        tmp['dst_ip_split'].append(dict(start=IPAddress(start_ip).value,
                                                                        end=IPAddress(end_ip).value))
                        elif ipaddr_regex.search(dst_item):
                            tmp['dst_ip_split'].append(
                                dict(start=IPNetwork(dst_item).first,
                                     end=IPNetwork(dst_item).last))
                elif isinstance(i['DestAddrList']['DestAddrItem'], str):
                    dst_addr.append(
                        dict(object=i['DestAddrList']['DestAddrItem']))
                    dst_addr_res = address_mongo.find(
                        query_dict=dict(
                            hostip=self.hostip, Name=i['DestAddrList']['DestAddrItem']),
                        fileds={'_id': 0, 'elements': 1})
                    if dst_addr_res:
                        for _dst_addr in dst_addr_res:
                            if 'elements' not in _dst_addr.keys():
                                continue
                            for _sub_addr in _dst_addr['elements']:
                                # 子网
                                if _sub_addr['Type'] == 'subnet':
                                    if all(k in _sub_addr for k in (
                                            "SubnetIPv4Address", "IPv4Mask")):
                                        _tmp_subnet = _sub_addr['SubnetIPv4Address'] + \
                                                      '/' + _sub_addr['IPv4Mask']
                                        tmp['dst_ip_split'].append(
                                            dict(start=IPNetwork(_tmp_subnet).first,
                                                 end=IPNetwork(_tmp_subnet).last))
                                # 范围
                                if _sub_addr['Type'] == 'range':
                                    if all(k in _sub_addr for k in (
                                            "StartIPv4Address", "EndIPv4Address")):
                                        start_ip = _sub_addr['StartIPv4Address']
                                        end_ip = _sub_addr['EndIPv4Address']
                                        tmp['dst_ip_split'].append(dict(start=IPAddress(start_ip).value,
                                                                        end=IPAddress(end_ip).value))
                                # 主机地址
                                if _sub_addr['Type'] == 'ip' and _dst_addr.get(
                                        'HostIPv4Address'):
                                    start_ip = _sub_addr['HostIPv4Address']
                                    end_ip = _sub_addr['HostIPv4Address']
                                    tmp['dst_ip_split'].append(dict(start=IPAddress(start_ip).value,
                                                                    end=IPAddress(end_ip).value))
                    elif ipaddr_regex.search(i['DestAddrList']['DestAddrItem']):
                        tmp['dst_ip_split'].append(
                            dict(start=IPNetwork(i['DestAddrList']['DestAddrItem']).first,
                                 end=IPNetwork(i['DestAddrList']['DestAddrItem']).last))
            # 自定义源地址
            if i.get('SrcSimpleAddrList'):
                if 'SrcSimpleAddrItem' in i['SrcSimpleAddrList'].keys():
                    if isinstance(i['SrcSimpleAddrList']
                                  ['SrcSimpleAddrItem'], list):
                        for _src_simple in i['SrcSimpleAddrList']['SrcSimpleAddrItem']:
                            if _src_simple.find('-') != -1:  # range
                                src_addr.append(dict(range=_src_simple))
                                start_ip = _src_simple.split('-')[0]
                                end_ip = _src_simple.split('-')[1]
                                tmp['src_ip_split'].append(dict(start=IPAddress(start_ip).value,
                                                                end=IPAddress(end_ip).value))
                            elif ipaddr_regex.search(_src_simple):  # subnet
                                src_addr.append(dict(ip=_src_simple))
                                tmp['src_ip_split'].append(
                                    dict(start=IPNetwork(_src_simple).first,
                                         end=IPNetwork(_src_simple).last))
                            elif host_ip_regex.search(_src_simple):  # host ip
                                src_addr.append(dict(ip=_src_simple))
                                tmp['src_ip_split'].append(dict(start=IPAddress(_src_simple).value,
                                                                end=IPAddress(_src_simple).value))

                    elif isinstance(i['SrcSimpleAddrList']['SrcSimpleAddrItem'], str):
                        _src_simple = i['SrcSimpleAddrList']['SrcSimpleAddrItem']
                        if _src_simple.find('-') != -1:  # range
                            src_addr.append(dict(range=_src_simple))
                            start_ip = _src_simple.split('-')[0]
                            end_ip = _src_simple.split('-')[1]
                            tmp['src_ip_split'].append(dict(start=IPAddress(start_ip).value,
                                                            end=IPAddress(end_ip).value))
                        elif ipaddr_regex.search(_src_simple):  # subnet
                            src_addr.append(dict(ip=_src_simple))
                            tmp['src_ip_split'].append(
                                dict(start=IPNetwork(_src_simple).first,
                                     end=IPNetwork(_src_simple).last))
                        elif host_ip_regex.search(_src_simple):  # host ip
                            src_addr.append(dict(ip=_src_simple))
                            tmp['src_ip_split'].append(dict(start=IPAddress(_src_simple).value,
                                                            end=IPAddress(_src_simple).value))
            # 自定义目的地址
            if i.get('DestSimpleAddrList'):
                if 'DestSimpleAddrItem' in i['DestSimpleAddrList'].keys():
                    if isinstance(i['DestSimpleAddrList']
                                  ['DestSimpleAddrItem'], list):
                        for _dst_simple in i['DestSimpleAddrList']['DestSimpleAddrItem']:
                            if _dst_simple.find('-') != -1:  # range
                                dst_addr.append(dict(range=_dst_simple))
                                start_ip = _dst_simple.split('-')[0]
                                end_ip = _dst_simple.split('-')[1]
                                tmp['dst_ip_split'].append(dict(start=IPAddress(start_ip).value,
                                                                end=IPAddress(end_ip).value))
                            elif ipaddr_regex.search(_dst_simple):  # subnet
                                dst_addr.append(dict(ip=_dst_simple))
                                tmp['dst_ip_split'].append(
                                    dict(start=IPNetwork(_dst_simple).first,
                                         end=IPNetwork(_dst_simple).last))
                            elif host_ip_regex.search(_dst_simple):  # host ip
                                dst_addr.append(dict(ip=_dst_simple))
                                tmp['dst_ip_split'].append(dict(start=IPAddress(_dst_simple).value,
                                                                end=IPAddress(_dst_simple).value))
                    elif isinstance(i['DestSimpleAddrList']['DestSimpleAddrItem'], str):
                        _dst_simple = i['DestSimpleAddrList']['DestSimpleAddrItem']
                        if _dst_simple.find('-') != -1:  # range
                            dst_addr.append(dict(range=_dst_simple))
                            start_ip = _dst_simple.split('-')[0]
                            end_ip = _dst_simple.split('-')[1]
                            tmp['dst_ip_split'].append(dict(start=IPAddress(start_ip).value,
                                                            end=IPAddress(end_ip).value))
                        elif ipaddr_regex.search(_dst_simple):  # subnet
                            dst_addr.append(dict(ip=_dst_simple))
                            tmp['dst_ip_split'].append(
                                dict(start=IPNetwork(_dst_simple).first,
                                     end=IPNetwork(_dst_simple).last))
                        elif host_ip_regex.search(_dst_simple):  # host ip
                            dst_addr.append(dict(ip=_dst_simple))
                            tmp['dst_ip_split'].append(dict(start=IPAddress(_dst_simple).value,
                                                            end=IPAddress(_dst_simple).value))
            src_zone = ''
            if i.get('SrcZoneList'):
                src_zone = i['SrcZoneList']['SrcZoneItem']
            dst_zone = ''
            if i.get('DestZoneList'):
                dst_zone = i['DestZoneList']['DestZoneItem']
            tmp['vendor'] = 'H3C'
            tmp['hostip'] = i['hostip']
            tmp['id'] = i.get('ID')
            tmp['name'] = i.get('Name')
            tmp['action'] = str(i.get('Action')).lower()
            tmp['enable'] = i.get('Enable')
            tmp['src_zone'] = src_zone
            tmp['dst_zone'] = dst_zone
            tmp['service'] = service
            tmp['src_addr'] = src_addr  # 地址组
            tmp['dst_addr'] = dst_addr  # 地址组
            tmp['src_ip'] = ''  # 单IP列表
            tmp['dst_ip'] = ''  # 单IP列表
            tmp['log'] = i['Log']
            tmp['description'] = i.get('Comment')
            results.append(tmp)
        my_mongo.insert_many(results)
        return

    def _arp_proc(self, res):
        arp_datas = []
        for i in res:
            tmp = dict(
                hostip=self.hostip,
                hostname=self.hostname,
                idc_name=self.idc_name,
                ipaddress=i['ipaddress'],
                macaddress=i['macaddress'],
                aging=i['aging'],
                type=i['type'],
                vlan=i['vlan'],
                interface=h3c_interface_format(i['interface']),
                vpninstance='',
                log_time=datetime.now()
            )
            arp_datas.append(tmp)
        if arp_datas:
            MongoNetOps.insert_table(
                'Automation', self.hostip, arp_datas, 'ARPTable')

    def _mac_proc(self, res):
        """
        有些华三设备没有MAC地址数据
        :param res:
        :return:
        """
        if isinstance(res, list):
            mac_datas = []
            for i in res:
                print('mac', i)
                tmp = dict(
                    hostip=self.hostip,
                    hostname=self.hostname,
                    idc_name=self.idc_name,
                    macaddress=i['macaddress'],
                    vlan=i['vlan'],
                    interface=h3c_interface_format(i['interface']),
                    type=i['state'],
                    log_time=datetime.now()
                )
                mac_datas.append(tmp)
            if mac_datas:
                MongoNetOps.insert_table(
                    'Automation', self.hostip, mac_datas, 'MACTable')

    def _ip_interface_proc(self, res):
        layer3datas = []
        for i in res:
            if isinstance(i['ipaddr'], list):
                for _ip in range(len(i['ipaddr'])):
                    # _ip 为数组下标 0，1，2，3
                    if i['ipaddr'][_ip].find('/') != -1:
                        _ipnet = IPNetwork(i['ipaddr'][_ip])
                        location = [dict(start=_ipnet.first, end=_ipnet.last)]
                        data = dict(
                            hostip=self.hostip,
                            interface=h3c_interface_format(
                                i['intf']),
                            line_status=i['line_status'],
                            protocol_status=i['protocol_status'],
                            ipaddress=_ipnet.ip.format(),
                            ipmask=_ipnet.netmask.format(),
                            location=location,
                            ip_type=i['ip_type'][_ip],
                            mtu=i['mtu'])
                        layer3datas.append(data)
                    else:
                        _ipnet = IPAddress(i['ipaddr'][_ip])
                        location = [dict(start=_ipnet.value, end=_ipnet.value)]
                        data = dict(
                            hostip=self.hostip,
                            interface=h3c_interface_format(
                                i['intf']),
                            line_status=i['line_status'],
                            protocol_status=i['protocol_status'],
                            ipaddress=_ipnet.format(),
                            ipmask='255.255.255.255',
                            location=location,
                            ip_type=i['ip_type'][_ip],
                            mtu=i['mtu'])
                        layer3datas.append(data)
            else:
                if i['ipaddr'].find('/') != -1:
                    _ipnet = IPNetwork(i['ipaddr'])
                    ipaddr = str(_ipnet.ip.format())
                    ipmask = str(_ipnet.netmask.format())
                    location = [dict(start=_ipnet.first, end=_ipnet.last)]
                    data = dict(
                        hostip=self.hostip,
                        interface=h3c_interface_format(
                            i['intf']),
                        line_status=i['line_status'],
                        protocol_status=i['protocol_status'],
                        ipaddress=ipaddr,
                        ipmask=ipmask,
                        ip_type=i['ip_type'],
                        location=location,
                        mtu=i['mtu'])
                    layer3datas.append(data)
                else:
                    _ipnet = IPAddress(i['ipaddr'])
                    location = [dict(start=_ipnet.value, end=_ipnet.value)]
                    data = dict(
                        hostip=self.hostip,
                        interface=h3c_interface_format(
                            i['intf']),
                        line_status=i['line_status'],
                        protocol_status=i['protocol_status'],
                        ipaddress=_ipnet.format(),
                        ipmask='255.255.255.255',
                        location=location,
                        ip_type=i['ip_type'],
                        mtu=i['mtu'])
                    layer3datas.append(data)
        if layer3datas:
            MongoNetOps.insert_table(
                db='Automation',
                hostip=self.hostip,
                datas=layer3datas,
                tablename='layer3interface')

    def _interface_brief(self, res):
        layer2datas = []
        # 会出现列表中全部都是三层route接口没有二层接口的情况，所以要判断类型
        if isinstance(res, list):
            for i in res:
                print(i)
                if i['interface'].startswith('BAGG'):
                    continue
                elif i['interface'].startswith('RAGG'):
                    continue
                elif i['interface'].startswith('Vlan'):
                    continue
                if i['speed'].find('-') != -1:
                    i['speed'] = 'IRF'
                elif i['speed'].find('(') != -1:
                    i['speed'] = i['speed'].split('(')[0]
                if i['duplex'].find('-') != -1:
                    i['duplex'] = 'IRF'
                if i['speed'] == 'auto':
                    i['speed'] = h3c_speed_format(
                        i['interface'])
                if i['speed'] == 'UP':
                    i['speed'] = h3c_speed_format(
                        i['interface'])
                    i['duplex'] = '--'
                data = dict(hostip=self.hostip,
                            interface=h3c_interface_format(
                                i['interface']),
                            status=i['status'],
                            speed=mathintspeed(i['speed']),
                            duplex=i['duplex'],
                            description=i['description'],
                            log_time=datetime.now())
                layer2datas.append(data)
            if layer2datas:
                MongoNetOps.insert_table(
                    db='Automation',
                    hostip=self.hostip,
                    datas=layer2datas,
                    tablename='layer2interface')

    def _aggre_port_proc(self, res):
        if isinstance(res, list):
            aggre_datas = []
            for i in res:
                if isinstance(i['memberports'], list):
                    memberports = []
                    for member in i['memberports']:
                        memberports.append(
                            h3c_interface_format(member))
                else:
                    memberports = i['memberports']
                tmp = dict(
                    hostip=self.hostip,
                    aggregroup=i['aggname'],
                    memberports=memberports,
                    status=i['status'],
                    mode=i.get('mode')
                )
                aggre_datas.append(tmp)
            if aggre_datas:
                MongoNetOps.insert_table(
                    'Automation', self.hostip, aggre_datas, 'AggreTable')

    def _lldp_proc(self, res):
        if isinstance(res, list):
            lldp_datas = []
            for i in res:
                neighbor_ip = ''
                if i['neighborsysname']:
                    tmp_neighbor_ip = cache.get('cmdb_' + i['neighborsysname'])
                    if tmp_neighbor_ip:
                        tmp_neighbor_ip = json.loads(tmp_neighbor_ip)
                        neighbor_ip = tmp_neighbor_ip[0]['manage_ip']
                    else:
                        tmp_neighbor_ip = NetworkDevice.objects.filter(name=i['neighborsysname']
                                                                       ).values('manage_ip').first()
                        neighbor_ip = tmp_neighbor_ip['manage_ip'] if tmp_neighbor_ip else ''
                tmp = dict(
                    hostip=self.hostip,
                    local_interface=i['local_interface'],
                    chassis_id=i['chassis_id'],
                    neighbor_port=i['neighbor_port'],
                    portdescription=i['portdescription'],
                    neighborsysname=i['neighborsysname'],
                    management_ip=i['management_ip'],
                    management_type=i['management_type'],
                    neighbor_ip=neighbor_ip
                )
                lldp_datas.append(tmp)
            if lldp_datas:
                MongoNetOps.insert_table(
                    'Automation', self.hostip, lldp_datas, 'LLDPTable')

    def _manuinfo_proc(self, res):
        if isinstance(res, dict):
            """
            单台：
            {'chassis_id': '', 'slot_type': 'Slot', 'slot_id': '1', 'device_name': 'S5120-48P-EI',
             'device_serial_number': '210235A0BKH145000294', 'manufacturing_date': '2014-05-19',
              'vendor_name': 'H3C', 'mac_address': '70F9-6D46-3E40'}
            """
            serial_num = res['device_serial_number']
            slot = res['slot_id']
            NetworkDevice.objects.filter(
                manage_ip=self.hostip,
                serial_num=serial_num).update(
                slot=int(slot))
        elif isinstance(res, list):
            update_flag = 0  # 先匹配框式，再匹配盒式
            for i in res:
                if i['slot_type'] == 'Chassis':
                    update_flag = 1
                    serial_num = i['device_serial_number']
                    chassis = int(i['chassis_id'])
                    # slot = int(i['slot_id'])
                    slot = 1
                    NetworkDevice.objects.filter(
                        serial_num=serial_num).update(
                        slot=slot, chassis=chassis)
            if update_flag == 0:
                for i in res:
                    if i['slot_type'] == 'Slot':
                        # update_flag = 1
                        serial_num = i['device_serial_number']
                        slot = int(i['slot_id'])
                        NetworkDevice.objects.filter(
                            serial_num=serial_num).update(
                            slot=slot)

    def _irf_proc(self, res):
        if isinstance(res, dict):
            """
            10.254.7.54为例  独立设备
            {'chassisid': '', 'memberid': '1', 'role': 'Master', 'priority': '1', 'mac': '0cda-41c2-8d5b'}

            """
            if res['role'] == 'Master' and res['memberid'] != '0':
                NetworkDevice.objects.filter(
                    manage_ip=self.hostip, slot=int(
                        res['memberid'])).update(
                    ha_status=0)
            elif res['role'] == 'Slave' and res['memberid'] != '0':
                NetworkDevice.objects.filter(
                    manage_ip=self.hostip, slot=int(
                        res['memberid'])).update(
                    ha_status=0)

        elif isinstance(res, list):
            """
            堆叠，以4.250为例 
            {'chassisid': '1', 'memberid': '0', 'role': 'Master', 'priority': '32', 'mac': ''}
            {'chassisid': '1', 'memberid': '1', 'role': 'Slave', 'priority': '32', 'mac': ''}
            {'chassisid': '2', 'memberid': '0', 'role': 'Slave', 'priority': '31', 'mac': ''}
            {'chassisid': '2', 'memberid': '1', 'role': 'Slave', 'priority': '31', 'mac': ''}
            也有单设备
            """
            if len(res) > 1:
                # master 集合
                master = [x for x in res if x['role'] == 'Master']
                # master 对应的chassis id
                master_chassisid = master[0]['chassisid']
                # slave集合 并排除 master的 chassis id
                slave = [x for x in res if x['role'] == 'Slave' and x['chassisid'] != master_chassisid]
                for i in master:
                    NetworkDevice.objects.filter(
                        manage_ip=self.hostip, chassis=int(
                            i['chassisid'])).update(
                        ha_status=1)
                    break
                for i in slave:
                    NetworkDevice.objects.filter(
                        manage_ip=self.hostip, chassis=int(
                            i['chassisid'])).update(
                        ha_status=2)
                    break
            elif len(res) == 1:
                if res[0]['role'] == 'Master' and res[0]['memberid'] != '0':
                    NetworkDevice.objects.filter(
                        manage_ip=self.hostip, slot=int(
                            res[0]['memberid'])).update(
                        ha_status=0)
                elif res[0]['role'] == 'Slave' and res[0]['memberid'] != '0':
                    NetworkDevice.objects.filter(
                        manage_ip=self.hostip, slot=int(
                            res[0]['memberid'])).update(
                        ha_status=0)

    def _evpn_route_arp_proc(self, res):
        for i in res:
            print(i)
        return

    def _evpn_route_mac_proc(self, res):
        for i in res:
            print(i)
        return

    def _l2vpn_vsi_verbose_proc(self, res):
        for i in res:
            print(i)
        return

    def _l2vpn_mac_proc(self, res):
        for i in res:
            print(i)
        return

    def _null_proc(self, res):
        """
        空处理
        :param res:
        :return:
        """
        return

    # 文件解析映射
    def path_map(self, file_name, res: list):
        fsm_map = {
            'display_version': self._null_proc,
            'display_irf': self._irf_proc,
            'display_device_manuinfo': self._manuinfo_proc,
            'display_arp': self._arp_proc,
            'display_mac-address': self._mac_proc,
            'display_interface_brief': self._interface_brief,
            'display_ip_interface': self._ip_interface_proc,
            'display_link-aggregation_verbose': self._aggre_port_proc,
            'display_lldp_neighbor-information_verbose': self._lldp_proc,
            'display_lldp_neighbor-information': self._lldp_proc,
            'display_evpn_route_arp': self._evpn_route_arp_proc,
            'display_evpn_route_mac': self._evpn_route_mac_proc,
            # 'display_l2vpn_vsi_verbose': self.l2vpn_vsi_verbose_proc,
            # 'display_l2vpn_mac-address': self.l2vpn_mac_proc
        }
        if file_name in fsm_map.keys():
            fsm_map[file_name](res)
        else:
            send_msg_netops("设备:{}\n命令:{}\n没有对应数据处理方法".format(self.hostip, file_name))

    # 命令采集分析
    def _collection_analysis(self, paths: list):
        # self.cmds += ['display mac-address']
        for path in paths:
            res = BatManMain.info_fsm(path=path['path'], fsm_platform=self.fsm_flag)
            self.path_map(path['cmd_file'], res)

    def _netconf_arp(self, res):
        arp_datas = []
        for i in res:
            tmp_mac = i['MacAddress'].split('-')
            macaddress = tmp_mac[0] + tmp_mac[1] + '-' + \
                         tmp_mac[2] + tmp_mac[3] + '-' + tmp_mac[4] + tmp_mac[5]
            tmp = dict(
                hostip=self.hostip,
                hostname=self.hostname,
                idc_name=self.idc_name,
                ipaddress=i['Ipv4Address'],
                macaddress=macaddress.lower(),
                aging='',
                type=i['ArpType'],
                vlan=i.get('VLANID'),
                interface=i['Name'],
                vpninstance=i.get('VrfName'),
                log_time=datetime.now()
            )
            arp_datas.append(tmp)
        # if host == '10.254.6.254':
        #     send_msg_netops("更新6.254，数据量{}".format(len(arp_datas)))
        MongoNetOps.insert_table(
            'Automation', self.hostip, arp_datas, 'ARPTable')

    def _netconf_interface_list(self, res):
        interface_datas = []
        layer2datas = []
        for i in res:
            i['hostip'] = self.hostip
            interface_datas.append(i)
        for i in res:
            # 正常物理接口都会带speed和duplex的key，不带则是逻辑接口
            if 'ActualSpeed' in i.keys() and 'ActualDuplex' in i.keys():
                if i['Name'].startswith('M-'):
                    continue
                elif i['Name'].startswith('Bridge-Aggregation'):
                    continue
                elif i['Name'].startswith('Vlan-interface'):
                    continue
                elif i['Name'].startswith('InLoopBack'):
                    continue
                elif i['Name'].startswith('NULL'):
                    continue
                if i['ActualSpeed'] == '0':
                    i['ActualSpeed'] = h3c_speed_format(
                        i['Name'])
                if mathintspeed(
                        i['ActualSpeed']) == '830G':
                    i['ActualSpeed'] = h3c_speed_format(
                        i['Name'])
                data = dict(hostip=self.hostip,
                            interface=i['Name'],
                            status=i['OperStatus'],
                            speed=mathintspeed(
                                i['ActualSpeed']),
                            duplex=i['ActualDuplex'],
                            description=i['Description'])
                # print(data)
                layer2datas.append(data)
        if layer2datas:
            MongoNetOps.insert_table(db='Automation', hostip=self.hostip, datas=layer2datas,
                                     tablename='layer2interface')
        MongoNetOps.insert_table(db='NETCONF', hostip=self.hostip, datas=interface_datas,
                                 tablename='h3c_interface_list')

    def _netconf_lagg_list(self, res):
        if res:
            aggre_datas = []
            for i in res:
                """
                {'GroupId': '44', 'LinkMode': 'Dynamic', 'IfIndex': '1640',
                'Memberlist': [{'IfIndex': '44', 'GroupId': '44', 'SelectedStatus': 'Selected.',
                'UnSelectedReason': '0', 'LacpEnable': 'true', 'LacpMode': '1', 'Name': 'Ten-GigabitEthernet1/0/44'}],
                'Name': 'Bridge-Aggregation44', 'attr': 'Layer 2 aggregation group'}
                {'GroupId': '45', 'LinkMode': 'Dynamic', 'IfIndex': '1641', 'Memberlist': [{'IfIndex': '45',
                'GroupId': '45', 'SelectedStatus': 'Selected.', 'UnSelectedReason': '0', 'LacpEnable': 'true',
                'LacpMode': '1', 'Name': 'Ten-GigabitEthernet1/0/45'}], 'Name': 'Bridge-Aggregation45',
                'attr': 'Layer 2 aggregation group'}
                {'GroupId': '46', 'LinkMode': 'Dynamic', 'IfIndex': '1642', 'Memberlist': [{'IfIndex': '46',
                'GroupId': '46', 'SelectedStatus': 'Selected.', 'UnSelectedReason': '0', 'LacpEnable': 'true',
                'LacpMode': '1', 'Name': 'Ten-GigabitEthernet1/0/46'}], 'Name': 'Bridge-Aggregation46',
                'attr': 'Layer 2 aggregation group'}
                {'GroupId': '47', 'LinkMode': 'Dynamic', 'IfIndex': '1643', 'Memberlist': [{'IfIndex': '47',
                'GroupId': '47', 'SelectedStatus': 'Selected.', 'UnSelectedReason': '0', 'LacpEnable': 'true',
                'LacpMode': '1', 'Name': 'Ten-GigabitEthernet1/0/47'}, {'IfIndex': '48', 'GroupId': '47',
                'SelectedStatus': 'Selected.', 'UnSelectedReason': '0', 'LacpEnable': 'true', 'LacpMode': '1',
                'Name': 'Ten-GigabitEthernet1/0/48'}], 'Name': 'Bridge-Aggregation47',
                'attr': 'Layer 2 aggregation group'}
                {'GroupId': '16437', 'LinkMode': 'Dynamic', 'IfIndex': '1623', 'Memberlist': [{'IfIndex': '69',
                'GroupId': '16437', 'SelectedStatus': 'Selected.', 'UnSelectedReason': '0', 'LacpEnable': 'true',
                'LacpMode': '1', 'Name': 'FortyGigE1/0/53'}, {'IfIndex': '74', 'GroupId': '16437',
                'SelectedStatus': 'Selected.', 'UnSelectedReason': '0', 'LacpEnable': 'true', 'LacpMode': '1',
                'Name': 'FortyGigE1/0/54'}], 'Name': 'Route-Aggregation53', 'attr': 'Layer 3 aggregation group'}
                """
                if 'Memberlist' in i.keys():
                    try:
                        memberports = []
                        memberstatus = []
                        for member in i['Memberlist']:
                            memberports.append(member['Name'])
                            memberstatus.append(
                                member.get('SelectedStatus'))
                    except Exception as e:
                        memberports = []
                        memberstatus = []
                    tmp = dict(
                        hostip=self.hostip,
                        aggregroup=i['Name'],
                        memberports=memberports,
                        status=memberstatus,
                        mode=''
                    )
                    aggre_datas.append(tmp)
                else:
                    tmp = dict(
                        hostip=self.hostip,
                        aggregroup=i['Name'],
                        memberports=[],
                        status=[],
                        mode=''
                    )
                    aggre_datas.append(tmp)
            if aggre_datas:
                MongoNetOps.insert_table(
                    'Automation', self.hostip, aggre_datas, 'AggreTable')

    def _netconf_arp_over_evpn(self, res):
        pass

    def _netconf_physical(self, res):
        if isinstance(res, dict):
            if self.ha_status != 0:
                NetworkDevice.objects.filter(serial_num=res['SerialNumber']).update(
                    ha_status=0)
            if res.get('Model', ''):
                tmp_model = res['Model']
                if self.model__name != tmp_model:
                    model_q = Model.objects.filter(name=tmp_model)
                    if model_q:
                        model_id = Model.objects.get(name=tmp_model)
                        NetworkDevice.objects.filter(manage_ip=self.hostip).update(model=model_id)
                    else:
                        model_id = Model.objects.create(
                            name=tmp_model, vendor=Vendor.objects.get(alias='H3C'))
                        NetworkDevice.objects.filter(manage_ip=self.hostip).update(model=model_id)
            if self.serial_num != res['SerialNumber']:
                send_msg_netops("独立设备{}序列号不一致,cmdb序列号为:{}, netconf序列号为:{}".format(
                    self.hostip, self.serial_num, res['SerialNumber']))
                NetworkDevice.objects.filter(serial_num=self.serial_num).update(
                    serial_num=res['SerialNumber'])
            # 框式标记对不上的需要更新
            if self.chassis != int(res['Chassis']) or self.slot != int(
                    res['Slot']):
                NetworkDevice.objects.filter(serial_num=res['SerialNumber']).update(
                    chassis=int(res['Chassis']), slot=int(res['Slot']),
                    soft_version=res['SoftwareRev'])
            # 软件版本对不上的，也需要更新
            elif self.soft_version != res['SoftwareRev']:
                NetworkDevice.objects.filter(serial_num=res['SerialNumber']).update(
                    chassis=int(res['Chassis']), slot=int(res['Slot']),
                    soft_version=res['SoftwareRev'])

        elif isinstance(res, list):
            for _physical in res:
                if _physical.get('Model'):
                    tmp_model = _physical['Model']
                    if self.model__name != tmp_model:
                        model_q = Model.objects.filter(name=tmp_model)
                        if model_q:
                            model_id = Model.objects.get(name=tmp_model)
                            NetworkDevice.objects.filter(manage_ip=self.hostip).update(model=model_id)
                        else:
                            model_id = Model.objects.create(
                                name=tmp_model, vendor=Vendor.objects.get(alias='H3C'))
                            NetworkDevice.objects.filter(manage_ip=self.hostip).update(model=model_id)
                NetworkDevice.objects.filter(serial_num=_physical['SerialNumber']).update(
                    chassis=int(_physical['Chassis']), slot=int(_physical['Slot']),
                    soft_version=_physical['SoftwareRev'])
            _serial_nums = [x['SerialNumber'] for x in res]
            if self.serial_num not in _serial_nums:
                send_msg_netops("堆叠设备{}序列号不一致,cmdb序列号为:{},netconf序列号为:{}".format(
                    self.hostip, self.serial_num, ','.join(_serial_nums)))
                # NetworkDevice.objects.filter(serial_num=self.serial_num).update(
                #     serial_num=res['SerialNumber'])

    def _netconf_device_base(self, res):
        """
        {'Uptime': '5358488', 'HostName': 'DZ.PO.IPsec.FW.001', 'HostOid': '1.3.6.1.4.1.25506.1.1557',
        'MinChassisNum': '0', 'MaxChassisNum': '0', 'MinSlotNum': '1', 'MaxSlotNum': '2', 'MinCPUIDNum': '0',
        'MaxCPUIDNum': '0',
         'HostDescription': 'H3C Comware Platform Software, Software Version 7.1.064,
         Release 9628P2416\n\nH3C SecPath F5060\n\nCopyright (c) 2004-2021 New H3C Technologies Co., Ltd.
         All rights reserved.',
         'LocalTime': '2022-07-14T17:20:07',
         'TimeZone': {'Zone': '+08:00:00', 'ZoneName': 'Beijing'}, 'ClockProtocol': {'Protocol': '3', 'MDCID': '1'}}
        :param res:
        :return:
        """
        if isinstance(res, dict):
            HostName = res['HostName']
            if self.hostname != HostName:
                NetworkDevice.objects.filter(manage_ip=self.hostip).update(name=HostName)

    def _netconf_irf(self, res):
        if isinstance(res, list):
            for dev in res:
                ha_status = 0
                if isinstance(dev['Board'], list):
                    if 'Master' in [x['Role'] for x in dev['Board']]:
                        ha_status = 1
                        _slot_num = [x['Slot'] for x in dev['Board'] if x['Role'] == 'Master']
                        _chassis_num = [x['Chassis'] for x in dev['Board'] if x['Role'] == 'Master']
                        if self.category__name == '防火墙':  # 因M9006 12.113 slot 硬件信息和irf的slot信息对应不上
                            NetworkDevice.objects.filter(manage_ip=self.hostip,
                                                         chassis=int(_chassis_num[0])).update(
                                ha_status=ha_status)
                        else:
                            NetworkDevice.objects.filter(manage_ip=self.hostip,
                                                         slot=int(_slot_num[0]),
                                                         chassis=int(_chassis_num[0])).update(
                                ha_status=ha_status)
                    else:
                        ha_status = 2
                        _slot_num = [
                            x['Slot'] for x in dev['Board'] if x['Role'] == 'Standby']
                        _chassis_num = [
                            x['Chassis'] for x in dev['Board'] if x['Role'] == 'Standby']
                        if self.category__name == '防火墙':  # 因M9006 12.113 slot 硬件信息和irf的slot信息对应不上
                            NetworkDevice.objects.filter(manage_ip=self.hostip,
                                                         chassis=int(_chassis_num[0])).update(
                                ha_status=ha_status)
                        else:
                            NetworkDevice.objects.filter(manage_ip=self.hostip,
                                                         slot=int(
                                                             _slot_num[0]),
                                                         chassis=int(_chassis_num[0])).update(
                                ha_status=ha_status)
                elif isinstance(dev['Board'], dict):
                    if dev['Board']['Role'] == 'Master':
                        ha_status = 1
                    elif dev['Board']['Role'] == 'Standby':
                        ha_status = 2
                    NetworkDevice.objects.filter(manage_ip=self.hostip,
                                                 slot=int(
                                                     dev['Board']['Slot']),
                                                 chassis=int(dev['Board']['Chassis'])).update(
                        ha_status=ha_status)

    def _netconf_ipv4address(self, res):
        ip_interface_datas = []
        layer3datas = []
        for i in res:
            i['hostip'] = self.hostip
            i['hostname'] = self.hostname
            # 安全纳管引擎，服务发布 定位用
            location = []
            if i['Ipv4Address'] != '0.0.0.0':
                _location_ip = IPNetwork(i['Ipv4Address'] + '/' + i['Ipv4Mask'])
                location += [dict(start=_location_ip.first, end=_location_ip.last)]
            data = dict(
                hostip=self.hostip,
                interface=i['Name'],
                line_status='',
                protocol_status='',
                ipaddress=i['Ipv4Address'],
                ipmask=i['Ipv4Mask'],
                ip_type=i['type'],
                mtu='', location=location)
            layer3datas.append(data)
            ip_interface_datas.append(i)
        # AutomationMongo.insert_table(db='NETCONF', hostip=host, datas=ip_interface_datas, tablename='netconf_ipv4')
        if layer3datas:
            MongoNetOps.insert_table(db='Automation', hostip=self.hostip, datas=layer3datas,
                                     tablename='layer3interface')

    def _netconf_ipv6address(self, res):
        if res:
            for i in res:
                i['hostip'] = self.hostip
            MongoNetOps.insert_table(db='NETCONF', hostip=self.hostip, datas=res,
                                     tablename='h3c_ipv6_address')
        return

    def _netconf_lldp(self, res):
        if res:
            lldp_datas = []
            for i in res:
                neighbor_ip = ''
                if i['SystemName']:
                    tmp_neighbor_ip = cache.get('cmdb_' + i['SystemName'])
                    if tmp_neighbor_ip:
                        tmp_neighbor_ip = json.loads(tmp_neighbor_ip)
                        neighbor_ip = tmp_neighbor_ip[0]['manage_ip']
                    else:
                        tmp_neighbor_ip = NetworkDevice.objects.filter(
                            name=i['SystemName']).values('manage_ip')
                        neighbor_ip = tmp_neighbor_ip[0]['manage_ip'] if tmp_neighbor_ip else ''
                tmp = dict(
                    hostip=self.hostip,
                    local_interface=i['LocalPort'],
                    chassis_id=i['ChassisId'],
                    neighbor_port=i['PortId'],
                    portdescription='',
                    neighborsysname=i['SystemName'],
                    management_ip=i.get('Address'),
                    management_type=i.get('SubType'),
                    neighbor_ip=neighbor_ip
                )
                lldp_datas.append(tmp)
            if lldp_datas:
                MongoNetOps.insert_table(
                    'Automation', self.hostip, lldp_datas, 'LLDPTable')

    def _netconf_mac_over_evpn(self, res):
        l2vpn_mac_datas = []
        for i in res:
            # 10.254.5.205 collection_mac_over_evpn
            # 会有部分没有portname的情况
            if i.get('PortName'):
                tmp_mac = i['MacAddr'].split('-')
                macaddress = tmp_mac[0] + tmp_mac[1] + '-' + tmp_mac[2] + tmp_mac[3] + '-' + tmp_mac[4] + \
                             tmp_mac[5]
                tmp = dict(
                    hostip=self.hostip,
                    hostname=self.hostname,
                    idc_name=self.idc_name,
                    macaddress=macaddress.lower(),
                    vlan=i.get('SrvID'),
                    interface=i.get('PortName'),
                    type='evpn',
                )
                l2vpn_mac_datas.append(tmp)
        if l2vpn_mac_datas:
            MongoNetOps.insert_table(
                'Automation', self.hostip, l2vpn_mac_datas, 'MACTable')

    def _netconf_mac_unicasttable(self, res):
        if res:
            mac_datas = []
            status_map = {
                '0': 'Other',
                '1': 'Security',
                '2': 'Learned',
                '3': 'Static',
                '4': 'Blackhole',
            }
            for i in res:
                tmp_mac = i['MacAddress'].split('-')
                macaddress = tmp_mac[0] + tmp_mac[1] + '-' + \
                             tmp_mac[2] + tmp_mac[3] + '-' + tmp_mac[4] + tmp_mac[5]
                tmp = dict(
                    hostip=self.hostip,
                    hostname=self.hostname,
                    idc_name=self.idc_name,
                    macaddress=macaddress.lower(),
                    vlan=i['VLANID'],
                    interface=i['PortName'],
                    type=status_map[i['Status']],
                    log_time=datetime.now()
                )
                mac_datas.append(tmp)
            if mac_datas:
                MongoNetOps.insert_table(
                    'Automation', self.hostip, mac_datas, 'MACTable')

    def _netconf_vrrp(self, res):
        if res:
            layer3datas = []
            for i in res:
                if i['OperState'] != 'Master':
                    continue
                data = dict(
                    hostip=self.hostip,
                    interface=i['Name'],
                    line_status='',
                    protocol_status='',
                    ipaddress=i['IpAddress'],
                    ipmask='255.255.255.255',
                    ip_type='virtual ip',
                    mtu='')
                layer3datas.append(data)
            if layer3datas:
                MongoNetOps.insert_table(db='Automation', hostip=self.hostip, datas=layer3datas,
                                         tablename='layer3interface', delete=False)

    def _netconf_patch_version(self, res):
        if res:
            if isinstance(res, list):
                patch_version = res[-1]['FilePlatVersion']
                if patch_version != self.patch_version:
                    NetworkDevice.objects.filter(
                        manage_ip=self.hostip).update(
                        patch_version=patch_version)
            elif isinstance(res, dict):
                patch_version = res['FilePlatVersion']
                if patch_version != self.patch_version:
                    NetworkDevice.objects.filter(
                        manage_ip=self.hostip).update(
                        patch_version=patch_version)

    # nat地址组
    def _netconf_netaddr_group(self, res):
        if isinstance(res, list) and len(res) > 0:
            self.nat_addr_groups = {x['GroupNumber']: x for x in res}
            netaddr_group_datas = []
            for i in res:
                i['hostip'] = self.hostip
                netaddr_group_datas.append(i)
            if netaddr_group_datas:
                MongoNetOps.insert_table(
                    'NETCONF', self.hostip, netaddr_group_datas, 'h3c_netaddr_group')

    def _netconf_server_on_policy(self, res):
        nat_int_policy_data = []
        # DNAT表项拼接
        if res:
            protocol_map = {
                "1": "icmp",
                "6": "tcp",
                "17": "udp",
            }
            try:
                for i in res:
                    i['hostip'] = self.hostip
                    global_ip_start = i['GlobalInfo']['GlobalStartIpv4Address']
                    global_ip_end = i['GlobalInfo']['GlobalEndIpv4Address'] if i['GlobalInfo'].get(
                        'GlobalEndIpv4Address') else i['GlobalInfo']['GlobalStartIpv4Address']
                    global_ip_result = '-'.join(
                        list({global_ip_start, global_ip_end}))
                    local_ip_start = i['LocalInfo']['LocalStartIpv4Address']
                    local_ip_end = i['LocalInfo']['LocalEndIpv4Address'] if i['LocalInfo'].get(
                        'LocalEndIpv4Address') else i['LocalInfo']['LocalStartIpv4Address']
                    local_ip_result = '-'.join(
                        list({local_ip_start, local_ip_end}))
                    global_port_start = int(
                        i['GlobalInfo']['GlobalStartPortNumber'])
                    global_port_end = int(i['GlobalInfo']['GlobalEndPortNumber']) if i['GlobalInfo'][
                        'GlobalEndPortNumber'] else int(i['GlobalInfo']['GlobalStartPortNumber'])
                    global_port_result = '-'.join(
                        list({str(global_port_start), str(global_port_end)}))
                    protocol = protocol_map[i['ProtocolType']] \
                        if i['ProtocolType'] in protocol_map.keys() else i['ProtocolType']
                    local_port_start = int(
                        i['LocalInfo']['LocalStartPortNumber'])
                    local_port_end = int(i['LocalInfo']['LocalEndPortNumber']) if i['LocalInfo'].get(
                        'LocalEndPortNumber') else int(i['LocalInfo']['LocalStartPortNumber'])
                    local_port_result = '-'.join(
                        list({str(local_port_start), str(local_port_end)}))

                    tmp = dict(
                        hostip=self.hostip,
                        name=i.get('RuleName'),
                        global_protocol='',
                        global_ip=[
                            dict(start=global_ip_start,
                                 end=global_ip_end,
                                 start_int=IPAddress(
                                     global_ip_start).value,
                                 end_int=IPAddress(
                                     global_ip_end).value,
                                 result=global_ip_result
                                 )],
                        global_port=[dict(
                            start=global_port_start,
                            end=global_port_end,
                            protocol=protocol,
                            result=global_port_result
                        )],
                        local_ip=[
                            dict(
                                start=local_ip_start,
                                end=local_ip_end,
                                start_int=IPAddress(
                                    local_ip_start).value,
                                end_int=IPAddress(
                                    local_ip_end).value,
                                result=local_ip_result
                            )
                        ],
                        local_port=[dict(
                            start=local_port_start,
                            end=local_port_end,
                            protocol=protocol,
                            result=local_port_result
                        )]
                    )
                    self.dnat_data.append(tmp)
                    nat_int_policy_data.append(i)
            except Exception as e:
                send_msg_netops(
                    "采集h3c防火墙{},格式化DNAT数据过程中失败:{}".format(
                        self.hostip, str(e)))
        if nat_int_policy_data:
            MongoNetOps.insert_table(
                'NETCONF', self.hostip, nat_int_policy_data, 'h3c_nat_int_policy')

    def _netconf_ipv4_paging(self, res):
        if res:
            self.addr_set = {x['Name']: x for x in res}
            for i in res:
                self.addr_map[i['Name']] = i
                i['hostip'] = self.hostip
            MongoNetOps.insert_table(db='NETCONF', hostip=self.hostip, datas=res,
                                     tablename='h3c_address_set')

    def _netconf_sec_policy(self, res):
        sec_policy_result = []
        if res:
            for i in res:
                i['hostip'] = self.hostip
                sec_policy_result.append(i)
            MongoNetOps.insert_table(
                'NETCONF', self.hostip, sec_policy_result, 'h3c_sec_policy')
        if sec_policy_result:
            self.h3c_secpath_sec_policy(sec_policy_result)

    def _netconf_server_groups(self, res):
        if res:
            for i in res:
                self.ser_map[i['Name']] = i
                i['hostip'] = self.hostip
            MongoNetOps.insert_table(db='NETCONF', hostip=self.hostip, datas=res,
                                     tablename='h3c_service_set')

    def _netconf_global_nat_policy(self, res):
        if res:
            for i in res:
                type_map = {
                    '0': 'Nested group',
                    '1': 'protocol',
                    '2': 'icmp',
                    '3': 'tcp',
                    '4': 'udp',
                    '5': 'icmpv6',
                }
                global_port = []
                if i['SrvObjGrpList']['ServiceObjGroup'] in self.ser_map.keys():
                    ser_tmp = self.ser_map[i['SrvObjGrpList']['ServiceObjGroup']
                    ['ServiceObjGroup']]['items']
                    for _ser_obj in ser_tmp:
                        # print(_ser_obj)
                        global_port.append(
                            dict(
                                start=int(
                                    _ser_obj['StartDestPort']) if _ser_obj.get('StartDestPort') else 0,
                                end=int(
                                    _ser_obj['EndDestPort']) if _ser_obj.get('EndDestPort') else 0,
                                protocol=type_map[_ser_obj['Type']],
                                result='-'.join(list(
                                    {str(_ser_obj.get('StartDestPort')), str(_ser_obj.get('EndDestPort'))}))
                            )
                        )
                # 目的地址 DstIPList => DstIP手工   DstObjGrpList =>
                # DstIpObjGroup对象
                global_ip = []
                if 'DstIPList' in i.keys():
                    global_ip.append(dict(
                        start=i['DstIPList']['DstIP'],
                        end=i['DstIPList']['DstIP'],
                        start_int=IPAddress(
                            i['DstIPList']['DstIP']).value,
                        end_int=IPAddress(
                            i['DstIPList']['DstIP']).value,
                        result='-'.join(list({i['DstIPList']
                                              ['DstIP'], i['DstIPList']['DstIP']}))
                    ))
                if 'DstObjGrpList' in i.keys():
                    if i['DstObjGrpList']['DstIpObjGroup'] in self.addr_map.keys():
                        addr_tmp = self.addr_map[i['DstObjGrpList']
                        ['DstIpObjGroup']]['ObjList']
                        for _addr_obj in addr_tmp:
                            if _addr_obj['Type'] == 'subnet':
                                _tmp_ip = IPNetwork(
                                    _addr_obj['SubnetIPv4Address'] + '/' + _addr_obj['IPv4Mask'])
                                global_ip.append(dict(
                                    start=IPAddress(
                                        _tmp_ip.first).format(),
                                    end=IPAddress(
                                        _tmp_ip.last).format(),
                                    start_int=_tmp_ip.first,
                                    end_int=_tmp_ip.last,
                                    result=str(_tmp_ip)
                                ))
                            elif _addr_obj['Type'] == 'range':
                                global_ip.append(dict(
                                    start=_addr_obj['StartIPv4Address'],
                                    end=_addr_obj['EndIPv4Address'],
                                    start_int=IPAddress(
                                        _addr_obj['StartIPv4Address']).value,
                                    end_int=IPAddress(
                                        _addr_obj['EndIPv4Address']).value,
                                    result=_addr_obj['StartIPv4Address'] +
                                           '-' + _addr_obj['EndIPv4Address']
                                ))
                            elif _addr_obj['Type'] == 'ip':
                                global_ip.append(dict(
                                    start=_addr_obj['HostIPv4Address'],
                                    end=_addr_obj['HostIPv4Address'],
                                    start_int=IPAddress(
                                        _addr_obj['HostIPv4Address']).value,
                                    end_int=IPAddress(
                                        _addr_obj['HostIPv4Address']).value,
                                    result=_addr_obj['HostIPv4Address']
                                ))
                local_ip_start = i['TransDstIP']
                local_ip_end = i['TransDstIP']
                local_ip_result = '-'.join(
                    list({local_ip_start, local_ip_end}))
                local_port_start = int(
                    i['TransDstPort']) if i.get('TransDstPort') else 1
                local_port_end = int(
                    i['TransDstPort']) if i.get('TransDstPort') else 65535
                local_port_result = '-'.join(
                    list({str(local_port_start), str(local_port_end)}))
                tmp = dict(
                    hostip=self.hostip,
                    name=i.get('RuleName'),
                    global_protocol='',
                    global_ip=global_ip,
                    global_port=global_port,
                    local_ip=[dict(
                        start=local_ip_start,
                        end=local_ip_end,
                        start_int=IPAddress(
                            local_ip_start).value,
                        end_int=IPAddress(local_ip_end).value,
                        result=local_ip_result
                    )
                    ],
                    local_port=[dict(
                        start=local_port_start,
                        end=local_port_end,
                        protocol='',
                        result=local_port_result
                    )]
                )
                self.dnat_data.append(tmp)
        return

    # SNAT
    def _netconf_source_nat(self, res):
        type_map = {
            '0': 'Nested group',
            '1': 'protocol',
            '2': 'icmp',
            '3': 'tcp',
            '4': 'udp',
            '5': 'icmpv6',
        }
        if isinstance(res, list):
            if not self.addr_set:
                send_msg_netops("华三防火墙:{}\nSNAT拼接时没有查询到地址对象集，请调整采集方法调用顺序".format(self.hostip))
            # if not self.nat_addr_groups:
            #     send_msg_netops("华三防火墙:{}\nSNAT拼接时没有查询NAT地址池，请调整采集方法调用顺序".format(self.hostip))
            for i in res:
                # self.nat_addr_groups
                # self.nat_addr_group_member
                if i['Disable'] != 'false':
                    continue
                trans_ip = []
                local_ip = []
                destination_ip = []
                destination_port = []  # 对应目标服务
                if i.get('SrcObjGrpList'):
                    # local_ip
                    src_obj_group = i['SrcObjGrpList']['SrcIpObjGroup']
                    if isinstance(src_obj_group, str):
                        src_obj_group = [src_obj_group]
                    for _local in src_obj_group:
                        if _local in self.addr_map.keys():
                            _tmp_local = self.addr_map[_local]
                            for obj in _tmp_local['ObjList']:
                                # 子网
                                if all(k in obj for k in ("SubnetIPv4Address", "IPv4Mask")):
                                    _tmp_subnet = obj['SubnetIPv4Address'] + '/' + obj['IPv4Mask']
                                    local_ip.append(dict(
                                        start=_tmp_subnet,
                                        end=_tmp_subnet,
                                        start_int=IPNetwork(_tmp_subnet).first,
                                        end_int=IPNetwork(_tmp_subnet).last,
                                        result=_tmp_subnet
                                    ))
                                # 范围
                                elif all(k in obj for k in ("StartIPv4Address", "EndIPv4Address")):
                                    start_ip = obj['StartIPv4Address']
                                    end_ip = obj['EndIPv4Address']
                                    local_ip.append(dict(
                                        start=start_ip,
                                        end=end_ip,
                                        start_int=IPAddress(start_ip).value,
                                        end_int=IPAddress(end_ip).value,
                                        result="{}-{}".format(start_ip, end_ip)
                                    ))
                                # 主机IP
                                elif obj['Type'] == 'ip' and obj.get('HostIPv4Address'):
                                    local_ip.append(dict(
                                        start=obj['HostIPv4Address'],
                                        end=obj['HostIPv4Address'],
                                        start_int=IPAddress(obj['HostIPv4Address']).value,
                                        end_int=IPAddress(obj['HostIPv4Address']).value,
                                        result=obj['HostIPv4Address']
                                    ))
                if i.get('DstObjGrpList'):
                    # destination_ip
                    dst_obj_group = i['DstObjGrpList']['DstIpObjGrou']
                    if isinstance(dst_obj_group, str):
                        dst_obj_group = [dst_obj_group]
                        for _dst in dst_obj_group:
                            _tmp_dst = self.addr_map[_dst]
                            for obj in _tmp_dst['ObjList']:
                                # 子网
                                if all(k in obj for k in ("SubnetIPv4Address", "IPv4Mask")):
                                    _tmp_subnet = obj['SubnetIPv4Address'] + '/' + obj['IPv4Mask']
                                    destination_ip.append(dict(
                                        start=_tmp_subnet,
                                        end=_tmp_subnet,
                                        start_int=IPNetwork(_tmp_subnet).first,
                                        end_int=IPNetwork(_tmp_subnet).last,
                                        result=_tmp_subnet
                                    ))
                                # 范围
                                elif all(k in obj for k in ("StartIPv4Address", "EndIPv4Address")):
                                    start_ip = obj['StartIPv4Address']
                                    end_ip = obj['EndIPv4Address']
                                    destination_ip.append(dict(
                                        start=start_ip,
                                        end=end_ip,
                                        start_int=IPAddress(start_ip).value,
                                        end_int=IPAddress(end_ip).value,
                                        result="{}-{}".format(start_ip, end_ip)
                                    ))
                                # 主机IP
                                elif obj['Type'] == 'ip' and obj.get('HostIPv4Address'):
                                    destination_ip.append(dict(
                                        start=obj['HostIPv4Address'],
                                        end=obj['HostIPv4Address'],
                                        start_int=IPAddress(obj['HostIPv4Address']).value,
                                        end_int=IPAddress(obj['HostIPv4Address']).value,
                                        result=obj['HostIPv4Address']
                                    ))
                if i.get('AddrGroupNumber'):
                    # global_ip
                    _global_group = i['AddrGroupNumber']
                    if _global_group in self.nat_addr_groups.keys():
                        # global_port 暂时没用上
                        global_port = self.nat_addr_groups[_global_group]['StartPort'] + \
                                      self.nat_addr_groups[_global_group]['EndPort']
                        _start = self.nat_addr_groups[_global_group]['StartIpv4Address']
                        _end = self.nat_addr_groups[_global_group]['EndIpv4Address']
                        trans_ip += [dict(
                            start=_start,
                            end=_end,
                            start_int=IPAddress(_start).value,
                            end_int=IPAddress(_end).value,
                            result="{}-{}".format(_start, _end))]
                    else:
                        send_msg_netops("华三防火墙:{}\nSNAT拼接时没有查询NAT地址池，请调整采集方法调用顺序".format(self.hostip))
                if i.get('SrvObjGrpList'):
                    _server_obj = i['SrvObjGrpList']['ServiceIpObjGroup']
                    if isinstance(_server_obj, str):
                        _server_obj = [_server_obj]
                    for _ser in _server_obj:
                        if _ser in self.ser_map.keys():
                            ser_tmp = self.ser_map[_ser]['items']
                            for _ser_obj in ser_tmp:
                                # print(_ser_obj)
                                destination_port.append(
                                    dict(
                                        start=int(
                                            _ser_obj['StartDestPort']) if _ser_obj.get('StartDestPort') else 0,
                                        end=int(
                                            _ser_obj['EndDestPort']) if _ser_obj.get('EndDestPort') else 0,
                                        protocol=type_map[_ser_obj['Type']],
                                        result='-'.join(list(
                                            {str(_ser_obj.get('StartDestPort')), str(_ser_obj.get('EndDestPort'))}))
                                    )
                                )
                elif i['Action'] == 'EasyIp':
                    # global_ip 出接口IP
                    pass
                tmp = dict(
                    rule_id=i['RuleName'],
                    hostip=self.hostip,
                    trans_ip=trans_ip,
                    local_ip=local_ip,
                    destination_ip=destination_ip,
                    destination_port=destination_port,
                    model=i['Action'],
                    source_zone=i.get('source-zone', ''),
                    destination_zone=i.get('destination-zone', ''),
                    log_time=datetime.now()
                )
                self.snat_data.append(tmp)

    # netconf 方法和数据处理映射
    def _netconf_method_map(self, method, res):
        ntf_map = {
            "colleciton_arp_list": self._netconf_arp,
            "colleciton_interface_list": self._netconf_interface_list,
            "colleciton_lagg_list": self._netconf_lagg_list,
            "collection_arp_over_evpn": self._netconf_arp_over_evpn,
            "collection_device_PhysicalEntities": self._netconf_physical,
            "get_secpath_physical": self._netconf_physical,
            "collection_ipv4address_list": self._netconf_ipv4address,
            "collection_ipv6address_list": self._netconf_ipv6address,
            "collection_lldp_info": self._netconf_lldp,
            "collection_mac_over_evpn": self._netconf_mac_over_evpn,
            "collection_mac_unicasttable": self._netconf_mac_unicasttable,
            "collection_vrrp_info": self._netconf_vrrp,
            "patch_version": self._netconf_patch_version,
            "collection_irf_info": self._netconf_irf,
            "collection_device_base": self._netconf_device_base,
            "get_nataddr_group": self._netconf_netaddr_group,  # 防火墙 NAT地址组
            "get_server_on_policy": self._netconf_server_on_policy,  # 防火墙 接口下NAT Server
            "get_ipv4_paging": self._netconf_ipv4_paging,  # 防火墙 地址集
            "get_sec_policy": self._netconf_sec_policy,  # 防火墙 安全策略
            "get_server_groups": self._netconf_server_groups,  # 防火墙 服务集
            "get_global_nat_policy": self._netconf_global_nat_policy,  # 防火墙 全局下DNAT
            "get_source_nat": self._netconf_source_nat,  # 防火墙 SNAT
        }
        if isinstance(res, str):
            return
        if method in ntf_map.keys():
            # print(method)
            return ntf_map[method](res)
        else:
            send_msg_netops("设备:{}\n方法:{}\n不被解析".format(self.hostip, method))

    def collection_run(self):
        # 先执行父类方法
        super(H3cProc, self).collection_run()
        if self.netconf_class == 'H3CinfoCollection':
            print('执行netconf采集')
            device = H3CinfoCollection(host=self.netconf_params['ip'],
                                       user=self.netconf_params['username'],
                                       password=self.netconf_params['password'],
                                       timeout=600)
            methods = json.loads(self.plan['netconf_method'])
            if methods:
                for method in methods:
                    print(method)
                    class_method = getattr(device, method, None)
                    if class_method:
                        try:
                            res = class_method()
                            # print("netconf_method:{} ==> res:{}".format(method, str(res)))
                            self._netconf_method_map(method, res)
                        except SessionCloseError as e:
                            time.sleep(3)
                            device.closed()
                            device = H3CinfoCollection(host=self.netconf_params['ip'],
                                                       user=self.netconf_params['username'],
                                                       password=self.netconf_params['password'],
                                                       timeout=600)
                            time.sleep(3)
                            NetworkDevice.objects.filter(manage_ip=self.hostip).update(l2vpn=False)
                            print("设备:{}\nnetconf方法:{}\n不被设备支持\n{}".format(self.hostip, method, str(e)))
                            # send_msg_netops("设备:{}\nnetconf方法:{}\n不被设备支持\n{}".format(self.hostip, method, str(e)))
                        except Exception as e:
                            print("设备:{}\nnetconf方法:{}\n执行过程中异常\n{}".format(self.hostip, method, str(e)))
            if self.dnat_data:
                MongoNetOps.insert_table(db='Automation', hostip=self.hostip, datas=self.dnat_data,
                                         tablename='DNAT')
            device.closed()
        elif self.netconf_class == 'H3CSecPath':
            device = H3CSecPath(host=self.netconf_params['ip'],
                                user=self.netconf_params['username'],
                                password=self.netconf_params['password'],
                                timeout=600)
            methods = json.loads(self.plan['netconf_method'])
            if methods:
                for method in methods:
                    class_method = getattr(device, method, None)
                    if class_method:
                        try:
                            res = class_method()
                            # print("netconf_method:{} ==> res:{}".format(method, str(res)))
                            self._netconf_method_map(method, res)
                        except Exception as e:
                            send_msg_netops("设备:{}\nnetconf方法:{}\n不被设备支持\n{}".format(self.hostip, method, str(e)))
                            print("设备:{}\nnetconf方法:{}\n不被设备支持\n{}".format(self.hostip, method, str(e)))
            if self.dnat_data:
                MongoNetOps.insert_table(db='Automation', hostip=self.hostip, datas=self.dnat_data,
                                         tablename='DNAT')
            if self.snat_data:
                MongoNetOps.insert_table(db='Automation', hostip=self.hostip, datas=self.snat_data,
                                         tablename='SNAT')
            device.closed()
        else:
            print("未被识别的netconf连接类\n设备:{}\n类:{}".format(self.hostip, self.netconf_class))

    # netconf执行手动任务
    def manual_netconf_run(self, method):
        print('执行netconf采集')
        device = H3CinfoCollection(host=self.netconf_params['ip'],
                                   user=self.netconf_params['username'],
                                   password=self.netconf_params['password'],
                                   timeout=600)
        class_method = getattr(device, method, None)
        if class_method:
            try:
                res = class_method()
                print("netconf_method:{} ==> res:{}".format(method, str(res)))
                self._netconf_method_map(method, res)
            except Exception as e:
                print("设备:{}\nnetconf方法:{}\n不被设备支持\n{}".format(self.hostip, method, str(e)))
        device.closed()


if __name__ == '__main__':
    pass
    # method_list = [func for func in dir(H3cNetconf) if
    #                callable(getattr(H3cNetconf, func)) and not func.startswith("__")]
    # print(method_list)
