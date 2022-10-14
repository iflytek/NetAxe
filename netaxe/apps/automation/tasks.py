# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      tasks
   Description:
   Author:          Lijiamin
   date：           2022/9/8 09:32
-------------------------------------------------
   Change Activity:
                    2022/9/8 09:32
-------------------------------------------------
"""
from __future__ import absolute_import, unicode_literals

import json
import logging
import math
import re
import subprocess
import time
import traceback
from celery import shared_task
from netboost.celery import AxeTask
from collections import OrderedDict
from django_celery_results.models import TaskResult
from django.core.cache import cache
from django.db import connections
from datetime import datetime, date
from apps.asset.models import AssetAccount, NetworkDevice
from apps.int_utilization.models import InterfaceUsedNew
from apps.automation.tools.h3c import H3cProc
from apps.automation.tools.hillstone import HillstoneProc
from apps.automation.tools.huawei import HuaweiProc
from apps.automation.tools.maipu import MaipuProc
from apps.automation.tools.cisco import CiscoProc
from apps.automation.tools.mellanox import MellanoxProc
from apps.automation.tools.ruijie import RuijieProc
from apps.automation.tools.centec import CentecProc
from apps.automation.tools.model_api import get_device_info_v2
from utils.netops_api import netOpsApi
from utils.db.mongo_ops import MongoOps, MongoNetOps


logger = logging.getLogger('celery')


class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        # if isinstance(obj, datetime.datetime):
        #     return int(mktime(obj.timetuple()))
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


arp_mongo = MongoOps(db='Automation', coll='ARPTable')
mac_mongo = MongoOps(db='Automation', coll='MACTable')
lagg_mongo = MongoOps(db='Automation', coll='AggreTable')
lldp_mongo = MongoOps(db='Automation', coll='LLDPTable')
cmdb_mongo = MongoOps(db='Automation', coll='networkdevice')
show_ip_mongo = MongoOps(db='Automation', coll='layer3interface')
log_mongo = MongoOps(db='logs', coll='xumi_time_cost')
interface_mongo = MongoOps(db='Automation', coll='layer2interface')


def clear_his_collect_res():
    # 清空定位成功数据
    # 清空testfsm记录
    MongoOps(db='Automation', coll='collect_textfsm_info').delete()
    # 清空netconf失败记录
    MongoOps(db='Automation', coll='netconf_failed').delete()
    netconf_db = MongoOps(db='NETCONF', coll='netconf_interface_ipv4v6')
    netconf_tables = netconf_db.all_table()
    for netconf_table in netconf_tables:
        MongoOps(db='NETCONF', coll=netconf_table).delete()
    return


@shared_task(base=AxeTask, once={'graceful': True})
def interface_used(device_ip=None):
    connections.close_all()
    """
    接口利用率最新分析表
    :return:
    """
    # 接口利用率落库mongo
    interface_log_mongo = MongoOps(db='logs', coll='interface_used_log')
    interface_log_mongo.delete()
    data_time = datetime.now()

    def data_to_table(**data: any) -> None:
        """
        执行落库和写缓存
        :param data:
        :return:
        """
        hostip = data['hostip']
        try:
            if 'chassis' in data.keys():
                dev_obj = NetworkDevice.objects.filter(
                    manage_ip=data['hostip'], chassis=data['chassis'], status=0).values(
                    'id', 'manage_ip', 'name').first()
                data.pop('chassis')
            elif 'slot' in data.keys():
                dev_obj = NetworkDevice.objects.filter(
                    manage_ip=data['hostip'], slot=data['slot'], status=0).values(
                    'id', 'manage_ip', 'name').first()
                data.pop('slot')
            else:
                dev_obj = NetworkDevice.objects.filter(
                    manage_ip=data['hostip'], status=0).values(
                    'id', 'manage_ip', 'name').first()
            if dev_obj:
                post_data = dict()
                post_data['host'] = dev_obj['name']
                post_data['host_ip'] = dev_obj['manage_ip']
                post_data['host_id'] = dev_obj['id']
                if data['int_used'] == 0:
                    post_data['utilization'] = 0
                elif data['int_total'] == 0:
                    post_data['utilization'] = 0
                else:
                    post_data['utilization'] = round(
                        (data['int_used'] / data['int_total']) * 100, 2)
                post_data['log_time'] = data_time
                data.pop('hostip')
                for k in data.keys():
                    post_data[k.lower()] = data[k]
                logger.info('落库data:{}'.format(post_data))
                try:
                    InterfaceUsedNew.objects.create(**post_data)
                    cache.set("interface_used_" + str(post_data['host_id']),
                              json.dumps(post_data, cls=JsonEncoder), 3600 * 5)
                except Exception as e:
                    interface_log_mongo.insert(
                        dict(
                            hostip=hostip,
                            msg=str(e),
                            post_data=post_data))
        except Exception as e:
            interface_log_mongo.insert(
                dict(
                    hostip=hostip,
                    msg='get数据错误未得到唯一对象' +
                        str(e)))
        return
    # 单独调试使用
    if device_ip:
        hosts = [device_ip]
    else:
        # 获取设备列表然后去重
        host_list = interface_mongo.find(fileds={'_id': 0, 'hostip': 1})
        # 所有待分析接口利用率的网络设备
        hosts = list(set([x['hostip'] for x in host_list]))
    for host in hosts:
        print(host)
        # 获取接口cmdb信息
        host_cmdb = cmdb_mongo.find(query_dict=dict(manage_ip=host, status=0),
                                    fileds={'_id': 0, 'slot': 1, 'chassis': 1})
        chassis_res = list(set([x['chassis'] for x in host_cmdb]))
        slot_res = list(set([x['slot'] for x in host_cmdb]))
        # 获取接口2层列表
        tmp = interface_mongo.find(
            query_dict=dict(
                hostip=host), fileds={
                '_id': 0})
        # 获取接口speed去重后的指标
        speed_list = list(set([x['speed'] for x in tmp])
                          )  # ['40G', '10G', '1G']
        # 判断堆叠
        mongo_res_slot = []
        for i in tmp:
            if i['interface'].startswith('lo'):
                continue
            elif i['interface'].startswith('mgmt'):
                continue
            elif i['interface'].startswith('AggregatePort'):
                continue
            _tmp_slot = i['interface'].split('/')[0]
            mongo_res_slot.append(int(_tmp_slot[-1]))
        mongo_res_slot = list(set(mongo_res_slot))
        print(mongo_res_slot, slot_res)
        if len(mongo_res_slot) == len(slot_res) and mongo_res_slot == slot_res:
            print('匹配独立设备')
            # 用于存储根据slot作为key ，接口列表作为value的 key-value结构
            _tmp_res = dict()
            for _slot in mongo_res_slot:
                _tmp_res[_slot] = []
                for i in tmp:
                    _int_slot = i['interface'].split('/')[0]
                    if _slot == int(_int_slot[-1]):
                        _tmp_res[_slot].append(i)
            for k_slot, v in _tmp_res.items():
                host_final_res = dict()
                host_final_res['int_total'] = 0
                host_final_res['int_used'] = 0
                host_final_res['int_unused'] = 0
                for key in speed_list:
                    if not key:
                        continue
                    if key == '1000m' or key == '1000M':
                        key = '1G'
                    elif key == '10000m' or key == '10000M':
                        key = '10G'
                    host_final_res['int_used_' + key] = 0
                    host_final_res['int_unused_' + key] = 0
                    for i in v:
                        if i['status'] == 'up' or i['status'] == 'UP':
                            if i['speed'] == key:
                                host_final_res['int_total'] += 1  # 接口总数
                                host_final_res['int_used_' + key] += 1  # 速率使用
                                host_final_res['int_used'] += 1  # 总使用
                        elif i['status'] == 'down' or i['status'] == 'DOWN':
                            if i['speed'] == key:
                                host_final_res['int_total'] += 1
                                host_final_res['int_unused_' + key] += 1
                                host_final_res['int_unused'] += 1
                print(k_slot, host_final_res)
                host_final_res['hostip'] = host
                host_final_res['slot'] = k_slot
                data_to_table(**host_final_res)
                # interface_res_mongo.insert(host_final_res)
        elif len(mongo_res_slot) == len(chassis_res) and mongo_res_slot == chassis_res:
            print('匹配框式')
            # 用于存储根据slot作为key ，接口列表作为value的 key-value结构
            _tmp_res = dict()
            for _slot in mongo_res_slot:
                _tmp_res[_slot] = []
                for i in tmp:
                    _int_slot = i['interface'].split('/')[0]
                    if _slot == int(_int_slot[-1]):
                        _tmp_res[_slot].append(i)
            for k_slot, v in _tmp_res.items():
                host_final_res = dict()
                host_final_res['int_total'] = 0
                host_final_res['int_used'] = 0
                host_final_res['int_unused'] = 0
                for key in speed_list:
                    if not key:
                        continue
                    if key == '1000m' or key == '1000M':
                        key = '1G'
                    elif key == '10000m' or key == '10000M':
                        key = '10G'
                    host_final_res['int_used_' + key] = 0
                    host_final_res['int_unused_' + key] = 0
                    for i in v:
                        if i['status'] == 'up' or i['status'] == 'UP':
                            if i['speed'] == key:
                                host_final_res['int_total'] += 1  # 接口总数
                                host_final_res['int_used_' + key] += 1  # 速率使用
                                host_final_res['int_used'] += 1  # 总使用
                        elif i['status'] == 'down' or i['status'] == 'DOWN':
                            if i['speed'] == key:
                                host_final_res['int_total'] += 1
                                host_final_res['int_unused_' + key] += 1
                                host_final_res['int_unused'] += 1
                print(k_slot, host_final_res)
                host_final_res['hostip'] = host
                host_final_res['chassis'] = k_slot
                data_to_table(**host_final_res)
                # interface_res_mongo.insert(host_final_res)
        else:
            print('slot不匹配')
            host_final_res = dict()
            host_final_res['hostip'] = host
            host_final_res['int_total'] = 0
            host_final_res['int_used'] = 0
            host_final_res['int_unused'] = 0
            for key in speed_list:
                if not key:
                    continue
                if key == '1000m' or key == '1000M':
                    key = '1G'
                elif key == '10000m' or key == '10000M':
                    key = '10G'
                host_final_res['int_used_' + key] = 0
                host_final_res['int_unused_' + key] = 0
                for i in tmp:
                    if i['status'] == 'up' or i['status'] == 'UP':
                        if i['speed'] == key:
                            host_final_res['int_total'] += 1  # 接口总数
                            host_final_res['int_used_' + key] += 1  # 速率使用
                            host_final_res['int_used'] += 1  # 总使用
                    elif i['status'] == 'down' or i['status'] == 'DOWN' or i['status'] == 'Administratively DOWN':
                        if i['speed'] == key:
                            host_final_res['int_total'] += 1
                            host_final_res['int_unused_' + key] += 1
                            host_final_res['int_unused'] += 1
            data_to_table(**host_final_res)
            # print(host_final_res)

    # send_msg_netops("完成{}个IP地址对应网络设备的接口利用率更新".format(str(len(hosts))))
    return


def standard_analysis_main():
    start_time = time.time()
    # mac地址合法性检查，正则匹配
    mac_kwargs = {'macaddress': re.compile('(\\w+-\\w+-\\w+)')}
    total_arp_tmp = arp_mongo.find_re(
        mac_kwargs,
        fileds={
            '_id': 0,
            'ipaddress': 1})
    total_arp_res = [x['ipaddress'] for x in total_arp_tmp]
    total_layer3ip_tmp = show_ip_mongo.find(fileds={'_id': 0, 'ipaddress': 1})
    total_layer3ip_res = [x['ipaddress'] for x in total_layer3ip_tmp]
    public_scan_tmp = MongoOps(
        db='logs',
        coll='scan_port_res').find_re(
        mac_kwargs,
        fileds={
            '_id': 0,
            'global_ip': 1})
    public_scan_res = [x['global_ip'] for x in public_scan_tmp]
    total_ip_tmp = list(set(total_arp_res)) + list(set(total_layer3ip_res)) + list(set(public_scan_res))
    # total_ip_tmp = MongoOps(db='Automation', coll='ARPTable').find(fileds={'_id': 0, 'ipaddress': 1})
    # total_ip_res = list(set([x['ipaddress'] for x in total_ip_tmp]))
    # result = OrderedDict()
    # # 多字典合并去重
    # for item in total_ip_tmp:
    #     result.setdefault(item, {**item})
    # xunmi_res = list(result.values())
    xunmi_res = [dict(ipaddress=x) for x in total_ip_tmp]
    # 所有IP明细存入mongo, 作为后面地址定位源数据
    total_ip_mongo = MongoOps(db='Automation', coll='Total_ip_list')
    total_ip_mongo.delete()
    total_ip_mongo.insert_many(xunmi_res)
    # ip地址统计信息存入monggo，首页显示
    ip_state_mongo = MongoOps(db='netops', coll='server_ip_statistics')
    ip_state_mongo.insert(dict(
        total=len(xunmi_res), log_time=datetime.today().strftime("%Y-%m-%d")
    ))
    total_time = (time.time() - start_time) / 60
    return


def datas_to_cache():
    # 获取ARP表的所有数据 tables 用来汇总查询条件
    tables = {
        'ARPTable': {'_id': 0, 'ipaddress': 1, 'idc_name': 1, 'hostip': 1, 'macaddress': 1, 'interface': 1},
        'MACTable': {'_id': 0, 'idc_name': 1, 'interface': 1, 'hostip': 1, 'macaddress': 1},
        'AggreTable': {'_id': 0, 'memberports': 1, 'hostip': 1, 'aggregroup': 1},
        'LLDPTable': {'_id': 0, 'neighborsysname': 1, 'hostip': 1, 'local_interface': 1, 'neighbor_ip': 1},
        'layer3interface': {'_id': 0, 'ipaddress': 1, 'hostip': 1},
    }
    init_time = time.time()
    start_time = time.time()

    # cmdb 以 name 作为key
    def cmdb_to_cache():
        cmdb_res = cmdb_mongo.find(query_dict={'status': 0}, fileds={'_id': 0, 'manage_ip': 1, 'name': 1})
        cmdb_result = dict()
        for _asset in cmdb_res:
            if _asset['name'] is not None:
                if _asset['name'] in cmdb_result.keys():
                    cmdb_result[_asset['name']].append(_asset)
                else:
                    cmdb_result[_asset['name']] = [_asset]
        for _asset in cmdb_result.keys():
            cache.set(
                "cmdb_" + _asset,
                json.dumps(
                    cmdb_result[_asset]),
                3600 * 12)

    # arp 以 arp_ + ip 作为key
    def arp_to_cache():
        # arp_mongo = MongoOps(db='Automation', coll='ARPTable')
        arp_res = arp_mongo.find(fileds={'_id': 0, 'log_time': 0})
        arp_result = dict()
        for _arp in arp_res:
            if _arp['ipaddress'] in arp_result.keys():
                arp_result[_arp['ipaddress']].append(_arp)
            else:
                arp_result[_arp['ipaddress']] = [_arp]
        for _arp in arp_result.keys():
            cache.set("arp_" + _arp, json.dumps(arp_result[_arp]), 3600 * 12)

    # mac地址 以 idc + mac 地址作为key
    def mac_to_cache():
        # mac_mongo = MongoOps(db='Automation', coll='MACTable')
        mac_res = mac_mongo.find(
            fileds={
                '_id': 0,
                'idc_name': 1,
                'interface': 1,
                'hostip': 1,
                'macaddress': 1})
        mac_result = dict()
        for _mac in mac_res:
            if _mac['idc_name'] + '_' + \
                    _mac['macaddress'] in mac_result.keys():
                mac_result[_mac['idc_name'] + '_' +
                           _mac['macaddress']].append(_mac)
            else:
                mac_result[_mac['idc_name'] + '_' +
                           _mac['macaddress']] = [_mac]
        for _mac in mac_result.keys():
            cache.set(
                "macaddress_" + _mac,
                json.dumps(
                    mac_result[_mac]),
                3600 * 12)

    # lagg 以 hostip aggregroup 作为key
    def lagg_to_cache():
        # lagg_mongo = MongoOps(db='Automation', coll='AggreTable')
        lagg_res = lagg_mongo.find(fileds=tables['AggreTable'])
        lagg_result = dict()
        for _lagg in lagg_res:
            if _lagg['hostip'] + '_' + \
                    _lagg['aggregroup'] in lagg_result.keys():
                lagg_result[_lagg['hostip'] + '_' +
                            _lagg['aggregroup']].append(_lagg)
            else:
                lagg_result[_lagg['hostip'] + '_' +
                            _lagg['aggregroup']] = [_lagg]
        for _lagg in lagg_result.keys():
            cache.set(
                "lagg_" + _lagg,
                json.dumps(
                    lagg_result[_lagg]),
                3600 * 12)

    # lldp 以 hostip local_interface 作为key
    def lldp_to_cache():
        # lldp_mongo = MongoOps(db='Automation', coll='LLDPTable')
        lldp_res = lldp_mongo.find(fileds=tables['LLDPTable'])
        lldp_result = dict()
        for _lldp in lldp_res:
            if _lldp['hostip'] + '_' + \
                    _lldp['local_interface'] in lldp_result.keys():
                lldp_result[_lldp['hostip'] + '_' +
                            _lldp['local_interface']].append(_lldp)
            else:
                lldp_result[_lldp['hostip'] + '_' +
                            _lldp['local_interface']] = [_lldp]
        for _lldp in lldp_result.keys():
            cache.set(
                "lldp_" + _lldp,
                json.dumps(
                    lldp_result[_lldp]),
                3600 * 12)

    # layer3interface以 hostip ipaddress 作为key
    def layer3interface_to_cache():
        # show_ip_mongo = MongoOps(db='Automation', coll='layer3interface')
        show_ip_res = show_ip_mongo.find(fileds=tables['layer3interface'])
        show_ip_result = dict()
        for _show_ip in show_ip_res:
            if _show_ip['hostip'] + '_' + \
                    _show_ip['ipaddress'] in show_ip_result.keys():
                show_ip_result[_show_ip['hostip'] + '_' +
                               _show_ip['ipaddress']].append(_show_ip)
            else:
                show_ip_result[_show_ip['hostip'] + '_' +
                               _show_ip['ipaddress']] = [_show_ip]
        for _show_ip in show_ip_result.keys():
            cache.set(
                "layer3interface_" + _show_ip,
                json.dumps(
                    show_ip_result[_show_ip]),
                3600 * 12)

    cmdb_to_cache()
    content = ''
    content += "{}缓存耗时{}秒\n".format('CMDB', int(time.time() - start_time))
    start_time = time.time()
    arp_to_cache()
    # print("{}缓存耗时{}秒\n".format('ARP地址库', int(time.time() - start_time)))
    content += "{}缓存耗时{}秒\n".format('ARP地址库', int(time.time() - start_time))
    start_time = time.time()
    mac_to_cache()
    # print("{}缓存耗时{}秒\n".format('mac地址库', int(time.time() - start_time)))
    content += "{}缓存耗时{}秒\n".format('MAC地址库', int(time.time() - start_time))
    start_time = time.time()
    lagg_to_cache()
    # print("{}缓存耗时{}秒\n".format('聚合端口库', int(time.time() - start_time)))
    content += "{}缓存耗时{}秒\n".format('聚合端口库', int(time.time() - start_time))
    start_time = time.time()
    lldp_to_cache()
    # print("{}缓存耗时{}秒\n".format('LLDP库', int(time.time() - start_time)))
    content += "{}缓存耗时{}秒\n".format('LLDP库', int(time.time() - start_time))
    start_time = time.time()
    layer3interface_to_cache()
    # print("{}缓存耗时{}秒\n".format('三层接口地址库', int(time.time() - start_time)))
    content += "{}缓存耗时{}秒\n".format('三层接口地址库', int(time.time() - start_time))
    content += "{}缓存耗时{}秒\n".format('总写入', int(time.time() - init_time))
    # send_msg_netops(content)
    return


class MainIn:
    # 获取netops CMDB 网络设备信息，并写Mongodb
    @staticmethod
    def cmdb_to_mongo():
        # 获取所有服务器信息
        _netOpsApi = netOpsApi()
        netops_results = _netOpsApi.get_all_device(limit=9000)
        # 获取Netops CMDB服务器数据
        MongoNetOps.post_cmdb(netops_results)
        return


def ping(host):
    i = subprocess.call('ping -c 1 {0}'.format(host), shell=True, stdout=open('/dev/null', 'w'),
                        stderr=subprocess.STDOUT)
    if i == 0:
        # print('已开始执行: {0}'.format(host))
        return True
    if i != 0:
        print('无法Ping通: {0}'.format(host))
        return False


@shared_task(base=AxeTask, once={'graceful': True})
def collect_device(**kwargs):
    connections.close_all()
    hostip = kwargs['manage_ip']  # 设备管理IP地址
    if hostip == '0.0.0.0':
        return {}
    plan = kwargs.get('plan_id', '')
    # todo 后期移动到上层调用的时候过滤掉
    if not plan:
        # send_msg_netops("设备:{}\n未关联数据采集方案".format(hostip))
        return {}
    if not kwargs['auto_enable']:
        # send_msg_netops("设备:{}\n未启用自动化纳管功能".format(hostip))
        return {}
    vendor_alias = kwargs['vendor__alias']  # 设备厂商名称（英文  别名）
    if vendor_alias == 'H3C':
        _H3cProc = H3cProc(**kwargs)
        _H3cProc.collection_run()
    elif vendor_alias == 'Huawei':
        _HuaweiProc = HuaweiProc(**kwargs)
        _HuaweiProc.collection_run()
    elif vendor_alias == 'Hillstone':
        _HillstoneProc = HillstoneProc(**kwargs)
        _HillstoneProc.collection_run()
    elif vendor_alias == 'Mellanox':
        _MellanoxProc = MellanoxProc(**kwargs)
        _MellanoxProc.collection_run()
    elif vendor_alias == 'centec':
        _CentecProc = CentecProc(**kwargs)
        _CentecProc.collection_run()
    elif vendor_alias == 'Ruijie':
        _RuijieProc = RuijieProc(**kwargs)
        _RuijieProc.collection_run()
    elif vendor_alias == 'Maipu':
        _MaipuProc = MaipuProc(**kwargs)
        _MaipuProc.collection_run()
    elif vendor_alias == 'Cisco':
        _CiscoProc = CiscoProc(**kwargs)
        _CiscoProc.collection_run()
    return


# 通用信息采集主调度任务
@shared_task(base=AxeTask, once={'graceful': True})
def collect_device_main(**kwargs):
    logger.info('开始执行信息采集主调度任务')
    MainIn.cmdb_to_mongo()
    if kwargs:
        hosts = get_device_info_v2(**kwargs)
    else:
        hosts = get_device_info_v2()
    logger.info('获取所有设备信息结束')
    # 参数初始化
    net_tower_tasks = []  # 寻觅任务id集合
    ping_result = []  # ping不通设备存储
    # 清空所有采集数据
    clear_his_collect_res()
    start_time = time.time()
    # 批量下发任务
    for host in hosts:
        if host['idc__name'] == 'B3寰宇':
            continue
        if ping(host['manage_ip']):
            # 必须是私有地址
            # _ip = netaddr.IPAddress(host['manage_ip'])
            # if _ip.is_private():
            net_tower_tasks.append(
                collect_device.apply_async(
                    kwargs=host,
                    queue='config',
                    retry=True))
        else:
            ping_result.append(host['manage_ip'])
    logger.info('批量下发任务结束')

    # 去除结果中的<EagerResult: None>
    for task in net_tower_tasks:
        if 'EagerResult' in str(type(task)):
            logger.info("存在无效task")
            net_tower_tasks.remove(task)

    # 获取tasks任务数量
    net_tower_tasks_counters = len(net_tower_tasks)
    net_tower_tasks_bak = net_tower_tasks.copy()

    # 等待子任务全部执行结束后执行下一步
    while len(net_tower_tasks) != 0:
        for i in net_tower_tasks:
            try:
                if i.ready():
                    net_tower_tasks.remove(i)
            except Exception as e:
                logger.error(str(e))
                net_tower_tasks.remove(i)
        time.sleep(10)
    logger.info('子任务全部执行结束')

    # 获取子任务执行结果，处理后发送
    FAILURE_TASK = []  # 失败任务
    for task_id in net_tower_tasks_bak:
        try:
            task_result = TaskResult.objects.filter(task_id=task_id).values('task_args', 'task_kwargs', 'status',
                                                                            'result')
            task_status = list(task_result)[0]['status']  # str
            if task_status == 'FAILURE':  # celery执行失败
                FAILURE_TASK.append((task_id, task_status))
                logger.error(
                    'celery执行失败,\ntask_id:{},\ntask_status{}\n'.format(
                        task_id, task_status))
        except Exception as e:  # 查询task_results失败
            FAILURE_TASK.append((task_id, e))
            logger.error(
                '查询task_results失败,\nTask_id:{},\nERROR:{}\n'.format(
                    task_id, e))
    logger.info('子任务执行结果查询结束')
    # 采集失败任务数量
    failed_logs_mongo = MongoOps(db='Automation', coll='collect_failed_logs')
    failed_res = failed_logs_mongo.find(fileds={'_id': 0})  # type int
    failed_res_list = [x['ip'] for x in failed_res]
    # netconf 失败数
    failed_netconf_mongo = MongoOps(db='Automation', coll='netconf_failed')
    failed_netconf_res = failed_netconf_mongo.find(
        fileds={'_id': 0})  # type int
    failed_netconf_list = [x['ip'] for x in failed_netconf_res]
    # 结果发送微信、邮箱
    total_time = (time.time() - start_time) / 60
    send_message = '设备数据采集分析结束:\n任务总数: {}\ncelery任务失败数：{}\n采集失败数：{} 详见mongo collect_failed_logs\n' \
                   'netconf 失败设备:{}\nPing不通设备：{}\n总耗时：{}分钟\n' \
        .format(net_tower_tasks_counters, len(FAILURE_TASK), '\n'.join(failed_res_list), '\n'.join(failed_netconf_list),
                '\n'.join(ping_result), int(total_time))
    logger.info(send_message)
    datas_to_cache()
    standard_analysis_main()
    interface_used.apply_async()
    return