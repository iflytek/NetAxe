# -*- coding: utf-8 -*-
# @Time    : 2022/4/14 16:01
# @Author  : jmli12
# @Site    :
# @File    : ruijie.py
# @Software: PyCharm
import re
from datetime import datetime

from netaddr import IPNetwork

from apps.asset.models import NetworkDevice, Model, Vendor
from utils.connect_layer.auto_main import BatManMain
from utils.db.mongo_ops import MongoNetOps
from utils.wechat_api import send_msg_netops
from .base_connection import BaseConn, InterfaceFormat


def ruijie_interface_format(interface):
    if re.search(r'^(Ag)', interface):
        return interface.replace('Ag', 'AggregatePort')
    elif re.search(r'^(Te)', interface):
        return interface.replace('Te', 'TenGigabitEthernetn')

    return interface


class RuijieProc(BaseConn):
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
                macaddress = i['hardware'].replace('.', '-')
            except Exception as e:
                macaddress = i.get('hardware', '')
                pass
            tmp = dict(
                hostip=self.hostip,
                hostname=self.hostname,
                idc_name=self.idc_name,
                ipaddress=i['address'],
                macaddress=macaddress,
                aging=i['agemin'],
                type=i['type'],
                vlan=i.get('vlan'),
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
                    interface=i['interface'].strip(),
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
            if i['priipaddr'] != 'no address':
                _ip = IPNetwork(i['priipaddr'])
                location = [dict(start=_ip.first, end=_ip.last)]
                data = dict(
                    hostip=self.hostip,
                    interface=i['interface'],
                    line_status=i['status'],
                    protocol_status=i['protocol'],
                    ipaddress=_ip.ip.format(),
                    ipmask=_ip.netmask.format(),
                    ip_type='Primary',
                    location=location,
                    mtu='')
                layer3datas.append(data)
            elif i['secipaddr'] != 'no address':
                _ip = IPNetwork(i['priipaddr'])
                location = [dict(start=_ip.first, end=_ip.last)]
                data = dict(
                    hostip=self.hostip,
                    interface=i['interface'],
                    line_status=i['status'],
                    protocol_status=i['protocol'],
                    ipaddress=_ip.ip.format(),
                    ipmask=_ip.netmask.format(),
                    ip_type='Sub',
                    location=location,
                    mtu='')
                layer3datas.append(data)
            else:
                data = dict(
                    hostip=self.hostip,
                    interface=i['interface'],
                    line_status=i['status'],
                    protocol_status=i['protocol'],
                    ipaddress=i['priipaddr'],
                    ip_type='', location=[],
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
        if isinstance(res, str):
            return
        aggre_datas = []
        for i in res:
            try:
                memberports = []
                tmp_members = i['ports'].split(',')
                for member in tmp_members:
                    memberports.append(ruijie_interface_format(member))
            except Exception as e:
                memberports = i['memberports'].split(',')
            tmp = dict(
                hostip=self.hostip,
                aggregroup=ruijie_interface_format(i['aggregateport']),
                memberports=memberports,
                status='',
                mode=''
            )
            aggre_datas.append(tmp)
        if aggre_datas:
            MongoNetOps.insert_table(
                'Automation', self.hostip, aggre_datas, 'AggreTable')

    def interface_status_proc(self, res):
        layer2datas = []
        for i in res:
            if i['interface'].startswith('AggregatePort'):
                continue
            if i['speed'] == 'Unknown' or i['speed'] == 'unknown':
                i['speed'] = InterfaceFormat.ruijie_speed_format(
                    i['interface'])
            data = dict(hostip=self.hostip,
                        interface=i['interface'],
                        status=i['status'],
                        # speed=i['speed'],
                        speed=InterfaceFormat.mathintspeed(i['speed']),
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

    def version_proc(self, res):
        if isinstance(res, dict):
            """
            {'member': '1', 'serialnum': 'G1GC10V000176'}
            """
            model_tmp = re.search(r'(\([^)]*\))', res['description']).group()
            if model_tmp:
                model_name = model_tmp[1:-1]
                model_q = Model.objects.get_or_create(name=model_name,
                                                           vendor=Vendor.objects.get(alias='Ruijie'))
                NetworkDevice.objects.filter(
                    manage_ip=self.hostip).update(model=model_q[0])
            NetworkDevice.objects.filter(
                manage_ip=self.hostip).update(serial_num=res['serialnum'],
                                              slot=int(res['member']), soft_version=res['version'])
        elif isinstance(res, list):
            """
            [{'member': '1', 'serialnum': 'G1GC10V000176'}
            {'member': '2', 'serialnum': 'G1GC10V000134'}]
            """
            if len(res) == 1:
                for i in res:
                    model_tmp = re.search(r'(\([^)]*\))', i['description']).group()
                    if model_tmp:
                        model_name = model_tmp[1:-1]
                        model_q = Model.objects.get_or_create(name=model_name,
                                                                   vendor=Vendor.objects.get(alias='Ruijie'))
                        NetworkDevice.objects.filter(
                            manage_ip=self.hostip).update(model=model_q[0])
                    NetworkDevice.objects.filter(
                        manage_ip=self.hostip).update(serial_num=i['serialnum'],
                                                      slot=int(i['member']), soft_version=i['version'])
            else:
                for i in res:
                    NetworkDevice.objects.filter(
                        manage_ip=self.hostip,
                        serial_num=i['serialnum']).update(
                        slot=int(i['member']), soft_version=i['version'])

    def switch_virtual_proc(self, res):
        if isinstance(res, dict):
            if res['role'] == 'ACTIVE':
                NetworkDevice.objects.filter(
                    manage_ip=self.hostip, slot=int(
                        res['member'])).update(
                    ha_status=1)
            elif res['role'] == 'STANDBY':
                NetworkDevice.objects.filter(
                    manage_ip=self.hostip, slot=int(
                        res['member'])).update(
                    ha_status=2)
        elif isinstance(res, list):
            for i in res:
                if i['role'] == 'ACTIVE':
                    NetworkDevice.objects.filter(
                        manage_ip=self.hostip, slot=int(
                            i['member'])).update(
                        ha_status=1)
                elif i['role'] == 'STANDBY':
                    NetworkDevice.objects.filter(
                        manage_ip=self.hostip, slot=int(
                            i['member'])).update(
                        ha_status=2)
        return

    def memeber_proc(self, res):
        if isinstance(res, dict):
            """
            {'member': '1', 'priority': '120', 'macaddr': '1414.4b74.d658', 'softver': ''}
            {'member': '2', 'priority': '100', 'macaddr': '1414.4b74.d658', 'softver': ''}
            """
            # if int(res['priority']) > 100:
            NetworkDevice.objects.filter(
                manage_ip=self.hostip, slot=int(
                    res['member'])).update(
                ha_status=1)
            # elif int(res['priority']) <= 100:
            #     NetworkDevice.objects.filter(manage_ip=hostip, slot=int(res['member'])).update(ha_status=2)
        elif isinstance(res, list):
            # 172.17.1.2 的堆叠 priority 都是120，会导致判断错误
            tmp_priority = list(set([int(x['priority']) for x in res]))
            if len(tmp_priority) == 1:
                return
            for i in res:
                if int(i['priority']) == max(tmp_priority):
                    NetworkDevice.objects.filter(
                        manage_ip=self.hostip, slot=int(
                            i['member'])).update(
                        ha_status=1)
                elif int(i['priority']) == min(tmp_priority):
                    NetworkDevice.objects.filter(
                        manage_ip=self.hostip, slot=int(
                            i['member'])).update(
                        ha_status=2)

    def path_map(self, file_name, res: list):
        fsm_map = {
            'show_ip_arp': self.arp_proc,
            'show_mac': self.mac_proc,
            'show_ip_interface_brief': self.ip_interface_proc,
            'show_interfaces_status': self.interface_status_proc,
            'show_aggregatePort_summary': self.aggre_port_proc,
            'show_version': self.version_proc,
            'show_switch_virtual': self.switch_virtual_proc,
            'show_member': self.memeber_proc,
        }
        if file_name in fsm_map.keys():
            fsm_map[file_name](res)
        else:
            send_msg_netops("设备:{}\n命令:{}\n不被解析".format(self.hostip, file_name))

    def _collection_analysis(self, paths: list):
        for path in paths:
            res = BatManMain.info_fsm(path=path['path'], fsm_platform=self.fsm_flag)
            self.path_map(path['cmd_file'], res)
