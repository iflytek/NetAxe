# -*- coding: utf-8 -*-
# @Time    : 2022/4/14 16:01
# @Author  : jmli12
# @Site    :
# @File    : huawei.py
# @Software: PyCharm
import json
import re
from datetime import datetime

from django.core.cache import cache
from netaddr import IPNetwork, IPAddress

from apps.asset.models import NetworkDevice, Model, Vendor
from utils.connect_layer.auto_main import BatManMain, HuaweiS
from utils.connect_layer.NETCONF.huawei_netconf import HuaweiCollection, HuaweiUSG
from utils.db.mongo_ops import MongoNetOps, MongoOps
from utils.wechat_api import send_msg_netops
from .base_connection import BaseConn, InterfaceFormat

# import traceback
address_mongo = MongoOps(db='NETCONF', coll='huawei_usg_address_set')
nat_address_mongo = MongoOps(db='NETCONF', coll='huawei_usg_nat_address')
sec_mongo = MongoOps(db='Automation', coll='sec_policy')


class HuaweiProc(BaseConn):
    """
    display interface
    display arp
    display mac-address
    display lldp neighbor
    display device manufacture-info
    display stack
    """

    def __init__(self, **kwargs):
        # 继承父类方法
        # 防火墙需要一些变量需要同时被多个方法调用
        super(HuaweiProc, self).__init__(**kwargs)
        # dnat解析的最终数据
        self.dnat_data = []
        # snat解析的最终数据
        self.snat_data = []
        # nat 地址池映射 暂没用
        self.nat_addr_group = []
        # 地址对象映射 暂没用
        self.address_set = []
        # 服务对象
        self.service_set = {}

    def huawei_usg_sec_policy(self, datas):
        """
        name: 'shipinghuiyi-deny',
        'source-zone': 'untrust',
        'destination-zone': 'trust',
        'destination-ip': {
            'address-set': 'shipinghuiyi'
        },
        service: {
            'service-object': 'tcp22'
        },
        enable: 'true',
        action: 'false',
        hostip: '172.21.250.251'
        :param host:
        :param datas:
        :return:
        """
        results = []
        action = 'Deny'
        for i in datas:
            if i['action']:
                action = 'Permit'
            tmp = dict()
            src_addr = []
            dst_addr = []
            service = []
            tmp['src_ip_split'] = []
            tmp['dst_ip_split'] = []
            tmp['vendor'] = 'huawei_usg'
            tmp['hostip'] = self.hostip
            tmp['id'] = ''
            tmp['name'] = i['name']
            tmp['description'] = i.get('desc')
            tmp['action'] = action.lower()
            tmp['enable'] = i['enable']
            tmp['src_zone'] = i.get('source-zone')
            tmp['dst_zone'] = i.get('destination-zone')
            # tmp['service'] = i.get('service')
            if i.get('source-ip'):
                # 纯IP地址 点分十进制格式， 与掩码之间使用“/”区分，掩码使用 0- 32 的整数表示，如
                # 192.168.1.0/24。
                if 'address-ipv4' in i['source-ip'].keys():
                    if isinstance(i['source-ip']['address-ipv4'], list):
                        for element in i['source-ip']['address-ipv4']:
                            src_addr.append(dict(ip=element))
                            tmp['src_ip_split'].append(dict(start=IPNetwork(element).first,
                                                            end=IPNetwork(element).last))
                    elif isinstance(i['source-ip']['address-ipv4'], str):
                        src_addr.append(
                            dict(ip=i['source-ip']['address-ipv4']))
                        tmp['src_ip_split'].append(dict(start=IPNetwork(i['source-ip']['address-ipv4']).first,
                                                        end=IPNetwork(i['source-ip']['address-ipv4']).last))
                # address-ipv4-range 表示 IPv4 地址段节点，仅用于容纳子节 点，自身无数据含义
                if 'address-ipv4-range' in i['source-ip'].keys():
                    if isinstance(i['source-ip']['address-ipv4-range'], list):
                        for element in i['source-ip']['address-ipv4-range']:
                            start_ip = element['start-ipv4']
                            end_ip = element['end-ipv4']
                            src_addr.append(
                                dict(range=start_ip + '-' + end_ip))
                            tmp['src_ip_split'].append(dict(start=IPAddress(start_ip).value,
                                                            end=IPAddress(end_ip).value))
                    elif isinstance(i['source-ip']['address-ipv4-range'], dict):
                        start_ip = i['source-ip']['address-ipv4-range']['start-ipv4']
                        end_ip = i['source-ip']['address-ipv4-range']['end-ipv4']
                        src_addr.append(dict(range=start_ip + '-' + end_ip))
                        tmp['src_ip_split'].append(dict(start=IPAddress(start_ip).value,
                                                        end=IPAddress(end_ip).value))
                # 表示源地址引用的地址(组)对象的名称
                if 'address-set' in i['source-ip'].keys():
                    if isinstance(i['source-ip']['address-set'], str):
                        src_addr.append(
                            dict(object=i['source-ip']['address-set']))
                        _tmp = address_mongo.find(
                            query_dict=dict(hostip=self.hostip, name=i['source-ip']['address-set']),
                            fileds={'_id': 0, 'elements': 1})
                        if _tmp:
                            for element in _tmp:
                                if isinstance(element['elements'], dict):
                                    if 'address-ipv4' in element['elements'].keys():
                                        tmp['src_ip_split'].append(
                                            dict(start=IPNetwork(element['elements']['address-ipv4']).first,
                                                 end=IPNetwork(element['elements']['address-ipv4']).last))
                                    if 'start-ipv4' and 'end-ipv4' in element['elements'].keys(
                                    ):
                                        start_ip = element['elements']['start-ipv4']
                                        end_ip = element['elements']['end-ipv4']
                                        tmp['src_ip_split'].append(
                                            dict(start=IPAddress(start_ip).value,
                                                 end=IPAddress(end_ip).value))
                                if isinstance(element['elements'], list):
                                    for ele_sub in element['elements']:
                                        if 'address-ipv4' in ele_sub.keys():
                                            tmp['src_ip_split'].append(
                                                dict(start=IPNetwork(ele_sub['address-ipv4']).first,
                                                     end=IPNetwork(ele_sub['address-ipv4']).last))
                                        if 'start-ipv4' and 'end-ipv4' in ele_sub.keys():
                                            start_ip = ele_sub['start-ipv4']
                                            end_ip = ele_sub['end-ipv4']
                                            tmp['src_ip_split'].append(
                                                dict(start=IPAddress(start_ip).value,
                                                     end=IPAddress(end_ip).value))
                    elif isinstance(i['source-ip']['address-set'], list):
                        src_addr += [{'object': x}
                                     for x in i['source-ip']['address-set']]
                        for add_set in i['source-ip']['address-set']:
                            _tmp = address_mongo.find(query_dict=dict(hostip=self.hostip, name=add_set),
                                                      fileds={'_id': 0, 'elements': 1})
                            if _tmp:
                                for element in _tmp:
                                    if isinstance(element['elements'], dict):
                                        if 'address-ipv4' in element['elements'].keys():
                                            tmp['src_ip_split'].append(
                                                dict(start=IPNetwork(element['address-ipv4']).first,
                                                     end=IPNetwork(element['address-ipv4']).last))
                                        elif 'start-ipv4' and 'end-ipv4' in element['elements'].keys():
                                            start_ip = element['elements']['start-ipv4']
                                            end_ip = element['elements']['end-ipv4']
                                            tmp['src_ip_split'].append(
                                                dict(start=IPAddress(start_ip).value,
                                                     end=IPAddress(end_ip).value))
                                    if isinstance(element['elements'], list):
                                        for ele_sub in element['elements']:
                                            if 'address-ipv4' in ele_sub.keys():
                                                tmp['src_ip_split'].append(
                                                    dict(start=IPNetwork(ele_sub['address-ipv4']).first,
                                                         end=IPNetwork(ele_sub['address-ipv4']).last))
                                            elif 'start-ipv4' and 'end-ipv4' in ele_sub.keys():
                                                start_ip = ele_sub['start-ipv4']
                                                end_ip = ele_sub['end-ipv4']
                                                tmp['src_ip_split'].append(
                                                    dict(start=IPAddress(start_ip).value,
                                                         end=IPAddress(end_ip).value))
            if i.get('destination-ip'):
                # 纯IP地址 点分十进制格式， 与掩码之间使用“/”区分，掩码使用 0- 32 的整数表示，如
                # 192.168.1.0/24。
                if 'address-ipv4' in i['destination-ip'].keys():
                    if isinstance(i['destination-ip']['address-ipv4'], list):
                        for element in i['destination-ip']['address-ipv4']:
                            dst_addr.append(dict(ip=element))
                            tmp['dst_ip_split'].append(dict(start=IPNetwork(element).first,
                                                            end=IPNetwork(element).last))
                    elif isinstance(i['destination-ip']['address-ipv4'], str):
                        dst_addr.append(
                            dict(ip=i['destination-ip']['address-ipv4']))
                        tmp['dst_ip_split'].append(
                            dict(start=IPNetwork(i['destination-ip']['address-ipv4']).first,
                                 end=IPNetwork(i['destination-ip']['address-ipv4']).last))
                # address-ipv4-range 表示 IPv4 地址段节点，仅用于容纳子节 点，自身无数据含义
                if 'address-ipv4-range' in i['destination-ip'].keys():
                    if isinstance(i['destination-ip']
                                  ['address-ipv4-range'], list):
                        for element in i['destination-ip']['address-ipv4-range']:
                            start_ip = element['start-ipv4']
                            end_ip = element['end-ipv4']
                            dst_addr.append(
                                dict(range=start_ip + '-' + end_ip))
                            tmp['dst_ip_split'].append(dict(start=IPAddress(start_ip).value,
                                                            end=IPAddress(end_ip).value))
                    elif isinstance(i['destination-ip']['address-ipv4-range'], dict):
                        start_ip = i['destination-ip']['address-ipv4-range']['start-ipv4']
                        end_ip = i['destination-ip']['address-ipv4-range']['end-ipv4']
                        dst_addr.append(dict(range=start_ip + '-' + end_ip))
                        tmp['dst_ip_split'].append(dict(start=IPAddress(start_ip).value,
                                                        end=IPAddress(end_ip).value))
                # 表示源地址引用的地址(组)对象的名称
                if 'address-set' in i['destination-ip'].keys():
                    if isinstance(i['destination-ip']['address-set'], str):
                        dst_addr.append(
                            dict(object=i['destination-ip']['address-set']))
                        _tmp = address_mongo.find(
                            query_dict=dict(hostip=self.hostip, name=i['destination-ip']['address-set']),
                            fileds={'_id': 0, 'elements': 1})
                        if _tmp:
                            for element in _tmp:
                                if isinstance(element['elements'], dict):
                                    if 'address-ipv4' in element['elements'].keys():
                                        tmp['src_ip_split'].append(
                                            dict(start=IPNetwork(element['elements']['address-ipv4']).first,
                                                 end=IPNetwork(element['elements']['address-ipv4']).last))
                                    if 'start-ipv4' and 'end-ipv4' in element['elements'].keys(
                                    ):
                                        start_ip = element['elements']['start-ipv4']
                                        end_ip = element['elements']['end-ipv4']
                                        tmp['dst_ip_split'].append(
                                            dict(start=IPAddress(start_ip).value,
                                                 end=IPAddress(end_ip).value))
                                if isinstance(element['elements'], list):
                                    for ele_sub in element['elements']:
                                        if 'address-ipv4' in ele_sub.keys():
                                            tmp['dst_ip_split'].append(
                                                dict(start=IPNetwork(ele_sub['address-ipv4']).first,
                                                     end=IPNetwork(ele_sub['address-ipv4']).last))
                                        if 'start-ipv4' and 'end-ipv4' in ele_sub.keys():
                                            start_ip = ele_sub['start-ipv4']
                                            end_ip = ele_sub['end-ipv4']
                                            tmp['dst_ip_split'].append(
                                                dict(start=IPAddress(start_ip).value,
                                                     end=IPAddress(end_ip).value))
                    elif isinstance(i['destination-ip']['address-set'], list):
                        dst_addr += [{'object': x}
                                     for x in i['destination-ip']['address-set']]
                        for add_set in i['destination-ip']['address-set']:
                            _tmp = address_mongo.find(query_dict=dict(hostip=self.hostip, name=add_set),
                                                      fileds={'_id': 0, 'elements': 1})
                            if _tmp:
                                for element in _tmp:
                                    if isinstance(element['elements'], dict):
                                        if 'address-ipv4' in element['elements'].keys():
                                            tmp['dst_ip_split'].append(
                                                dict(start=IPNetwork(element['address-ipv4']).first,
                                                     end=IPNetwork(element['address-ipv4']).last))
                                        elif 'start-ipv4' and 'end-ipv4' in element['elements'].keys():
                                            start_ip = element['elements']['start-ipv4']
                                            end_ip = element['elements']['end-ipv4']
                                            tmp['dst_ip_split'].append(
                                                dict(start=IPAddress(start_ip).value,
                                                     end=IPAddress(end_ip).value))
                                    if isinstance(element['elements'], list):
                                        for ele_sub in element['elements']:
                                            if 'address-ipv4' in ele_sub.keys():
                                                tmp['dst_ip_split'].append(
                                                    dict(start=IPNetwork(ele_sub['address-ipv4']).first,
                                                         end=IPNetwork(ele_sub['address-ipv4']).last))
                                            elif 'start-ipv4' and 'end-ipv4' in ele_sub.keys():
                                                start_ip = ele_sub['start-ipv4']
                                                end_ip = ele_sub['end-ipv4']
                                                tmp['dst_ip_split'].append(
                                                    dict(start=IPAddress(start_ip).value,
                                                         end=IPAddress(end_ip).value))
            if i.get('service'):
                if 'service-object' in i['service'].keys():
                    if isinstance(i['service']['service-object'], str):
                        service.append(
                            dict(object=i['service']['service-object']))
                    elif isinstance(i['service']['service-object'], list):
                        service += [{'object': x}
                                    for x in i['service']['service-object']]
                if 'service-items' in i['service'].keys():
                    if isinstance(i['service']['service-items'], dict):
                        for key in i['service']['service-items'].keys():
                            if key in ['tcp', 'udp']:
                                if isinstance(
                                        i['service']['service-items'][key], list):
                                    for item in i['service']['service-items'][key]:
                                        _src_port = item['source-port']
                                        _dst_port = item['dest-port']
                                        if _src_port.find('to') != -1:
                                            _src_port = _src_port.split('to')
                                        if _dst_port.find('to') != -1:
                                            _dst_port = _dst_port.split('to')
                                        service.append(dict(item={
                                            "Type": key,
                                            "StartSrcPort": _src_port[0].strip() if isinstance(_src_port,
                                                                                               list) else _src_port,
                                            "EndSrcPort": _src_port[1].strip() if isinstance(_src_port,
                                                                                             list) else _src_port,
                                            "StartDestPort": _dst_port[1].strip() if isinstance(_dst_port,
                                                                                                list) else _dst_port,
                                            "EndDestPort": _dst_port[1].strip() if isinstance(_dst_port,
                                                                                              list) else _dst_port,
                                        }))
                                elif isinstance(i['service']['service-items'][key], dict):
                                    _src_port = i['service']['service-items'][key]['source-port']
                                    _dst_port = i['service']['service-items'][key]['dest-port']
                                    if _src_port.find('to') != -1:
                                        _src_port = _src_port.split('to')
                                    if _dst_port.find('to') != -1:
                                        _dst_port = _dst_port.split('to')
                                    service.append(dict(item={
                                        "Type": key,
                                        "StartSrcPort": _src_port[0].strip() if isinstance(_src_port,
                                                                                           list) else _src_port,
                                        "EndSrcPort": _src_port[1].strip() if isinstance(_src_port,
                                                                                         list) else _src_port,
                                        "StartDestPort": _dst_port[1].strip() if isinstance(_dst_port,
                                                                                            list) else _dst_port,
                                        "EndDestPort": _dst_port[1].strip() if isinstance(_dst_port,
                                                                                          list) else _dst_port,
                                    }))
                            if key == 'icmp-item':
                                if isinstance(
                                        i['service']['service-items'][key], list):
                                    for item in i['service']['service-items'][key]:
                                        service.append(dict(item={
                                            "Type": "icmp",
                                        }))
                                elif isinstance(i['service']['service-items'][key], dict):
                                    service.append(dict(item={
                                        "Type": "icmp",
                                    }))
                        # 'ServObjList': {'ServObjItem': '{ "Type": "0", "StartSrcPort": "0", "EndSrcPort": "65535", "StartDestPort": "80", "EndDestPort": "80" }'},
                    # todo 继续拆解 {'tcp': {'source-port': '0 to 65535',
                    # 'dest-port': '80'}}}
            tmp['service'] = service
            tmp['src_addr'] = src_addr
            tmp['dst_addr'] = dst_addr
            results.append(tmp)
        sec_mongo.delete_many(query=dict(hostip=self.hostip))
        sec_mongo.insert_many(results)
        return

    def arp_proc(self, res):
        if isinstance(res, list):
            arp_datas = []
            for i in res:
                tmp = dict(
                    hostip=self.hostip,
                    hostname=self.hostname,
                    idc_name=self.idc_name,
                    ipaddress=i['ipaddress'],
                    macaddress=i['macaddress'],
                    aging=i['expire'],
                    type=i['type'],
                    vlan=i.get('vlan', ''),
                    interface=InterfaceFormat.huawei_interface_format(
                        i['interface']),
                    vpninstance=i['vpninstance'],
                    log_time=datetime.now()
                )
                arp_datas.append(tmp)
            if arp_datas:
                MongoNetOps.insert_table(
                    'Automation', self.hostip, arp_datas, 'ARPTable')

    def mac_proc(self, res):
        """
        {'macaddress': '04d7-a541-2eea', 'vlan': '1001', 'interface': 'GE1/1/1', 'type': 'dynamic', 'age': '300'}
        :param res:
        :return:
        """
        if isinstance(res, list):
            mac_datas = []
            for i in res:
                tmp = dict(
                    hostip=self.hostip,
                    hostname=self.hostname,
                    idc_name=self.idc_name,
                    macaddress=i['macaddress'],
                    vlan=i['vlan'],
                    interface=InterfaceFormat.huawei_interface_format(
                        i['interface']),
                    type=i['type'],
                    log_time=datetime.now()
                )
                mac_datas.append(tmp)
            if mac_datas:
                MongoNetOps.insert_table(
                    'Automation', self.hostip, mac_datas, 'MACTable')

    def interface_proc(self, path):
        eth_trunk_res = HuaweiS.eth_trunk(path=path)
        interface_res = HuaweiS.interface(path=path)
        aggre_datas = []
        layer3datas = []
        layer2datas = []
        if eth_trunk_res:
            for i in eth_trunk_res:
                if i['IPADDR']:
                    for _ip in range(len(i['IPADDR'])):
                        # _ip 为数组下标 0，1，2，3
                        if i['IPADDR'][_ip].find('/') != -1:
                            _ipnet = IPNetwork(i['IPADDR'][_ip])
                            location = [dict(start=_ipnet.first, end=_ipnet.last)]
                            data = dict(
                                hostip=self.hostip,
                                interface=i['Interface'],
                                line_status=i['Status'],
                                protocol_status=i['ProtocolStatus'],
                                ipaddress=_ipnet.ip.format(),
                                ipmask=_ipnet.netmask.format(),
                                ip_type=i['IPTYPE'][_ip],
                                location=location,
                                mtu='')
                            layer3datas.append(data)
                tmp = dict(
                    hostip=self.hostip,
                    aggregroup=i['Interface'],
                    memberports=i['MemberPort'],
                    status=i['MemberPortStatus'],
                    mode=''
                )
                aggre_datas.append(tmp)
        if interface_res:
            for i in interface_res:
                if i['IPADDR']:
                    for _ip in range(len(i['IPADDR'])):
                        # _ip 为数组下标 0，1，2，3
                        if i['IPADDR'][_ip].find('/') != -1:
                            _ipnet = IPNetwork(i['IPADDR'][_ip])
                            location = [dict(start=_ipnet.first, end=_ipnet.last)]
                            data = dict(
                                hostip=self.hostip,
                                interface=i['Interface'],
                                line_status=i['Status'],
                                protocol_status=i['ProtocolStatus'],
                                ipaddress=_ipnet.ip.format(),
                                ipmask=_ipnet.netmask.format(),
                                ip_type=i['IPTYPE'][_ip],
                                location=location,
                                mtu='')
                            layer3datas.append(data)
                if i['Interface'].startswith('LoopBack'):
                    continue
                if i['Interface'].startswith('NULL'):
                    continue
                if i['Interface'].startswith('Vlanif'):
                    continue
                if i['Interface'].startswith('Ethernet0/0/0'):
                    continue
                data = dict(hostip=self.hostip,
                            interface=i['Interface'],
                            status=i['Status'],
                            # speed=i['Speed'],
                            speed=InterfaceFormat.mathintspeed(i['Speed']),
                            duplex=i['Duplex'],
                            description=i['Description'])
                layer2datas.append(data)
        if aggre_datas:
            MongoNetOps.insert_table(
                'Automation', self.hostip, aggre_datas, 'AggreTable')
        if layer3datas:
            MongoNetOps.insert_table(
                db='Automation',
                hostip=self.hostip,
                datas=layer3datas,
                tablename='layer3interface')
        if layer2datas:
            MongoNetOps.insert_table(
                db='Automation',
                hostip=self.hostip,
                datas=layer2datas,
                tablename='layer2interface')
        return

    def lldp_proc(self, res):
        lldp_datas = []
        for i in res:
            if not isinstance(i, dict):
                continue
            neighbor_ip = ''
            if 'neighborsysname' in i.keys():
                if i['neighborsysname']:
                    tmp_neighbor_ip = cache.get('cmdb_' + i['neighborsysname'])
                    if tmp_neighbor_ip:
                        tmp_neighbor_ip = json.loads(tmp_neighbor_ip)
                        neighbor_ip = tmp_neighbor_ip[0]['manage_ip']
                    else:
                        tmp_neighbor_ip = NetworkDevice.objects.filter(name=i['neighborsysname']
                                                                       ).values('manage_ip')
                        neighbor_ip = tmp_neighbor_ip[0]['manage_ip'] if tmp_neighbor_ip else ''
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

    def manuinfo_proc(self, res):
        if isinstance(res, list):
            for _tmp in res:
                NetworkDevice.objects.filter(manage_ip=self.hostip, serial_num=_tmp['serialnum']) \
                    .update(slot=int(_tmp['slot']))
        elif isinstance(res, dict):
            NetworkDevice.objects.filter(manage_ip=self.hostip, serial_num=res['serialnum']) \
                .update(slot=int(res['slot']))

    def stack_proc(self, res):
        if isinstance(res, list):
            if len(res) == 1:
                for _tmp in res:
                    if _tmp['role'] == 'Master':
                        NetworkDevice.objects.filter(manage_ip=self.hostip, slot=int(_tmp['slot'])).update(
                            ha_status=0)
                    elif _tmp['role'] == 'Standby':
                        NetworkDevice.objects.filter(manage_ip=self.hostip, slot=int(_tmp['slot'])).update(
                            ha_status=0)
            else:
                for _tmp in res:
                    if _tmp['role'] == 'Master':
                        NetworkDevice.objects.filter(manage_ip=self.hostip, slot=int(_tmp['slot'])).update(
                            ha_status=1)
                    elif _tmp['role'] == 'Standby':
                        NetworkDevice.objects.filter(manage_ip=self.hostip, slot=int(_tmp['slot'])).update(
                            ha_status=2)
        elif isinstance(res, dict):
            NetworkDevice.objects.filter(
                manage_ip=self.hostip, slot=int(
                    res['slot'])).update(
                ha_status=0)
            # if res['role'] == 'Master':
            #     NetworkDevice.objects.filter(
            #         manage_ip=hostip, slot=int(
            #             res['slot'])).update(
            #         ha_status=1)
            # elif res['role'] == 'Standby':
            #     NetworkDevice.objects.filter(
            #         manage_ip=hostip, slot=int(
            #             res['slot'])).update(
            #         ha_status=2)

    # 命令结果解析模块
    def path_map(self, file_name, res: list):
        fsm_map = {
            'display_arp': self.arp_proc,
            'display_arp_all': self.arp_proc,
            'display_mac-address': self.mac_proc,
            'display_lldp_neighbor': self.lldp_proc,
            'display_device_manufacture-info': self.manuinfo_proc,
            'display_stack': self.stack_proc
        }
        if file_name in fsm_map.keys():
            fsm_map[file_name](res)
        else:
            send_msg_netops("设备:{}\n命令:{}\n不被解析".format(self.hostip, file_name))

    def _collection_analysis(self, paths: list):
        # self.cmds += ['display mac-address']
        for path in paths:
            if path['cmd_file'] == 'display_interface':
                self.interface_proc(path)
            else:
                res = BatManMain.info_fsm(path=path['path'], fsm_platform=self.fsm_flag)
                self.path_map(path['cmd_file'], res)

    def _netconf_ce_system_info(self, res: list):
        """
        {'sysName': 'DZ.PO.IN.CO.X01S', 'sysContact': 'R&D Beijing, Huawei Technologies co.,Ltd.', 'sysLocation':
        'Beijing China', 'sysDesc': 'Huawei Versatile Routing Platform Software \nVRP (R) software, Version 8.150 (
        CE6855HI V200R002C50SPC800) \nCopyright (C) 2012-2017 Huawei Technologies Co., Ltd. \nHUAWEI
        CE6855-48S6Q-HI', 'sysObjectId': '1.3.6.1.4.1.2011.2.239.29', 'sysGmtTime': '1662362848', 'sysUpTime':
        '134780738', 'sysService': '78', 'platformName': 'VRP', 'platformVer': 'V800R015C00SPC789', 'productName':
        'CE6855HI', 'productVer': 'V200R002C50SPC800', 'patchVer': 'V200R002SPH008', 'esn': '2102350RTC6TJ3329',
        'mac': '58F9-8726-0431', 'lsRole': 'admin', 'authenFlag': 'false'} :param res: :return:
        """
        if res:
            if isinstance(res, dict):
                if self.hostname != res['sysName']:
                    NetworkDevice.objects.filter(manage_ip=self.hostip, status=0).update(
                        name=res['sysName'], soft_version=res['platformVer'], patch_version=res['patchVer']
                    )
                model_q = Model.objects.filter(name=res['productName'])
                if model_q:
                    model_obj = Model.objects.get(name=res['productName'])
                    NetworkDevice.objects.filter(manage_ip=self.hostip, status=0) \
                        .update(model=model_obj)
                else:
                    model_q = Model.objects.create(name=res['productName'],
                                                        vendor=Vendor.objects.get(alias='Huawei'))
                    NetworkDevice.objects.filter(manage_ip=self.hostip, status=0) \
                        .update(model=model_q)
            if isinstance(res, list):
                for _sysinfo in res:
                    if self.hostname != _sysinfo['sysName']:
                        NetworkDevice.objects.filter(manage_ip=self.hostip, status=0).update(
                            name=_sysinfo['sysName'], soft_version=_sysinfo['platformVer'],
                            patch_version=_sysinfo['patchVer']
                        )
                    model_q = Model.objects.filter(name=_sysinfo['productName'])
                    if model_q:
                        model_obj = Model.objects.get(name=_sysinfo['productName'])
                        NetworkDevice.objects.filter(manage_ip=self.hostip, status=0) \
                            .update(model=model_obj)
                    else:
                        model_q = Model.objects.create(name=_sysinfo['productName'],
                                                            vendor=Vendor.objects.get(alias='Huawei'))
                        NetworkDevice.objects.filter(manage_ip=self.hostip, status=0) \
                            .update(model=model_q)

    def _netconf_moduleinfo(self, dev_moduleinfo):
        if dev_moduleinfo:
            if isinstance(dev_moduleinfo, list):
                """
                {'entClass': 'mpuModule', 'position': '1', 'entSerialNo': '0', 'entSerialNum': '2102350RTC6TJ3001332'}
                {'entClass': 'mpuModule', 'position': '2', 'entSerialNo': '0', 'entSerialNum': '2102350RTC6TJ3001314'}

                {'entClass': 'chassis', 'position': '1', 'entSerialNo': '0', 'entSerialNum': '2102113773P0J6000150'}
                {'entClass': 'chassis', 'position': '2', 'entSerialNo': '0', 'entSerialNum': '2102113773P0J6000152'}
                """
                for _dev in dev_moduleinfo:
                    NetworkDevice.objects.filter(manage_ip=self.hostip, serial_num=_dev['entSerialNum']) \
                        .update(slot=int(_dev['position']))
            elif isinstance(dev_moduleinfo, dict):
                NetworkDevice.objects.filter(manage_ip=self.hostip, serial_num=dev_moduleinfo['entSerialNum']) \
                    .update(slot=int(dev_moduleinfo['position']))

    def _netconf_stack(self, stack_info):
        if stack_info:
            if isinstance(stack_info, list):
                for _stack in stack_info:
                    if _stack['role'] == 'Master':
                        NetworkDevice.objects.filter(manage_ip=self.hostip, slot=int(_stack['memberID'])).update(
                            ha_status=1)
                    elif _stack['role'] == 'Standby':
                        NetworkDevice.objects.filter(manage_ip=self.hostip, slot=int(_stack['memberID'])).update(
                            ha_status=2)
            elif isinstance(stack_info, dict):
                if stack_info['role'] == 'Master':
                    NetworkDevice.objects.filter(manage_ip=self.hostip, slot=int(stack_info['memberID'])).update(
                        ha_status=1)
                elif stack_info['role'] == 'Standby':
                    NetworkDevice.objects.filter(manage_ip=self.hostip, slot=int(stack_info['memberID'])).update(
                        ha_status=2)

    def _netconf_intf_ipv4v6(self, intf_ip_res):
        if intf_ip_res:
            intf_datas = []
            layer3datas = []
            layer2datas = []
            for i in intf_ip_res:
                if 'ipv4Oper' in i.keys():
                    if isinstance(i['ipv4Oper']['ipv4Addrs']
                                  ['ipv4Addr'], dict):
                        ipaddr = i['ipv4Oper']['ipv4Addrs']['ipv4Addr']['ifIpAddr']
                        ip_type = i['ipv4Oper']['ipv4Addrs']['ipv4Addr']['addrType']
                        ipmask = i['ipv4Oper']['ipv4Addrs']['ipv4Addr']['subnetMask']
                        _ipnet = IPNetwork("{}/{}".format(ipaddr, ipmask))
                        location = [dict(start=_ipnet.first, end=_ipnet.last)]
                        data = dict(
                            hostip=self.hostip,
                            interface=i['ifName'],
                            line_status=i['ifDynamicInfo']['ifLinkStatus'],
                            protocol_status=i['ifDynamicInfo']['ifV4State'],
                            ipaddress=_ipnet.ip.format(),
                            ipmask=_ipnet.netmask.format(),
                            ip_type=ip_type,
                            location=location,
                            mtu=i['ifDynamicInfo']['ifOpertMTU'])
                        layer3datas.append(data)
                    elif isinstance(i['ipv4Oper']['ipv4Addrs']['ipv4Addr'], list):
                        tmp_iplist = i['ipv4Oper']['ipv4Addrs']['ipv4Addr']
                        for _ip in tmp_iplist:
                            _ipnet = IPNetwork("{}/{}".format(_ip['ifIpAddr'], _ip['subnetMask']))
                            location = [dict(start=_ipnet.first, end=_ipnet.last)]
                            data = dict(
                                hostip=self.hostip,
                                interface=i['ifName'],
                                line_status=i['ifDynamicInfo']['ifLinkStatus'],
                                protocol_status=i['ifDynamicInfo']['ifV4State'],
                                ipaddress=_ipnet.ip.format(),
                                ipmask=_ipnet.netmask.format(),
                                ip_type=_ip['addrType'],
                                location=location,
                                mtu=i['ifDynamicInfo']['ifOpertMTU'])
                            layer3datas.append(data)
                i['hostip'] = self.hostip
                i['hostname'] = self.hostname
                intf_datas.append(i)
            for i in intf_ip_res:
                if i['ifName'].startswith('Tunnel'):
                    continue
                if i['ifName'].startswith('Stack-Port'):
                    continue
                if i['ifName'].startswith('MEth'):
                    continue
                if i['ifName'].startswith('Vbdif'):
                    continue
                if i['ifName'].startswith('Vlanif'):
                    continue
                if 'ifDynamicInfo' in i.keys(
                ) and not i['ifName'].startswith('Eth-Trunk'):
                    if 'ifOperSpeed' in i['ifDynamicInfo'].keys():
                        data = dict(hostip=self.hostip,
                                    interface=i['ifName'],
                                    status=i['ifDynamicInfo']['ifOperStatus'],
                                    speed=InterfaceFormat.mathintspeed(
                                        i['ifDynamicInfo']['ifOperSpeed']),
                                    duplex='',
                                    description='')
                        layer2datas.append(data)
            if layer2datas:
                MongoNetOps.insert_table(db='Automation', hostip=self.hostip, datas=layer2datas,
                                         tablename='layer2interface')
            if layer3datas:
                MongoNetOps.insert_table(db='Automation', hostip=self.hostip, datas=layer3datas,
                                         tablename='layer3interface')
            MongoNetOps.insert_table(db='NETCONF', hostip=self.hostip, datas=intf_datas,
                                     tablename='huawei_interface_ipv4v6')

    def _netconf_arp_list(self, arp_res):
        if arp_res:
            """
            {'vrfName': '_public_', 'ipAddr': '172.16.191.127', 'expireTime': '1', 'styleType': 'DynamicArp',
            'ifName': 'Vlanif691'}
            {'vrfName': '_public_', 'ipAddr': '172.16.49.254', 'macAddr': 'a4be-2b89-170b',
            'styleType': 'InterfaceArp', 'ifName': 'Vlanif549'}
            {'vrfName': '_public_', 'ipAddr': '172.16.49.11', 'macAddr': '6c92-bf3b-d721',
            'expireTime': '12', 'styleType': 'DynamicArp', 'ifName': 'Eth-Trunk416', 'peVid': '549'
            """
            arp_datas = []
            for i in arp_res:
                tmp = dict(
                    hostip=self.hostip,
                    hostname=self.hostname,
                    idc_name=self.idc_name,
                    ipaddress=i['ipAddr'],
                    macaddress=i.get('macAddr'),
                    aging=i.get('expireTime'),
                    type=i.get('styleType'),
                    vlan=i.get('peVid'),
                    interface=i['ifName'],
                    vpninstance=i.get('vrfName'),
                    log_time=datetime.now()
                )
                arp_datas.append(tmp)
            MongoNetOps.insert_table(
                'Automation', self.hostip, arp_datas, 'ARPTable')

    def _netconf_mac_bd(self, mac_bd):
        if mac_bd:
            mac_bd_datas = []
            for i in mac_bd:
                tmp = dict(
                    hostip=self.hostip,
                    hostname=self.hostname,
                    idc_name=self.idc_name,
                    macaddress=i['macAddress'],
                    vlan='-',
                    bdId=i['bdId'],
                    interface=i.get('outIfName'),
                    type=i['macType'],
                    log_time=datetime.now()
                )
                mac_bd_datas.append(tmp)
            MongoNetOps.insert_table(db='Automation', hostip=self.hostip,
                                     datas=mac_bd_datas, tablename='MACTable')

    def _netconf_mac_vxlan(self, mac_vxlan):
        if mac_vxlan:
            mac_vxlan_datas = []
            for i in mac_vxlan:
                i['hostip'] = self.hostip
                mac_vxlan_datas.append(i)
            MongoNetOps.insert_table(db='NETCONF', hostip=self.hostip,
                                     datas=mac_vxlan_datas, tablename='netconf_mac_vxlan')

    def _netconf_mac_vxlan_control(self, mac_vxlan_control):
        if mac_vxlan_control:
            mac_vxlan_control_datas = []
            for i in mac_vxlan_control:
                i['hostip'] = self.hostip
                mac_vxlan_control_datas.append(i)
            MongoNetOps.insert_table(db='NETCONF', hostip=self.hostip,
                                     datas=mac_vxlan_control_datas, tablename='netconf_mac_vxlan_control')

    def _netconf_mac_table(self, mac_res):
        if mac_res:
            """
            {'slotId': '0', 'vlanId': '654', 'macAddress': 'd4ae-52a7-b954', 'macType': 'dynamic',
            'outIfName': 'Eth-Trunk227'}
            {'slotId': '0', 'vlanId': '654', 'macAddress': 'fa16-3e4d-cedb', 'macType': 'blackHole'}
            """
            mac_datas = []
            for i in mac_res:
                tmp = dict(
                    hostip=self.hostip,
                    hostname=self.hostname,
                    idc_name=self.idc_name,
                    macaddress=i['macAddress'],
                    vlan=i['vlanId'],
                    interface=i.get('outIfName'),
                    type=i['macType'],
                    log_time=datetime.now()
                )
                mac_datas.append(tmp)
            if mac_datas:
                MongoNetOps.insert_table(
                    'Automation', self.hostip, mac_datas, 'MACTable', delete=False)

    def _netconf_lldp(self, lldp_res):
        if lldp_res:
            lldp_datas = []
            for i in lldp_res:
                if 'lldpNeighbors' in i.keys():
                    if i['lldpNeighbors']['lldpNeighbor']['portIdSubtype'] == 'macAddress':
                        continue
                    else:
                        lldpNeighbor = i['lldpNeighbors']['lldpNeighbor']
                        management_ip = ''
                        management_type = ''
                        if 'managementAddresss' in lldpNeighbor.keys():
                            if isinstance(
                                    lldpNeighbor['managementAddresss']['managementAddress'], list):
                                for _manage_ip in lldpNeighbor['managementAddresss']['managementAddress']:
                                    if _manage_ip['manAddrSubtype'] == 'ipv4':
                                        management_ip = _manage_ip['manAddr']
                                        management_type = _manage_ip['manAddrSubtype']
                            else:
                                management_ip = lldpNeighbor['managementAddresss']['managementAddress']['manAddr']
                                management_type = lldpNeighbor['managementAddresss']['managementAddress'][
                                    'manAddrSubtype']
                        else:
                            management_ip = None
                            management_type = None
                        neighbor_ip = ''
                        if lldpNeighbor.get('systemName'):
                            tmp_neighbor_ip = cache.get(
                                'cmdb_' + lldpNeighbor['systemName'])
                            if tmp_neighbor_ip:
                                tmp_neighbor_ip = json.loads(
                                    tmp_neighbor_ip)
                                neighbor_ip = tmp_neighbor_ip[0]['manage_ip']
                            else:
                                tmp_neighbor_ip = NetworkDevice.objects.filter(name=lldpNeighbor['systemName']
                                                                               ).values('manage_ip')
                                neighbor_ip = tmp_neighbor_ip[0]['manage_ip'] if tmp_neighbor_ip else ''
                        tmp = dict(
                            hostip=self.hostip,
                            local_interface=i['ifName'],
                            chassis_id=lldpNeighbor['chassisId'],
                            neighbor_port=lldpNeighbor['portId'],
                            portdescription=lldpNeighbor.get(
                                'portDescription'),
                            neighborsysname=lldpNeighbor.get('systemName'),
                            management_ip=management_ip,
                            management_type=management_type,
                            neighbor_ip=neighbor_ip
                        )
                        lldp_datas.append(tmp)
            if lldp_datas:
                MongoNetOps.insert_table(
                    'Automation', self.hostip, lldp_datas, 'LLDPTable')

    def _netconf_trunk_lacp(self, eth_trunk_res):
        if eth_trunk_res:
            aggre_datas = []
            for i in eth_trunk_res:
                if 'TrunkMemberIfs' in i.keys():
                    try:
                        memberports = []
                        memberstatus = []
                        if isinstance(i['TrunkMemberIfs']
                                      ['TrunkMemberIf'], list):
                            for member in i['TrunkMemberIfs']['TrunkMemberIf']:
                                memberports.append(member['memberIfName'])
                                memberstatus.append(
                                    member['memberIfState'])
                        else:
                            memberports.append(
                                i['TrunkMemberIfs']['TrunkMemberIf']['memberIfName'])
                            memberstatus.append(
                                i['TrunkMemberIfs']['TrunkMemberIf']['memberIfState'])
                    except Exception as e:
                        memberports = []
                        memberstatus = []
                    tmp = dict(
                        hostip=self.hostip,
                        aggregroup=i['ifName'],
                        memberports=memberports,
                        status=memberstatus,
                        mode=''
                    )
                    aggre_datas.append(tmp)
            if aggre_datas:
                MongoNetOps.insert_table(
                    'Automation', self.hostip, aggre_datas, 'AggreTable')

    def _netcocnf_system_info(self, dev_sysinfo):
        if dev_sysinfo:
            if isinstance(dev_sysinfo, dict):
                model_q = Model.objects.filter(name=dev_sysinfo['model'])
                if model_q:
                    NetworkDevice.objects.filter(manage_ip=self.hostip, status=0) \
                        .update(model=Model.objects.get(name=dev_sysinfo['model']),
                                soft_version=dev_sysinfo['version'],
                                patch_version=dev_sysinfo['patch-version'])
                else:
                    model_q = Model.objects.create(name=dev_sysinfo['model'],
                                                        vendor=Vendor.objects.get(alias='Huawei'))
                    NetworkDevice.objects.filter(manage_ip=self.hostip, status=0) \
                        .update(model=model_q,
                                soft_version=dev_sysinfo['version'],
                                patch_version=dev_sysinfo['patch-version'])
            if isinstance(dev_sysinfo, list):
                for _sysinfo in dev_sysinfo:
                    model_q = Model.objects.filter(name=_sysinfo['model'])
                    if model_q:
                        NetworkDevice.objects.filter(manage_ip=self.hostip, status=0) \
                            .update(model=Model.objects.get(name=_sysinfo['model']),
                                    soft_version=_sysinfo['version'],
                                    patch_version=_sysinfo['patch-version'])
                    else:
                        model_q = Model.objects.create(name=_sysinfo['model'],
                                                            vendor=Vendor.objects.get(alias='Huawei'))
                        NetworkDevice.objects.filter(manage_ip=self.hostip, status=0) \
                            .update(model=model_q,
                                    soft_version=_sysinfo['version'],
                                    patch_version=_sysinfo['patch-version'])

    def _netconf_usg_interface_list(self, inter_res):
        if inter_res:
            intf_datas = []
            for i in inter_res:
                if 'ip:ipv4' in i.keys():
                    if isinstance(i['ip:ipv4'], dict):
                        ipaddr = i['ip:ipv4']['ip:address']['ip:ip']
                        ip_type = 'ipv4'
                        ipmask = i['ip:ipv4']['ip:address']['ip:netmask']
                        # 安全纳管引擎，服务发布 定位用 这地方居然没生效
                        _location_ip = IPNetwork(ipaddr + '/' + ipmask)
                        location = [dict(start=_location_ip.first, end=_location_ip.last)]
                        data = dict(
                            hostip=self.hostip,
                            interface=i['name'],
                            line_status='',
                            protocol_status='',
                            ipaddress=_location_ip.ip.format(),
                            ipmask=_location_ip.netmask.format(),
                            ip_type=ip_type,
                            mtu='', location=location)
                        self.layer3datas.append(data)
                i['hostip'] = self.hostip
                i['hostname'] = self.hostname
                intf_datas.append(i)
            MongoNetOps.insert_table(db='NETCONF', hostip=self.hostip, datas=intf_datas,
                                     tablename='huawei_usg_interface_ipv4v6')

    def _netconf_usg_vrrp_info(self, vrrp_res):
        if vrrp_res:
            host_ip_regex = re.compile('^\\d+.\\d+.\\d+.\\d+$')
            host_ipmask_regex = re.compile(
                '^\\d+.\\d+.\\d+.\\d+\\s\\d+.\\d+.\\d+.\\d+$')
            for i in vrrp_res:
                if i['vrrp4'].get('config-state') != 'active' or 'config-state' not in i['vrrp4'].keys():
                    continue
                mask = '255.255.255.255'
                if host_ip_regex.search(i['vrrp4']['virtual-ip']):
                    ip = i['vrrp4']['virtual-ip']
                elif host_ipmask_regex.search(i['vrrp4']['virtual-ip']):
                    ip = i['vrrp4']['virtual-ip'].split()[0]
                    mask = i['vrrp4']['virtual-ip'].split()[1]
                else:
                    ip = i['vrrp4']['virtual-ip']
                _ipnet = IPNetwork("{}/{}".format(ip, mask))
                location = [dict(start=_ipnet.first, end=_ipnet.last)]
                data = dict(
                    hostip=self.hostip,
                    interface=i['interface-name'],
                    line_status='',
                    protocol_status='',
                    ipaddress=ip,
                    ipmask=mask,
                    ip_type='virtual ip',
                    location=location,
                    mtu='')
                self.layer3datas.append(data)

    def _netconf_usg_hrp_state(self, hrp_res):
        if hrp_res:
            """
            hrp-status  当前状态  active   standby
            heartbeat-status 心跳状态  running
            config-master 配置主设备  true  false
            hrp-switch-info  历史切换记录
            """
            ha_state = hrp_res['hrp-status']
            if ha_state == 'active':
                NetworkDevice.objects.filter(
                    manage_ip=self.hostip).update(
                    ha_status=1)
            elif ha_state == 'standby':
                NetworkDevice.objects.filter(
                    manage_ip=self.hostip).update(
                    ha_status=2)
            else:
                NetworkDevice.objects.filter(
                    manage_ip=self.hostip).update(
                    ha_status=0)

    # SNAT
    def _netconf_usg_nat_policy(self, nat_policy):
        """
        表示 NAT 策略规则的动作。取值"no-nat"，表示匹配该规则的流量不做 NAT 转换;
        取值"easyip"，表示匹配该规则的流量报文源IP修改为出接口的IP地址;
        取值"nat-address-group"，表示匹配该规则的流量报文源IP修改所配置的NAT地址池中的IP地址。如果该动作未赋值，则该策略规则不生效。
        :param nat_policy:
        :return:
        """
        try:
            if nat_policy:
                for record in nat_policy:
                    record['hostip'] = self.hostip
                    if record['rule']:
                        for i in record['rule']:
                            if i['enable'] != 'true':
                                continue
                            local_ip = []
                            trans_ip = []
                            destination_ip = []
                            destination_port = []
                            action = i.get('action') or 'unknow'
                            # 内网IP
                            if i.get('source-ip'):
                                if 'address-set' in i['source-ip'].keys():
                                    _local_q = address_mongo.find(
                                        query_dict={'hostip': self.hostip, 'name': i['source-ip']['address-set']},
                                        fileds={'_id': 0})
                                    if _local_q:
                                        _items = _local_q[0]['elements']
                                        if isinstance(_items, dict):
                                            _items = [_items]
                                        for _item in _items:
                                            if 'address-ipv4' in _item.keys():
                                                local_ip += [dict(start=_item['address-ipv4'],
                                                                  end=_item['address-ipv4'],
                                                                  start_int=IPNetwork(
                                                                      _item['address-ipv4']).first,
                                                                  end_int=IPNetwork(
                                                                      _item['address-ipv4']).last,
                                                                  result=_item['address-ipv4'] + '-' + _item[
                                                                      'address-ipv4'])]
                                            if 'start-ipv4' in _item.keys():
                                                local_ip += [dict(start=_item['start-ipv4'],
                                                                  end=_item['end-ipv4'],
                                                                  start_int=IPAddress(
                                                                      _item['start-ipv4']).value,
                                                                  end_int=IPAddress(
                                                                      _item['end-ipv4']).value,
                                                                  result=_item['start-ipv4'] + '-' + _item['end-ipv4'])]

                                if 'address-ipv4' in i['source-ip'].keys():
                                    pass
                            # 目的地址
                            if i.get('destination-ip'):
                                if 'address-set' in i['destination-ip'].keys():
                                    _local_q = address_mongo.find(
                                        query_dict={'hostip': self.hostip, 'name': i['destination-ip']['address-set']},
                                        fileds={'_id': 0})
                                    if _local_q:
                                        _items = _local_q[0]['elements']
                                        if isinstance(_items, dict):
                                            _items = [_items]
                                        for _item in _items:
                                            if 'address-ipv4' in _item.keys():
                                                destination_ip += [dict(start=_item['address-ipv4'],
                                                                        end=_item['address-ipv4'],
                                                                        start_int=IPNetwork(
                                                                            _item['address-ipv4']).first,
                                                                        end_int=IPNetwork(
                                                                            _item['address-ipv4']).last,
                                                                        result=_item['address-ipv4'] + '-' + _item[
                                                                            'address-ipv4'])]
                                            if 'start-ipv4' in _item.keys():
                                                destination_ip += [dict(start=_item['start-ipv4'],
                                                                        end=_item['end-ipv4'],
                                                                        start_int=IPAddress(
                                                                            _item['start-ipv4']).value,
                                                                        end_int=IPAddress(
                                                                            _item['end-ipv4']).value,
                                                                        result=_item['start-ipv4'] + '-' + _item[
                                                                            'end-ipv4'])]
                            # 服务
                            if i.get('service'):
                                if 'service-object' in i['service'].keys():
                                    objs = i['service']['service-object']
                                    if isinstance(objs, str):
                                        objs = [objs]
                                    for obj in objs:
                                        if obj in self.service_set.keys():
                                            service_obj = self.service_set[obj]
                                            if 'items' in service_obj.keys():
                                                if isinstance(service_obj['items'], dict):
                                                    self.service_set[obj]['items'] = [self.service_set[obj]['items']]
                                                for item in self.service_set[obj]['items']:
                                                    if 'tcp' in item.keys():
                                                        destination_port += [dict(
                                                            start=int(item['dest-port']['start']),
                                                            end=int(item['dest-port']['end']),
                                                            protocol='tcp',
                                                            result='tcp_{}_{}'.format(
                                                                item['dest-port']['start'], item['dest-port']['end'])
                                                        )]
                                                    elif 'udp' in item.keys():
                                                        destination_port += [dict(
                                                            start=int(item['dest-port']['start']),
                                                            end=int(item['dest-port']['end']),
                                                            protocol='udp',
                                                            result='udp_{}_{}'.format(
                                                                item['dest-port']['start'], item['dest-port']['end'])
                                                        )]
                                                    else:
                                                        destination_port += [dict(
                                                            start=0,
                                                            end=0,
                                                            protocol=service_obj['name'],
                                                            result=service_obj['name']
                                                        )]
                                            else:
                                                # 系统预定义服务
                                                destination_port += [dict(
                                                    start=0,
                                                    end=0,
                                                    protocol=service_obj['name'],
                                                    result=service_obj['name']
                                                )]
                                        else:
                                            # 没有对应的服务对象
                                            pass
                                if 'service-items' in i['service'].keys():
                                    pass
                                    # if isinstance(i['service']['service-items'], dict):
                                    #     for key in i['service']['service-items'].keys():
                                    #         if key in ['tcp', 'udp']:
                                    #             if isinstance(
                                    #                     i['service']['service-items'][key], list):
                                    #                 for item in i['service']['service-items'][key]:
                                    #                     _src_port = item['source-port']
                                    #                     _dst_port = item['dest-port']
                                    #                     if _src_port.find('to') != -1:
                                    #                         _src_port = _src_port.split('to')
                                    #                     if _dst_port.find('to') != -1:
                                    #                         _dst_port = _dst_port.split('to')
                                    #                     service.append(dict(item={
                                    #                         "Type": key,
                                    #                         "StartSrcPort": _src_port[0].strip() if isinstance(
                                    #                             _src_port,
                                    #                             list) else _src_port,
                                    #                         "EndSrcPort": _src_port[1].strip() if isinstance(_src_port,
                                    #                                                                          list) else _src_port,
                                    #                         "StartDestPort": _dst_port[1].strip() if isinstance(
                                    #                             _dst_port,
                                    #                             list) else _dst_port,
                                    #                         "EndDestPort": _dst_port[1].strip() if isinstance(_dst_port,
                                    #                                                                           list) else _dst_port,
                                    #                     }))
                                    #             elif isinstance(i['service']['service-items'][key], dict):
                                    #                 _src_port = i['service']['service-items'][key]['source-port']
                                    #                 _dst_port = i['service']['service-items'][key]['dest-port']
                                    #                 if _src_port.find('to') != -1:
                                    #                     _src_port = _src_port.split('to')
                                    #                 if _dst_port.find('to') != -1:
                                    #                     _dst_port = _dst_port.split('to')
                                    #                 service.append(dict(item={
                                    #                     "Type": key,
                                    #                     "StartSrcPort": _src_port[0].strip() if isinstance(_src_port,
                                    #                                                                        list) else _src_port,
                                    #                     "EndSrcPort": _src_port[1].strip() if isinstance(_src_port,
                                    #                                                                      list) else _src_port,
                                    #                     "StartDestPort": _dst_port[1].strip() if isinstance(_dst_port,
                                    #                                                                         list) else _dst_port,
                                    #                     "EndDestPort": _dst_port[1].strip() if isinstance(_dst_port,
                                    #                                                                       list) else _dst_port,
                                    #                 }))
                                    #         if key == 'icmp-item':
                                    #             if isinstance(
                                    #                     i['service']['service-items'][key], list):
                                    #                 for item in i['service']['service-items'][key]:
                                    #                     service.append(dict(item={
                                    #                         "Type": "icmp",
                                    #                     }))
                                    #             elif isinstance(i['service']['service-items'][key], dict):
                                    #                 service.append(dict(item={
                                    #                     "Type": "icmp",
                                    #                 }))
                            # 出公网IP 转换成公网地址池
                            if action is not None:
                                if action == 'nat-address-group' and i.get('nat-address-group'):
                                    _global_q = nat_address_mongo.find(
                                        query_dict={'hostip': self.hostip, 'name': i['nat-address-group']},
                                        fileds={'_id': 0})
                                    if _global_q:
                                        _items = _global_q[0]['section']
                                        if isinstance(_items, dict):
                                            _items = [_items]
                                        for _item in _items:
                                            trans_ip += [dict(start=_item['start-ip'],
                                                              end=_item['end-ip'],
                                                              start_int=IPAddress(
                                                                  _item['start-ip']).value,
                                                              end_int=IPAddress(
                                                                  _item['end-ip']).value,
                                                              result=_item['start-ip'] + '-' + _item['end-ip'])]
                                # 转换成出接口IP
                                elif action == 'easyip':
                                    pass
                            tmp = dict(
                                rule_id=i['name'],
                                hostip=self.hostip,
                                trans_ip=trans_ip,
                                local_ip=local_ip,
                                destination_ip=destination_ip,
                                destination_port=destination_port,
                                source_zone=i.get('source-zone', ''),
                                destination_zone=i.get('destination-zone', ''),
                                model=action,
                                log_time=datetime.now()
                            )
                            self.snat_data.append(tmp)
                MongoNetOps.insert_table(
                    db='NETCONF',
                    hostip=self.hostip,
                    datas=nat_policy,
                    tablename='huawei_usg_nat_policy')
        except Exception as e:
            # print(traceback.print_exc())
            send_msg_netops("设备:{}\nSNAT解析失败\n{}".format(self.hostip, str(e)))

    # DNAT
    def _netconf_usg_nat_server(self, nat_server):
        if nat_server:
            protocol_map = {
                "1": "icmp",
                "6": "tcp",
                "17": "udp",
            }
            for i in nat_server:
                i['hostip'] = self.hostip
                # DNAT表项拼接
                global_ip = i['global'].get(
                    'start-ip') if 'global' in i.keys() else ''
                global_port = i['global-port'].get(
                    'start-port') if 'global-port' in i.keys() else ''
                local_ip = i['inside'].get(
                    'start-ip') if 'inside' in i.keys() else ''
                local_port = i['inside-port'].get(
                    'start-port') if 'inside-port' in i.keys() else ''
                # 一对一转换
                if 'protocol' not in i.keys():
                    protocol = 'any'
                # 协议端口转换
                else:
                    protocol = protocol_map[i['protocol']] if i['protocol'] in protocol_map.keys(
                    ) else i['protocol']
                tmp = dict(
                    hostip=self.hostip,
                    name=i.get('name'),
                    global_ip=[
                        dict(start=global_ip,
                             end=global_ip,
                             start_int=IPAddress(global_ip).value,
                             end_int=IPAddress(global_ip).value,
                             result=global_ip
                             )],
                    global_port=[dict(
                        start=int(global_port) if global_port else 0,
                        end=int(global_port) if global_port else 65535,
                        protocol=protocol,
                        result=str(global_port) if global_port else '0-65535'
                    )],
                    local_ip=[
                        dict(start=local_ip,
                             end=local_ip,
                             start_int=IPAddress(local_ip).value,
                             end_int=IPAddress(local_ip).value,
                             result=local_ip
                             )],
                    local_port=[dict(
                        start=int(local_port) if local_port else 0,
                        end=int(local_port) if local_port else 65535,
                        protocol=protocol,
                        result=str(local_port) if local_port else '0-65535'
                    )]
                )
                self.dnat_data.append(tmp)

            MongoNetOps.insert_table(db='NETCONF', hostip=self.hostip, datas=nat_server,
                                     tablename='huawei_usg_nat_server')

    # NAT地址池
    def _netconf_usg_nat_address_group(self, nat_address):
        """
        NAT地址池
        :param nat_address:
        :return:
        """
        if nat_address:
            for i in nat_address:
                i['hostip'] = self.hostip
            MongoNetOps.insert_table(db='NETCONF', hostip=self.hostip, datas=nat_address,
                                     tablename='huawei_usg_nat_address')

    # 地址对象
    def _netconf_usg_address_set(self, address_set):
        if address_set:
            for i in address_set:
                i['hostip'] = self.hostip
            MongoNetOps.insert_table(db='NETCONF', hostip=self.hostip, datas=address_set,
                                     tablename='huawei_usg_address_set')

    def _netconf_usg_slb_info(self, slb_pool):
        if slb_pool:
            for i in slb_pool:
                i['hostip'] = self.hostip
            MongoNetOps.insert_table(db='NETCONF', hostip=self.hostip, datas=slb_pool,
                                     tablename='huawei_usg_slb_pool')

    def _netconf_usg_service_set(self, res):
        if res:
            for i in res:
                self.service_set[i['name']] = i
                i['hostip'] = self.hostip
            MongoNetOps.insert_table(db='NETCONF', hostip=self.hostip, datas=res,
                                     tablename='huawei_usg_service_set')

    def _netconf_usg_trunk_lacp(self, aggr_res):
        if aggr_res:
            aggre_datas = []
            for i in aggr_res:
                if i['name'].startswith('Eth-Trunk'):
                    tmp = dict(
                        hostip=self.hostip,
                        aggregroup=i['name'],
                        memberports=i['hw-eth-trunk:eth-trunk'].get(
                            'hw-eth-trunk:assign-interface'),
                        status='',
                        mode=''
                    )
                    aggre_datas.append(tmp)
            if aggre_datas:
                MongoNetOps.insert_table(
                    'Automation', self.hostip, aggre_datas, 'AggreTable')

    def _netconf_usg_sec_policy(self, sec_policy_res):
        if sec_policy_res:
            sec_policy_rule = sec_policy_res['static-policy']['rule']
            sec_policy_result = []
            if sec_policy_rule:
                for i in sec_policy_rule:
                    i['hostip'] = self.hostip
                    sec_policy_result.append(i)
            if sec_policy_result:
                # 格式化落库
                self.huawei_usg_sec_policy(sec_policy_result)
                # 原始数据格式落库
                MongoNetOps.insert_table(db='NETCONF', hostip=self.hostip, datas=sec_policy_result,
                                         tablename='huawei_sec_policy')

    # 安全策略分析
    def _netconf_usg_sec_policy_counting(self, sec_policy_counting):
        if sec_policy_counting:
            for i in sec_policy_counting['vsys']['static-policy']['rule']:
                # {'name': 'REQ20220413000053', 'hit-times': '4'}
                i['hostip'] = self.hostip
            MongoNetOps.insert_table(
                db='NETCONF',
                hostip=self.hostip,
                datas=sec_policy_counting['vsys']['static-policy']['rule'],
                tablename='sec_policy_counting')
        return

    def _netconf_method_map(self, method, res):
        ntf_map = {
            "colleciton_system_info": self._netconf_ce_system_info,
            "colleciton_moduleinfo": self._netconf_moduleinfo,
            "colleciton_stack": self._netconf_stack,
            "collection_intf_ipv4v6": self._netconf_intf_ipv4v6,
            "colleciton_arp_list": self._netconf_arp_list,
            "collection_mac_bd": self._netconf_mac_bd,
            "collection_mac_vxlan": self._netconf_mac_vxlan,
            "collection_mac_vxlan_control": self._netconf_mac_vxlan_control,
            "collection_mac_table": self._netconf_mac_table,
            "collection_lldp_ip": self._netconf_lldp,
            "colleciton_trunk_lacp": self._netconf_lldp,
            "get_system_info": self._netcocnf_system_info,
            "get_interface_list": self._netcocnf_system_info,
            "get_vrrp_info": self._netcocnf_system_info,
            "get_hrp_state": self._netconf_usg_hrp_state,
            "get_nat_policy": self._netconf_usg_nat_policy,
            "get_nat_server": self._netconf_usg_nat_server,
            "get_nat_address": self._netconf_usg_nat_address_group,
            "get_address_set": self._netconf_usg_address_set,
            "get_slb_info": self._netconf_usg_slb_info,
            "get_service_set": self._netconf_usg_service_set,
            "get_trunk_lacp": self._netconf_usg_trunk_lacp,
            "get_sec_policy": self._netconf_usg_sec_policy,
            "get_sec_policy_counting": self._netconf_usg_sec_policy_counting,
        }
        if callable(ntf_map[method]):
            return ntf_map[method](res)
        else:
            send_msg_netops("设备:{}\n方法:{}\n不被解析".format(self.hostip, method))

    # 根据采集清单执行
    def collection_run(self):
        # 先执行父类方法
        super(HuaweiProc, self).collection_run()
        if self.netconf_class:
            if self.netconf_flag == 'huawei_usg':
                device = HuaweiUSG(host=self.netconf_params['ip'],
                                   user=self.netconf_params['username'],
                                   password=self.netconf_params['password'],
                                   timeout=600)
            else:
                device = HuaweiCollection(host=self.netconf_params['ip'],
                                          user=self.netconf_params['username'],
                                          password=self.netconf_params['password'],
                                          timeout=600)
            methods = json.loads(self.plan['netconf_method'])
            if methods:
                for method in methods:
                    # print("开始执行{}方法".format(method))
                    class_method = getattr(device, method, None)
                    if class_method:
                        try:
                            res = class_method()
                            # print("netconf_method:{} ==> res:{}".format(method, str(res)))
                            if res:
                                self._netconf_method_map(method, res)
                        except Exception as e:
                            send_msg_netops("设备:{}\nnetconf方法:{}\n不被设备支持\n{}".format(self.hostip, method, str(e)))
            if self.layer3datas:
                MongoNetOps.insert_table(db='Automation', hostip=self.hostip, datas=self.layer3datas,
                                         tablename='layer3interface')
            if self.dnat_data:
                MongoNetOps.insert_table(db='Automation', hostip=self.hostip, datas=self.dnat_data,
                                         tablename='DNAT')
            if self.snat_data:
                MongoNetOps.insert_table(db='Automation', hostip=self.hostip, datas=self.snat_data,
                                         tablename='SNAT')
            device.closed()

    # netconf执行手动任务
    def manual_netconf_run(self, method):
        # print('执行netconf采集')
        if self.netconf_flag == 'huawei_usg':
            device = HuaweiUSG(host=self.netconf_params['ip'],
                               user=self.netconf_params['username'],
                               password=self.netconf_params['password'],
                               timeout=600)
        else:
            device = HuaweiCollection(host=self.netconf_params['ip'],
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
                print(str(e))
        else:
            send_msg_netops("设备:{}\nnetconf方法:{}\n不被设备支持\n".format(self.hostip, method))
        if self.layer3datas:
            MongoNetOps.insert_table(db='Automation', hostip=self.hostip, datas=self.layer3datas,
                                     tablename='layer3interface')
        if self.dnat_data:
            MongoNetOps.insert_table(db='Automation', hostip=self.hostip, datas=self.dnat_data,
                                     tablename='DNAT')
        if self.snat_data:
            MongoNetOps.insert_table(db='Automation', hostip=self.hostip, datas=self.snat_data,
                                     tablename='SNAT')
        device.closed()
