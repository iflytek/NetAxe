# -*- coding: utf-8 -*-
# @Time    : 2022/4/14 16:01
# @Author  : jmli12
# @Site    :
# @File    : maipu.py
# @Software: PyCharm
import json
from datetime import datetime
from netaddr import IPNetwork
from django.core.cache import cache
from .base_connection import BaseConn, InterfaceFormat
from utils.connect_layer.auto_main import BatManMain
from apps.asset.models import NetworkDevice
from utils.db.mongo_ops import MongoNetOps
from utils.wechat_api import send_msg_netops


class MaipuProc(BaseConn):
    """
    show arp
    show mac-address all
    show system version brief
    show interface
    show link-aggregation interface
    show lldp neighbors
    """

    def arp_proc(self, res):
        arp_datas = []
        for i in res:
            try:
                macaddress = i['macaddress'].replace('.', '-')
            except Exception as e:
                macaddress = i.get('macaddress')
                pass
            tmp = dict(
                hostip=self.hostip,
                hostname=self.hostname,
                idc_name=self.idc_name,
                ipaddress=i['ipaddress'],
                macaddress=macaddress.lower(),
                aging=i['age'],
                type=i['type'],
                vlan=i['vlan'],
                interface=i['interface'],
                vpninstance='',
                log_time=datetime.now()
            )
            arp_datas.append(tmp)
        if arp_datas:
            MongoNetOps.insert_table(
                'Automation', self.hostip, arp_datas, 'ARPTable')

    def mac_proc(self, res):
        mac_datas = []
        for i in res:
            try:
                macaddress = i['macaddress'].replace('.', '-')
            except Exception as e:
                macaddress = i.get('macaddress')
                pass
            tmp = dict(
                hostip=self.hostip,
                hostname=self.hostname,
                idc_name=self.idc_name,
                macaddress=macaddress.lower(),
                vlan=i['vlan'],
                interface=i['interface'].strip(),
                type=i['type'].lower(),
                log_time=datetime.now()
            )
            mac_datas.append(tmp)
        if mac_datas:
            MongoNetOps.insert_table(
                'Automation', self.hostip, mac_datas, 'MACTable')

    def interface_proc(self, res):
        layer3datas = []
        layer2datas = []
        for i in res:
            speed = i['speed']
            if speed == '1000 M':
                speed = '1G'
            elif speed == '10000 M':
                speed = '10G'
            elif speed == '1000M':
                speed = '10G'
            data = dict(hostip=self.hostip,
                        interface=i['interface'],
                        status=i['protocolstatus'],
                        speed=speed,
                        duplex=i['duplex'],
                        description=i['description'])
            layer2datas.append(data)
            if i['ipaddr']:
                for _ip in i['ipaddr']:
                    _ipnet = IPNetwork(_ip)
                    location = [dict(start=_ipnet.first, end=_ipnet.last)]
                    data = dict(
                        hostip=self.hostip,
                        interface=i['interface'],
                        line_status=i['protocolstatus'],
                        protocol_status=i['protocolstatus'],
                        ipaddress=_ipnet.ip.format(),
                        ipmask=_ipnet.netmask.format(),
                        ip_type='', location=location,
                        mtu=i['mtu'])
                    layer3datas.append(data)
        if layer2datas:
            MongoNetOps.insert_table(
                db='Automation',
                hostip=self.hostip,
                datas=layer2datas,
                tablename='layer2interface')
        if layer3datas:
            MongoNetOps.insert_table(
                db='Automation',
                hostip=self.hostip,
                datas=layer3datas,
                tablename='layer3interface')
        return

    def aggre_port_proc(self, res):
        """盛科的聚合口没有做解析"""
        aggre_datas = []
        tmp = {}
        for i in res:
            if i['aggregate'] in tmp.keys():
                tmp[i['aggregate']]['memberports'].append(i['interface'])
                tmp[i['aggregate']]['status'].append(i['selected'])
                tmp[i['aggregate']]['mode'].append(i['mode'])
            else:
                tmp[i['aggregate']] = {
                    'memberports': [i['interface']],
                    'status': [i['selected']],
                    'mode': [i['mode']]
                }
        for i in tmp.keys():
            aggre_datas.append(dict(
                hostip=self.hostip,
                aggregroup=i,
                memberports=tmp[i]['memberports'],
                status=tmp[i]['status'],
                mode=tmp[i]['mode']
            ))
        if aggre_datas:
            MongoNetOps.insert_table(
                'Automation', self.hostip, aggre_datas, 'AggreTable')

    def lldp_proc(self, res):
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
                local_interface=InterfaceFormat.maipu_interface_format(i['local_interface']),
                chassis_id='',
                neighbor_port=i['neighbor_port'],
                portdescription='',
                neighborsysname=i['neighborsysname'],
                management_ip=neighbor_ip,
                management_type='',
                neighbor_ip=neighbor_ip
            )
            lldp_datas.append(tmp)
        if lldp_datas:
            MongoNetOps.insert_table(
                'Automation', self.hostip, lldp_datas, 'LLDPTable')

    # 空处理
    def null_proc(self, res):
        pass

    def path_map(self, file_name, res: list):
        fsm_map = {
            'more_off': self.null_proc,
            'show_arp': self.arp_proc,
            'show_mac-address_all': self.mac_proc,
            'show_system_version_brief': self.null_proc,
            'show_interface': self.interface_proc,
            'show_link-aggregation_interface': self.aggre_port_proc,
            'show_lldp_neighbors': self.lldp_proc,
        }
        if file_name in fsm_map.keys():
            fsm_map[file_name](res)
        else:
            send_msg_netops("设备:{}\n命令:{}\n不被解析".format(self.hostip, file_name))

    def _collection_analysis(self, paths: list):
        for path in paths:
            res = BatManMain.info_fsm(path=path['path'], fsm_platform=self.fsm_flag)
            self.path_map(path['cmd_file'], res)
