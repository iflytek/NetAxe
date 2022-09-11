# -*- coding: utf-8 -*-
# @Time    : 2022/4/14 16:01
# @Author  : jmli12
# @Site    :
# @File    : centec.py
# @Software: PyCharm
from datetime import datetime
from netaddr import IPNetwork
from .base_connection import BaseConn, InterfaceFormat
from utils.connect_layer.auto_main import BatManMain
from utils.db.mongo_ops import MongoNetOps
from utils.wechat_api import send_msg_netops


class CentecProc(BaseConn):
    """
    show ip arp
    show mac address-table
    show ip interface brief
    show interface status
    show channel-group summary
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
                ipaddress=i['ip'],
                macaddress=macaddress,
                aging=i['age'],
                type='',
                vlan='',
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
                macaddress=macaddress,
                vlan=i['vlan'],
                interface=i['ports'].strip(),
                type=i['type'].lower(),
                log_time=datetime.now()
            )
            mac_datas.append(tmp)
        if mac_datas:
            MongoNetOps.insert_table(
                'Automation', self.hostip, mac_datas, 'MACTable')

    def ip_interface_proc(self, res):
        layer3datas = []
        for i in res:
            data = dict(
                hostip=self.hostip,
                interface=i['interface'],
                line_status=i['status'],
                protocol_status=i['protocol'],
                ipaddress=i['ip'],
                ip_type='',
                mtu='')
            layer3datas.append(data)
        if layer3datas:
            MongoNetOps.insert_table(
                db='Automation',
                hostip=self.hostip,
                datas=layer3datas,
                tablename='layer3interface')
        return

    def aggre_port_proc(self, res):
        """盛科的聚合口没有做解析"""
        pass

    def interface_status_proc(self, res):
        layer2datas = []
        for i in res:
            speed = i['speed']
            if i['speed'].startswith('a-'):
                speed = i['speed'].split('a-')[1]
            data = dict(hostip=self.hostip,
                        interface=i['interface'],
                        status=i['status'],
                        speed=InterfaceFormat.mathintspeed(speed),
                        duplex=i['duplex'],
                        description=i.get('description'))
            layer2datas.append(data)
        if layer2datas:
            MongoNetOps.insert_table(
                db='Automation',
                hostip=self.hostip,
                datas=layer2datas,
                tablename='layer2interface')
        return

    def path_map(self, file_name, res: list):
        fsm_map = {
            'show_ip_arp': self.arp_proc,
            'show_mac_address-table': self.mac_proc,
            'show_ip_interface_brief': self.ip_interface_proc,
            'show_interface_status': self.interface_status_proc,
            'show_channel-group_summary': self.aggre_port_proc,
        }
        if file_name in fsm_map.keys():
            fsm_map[file_name](res)
        else:
            send_msg_netops("设备:{}\n命令:{}\n不被解析".format(self.hostip, file_name))

    def _collection_analysis(self, paths: list):
        for path in paths:
            res = BatManMain.info_fsm(path=path['path'], fsm_platform=self.fsm_flag)
            self.path_map(path['cmd_file'], res)
