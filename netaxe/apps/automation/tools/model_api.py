# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      model_api
   Description:
   Author:          Lijiamin
   date：           2022/9/8 11:02
-------------------------------------------------
   Change Activity:
                    2022/9/8 11:02
-------------------------------------------------
"""
from collections import OrderedDict
from django.db import connections
from apps.asset.models import NetworkDevice, AssetAccount
from utils.crypt_pwd import CryptPwd


# 获取登录网络设备所需相关信息
def get_device_info_v2(**kwargs):
    hosts = []
    _CryptPwd = CryptPwd()  # 密码解码
    support_vendor = [
        'H3C', 'Huawei', 'Ruijie', 'Maipu', 'Hillstone', 'Mellanox', 'centec', 'Cisco', 'CISCO', 'cisco'
    ]
    if kwargs:
        kwargs['status'] = 0
        kwargs['auto_enable'] = True
        all_devs = NetworkDevice.objects.filter(**kwargs).select_related(
            'idc_model', 'model', 'role', 'attribute', 'category', 'vendor', 'idc', 'framework', 'plan', 'zone',
            'rack').prefetch_related('bgbu', 'bind_ip', 'adpp_device').values(
            'id', 'serial_num', 'manage_ip', 'name', 'vendor__name', 'soft_version', 'vendor__alias', 'plan_id',
            'category__name', 'framework__name', 'model__name', 'account',
            'patch_version', 'soft_version', 'status', 'idc__name', 'auto_enable',
            'ha_status', 'chassis', 'slot', 'bind_ip__ipaddr')
    else:
        # 获取所有cmdb设备
        all_devs = NetworkDevice.objects.filter(
            status=0, vendor__alias__in=support_vendor, auto_enable=True).select_related(
            'idc_model', 'model', 'role', 'attribute', 'category', 'vendor', 'idc', 'framework', 'plan', 'zone',
            'rack').prefetch_related('bgbu', 'bind_ip', 'account').values(
            'id', 'serial_num', 'manage_ip', 'name', 'soft_version', 'vendor__name', 'vendor__alias',
            'category__name', 'framework__name', 'model__name', 'plan_id',
            'patch_version', 'soft_version', 'status', 'idc__name', 'auto_enable',
            'ha_status', 'chassis', 'slot')  # bind_ip__ipaddr
    # 获取中文标识的port、username、password表，方便处理
    # 过滤需要设备:在线,主设备或独立设备,有管理ip,支持的类型
    for dev in all_devs:
        try:
            tmp_account = AssetAccount.objects.filter(networkdevice__id=dev['id']).values(
                'networkdevice__account__name',
                'networkdevice__account__username',
                'networkdevice__account__password',
                'networkdevice__account__protocol',
                'networkdevice__account__port',
                'networkdevice__account__en_pwd',
            )
            tmp_protocol = []
            for _account in tmp_account:
                _protocol = _account["networkdevice__account__protocol"].lower()
                if _protocol in ['ssh', 'telnet', 'netconf']:
                    dev[_protocol] = dict()
                    dev[_protocol]['username'] = _account["networkdevice__account__username"]
                    dev[_protocol]['password'] = _CryptPwd.decrypt_pwd(_account["networkdevice__account__password"])
                    dev[_protocol]['port'] = _account["networkdevice__account__port"]
                    tmp_protocol.append(_protocol)
            tmp_protocol = list(set(tmp_protocol))
            dev['protocol'] = tmp_protocol
            hosts.append(dev)
        except Exception as e:
            print(e)
    result = OrderedDict()
    for item in hosts:
        result.setdefault(item['manage_ip'], {**item})
    connections.close_all()
    return list(result.values())
