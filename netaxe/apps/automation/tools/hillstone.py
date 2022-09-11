# -*- coding: utf-8 -*-
# @Time    : 2022/4/14 16:01
# @Author  : jmli12
# @Site    :
# @File    : hillstone.py
# @Software: PyCharm
import re
# from django.core.cache import cache
# from apps.asset.models import NetworkDevice
import traceback
from datetime import datetime

from netaddr import IPNetwork, IPAddress

from apps.asset.models import Model, NetworkDevice, Vendor
from utils.connect_layer.auto_main import BatManMain, HillstoneFsm
from utils.db.mongo_ops import MongoNetOps, MongoOps
from utils.wechat_api import send_msg_netops
from .base_connection import BaseConn

layer3_mongo = MongoOps(db='Automation', coll='layer3interface')
address_mongo = MongoOps(db='Automation', coll='hillstone_address')
service_mongo = MongoOps(db='Automation', coll='hillstone_service')
servgroup_mongo = MongoOps(db='Automation', coll='hillstone_servgroup')
slb_server_mongo = MongoOps(
    db='Automation', coll='hillstone_slb_server')
aggr_group_mongo = MongoOps(db='Automation', coll='AggreTable')
service_predefined_mongo = MongoOps(
    db='Automation', coll='hillstone_service_predefined')


def is_ip(ip):
    num_list = ip.split(".")
    if len(num_list) != 4:
        return False
    check_num = 0
    for num in num_list:
        if num.isdigit() and 0 <= int(num) <= 255 and str(int(num)) == num:
            check_num = check_num + 1
    if check_num == 4:
        return True
    else:
        return False


