# -*- coding: utf-8 -*-
# @Time    : 2022/4/14 16:01
# @Author  : jmli12
# @Site    :
# @File    : cisco.py
# @Software: PyCharm
import re
from datetime import datetime

from netaddr import IPNetwork

from apps.asset.models import NetworkDevice, Model, Vendor
from utils.connect_layer.auto_main import BatManMain
from utils.db.mongo_ops import MongoNetOps
from utils.wechat_api import send_msg_netops
from .base_connection import BaseConn, InterfaceFormat


def cisco_interface_format(interface):
    if re.search(r'^(Gi)', interface):
        return interface.replace('Gi', 'GigabitEthernet0')

    return interface


class CiscoProc(BaseConn):
    """
    show ip arp
    show mac
    show ip interface brief
    show interfaces status
    show aggregatePort summary
    show version
    show switch virtual
    show member
    """

    def arp_proc(self, res):
        arp_datas = []
        for i in res:
            try:
                macaddress = i['mac'].replace('.', '-')
            except Exception as e:
                macaddress = i.get('mac', '')
                pass
            tmp = dict(
                hostip=self.hostip,
                hostname=self.hostname,
                idc_name=self.idc_name,
                ipaddress=i['address'],
                macaddress=macaddress,
                aging=i['age'],
                type=i['type'],
                vlan=i.get('vlan', ''),
                interface=i['interface'].strip(),
                vpninstance='',
                log_time=datetime.now()
            )
            arp_datas.append(tmp)
        if arp_datas:
            MongoNetOps.insert_table(
                'Automation', self.hostip, arp_datas, 'ARPTable')

    def mac_proc(self, res):
        if isinstance(res, list):
            mac_datas = []
            for i in res:
                try:
                    macaddress = i['destination_address'].replace('.', '-')
                except Exception as e:
                    macaddress = i.get('destination_address', '')
                    pass
                tmp = dict(
                    hostip=self.hostip,
                    hostname=self.hostname,
                    idc_name=self.idc_name,
                    macaddress=macaddress,
                    vlan=i['vlan'],
                    interface=cisco_interface_format(i['destination_port'].strip()),
                    type=i['type'].lower(),
                    log_time=datetime.now()
                )
                mac_datas.append(tmp)
            if mac_datas:
                MongoNetOps.insert_table(
                    'Automation', self.hostip, mac_datas, 'MACTable')

    def interface_proc(self, res):
        layer2datas = []
        layer3datas = []
        for i in res:
            if i['ip_address']:
                _ip = IPNetwork(i['ip_address'])
                location = [dict(start=_ip.first, end=_ip.last)]
                data = dict(
                    hostip=self.hostip,
                    interface=i['interface'],
                    line_status=i['link_status'],
                    protocol_status=i['protocol_status'],
                    ipaddress=_ip.ip.format(),
                    ipmask=_ip.netmask.format(),
                    ip_type='Primary',
                    location=location,
                    mtu='')
                layer3datas.append(data)
            else:
                if i['interface'].startswith('AggregatePort'):
                    continue
                i['speed'] = InterfaceFormat.cisco_speed_format(i['interface'])
                data = dict(hostip=self.hostip,
                            interface=i['interface'],
                            status=i['link_status'],
                            speed=i['speed'],
                            duplex=i['duplex'].strip('-duplex'),
                            description=i.get('description'))
                layer2datas.append(data)
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

    def version_proc(self, res):
        if isinstance(res, dict):
            """
            {'member': '1', 'serialnum': 'G1GC10V000176'}
            """
            model_name = res['hardware'][1:-1]
            model_q = Model.objects.get_or_create(name=model_name,
                                                  vendor=Vendor.objects.get(alias='Cisco'))
            NetworkDevice.objects.filter(
                manage_ip=self.hostip).update(model=model_q[0])
            NetworkDevice.objects.filter(
                manage_ip=self.hostip).update(serial_num=res['serial'][1:-1],
                                              slot=int(res['member']), soft_version=res['version'])

    def path_map(self, file_name, res: list):
        fsm_map = {
            'show_ip_arp': self.arp_proc,
            'show_mac-address-table': self.mac_proc,
            'show_interfaces': self.interface_proc,
            'show_version': self.version_proc,
        }
        if file_name in fsm_map.keys():
            fsm_map[file_name](res)
        else:
            send_msg_netops("设备:{}\n命令:{}\n不被解析".format(self.hostip, file_name))

    def _collection_analysis(self, paths: list):
        for path in paths:
            res = BatManMain.info_fsm(path=path['path'], fsm_platform=self.fsm_flag)
            self.path_map(path['cmd_file'], res)
