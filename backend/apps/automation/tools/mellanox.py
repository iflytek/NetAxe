# -*- coding: utf-8 -*-
# @Time    : 2022/4/14 16:01
# @Author  : jmli12
# @Site    :
# @File    : mellanox.py
# @Software: PyCharm
from datetime import datetime
from netaddr import IPNetwork
from .base_connection import BaseConn
from utils.connect_layer.auto_main import BatManMain
from utils.db.mongo_ops import MongoNetOps
from utils.wechat_api import send_msg_netops


class MellanoxProc(BaseConn):
    """
    show ip interface brief
    show ip arp
    show mac-address-table
    show interface port-channel summary
    show interfaces
    """

    def arp_proc(self, res):
        arp_datas = []
        for i in res:
            try:
                tmp = i['macaddress'].split(':')
                macaddress = tmp[0] + tmp[1] + '-' + \
                             tmp[2] + tmp[3] + '-' + tmp[4] + tmp[5]
            except Exception as e:
                macaddress = i.get('macaddress')
            tmp = dict(
                hostip=self.hostip,
                hostname=self.hostname,
                idc_name=self.idc_name,
                ipaddress=i['ipaddr'],
                macaddress=macaddress.lower(),
                aging='',
                type=i['type'],
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
        if isinstance(res, list):
            mac_datas = []
            for i in res:
                try:
                    tmp = i['macaddress'].split(':')
                    macaddress = tmp[0] + tmp[1] + '-' + \
                                 tmp[2] + tmp[3] + '-' + tmp[4] + tmp[5]
                except Exception as e:
                    macaddress = i.get('macaddress')
                    pass
                tmp = dict(
                    hostip=self.hostip,
                    hostname=self.hostname,
                    idc_name=self.idc_name,
                    macaddress=macaddress.lower(),
                    vlan=i['vlan'],
                    interface=i['interface'],
                    type=i['type'],
                    log_time=datetime.now()
                )
                mac_datas.append(tmp)
            if mac_datas:
                MongoNetOps.insert_table(
                    'Automation', self.hostip, mac_datas, 'MACTable')

    def ip_interface_proc(self, res):
        layer3datas = []
        for i in res:
            if i['ipaddr'] != 'Unassigned':
                _ip = IPNetwork(i['ipaddr'])
                location = [dict(start=_ip.first, end=_ip.last)]
                data = dict(
                    hostip=self.hostip,
                    interface=i['interface'],
                    line_status=i['operstate'],
                    protocol_status='',
                    ipaddress=_ip.ip.format(),
                    ipmask=_ip.netmask.format(),
                    ip_type=i['primary'], location=location,
                    mtu=i['mtu']
                )
                layer3datas.append(data)
        if layer3datas:
            MongoNetOps.insert_table(
                db='Automation',
                hostip=self.hostip,
                datas=layer3datas,
                tablename='layer3interface')
        return

    def aggre_port_proc(self, res):
        if isinstance(res, list):
            aggre_datas = []
            for i in res:
                try:
                    memberports = []
                    tmp_members = i['memberports'].split()
                    for member in tmp_members:
                        memberports.append(member.split('(')[0])
                except Exception as e:
                    memberports = i['memberports'].split()
                tmp = dict(
                    hostip=self.hostip,
                    aggregroup=i['portchannel'],
                    memberports=memberports,
                    status='',
                    mode=i.get('type')
                )
                aggre_datas.append(tmp)
            if aggre_datas:
                MongoNetOps.insert_table(
                    'Automation', self.hostip, aggre_datas, 'AggreTable')

    def mellanox_interface(self, res):
        result = []
        """
        """
        layer3datas = []
        layer2datas = []
        for i in res:
            i['hostip'] = self.hostip
            if i['interface'].startswith('mgmt'):
                continue
            if i['interface'].startswith('lo'):
                continue
            data = dict(hostip=self.hostip,
                        interface=i['interface'],
                        status=i['operationalstate'].lower(),
                        speed=i['advertisedspeeds'],
                        # advertisedspeeds  actualspeed 100G  40G
                        duplex='',
                        description=i['description'])
            layer2datas.append(data)
            result.append(i)
        if result:
            MongoNetOps.insert_table(
                'Automation', self.hostip, result, 'mellanox_interface')
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
            'show_mac-address-table': self.mac_proc,
            'show_interface_port-channel_summary': self.aggre_port_proc,
            'show_ip_interface_brief': self.ip_interface_proc,
            'show_interfaces': self.mellanox_interface,
        }
        if file_name in fsm_map.keys():
            fsm_map[file_name](res)
        else:
            send_msg_netops("设备:{}\n命令:{}\n不被解析".format(self.hostip, file_name))

    def _collection_analysis(self, paths: list):
        # self.cmds += ['display mac-address']
        for path in paths:
            res = BatManMain.info_fsm(path=path['path'], fsm_platform=self.fsm_flag)
            self.path_map(path['cmd_file'], res)