class HillstoneProc(BaseConn):
    """
    show interface
    show arp
    show mac
    show configuration
    show service predefined
    show zone
    """

    def __init__(self, **kwargs):
        # 继承父类方法
        # 防火墙需要一些变量需要同时被多个方法调用
        super(HillstoneProc, self).__init__(**kwargs)
        # 系统预定义服务
        self.service_predefined_map = {}
        # 地址对象
        self.address_map = {}
        # 山石服务组
        self.servgroup_map = dict()
        # 服务对象
        self.service_map = dict()
        # SLB对象映射集
        self.slb_map = dict()
        # dnat解析的原始数据
        self.dnat_result = []
        # dnat解析的最终数据
        self.dnat_data = []
        # snat解析的原始数据
        self.snat_result = []
        # snat解析的最终数据
        self.snat_data = []

    def _version_proc(self, res):
        """
        {'version': '5.5', 'product': 'SG-6000-P926', 'sn': '2508343195016552'}
        :param res:
        :return:
        """
        if isinstance(res, list):
            for i in res:
                model_q = Model.objects.get_or_create(name=i['product'],
                                                           vendor=Vendor.objects.get(alias='Hillstone'))
                NetworkDevice.objects.filter(manage_ip=self.hostip).update(model=model_q[0],
                                                                           # serial_num=i['sn'],
                                                                           soft_version=i['version'])

        return

    def _arp_proc(self, res):
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
                macaddress=macaddress,
                aging=i['age'],
                type=i['typeflag'],
                vlan='',
                interface=i['interface'],
                vpninstance='',
                log_time=datetime.now()
            )
            arp_datas.append(tmp)
        if arp_datas:
            MongoNetOps.insert_table(
                'Automation', self.hostip, arp_datas, 'ARPTable')

    def _mac_proc(self, res):
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
                vlan=i['switch'],
                interface=i['interface'],
                type=i['type'],
                log_time=datetime.now()
            )
            mac_datas.append(tmp)
        if mac_datas:
            MongoNetOps.insert_table(
                'Automation', self.hostip, mac_datas, 'MACTable')

    def _interface_proc(self, res):
        result = []
        layer3datas = []
        layer2datas = []
        int_regex = re.compile('ethernet')
        for i in res:
            i['hostip'] = self.hostip
            physical_status_map = {'U': 'up', 'D': 'down', 'K': 'ha'}
            try:
                # H:physical state;A:admin state;L:link state;P:protocol state;U:up;D:down;K:ha keep up
                # macaddr = i['macaddress'].replace('.', '-')
                tmp = i['halp'].split()
                physical_status = physical_status_map[tmp[0]]
                line_status = physical_status_map[tmp[2]]
                protocol_status = physical_status_map[tmp[3]]
            except Exception:
                # macaddr = i['macaddress']
                physical_status = ''
                line_status = ''
                protocol_status = ''
            if int_regex.search(i['interface']):
                if i['interface'].startswith('ethernet'):
                    speed = '1G'
                elif i['interface'].startswith('xethernet'):
                    speed = '10G'
                else:
                    speed = 'auto'
                data = dict(hostip=self.hostip,
                            interface=i['interface'],
                            status=physical_status,
                            speed=speed,
                            duplex='',
                            description=i['description'])
                layer2datas.append(data)
            if i['ipaddr']:
                _ipnet = IPNetwork(i['ipaddr'])
                # 安全纳管引擎，服务发布 定位用
                location = []
                if i['ipaddr'] != '0.0.0.0/0':
                    location = [dict(start=_ipnet.first,
                                     end=_ipnet.last)]
                data = dict(
                    hostip=self.hostip,
                    interface=i['interface'],
                    line_status=line_status,
                    protocol_status=protocol_status,
                    ipaddress=_ipnet.ip.format(),
                    ipmask=_ipnet.netmask.format(),
                    ip_type='',
                    mtu='', location=location)
                layer3datas.append(data)
            result.append(i)
        MongoNetOps.insert_table(
            'Automation', self.hostip, result, 'hillstone_interface')
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

    def _hillstone_sec_policy(self, datas, method='bulk'):
        """
        action: 'deny',
        dst_addr: {
            addr: 'Any'
        },
        id: '4',
        name: '封锁IP策略',
        service: 'Any',
        src_addr: {
            addr: '封锁IP'
        },
        hostip: '172.16.75.1'
        :param host:
        :param datas:
        :return:
        """
        my_mongo = MongoOps(db='Automation', coll='sec_policy')
        address_mongo = MongoOps(db='Automation', coll='hillstone_address')
        # 地址数据映射集
        address_map = dict()
        address_res = address_mongo.find(
            query_dict=dict(
                hostip=self.hostip), fileds={
                "_id": 0})
        if address_res:
            for _addr in address_res:
                if _addr['name'] in address_map.keys():
                    address_map[_addr['name']].append(_addr)
                else:
                    address_map[_addr['name']] = [_addr]
        if method == 'bulk':
            my_mongo.delete_many(query=dict(hostip=self.hostip))
        results = []
        for i in datas:
            # print(i)
            tmp = dict()
            tmp['src_ip_split'] = []
            tmp['dst_ip_split'] = []
            service = []
            src_addr = []
            dst_addr = []
            # if i.get('service'):
            #     if isinstance(i['service'], list):
            #         service = [x['service'] for x in i['service']]
            #     else:
            #         service.append(i['service']['service'])
            log = ''
            if i.get('logs'):
                if isinstance(i['logs'], dict):
                    log = i['logs']['log']
                elif isinstance(i['logs'], list):
                    log = ','.join([x['log'] for x in i['logs']])
            # 地址对象
            # src_addr = ''
            if i.get('src_addr'):
                # tmp_src_addr = []
                if isinstance(i['src_addr'], dict):
                    # tmp_src_addr = [i['src_addr'][x] for x in i['src_addr'].keys()]
                    # src_addr = ','.join(tmp_src_addr)
                    if 'object' in i['src_addr'].keys():
                        # src_addr = i['src_addr']['object']
                        # _addr_res = address_mongo.find(query_dict=dict(address=src_addr, hostip=host), fileds={'_id': 0})
                        src_addr.append(dict(object=i['src_addr']['object']))
                        if i['src_addr']['object'] in address_map.keys():
                            _addr_res = address_map[i['src_addr']['object']]
                            for _sub_src_ip in _addr_res:
                                if 'ip' in _sub_src_ip.keys():
                                    for _t_ip in _sub_src_ip['ip']:
                                        tmp['src_ip_split'].append(dict(start=IPNetwork(_t_ip['ip']).first,
                                                                        end=IPNetwork(_t_ip['ip']).last))
                                if 'range' in _sub_src_ip.keys():
                                    for _t_ip in _sub_src_ip['range']:
                                        tmp['src_ip_split'].append(dict(start=IPAddress(_t_ip['start']).value,
                                                                        end=IPAddress(_t_ip['end']).value))
                    elif 'ip' in i['src_addr'].keys():
                        _ip = IPNetwork(i['src_addr']['ip'])
                        src_addr.append(dict(ip=i['src_addr']['ip']))
                        tmp['src_ip_split'].append(dict(start=IPNetwork(_ip).first,
                                                        end=IPNetwork(_ip).last))
                    elif 'range' in i['src_addr'].keys():
                        start_ip = i['src_addr']['range'].split()[0]
                        end_ip = i['src_addr']['range'].split()[1]
                        src_addr.append(dict(range=start_ip + '-' + end_ip))
                        tmp['src_ip_split'].append(dict(start=IPNetwork(start_ip).first,
                                                        end=IPNetwork(end_ip).last))

                elif isinstance(i['src_addr'], list):
                    # src_addr = ','.join([x['addr'] for x in i['src_addr']])
                    for _src_tmp in i['src_addr']:
                        # tmp_src_addr += [_src_tmp[x] for x in _src_tmp.keys()]
                        if 'object' in _src_tmp.keys():
                            src_addr.append(dict(object=_src_tmp['object']))
                            if _src_tmp['object'] in address_map.keys():
                                _addr_res = address_map[_src_tmp['object']]
                                for _sub_src_ip in _addr_res:
                                    if 'ip' in _sub_src_ip.keys():
                                        for _t_ip in _sub_src_ip['ip']:
                                            tmp['src_ip_split'].append(dict(start=IPNetwork(_t_ip['ip']).first,
                                                                            end=IPNetwork(_t_ip['ip']).last))
                                    if 'range' in _sub_src_ip.keys():
                                        for _t_ip in _sub_src_ip['range']:
                                            tmp['src_ip_split'].append(
                                                dict(start=IPAddress(_t_ip['start']).value,
                                                     end=IPAddress(_t_ip['end']).value))
                        elif 'ip' in _src_tmp.keys():
                            _ip = IPNetwork(_src_tmp['ip'])
                            src_addr.append(dict(ip=_src_tmp['ip']))
                            tmp['src_ip_split'].append(dict(start=IPNetwork(_ip).first,
                                                            end=IPNetwork(_ip).last))
                        elif 'range' in _src_tmp.keys():
                            start_ip = _src_tmp['range'].split()[0]
                            end_ip = _src_tmp['range'].split()[1]
                            src_addr.append(
                                dict(range=start_ip + '-' + end_ip))
                            tmp['src_ip_split'].append(dict(start=IPNetwork(start_ip).first,
                                                            end=IPNetwork(end_ip).last))
                    # src_addr = ','.join(tmp_src_addr)
            # dst_addr = ''
            if i.get('dst_addr'):
                # tmp_dst_addr = []
                if isinstance(i['dst_addr'], dict):
                    # tmp_dst_addr = [i['dst_addr'][x] for x in i['dst_addr'].keys()]
                    # dst_addr = ','.join(tmp_dst_addr)
                    if 'object' in i['dst_addr'].keys():
                        dst_addr.append(dict(object=i['dst_addr']['object']))
                        if i['dst_addr']['object'] in address_map.keys():
                            _addr_res = address_map[i['dst_addr']['object']]
                            for _sub_dst_ip in _addr_res:
                                if 'ip' in _sub_dst_ip.keys():
                                    for _t_ip in _sub_dst_ip['ip']:
                                        tmp['dst_ip_split'].append(dict(start=IPNetwork(_t_ip['ip']).first,
                                                                        end=IPNetwork(_t_ip['ip']).last))
                                if 'range' in _sub_dst_ip.keys():
                                    for _t_ip in _sub_dst_ip['range']:
                                        tmp['dst_ip_split'].append(dict(start=IPAddress(_t_ip['start']).value,
                                                                        end=IPAddress(_t_ip['end']).value))
                    elif 'ip' in i['dst_addr'].keys():
                        dst_addr.append(dict(ip=i['dst_addr']['ip']))
                        _ip = IPNetwork(i['dst_addr']['ip'])
                        tmp['dst_ip_split'].append(dict(start=IPNetwork(_ip).first,
                                                        end=IPNetwork(_ip).last))
                    elif 'range' in i['dst_addr'].keys():
                        start_ip = i['dst_addr']['range'].split()[0]
                        end_ip = i['dst_addr']['range'].split()[1]
                        dst_addr.append(dict(range=start_ip + '-' + end_ip))
                        tmp['dst_ip_split'].append(dict(start=IPNetwork(start_ip).first,
                                                        end=IPNetwork(end_ip).last))
                elif isinstance(i['dst_addr'], list):
                    # dst_addr = ','.join([x['addr'] for x in i['dst_addr']])
                    for _dst_tmp in i['dst_addr']:
                        # tmp_dst_addr += [_dst_tmp[x] for x in _dst_tmp.keys()]
                        if 'object' in _dst_tmp.keys():
                            dst_addr.append(dict(object=_dst_tmp['object']))
                            if _dst_tmp['object'] in address_map.keys():
                                _addr_res = address_map[_dst_tmp['object']]
                                for _sub_src_ip in _addr_res:
                                    if 'ip' in _sub_src_ip.keys():
                                        for _t_ip in _sub_src_ip['ip']:
                                            tmp['dst_ip_split'].append(dict(start=IPNetwork(_t_ip['ip']).first,
                                                                            end=IPNetwork(_t_ip['ip']).last))
                                    if 'range' in _sub_src_ip.keys():
                                        for _t_ip in _sub_src_ip['range']:
                                            tmp['dst_ip_split'].append(
                                                dict(start=IPAddress(_t_ip['start']).value,
                                                     end=IPAddress(_t_ip['end']).value))
                        elif 'ip' in _dst_tmp.keys():
                            dst_addr.append(dict(ip=_dst_tmp['ip']))
                            _ip = IPNetwork(_dst_tmp['ip'])
                            tmp['dst_ip_split'].append(dict(start=IPNetwork(_ip).first,
                                                            end=IPNetwork(_ip).last))
                        elif 'range' in _dst_tmp.keys():
                            start_ip = _dst_tmp['range'].split()[0]
                            end_ip = _dst_tmp['range'].split()[1]
                            dst_addr.append(
                                dict(range=start_ip + '-' + end_ip))
                            tmp['dst_ip_split'].append(dict(start=IPNetwork(start_ip).first,
                                                            end=IPNetwork(end_ip).last))
                    # dst_addr = ','.join(tmp_dst_addr)
            enable = True
            if i.get('disable'):
                enable = False
            tmp['vendor'] = 'hillstone'
            tmp['hostip'] = i['hostip']
            tmp['id'] = i.get('id')
            tmp['name'] = i.get('name')
            tmp['action'] = i.get('action')
            tmp['enable'] = enable
            tmp['src_zone'] = i.get('src-zone') if i.get('src-zone') else 'Any'
            tmp['dst_zone'] = i.get('dst-zone') if i.get('dst-zone') else 'Any'
            tmp['service'] = i.get('service')
            tmp['src_addr'] = i.get('src_addr')  # 地址组
            tmp['dst_addr'] = i.get('dst_addr')  # 地址组
            tmp['log'] = log
            tmp['description'] = i.get('description')
            results.append(tmp)
        my_mongo.insert_many(results)
        return

    # dnat 处理
    def _dnat_proc(self, dnat_res):
        for i in dnat_res:
            if i['RULESTATE'] == 'disable':
                continue
            # print(i)
            i['hostip'] = self.hostip
            # 变量初始化定义 start
            local_ip = []
            global_ip = []
            global_ip_range = []
            global_port = []
            local_port = []
            # 变量初始化定义 end
            if i['TO_IP'] in self.address_map.keys():
                try:
                    global_ip = [dict(start=i['TO_IP'],
                                      end=i['TO_IP'],
                                      start_int=IPAddress(
                                          i['TO_IP']).value,
                                      end_int=IPAddress(
                                          i['TO_IP']).value,
                                      result=i['TO_IP'])]
                except Exception as e:
                    send_msg_netops(
                        "设备:{} 山石防火墙DNAT解析 TO_IP 字段不是纯IP：{}".format(
                            i['TO_IP'], self.hostip))
                    global_ip = [
                        dict(
                            start=i['TO_IP'],
                            end=i['TO_IP'],
                            result=i['TO_IP'])]
            elif i['TO'] in self.address_map.keys():
                _global_ip_query = self.address_map[i['TO']]
                # print('_global_ip', _global_ip)
                # _global_ip = _global_ip[0]
                _global_ip_list = [x for x in _global_ip_query if x.get('ip') or x.get('range')]
                # global_ip_list = [x['ip'] for x in _global_ip['ip'] if _global_ip.get('ip')]
                for _global_ip in _global_ip_list:
                    if _global_ip.get('ip'):
                        global_ip += list([dict(start=x['ip'],
                                                end=x['ip'],
                                                start_int=IPNetwork(
                                                    x['ip']).first,
                                                end_int=IPNetwork(
                                                    x['ip']).last,
                                                result=x['ip']) for x in _global_ip['ip']])
                    if _global_ip.get('range'):
                        global_ip_range += list([dict(start=x['start'],
                                                      end=x['end'],
                                                      start_int=IPAddress(
                                                          x['start']).value,
                                                      end_int=IPAddress(
                                                          x['end']).value,
                                                      result=x['start'] +
                                                             '-' + x['end']
                                                      ) for x in _global_ip['range']])
                    global_ip = global_ip + global_ip_range
            elif i['TO_IP']:
                try:
                    if i['TO_IP'].find('/') != -1:
                        global_ip = [dict(start=i['TO_IP'],
                                          end=i['TO_IP'],
                                          start_int=IPNetwork(
                                              i['TO_IP']).first,
                                          end_int=IPNetwork(
                                              i['TO_IP']).last,
                                          result=i['TO_IP'])]
                    else:
                        global_ip = [dict(start=i['TO_IP'],
                                          end=i['TO_IP'],
                                          start_int=IPAddress(
                                              i['TO_IP']).value,
                                          end_int=IPAddress(
                                              i['TO_IP']).value,
                                          result=i['TO_IP'])]
                except Exception as e:
                    global_ip = [
                        dict(
                            start=i['TO_IP'],
                            end=i['TO_IP'],
                            result=i['TO_IP'])]
            else:
                try:
                    if i['TO'].find('/') != -1:
                        global_ip = [dict(start=i['TO'],
                                          end=i['TO'],
                                          start_int=IPNetwork(
                                              i['TO']).first,
                                          end_int=IPNetwork(
                                              i['TO']).last,
                                          result=i['TO'])]
                    else:
                        global_ip = [dict(start=i['TO'],
                                          end=i['TO'],
                                          start_int=IPAddress(
                                              i['TO']).value,
                                          end_int=IPAddress(
                                              i['TO']).value,
                                          result=i['TO'])]
                except Exception as e:
                    global_ip = [
                        dict(
                            start=i['TO'],
                            end=i['TO'],
                            result=i['TO'])]
            # 判断是否系统预定义服务
            if i['SERVICE'] in self.service_predefined_map.keys():
                _global_port = self.service_predefined_map[i['SERVICE']]
                for _sub_global_port in _global_port:
                    try:
                        global_port.append(dict(start=int(_sub_global_port['dstport']),
                                                end=int(
                                                    _sub_global_port['dstport']),
                                                protocol=_sub_global_port['protocol'],
                                                result=str(
                                                    _sub_global_port['dstport'])
                                                ))
                    except BaseException:
                        global_port.append(dict(start=_sub_global_port['dstport'],
                                                end=_sub_global_port['dstport'],
                                                protocol=_sub_global_port['protocol'],
                                                result=str(
                                                    _sub_global_port['dstport'])
                                                ))
            # 判断是否服务组
            elif i['SERVICE'] in self.servgroup_map.keys():
                _servgroup = self.servgroup_map[i['SERVICE']]
                # _portlist = []
                for _ser_port in _servgroup:
                    # _tmp = service_mongo.find(
                    #     query_dict=dict(hostip=hostip, service=str(_ser_port['Service'])),
                    #     fileds={"_id": 0, 'Port': 1, 'Protocol': 1})
                    if _ser_port['service'] in self.service_predefined_map.keys():
                        _tmp = self.service_predefined_map[_ser_port['service']]
                        for _sub_global_port in _tmp:
                            try:
                                global_port.append(dict(start=int(_sub_global_port['dstport']),
                                                        end=int(
                                                            _sub_global_port['dstport']),
                                                        protocol=_sub_global_port['protocol'],
                                                        result=str(_sub_global_port['dstport'])))
                            except BaseException:
                                global_port.append(dict(start=_sub_global_port['dstport'],
                                                        end=_sub_global_port['dstport'],
                                                        protocol=_sub_global_port['protocol'],
                                                        result=str(
                                                            _sub_global_port['dstport'])
                                                        ))
                    elif _ser_port['service'] in self.service_map.keys():
                        _tmp = self.service_map[_ser_port['service']]
                        for _tmp_port in _tmp:
                            if all(k in _tmp_port for k in (
                                    "dst-port-min", "dst-port-max")):
                                # _portlist.append(_tmp_port['Port'])
                                # _global_protocol.append(_tmp_port['protocol'])
                                global_port.append(dict(start=int(_tmp_port['dst-port-min']),
                                                        end=int(
                                                            _tmp_port['dst-port-max']),
                                                        protocol=_tmp_port['protocol'],
                                                        result=str(_tmp_port['dst-port-min']) + '-' + str(
                                                            _tmp_port['dst-port-max'])
                                                        ))
                            elif 'dst-port-min' in _tmp_port.keys():
                                # _portlist.append(_tmp_port['Port'])
                                # _global_protocol.append(_tmp_port['protocol'])
                                global_port.append(dict(start=int(_tmp_port['dst-port-min']),
                                                        end=int(
                                                            _tmp_port['dst-port-min']),
                                                        protocol=_tmp_port['protocol'],
                                                        result=str(
                                                            _tmp_port['dst-port-min'])
                                                        ))
                    else:
                        global_port.append(dict(start=_ser_port['service'],
                                                end=_ser_port['service'],
                                                protocol=_ser_port['service'],
                                                result=_ser_port['service']
                                                ))
                        # _portlist.append(str(_ser_port['service']))
                        # _global_protocol.append(_ser_port['service'])
                # 统一转str格式
                # global_port = list([str(x) for x in _portlist])
                # _global_protocol = list([str(x) for x in _global_protocol])
                # global_port = ','.join(global_port)
                # global_protocol = ','.join(_global_protocol)
            # 判断是否服务
            elif i['SERVICE'] in self.service_map.keys():
                # _global_port = service_mongo.find(query_dict=dict(hostip=hostip, service=str(i['SERVICE'])),
                # fileds={"_id": 0, 'Port': 1, 'Protocol': 1})
                _tmp = self.service_map[i['SERVICE']]
                for _tmp_port in _tmp:
                    if all(k in _tmp_port for k in (
                            "dst-port-min", "dst-port-max")):
                        # _portlist.append(_tmp_port['Port'])
                        # _global_protocol.append(_tmp_port['protocol'])
                        global_port.append(dict(start=int(_tmp_port['dst-port-min']),
                                                end=int(
                                                    _tmp_port['dst-port-max']),
                                                protocol=_tmp_port['protocol'],
                                                result=str(_tmp_port['dst-port-min']) + '-' + str(
                                                    _tmp_port['dst-port-max'])))
                    elif 'dst-port-min' in _tmp_port.keys():
                        # _portlist.append(_tmp_port['Port'])
                        # _global_protocol.append(_tmp_port['protocol'])
                        global_port.append(dict(start=int(_tmp_port['dst-port-min']),
                                                end=int(
                                                    _tmp_port['dst-port-min']),
                                                protocol=_tmp_port['protocol'],
                                                result=str(
                                                    _tmp_port['dst-port-min'])
                                                ))
                    # _global_port = service_map[i['SERVICE']]
                    # global_port = list([str(x['Port']) for x in _global_port])
                    # _global_protocol = list(set([str(x['Protocol']) for x in _global_port]))
                    # _global_protocol = list([str(x['Protocol']) for x in _global_port])
                    # global_port = ','.join(global_port)
                    # global_protocol = ','.join(_global_protocol)
            else:
                global_port.append(dict(start=i['SERVICE'],
                                        end=i['SERVICE'],
                                        protocol=i['SERVICE'],
                                        result=i['SERVICE']))
            if i['TRANSTO_IP'] and i['TRANSTO_IP'] != '':
                try:
                    local_ip = [dict(start=i['TRANSTO_IP'],
                                     end=i['TRANSTO_IP'],
                                     start_int=IPAddress(
                                         i['TRANSTO_IP']).value,
                                     end_int=IPAddress(
                                         i['TRANSTO_IP']).value,
                                     result=i['TRANSTO_IP'])]
                except Exception as e:
                    local_ip = [
                        dict(
                            start=i['TRANSTO_IP'],
                            end=i['TRANSTO_IP'],
                            result=i['TRANSTO_IP'])]
            elif i['TRANSTO']:
                if i['TRANSTO'] in self.address_map.keys():
                    _local_ip = self.address_map[i['TRANSTO']]
                    _local_ip = _local_ip[0]
                    if _local_ip.get('ip'):
                        local_ip = list([dict(start=x['ip'],
                                              end=x['ip'],
                                              start_int=IPNetwork(
                                                  x['ip']).first,
                                              end_int=IPNetwork(
                                                  x['ip']).last,
                                              result=x['ip']
                                              ) for x in _local_ip['ip']])
                    local_ip_range = []
                    if _local_ip.get('range'):
                        local_ip_range = list([dict(start=x['start'],
                                                    end=x['end'],
                                                    start_int=IPAddress(
                                                        x['start']).value,
                                                    end_int=IPAddress(
                                                        x['end']).value,
                                                    result=x['start'] +
                                                           '-' + x['end']
                                                    ) for x in _local_ip['range']])
                    local_ip = local_ip + local_ip_range
                else:
                    try:
                        local_ip = [dict(start=i['TRANSTO'],
                                         end=i['TRANSTO'],
                                         start_int=IPAddress(
                                             i['TRANSTO']).value,
                                         end_int=IPAddress(
                                             i['TRANSTO']).value,
                                         result=i['TRANSTO']
                                         )]
                    except Exception as e:
                        local_ip = [
                            dict(
                                start=i['TRANSTO'],
                                end=i['TRANSTO'],
                                result=i['TRANSTO'])]
            elif i['POOLNAME']:
                # PODNAME
                if i['POOLNAME'] in self.slb_map.keys():
                    _res = self.slb_map[i['POOLNAME']]
                    for _ip in _res:
                        if _ip['ADDRTYPE'] == 'ip':
                            local_ip.append(dict(start=_ip['SERVERIP'],
                                                 end=_ip['SERVERIP'],
                                                 start_int=IPNetwork(
                                                     _ip['SERVERIP']).first,
                                                 end_int=IPNetwork(
                                                     _ip['SERVERIP']).last,
                                                 result=_ip['SERVERIP']))
                        if _ip['ADDRTYPE'] == 'ip-range':
                            tmp = _ip['SERVERIP'].split()
                            local_ip.append(dict(start=tmp[0],
                                                 end=tmp[1],
                                                 start_int=IPAddress(
                                                     tmp[0]).value,
                                                 end_int=IPAddress(
                                                     tmp[1]).value,
                                                 result=tmp[0] + '-' + tmp[1]))
            else:
                try:
                    local_ip = [dict(start=i['POOLNAME'],
                                     end=i['POOLNAME'],
                                     start_int=IPAddress(
                                         i['POOLNAME']).value,
                                     end_int=IPAddress(
                                         i['POOLNAME']).value,
                                     result=i['POOLNAME'])]
                except Exception as e:
                    local_ip = [
                        dict(
                            start=i['POOLNAME'],
                            end=i['POOLNAME'],
                            result=i['POOLNAME'])]
            port_regex = re.compile('^\\d+$')
            if i['PORT'] in self.service_map.keys():
                _tmp = self.service_map[i['PORT']]
                for _tmp_port in _tmp:
                    if all(k in _tmp_port for k in (
                            "dst-port-min", "dst-port-max")):
                        local_port.append(dict(start=int(_tmp_port['dst-port-min']),
                                               end=int(
                                                   _tmp_port['dst-port-max']),
                                               protocol=_tmp_port['protocol'],
                                               result=str(_tmp_port['dst-port-min']) + '-' + str(
                                                   _tmp_port['dst-port-max'])))
                    elif 'dst-port-min' in _tmp_port.keys():
                        local_port.append(dict(start=int(_tmp_port['dst-port-min']),
                                               end=int(
                                                   _tmp_port['dst-port-min']),
                                               protocol=_tmp_port['protocol'],
                                               result=str(_tmp_port['dst-port-min'])))
                else:
                    local_port.append(dict(start=i['PORT'],
                                           end=i['PORT'],
                                           protocol=i['PORT'],
                                           result=i['PORT']))
            elif port_regex.search(i['PORT']):
                local_port = [dict(start=int(i['PORT']),
                                   end=int(i['PORT']),
                                   protocol=global_port[0]['protocol'],
                                   result=i['PORT']
                                   )]
            else:
                local_port = global_port
            i['log_time'] = datetime.now()
            self.dnat_result.append(i)  # 存储原始数据信息
            tmp = dict(
                rule_id=i['ID'],
                hostip=self.hostip,
                global_ip=global_ip,
                global_port=global_port,
                local_ip=local_ip,
                local_port=local_port,
            )
            self.dnat_data.append(tmp)  # 存储格式化后的数据信息

    # snat 处理
    def _snat_proc(self, snat_res):
        if isinstance(snat_res, list):
            if not self.address_map:
                send_msg_netops("山石防火墙:{}\nSNAT拼接时没有查询到地址对象集合，请调整采集方法调用顺序".format(self.hostip))
            for i in snat_res:
                if i['DISABLE'] == 'disable':
                    continue
                i['hostip'] = self.hostip
                # 变量初始化定义 start
                local_ip = []
                local_exclude_ip = []
                trans_ip = []
                destination_ip = []
                destination_port = []
                # 变量初始化定义 end
                # FROM 是 内网IP
                if i['FROM_IP']:
                    try:
                        local_ip = [dict(start=i['FROM_IP'],
                                         end=i['FROM_IP'],
                                         start_int=IPAddress(
                                             i['FROM_IP']).value,
                                         end_int=IPAddress(
                                             i['FROM_IP']).value,
                                         result=i['FROM_IP'])]
                    except Exception as e:
                        local_ip = [
                            dict(
                                start=i['FROM_IP'],
                                end=i['FROM_IP'],
                                result=i['FROM_IP'])]
                if i['FROM'] and i['FROM'] in self.address_map.keys():
                    _local_ip = self.address_map[i['FROM']]
                    _local_ip = _local_ip[0]
                    if _local_ip.get('ip'):
                        local_ip += list([dict(start=x['ip'],
                                               end=x['ip'],
                                               start_int=IPNetwork(
                                                   x['ip']).first,
                                               end_int=IPNetwork(
                                                   x['ip']).last,
                                               result=x['ip']
                                               ) for x in _local_ip['ip']])
                    if _local_ip.get('range'):
                        local_ip += list([dict(start=x['start'],
                                               end=x['end'],
                                               start_int=IPAddress(
                                                   x['start']).value,
                                               end_int=IPAddress(
                                                   x['end']).value,
                                               result=x['start'] + '-' + x['end']
                                               ) for x in _local_ip['range']])
                    if _local_ip.get('exclude_ip'):
                        local_exclude_ip += list([dict(start=x['ip'],
                                                       end=x['ip'],
                                                       start_int=IPNetwork(
                                                           x['ip']).first,
                                                       end_int=IPNetwork(
                                                           x['ip']).last,
                                                       result=x['ip']
                                                       ) for x in _local_ip['exclude_ip']])
                    if _local_ip.get('c'):
                        local_exclude_ip += list([dict(start=x['start'],
                                                       end=x['end'],
                                                       start_int=IPAddress(
                                                           x['start']).value,
                                                       end_int=IPAddress(
                                                           x['end']).value,
                                                       result=x['start'] + '-' + x['end']
                                                       ) for x in _local_ip['exclude_ip']])
                if i['FROM'] == 'Any':
                    local_ip += [dict(start='',
                                      end='',
                                      result='Any')]
                # TO字段是限制访问的目的的
                if i['TO'] and i['TO'] in self.address_map.keys():
                    _dest_ip = self.address_map[i['TO']]
                    _dest_ip = _dest_ip[0]
                    if _dest_ip.get('ip'):
                        destination_ip += list([dict(start=x['ip'],
                                                     end=x['ip'],
                                                     start_int=IPNetwork(
                                                         x['ip']).first,
                                                     end_int=IPNetwork(
                                                         x['ip']).last,
                                                     result=x['ip']
                                                     ) for x in _dest_ip['ip']])
                    if _dest_ip.get('range'):
                        destination_ip += list([dict(start=x['start'],
                                                     end=x['end'],
                                                     start_int=IPAddress(
                                                         x['start']).value,
                                                     end_int=IPAddress(
                                                         x['end']).value,
                                                     result=x['start'] + '-' + x['end']
                                                     ) for x in _dest_ip['range']])
                if is_ip(i['TO_IP']):
                    destination_ip += [dict(start=i['TO_IP'],
                                            end=i['TO_IP'],
                                            start_int=IPAddress(
                                                i['TO_IP']).value,
                                            end_int=IPAddress(
                                                i['TO_IP']).value,
                                            result=i['TO_IP'])]
                if i['TO'] == 'Any':
                    destination_ip += [dict(start='',
                                            end='',
                                            result='Any')]
                if i['TRANSTO_IP']:
                    try:
                        if i['TO_IP'].find('/') != -1:
                            trans_ip = [dict(start=i['TRANSTO_IP'],
                                             end=i['TRANSTO_IP'],
                                             start_int=IPNetwork(
                                                 i['TRANSTO_IP']).first,
                                             end_int=IPNetwork(
                                                 i['TRANSTO_IP']).last,
                                             result=i['TRANSTO_IP'])]
                        else:
                            trans_ip = [dict(start=i['TRANSTO_IP'],
                                             end=i['TRANSTO_IP'],
                                             start_int=IPAddress(
                                                 i['TRANSTO_IP']).value,
                                             end_int=IPAddress(
                                                 i['TRANSTO_IP']).value,
                                             result=i['TRANSTO_IP'])]
                    except Exception as e:
                        trans_ip = [
                            dict(
                                start=i['TRANSTO_IP'],
                                end=i['TRANSTO_IP'],
                                result=i['TRANSTO_IP'])]
                elif i['TRANSTO'] in self.address_map.keys():
                    _global_ip_query = self.address_map[i['TRANSTO']]
                    _global_ip_list = [x for x in _global_ip_query if x.get('ip') or x.get('range')]
                    for _global_ip in _global_ip_list:
                        if _global_ip.get('ip'):
                            trans_ip += list([dict(start=x['ip'],
                                                   end=x['ip'],
                                                   start_int=IPNetwork(
                                                       x['ip']).first,
                                                   end_int=IPNetwork(
                                                       x['ip']).last,
                                                   result=x['ip']) for x in _global_ip['ip']])
                        if _global_ip.get('range'):
                            trans_ip += list([dict(start=x['start'],
                                                   end=x['end'],
                                                   start_int=IPAddress(
                                                       x['start']).value,
                                                   end_int=IPAddress(
                                                       x['end']).value,
                                                   result=x['start'] +
                                                          '-' + x['end']
                                                   ) for x in _global_ip['range']])
                elif i['TRANSTO_EIP']:
                    _tmp_int = layer3_mongo.find(
                        query_dict={'interface': i['EGRESS_INTERFACE'], 'hostip': self.hostip}, fileds={'_id': 0})
                    if _tmp_int:
                        _tmp_int = _tmp_int[0]
                        _tmp_ip = IPNetwork('{}/{}'.format(_tmp_int['ipaddress'], _tmp_int['ipmask']))
                        # 走to地址所在的出接口
                        trans_ip += list([dict(
                            start='{}/{}'.format(_tmp_int['ipaddress'], _tmp_int['ipmask']),
                            end='{}/{}'.format(_tmp_int['ipaddress'], _tmp_int['ipmask']),
                            start_int=_tmp_ip.first,
                            end_int=_tmp_ip.last,
                            result='{}/{}'.format(_tmp_int['ipaddress'], _tmp_int['ipmask'])
                        )])
                # SERVICE 标记 destination_port
                if i['SERVICE'] != 'Any':
                    # 判断是否系统预定义服务
                    if i['SERVICE'] in self.service_predefined_map.keys():
                        _global_port = self.service_predefined_map[i['SERVICE']]
                        for _sub_global_port in _global_port:
                            try:
                                destination_port.append(dict(start=int(_sub_global_port['dstport']),
                                                             end=int(
                                                                 _sub_global_port['dstport']),
                                                             protocol=_sub_global_port['protocol'],
                                                             result=str(
                                                                 _sub_global_port['dstport'])
                                                             ))
                            except Exception:
                                destination_port.append(dict(start=_sub_global_port['dstport'],
                                                             end=_sub_global_port['dstport'],
                                                             protocol=_sub_global_port['protocol'],
                                                             result=str(
                                                                 _sub_global_port['dstport'])
                                                             ))
                    # 判断是否服务组
                    elif i['SERVICE'] in self.servgroup_map.keys():
                        _servgroup = self.servgroup_map[i['SERVICE']]
                        for _ser_port in _servgroup:
                            if _ser_port['service'] in self.service_predefined_map.keys():
                                _tmp = self.service_predefined_map[_ser_port['service']]
                                for _sub_global_port in _tmp:
                                    try:
                                        destination_port.append(dict(start=int(_sub_global_port['dstport']),
                                                                     end=int(
                                                                         _sub_global_port['dstport']),
                                                                     protocol=_sub_global_port['protocol'],
                                                                     result=str(_sub_global_port['dstport'])))
                                    except Exception:
                                        destination_port.append(dict(start=_sub_global_port['dstport'],
                                                                     end=_sub_global_port['dstport'],
                                                                     protocol=_sub_global_port['protocol'],
                                                                     result=str(
                                                                         _sub_global_port['dstport'])
                                                                     ))
                            elif _ser_port['service'] in self.service_map.keys():
                                _tmp = self.service_map[_ser_port['service']]
                                for _tmp_port in _tmp:
                                    if all(k in _tmp_port for k in (
                                            "dst-port-min", "dst-port-max")):
                                        destination_port.append(dict(start=int(_tmp_port['dst-port-min']),
                                                                     end=int(
                                                                         _tmp_port['dst-port-max']),
                                                                     protocol=_tmp_port['protocol'],
                                                                     result=str(_tmp_port['dst-port-min']) + '-' + str(
                                                                         _tmp_port['dst-port-max'])
                                                                     ))
                                    elif 'dst-port-min' in _tmp_port.keys():
                                        destination_port.append(dict(start=int(_tmp_port['dst-port-min']),
                                                                     end=int(
                                                                         _tmp_port['dst-port-min']),
                                                                     protocol=_tmp_port['protocol'],
                                                                     result=str(
                                                                         _tmp_port['dst-port-min'])
                                                                     ))
                            else:
                                destination_port.append(dict(start=_ser_port['service'],
                                                             end=_ser_port['service'],
                                                             protocol=_ser_port['service'],
                                                             result=_ser_port['service']
                                                             ))
                    # 判断是否服务
                    elif i['SERVICE'] in self.service_map.keys():
                        _tmp = self.service_map[i['SERVICE']]
                        for _tmp_port in _tmp:
                            if all(k in _tmp_port for k in (
                                    "dst-port-min", "dst-port-max")):
                                destination_port.append(dict(start=int(_tmp_port['dst-port-min']),
                                                             end=int(
                                                                 _tmp_port['dst-port-max']),
                                                             protocol=_tmp_port['protocol'],
                                                             result=str(_tmp_port['dst-port-min']) + '-' + str(
                                                                 _tmp_port['dst-port-max'])))
                            elif 'dst-port-min' in _tmp_port.keys():
                                destination_port.append(dict(start=int(_tmp_port['dst-port-min']),
                                                             end=int(
                                                                 _tmp_port['dst-port-min']),
                                                             protocol=_tmp_port['protocol'],
                                                             result=str(
                                                                 _tmp_port['dst-port-min'])
                                                             ))
                    else:
                        destination_port.append(dict(start=i['SERVICE'],
                                                     end=i['SERVICE'],
                                                     protocol=i['SERVICE'],
                                                     result=i['SERVICE']))
                        send_msg_netops("山石防火墙:{}\nSNAT查询服务对象:{}失败".format(self.hostip, i['SERVICE']))
                self.snat_result.append(i)
                tmp = dict(
                    rule_id=i['ID'],
                    hostip=self.hostip,
                    trans_ip=trans_ip,
                    local_ip=local_ip,
                    local_exclude_ip=local_exclude_ip,
                    destination_ip=destination_ip,
                    destination_port=destination_port,
                    model=i['MODE'],
                    source_zone='',
                    destination_zone='',
                    log_time=datetime.now()
                )
                self.snat_data.append(tmp)

    def _configfile_proc(self, path):
        # 安全策略
        try:
            sec_policy_res = HillstoneFsm.sec_policy(path=path)
            sec_policy_result = []
            if sec_policy_res:
                for i in sec_policy_res:
                    i['hostip'] = self.hostip
                    sec_policy_result.append(i)
            if sec_policy_result:
                try:
                    self._hillstone_sec_policy(sec_policy_result)
                except Exception as e:
                    send_msg_netops(
                        "山石防火墙安全策略入库失败,设备:{},错误:{}".format(
                            self.hostip, str(e)))
        except Exception as e:
            print('山石配置文件安全策略解析异常', str(e))
            MongoNetOps.failed_log(
                ip=self.hostip,
                fsm_flag='hillstone',
                cmd='sec_policy',
                version=str(e))
        # 地址组
        try:
            address_res = HillstoneFsm.address_group(path=path)
            address_result = []
            for i in address_res:
                if i['name'] in self.address_map.keys():
                    self.address_map[i['name']].append(i)
                else:
                    self.address_map[i['name']] = [i]
                i['hostip'] = self.hostip
                address_result.append(i)
            if address_result:
                address_mongo.delete_many(query=dict(hostip=self.hostip))
                address_mongo.insert_many(address_result)
        except Exception as e:
            print('山石配置文件地址组解析异常', str(e))
            MongoNetOps.failed_log(
                ip=self.hostip,
                fsm_flag='hillstone',
                cmd='address',
                version=str(e))
        # 服务
        try:
            service_res = HillstoneFsm.service_proc(path=path)
            service_result = []
            for i in service_res:
                self.service_map[i['name']] = i['items']
                i['hostip'] = self.hostip
                service_result.append(i)
            if service_result:
                service_mongo.delete_many(query=dict(hostip=self.hostip))
                service_mongo.insert_many(service_result)
        except Exception as e:
            print('山石配置文件服务解析异常', str(e))
            MongoNetOps.failed_log(
                ip=self.hostip,
                fsm_flag='hillstone',
                cmd='service',
                version=str(e))
        # 服务组
        try:
            servgroup_res = HillstoneFsm.servgroup_proc(path=path)
            servgroup_result = []
            for i in servgroup_res:
                i['hostip'] = self.hostip
                self.servgroup_map[i['servgroup']] = i['services']
                # if i['Service'] == 'FTP':
                #     i['Service'] = '21'
                # elif i['Service'] == 'HTTP':
                #     i['Service'] = '80'
                # elif i['Service'] == 'HTTPS':
                #     i['Service'] = '443'
                servgroup_result.append(i)
            if servgroup_result:
                servgroup_mongo.delete_many(query=dict(hostip=self.hostip))
                servgroup_mongo.insert_many(servgroup_result)
        except Exception as e:
            print('山石配置文件服务组解析异常', str(e))
            MongoNetOps.failed_log(
                ip=self.hostip,
                fsm_flag='hillstone',
                cmd='servgroup',
                version=str(e))
        # slb
        try:
            slb_server_res = HillstoneFsm.slb_server_proc(path=path)
            # 如果没有需要清空
            if slb_server_res:
                slb_server_result = []
                for i in slb_server_res:
                    if i['POOLNAME'] in self.slb_map.keys():
                        self.slb_map[i['POOLNAME']].append(i)
                    else:
                        self.slb_map[i['POOLNAME']] = [i]
                    i['hostip'] = self.hostip
                    slb_server_result.append(i)
                if slb_server_result:
                    slb_server_mongo.delete_many(query=dict(hostip=self.hostip))
                    slb_server_mongo.insert_many(slb_server_result)
            else:
                slb_server_mongo.delete_many(query=dict(hostip=self.hostip))
        except Exception as e:
            print('山石配置文件SLB解析异常', str(e))
            MongoNetOps.failed_log(
                ip=self.hostip,
                fsm_flag='hillstone',
                cmd='slb_server',
                version=str(e))
        # 聚合组
        try:
            aggr_group_res = HillstoneFsm.aggr_group(path=path)
            aggr_group_result = dict()
            aggre_datas = []
            if aggr_group_res:
                aggregate_group = list(
                    set([x['aggregate'] for x in aggr_group_res]))
                if aggregate_group:
                    for aggr_key in aggregate_group:
                        if aggr_key:
                            for member in aggr_group_res:
                                if member['aggregate'] == aggr_key:
                                    if aggr_key not in aggr_group_result.keys():
                                        aggr_group_result[aggr_key] = [
                                            {member['INTF']: member['status']}]
                                    else:
                                        aggr_group_result[aggr_key].append(
                                            {member['INTF']: member['status']})
            for k, v in aggr_group_result.items():
                # print(k, v)
                # {'aggregate2': [{'xethernet4/0': ''}, {'xethernet4/1': ''}],
                #  'aggregate1': [{'ethernet0/3': ''}, {'ethernet0/5': ''}]}
                member_list = []
                member_status = []
                for member in v:
                    for mem_k, mem_v in member.items():
                        member_list.append(mem_k)
                        tmp_status = 'Up' if mem_v != 'shutdown' else 'shutdown'
                        member_status.append(tmp_status)
                tmp = dict(hostip=self.hostip,
                           aggregroup=k,
                           memberports=member_list,
                           status=member_status,
                           mode='')
                aggre_datas.append(tmp)
            if aggre_datas:
                aggr_group_mongo.delete_many(query=dict(hostip=self.hostip))
                aggr_group_mongo.insert_many(aggre_datas)
        except Exception as e:
            print('山石配置文件聚合组解析异常', str(e))
            MongoNetOps.failed_log(
                ip=self.hostip,
                fsm_flag='hillstone',
                cmd='aggr_group',
                version=str(e))
        # 系统配置项映射
        try:
            # 获取系统预定义服务集合
            service_predefined_res = service_predefined_mongo.find(query_dict=dict(hostip=self.hostip),
                                                                   fileds={"_id": 0})
            # 系统预定义服务映射集
            if service_predefined_res:
                for _service_predefined in service_predefined_res:
                    if _service_predefined['name'] in self.service_predefined_map.keys():
                        self.service_predefined_map[_service_predefined['name']].append(
                            _service_predefined)
                    else:
                        self.service_predefined_map[_service_predefined['name']] = [
                            _service_predefined]
            # 地址数据映射集
            # address_res = address_mongo.find(
            #     query_dict=dict(hostip=self.hostip), fileds={"_id": 0})
            # if address_res:
            #     for _addr in address_res:
            #         if _addr['name'] in self.address_map.keys():
            #             self.address_map[_addr['name']].append(_addr)
            #         else:
            #             self.address_map[_addr['name']] = [_addr]
            # 服务组数据映射集 假设服务组不存在重名，直接map映射进字典
            # servgroup_res = servgroup_mongo.find(
            #     query_dict=dict(hostip=self.hostip), fileds={"_id": 0})
            # if servgroup_res:
            #     for _sergroup in servgroup_res:
            #         self.servgroup_map[_sergroup['servgroup']] = _sergroup['services']
            # 服务对象数据映射集 假设服务不存在重名，直接map映射进字典
            # service_res = service_mongo.find(
            #     query_dict=dict(hostip=self.hostip), fileds={"_id": 0})
            # if service_res:
            #     for _service in service_res:
            #         self.service_map[_service['name']] = _service['items']

            # slb_res = slb_server_mongo.find(
            #     query_dict=dict(
            #         hostip=self.hostip), fileds={
            #         "_id": 0})
            # if slb_res:
            #     for _slb in slb_res:
            #         if _slb['POOLNAME'] in self.slb_map.keys():
            #             self.slb_map[_slb['POOLNAME']].append(_slb)
            #         else:
            #             self.slb_map[_slb['POOLNAME']] = [_slb]
        except Exception as e:
            send_msg_netops('山石配置文件配置项解析异常\n设备:{}\n异常:{}'.format(self.hostip, str(e)))
        # DNAT表项拼接
        try:
            dnat_res = HillstoneFsm.dnat_proc(path=path)
            if not isinstance(dnat_res, list):
                send_msg_netops("山石防火墙:{} DNAT表项解析为空".format(self.hostip))
            self._dnat_proc(dnat_res)
        except Exception as e:
            # print(traceback.print_exc())
            send_msg_netops('山石配置文件DNAT拼接解析异常\n设备:{}\n异常:{}'.format(self.hostip, str(e)))
        # SNAT表项拼接
        try:
            snat_res = HillstoneFsm.snat_proc(path=path)
            if isinstance(snat_res, list) and len(snat_res) > 0:
                self._snat_proc(snat_res)
            else:
                send_msg_netops('山石配置文件SNAT没有正常解析\n设备:{}'.format(self.hostip))
        except Exception as e:
            print(traceback.print_exc())
            send_msg_netops('山石配置文件SNAT拼接解析异常\n设备:{}\n异常:{}'.format(self.hostip, str(e)))

    def _hillstone_service_predefined(self, res):
        service_predefined_res = []
        for i in res:
            i['hostip'] = self.hostip
            if re.match("^\\d+-\\d+", i['dstport']):
                """
                参考10.254.12.251
                配置文件摘要如下：
                AFS                               TCP         7002-7009                 -        -
                需要识别出端口范围并生成range遍历添加
                {'name': 'AFS', 'protocol': 'TCP', 'dstport': ['7002', '7003', '7004', '7005', '7006', '7007', '7008', '7009'], 'srcport': '-', 'timeout': '-'}
                """
                dstport_start = int(i['dstport'].split('-')[0])
                dstport_end = int(i['dstport'].split('-')[1])
                service_list = [str(item) for item in
                                range(dstport_start, dstport_end + 1)]
                for _tmp_service in service_list:
                    service_predefined_res.append(dict(
                        name=i['name'],
                        protocol=i['protocol'].lower(),
                        dstport=_tmp_service,
                        srcport=i['srcport'],
                        timeout=i['timeout'],
                        dstport_start=dstport_start,
                        dstport_end=dstport_end,
                        hostip=self.hostip
                    ))
            else:
                service_predefined_res.append(i)
        if service_predefined_res:
            service_predefined_mongo = MongoOps(
                db='Automation', coll='hillstone_service_predefined')
            service_predefined_mongo.delete_many(query=dict(hostip=self.hostip))
            service_predefined_mongo.insert_many(service_predefined_res)
        return

    def _zone_proc(self, res):
        for i in res:
            i['hostip'] = self.hostip
        MongoNetOps.insert_table(
            db='Automation',
            hostip=self.hostip,
            datas=res,
            tablename='hillstone_zone')
        return

    def path_map(self, file_name, res: list):
        fsm_map = {
            'show_arp': self._arp_proc,
            'show_mac': self._mac_proc,
            'show_zone': self._zone_proc,
            'show_version': self._version_proc,
            'show_interface': self._interface_proc,
            'show_service_predefined': self._hillstone_service_predefined,
        }
        if file_name in fsm_map.keys():
            fsm_map[file_name](res)
        else:
            send_msg_netops("设备:{}\n命令:{}\n不被解析".format(self.hostip, file_name))

    def _collection_analysis(self, paths: list):
        # self.cmds += ['display mac-address']
        for path in paths:
            if path['cmd_file'] == 'show_configuration':
                self._configfile_proc(path['path'])
            else:
                res = BatManMain.info_fsm(path=path['path'], fsm_platform=self.fsm_flag)
                self.path_map(path['cmd_file'], res)
        if self.dnat_data:
            MongoNetOps.insert_table(
                'Automation', self.hostip, self.dnat_data, 'DNAT', True)
        if self.dnat_result:
            MongoNetOps.insert_table(
                'Automation', self.hostip, self.dnat_result, 'hillstone_dnat', True)
        if self.snat_data:
            MongoNetOps.insert_table(
                'Automation', self.hostip, self.snat_data, 'SNAT', True)
        if self.snat_result:
            MongoNetOps.insert_table(
                'Automation', self.hostip, self.snat_result, 'hillstone_snat', True)
