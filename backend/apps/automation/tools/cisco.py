# -*- coding: utf-8 -*-
# @Time    : 2022/4/14 16:01
# @Author  : jmli12
# @Site    :
# @File    : cisco.py
# @Software: PyCharm
import re
import json
from datetime import datetime

from netaddr import IPNetwork
from django.core.cache import cache
from apps.asset.models import NetworkDevice, Model, Vendor
from utils.connect_layer.auto_main import BatManMain
from utils.db.mongo_ops import MongoNetOps
from utils.wechat_api import send_msg_netops
from .base_connection import BaseConn, InterfaceFormat


def cisco_interface_format(interface):
    if re.search(r'^(Gi)', interface):
        return interface.replace('Gi', 'GigabitEthernet')

    return interface


class CiscoProc(BaseConn):
    """
    """

    def __init__(self, **kwargs):
        super(CiscoProc, self).__init__(**kwargs)
        self.lldp_datas = []

    def _arp_proc(self, res):
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

    def _mac_proc(self, res):
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

    def _interface_proc(self, res):
        layer2datas = []
        layer3datas = []
        int_regex = re.compile('^\w+[\d\/]+$')
        exclude_regex = re.compile('^((?!(Serial|Embedded|NVI|Virtual|Vlan|Loopback|Tunnel)).)*$')
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
        for i in res:
            # 排除一些接口列表并且接口名称不包含子接口
            if exclude_regex.search(i['interface']) and int_regex.search(i['interface']):
                duplex = 'auto'
                if 'Auto' in i['duplex']:
                    duplex = 'auto'
                elif 'Full' in i['duplex']:
                    duplex = 'full'
                elif 'Half' in i['duplex']:
                    duplex = 'half'
                data = dict(hostip=self.hostip,
                            interface=i['interface'],
                            status=i['link_status'],
                            speed=InterfaceFormat.cisco_speed_format(i['interface']),
                            duplex=duplex,
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

    def _version_proc(self, res):
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

    def _lldp_proc(self, res):
        """
        {'neighbor': 'ic-ofce-sw', 'local_interface': 'Gi0/0/1', 'capabilities': 'B', 'neighbor_interface': 'GigabitEthernet0/0/24'}
        """
        if not res or isinstance(res, str):
            return
        if isinstance(res, dict):
            res = [res]
        for i in res:
            neighbor_ip = ''
            if i['neighbor']:
                tmp_neighbor_ip = cache.get('cmdb_' + i['neighbor'])
                if tmp_neighbor_ip:
                    tmp_neighbor_ip = json.loads(tmp_neighbor_ip)
                    neighbor_ip = tmp_neighbor_ip[0]['manage_ip']
                else:
                    tmp_neighbor_ip = NetworkDevice.objects.filter(
                        name=i['neighbor']).values('manage_ip')
                    neighbor_ip = tmp_neighbor_ip[0]['manage_ip'] if tmp_neighbor_ip else ''
            tmp = dict(
                hostip=self.hostip,
                local_interface=cisco_interface_format(i['local_interface']),
                chassis_id='',
                neighbor_port=i['neighbor_port_id'],
                portdescription='',
                neighborsysname=i['neighbor'],
                management_ip=i.get('management_ip', ''),
                management_type='ipv4',
                neighbor_ip=neighbor_ip
            )
            self.lldp_datas.append(tmp)

    def _cdp_proc(self, res):
        if not res or isinstance(res, str):
            return
        if isinstance(res, dict):
            res = [res]
        for i in res:
            neighbor_ip = ''
            if i['destination_host']:
                tmp_neighbor_ip = cache.get('cmdb_' + i['destination_host'])
                if tmp_neighbor_ip:
                    tmp_neighbor_ip = json.loads(tmp_neighbor_ip)
                    neighbor_ip = tmp_neighbor_ip[0]['manage_ip']
                else:
                    tmp_neighbor_ip = NetworkDevice.objects.filter(
                        name=i['destination_host']).values('manage_ip')
                    neighbor_ip = tmp_neighbor_ip[0]['manage_ip'] if tmp_neighbor_ip else ''
            tmp = dict(
                hostip=self.hostip,
                local_interface=i['local_port'],
                chassis_id='',
                neighbor_port=i['remote_port'],
                portdescription='',
                neighborsysname=i['destination_host'],
                management_ip=i.get('management_ip'),
                management_type='CDP',
                neighbor_ip=neighbor_ip
            )
            self.lldp_datas.append(tmp)

    def path_map(self, file_name, res: list):
        fsm_map = {
            'show_ip_arp': self._arp_proc,
            'show_mac-address-table': self._mac_proc,
            'show_interfaces': self._interface_proc,
            'show_version': self._version_proc,
            'show_lldp_neighbors_detail': self._lldp_proc,
            'show_cdp_neighbors_detail': self._cdp_proc,
        }
        if file_name in fsm_map.keys():
            fsm_map[file_name](res)
        else:
            send_msg_netops("设备:{}\n命令:{}\n不被解析".format(self.hostip, file_name))

    def collection_run(self):
        # 先执行父类方法
        super(CiscoProc, self).collection_run()
        if self.lldp_datas:
            MongoNetOps.insert_table(
                'Automation', self.hostip, self.lldp_datas, 'LLDPTable')

    def _collection_analysis(self, paths: list):
        for path in paths:
            res = BatManMain.info_fsm(path=path['path'], fsm_platform=self.fsm_flag)
            self.path_map(path['cmd_file'], res)
