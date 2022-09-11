#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/7 19:36
# @Author  : dingyifei
import os

from netmiko import ssh_dispatcher

from netboost.settings import BASE_DIR
from .hillstone import HillstoneTelnet, HillstoneSSH

os.environ["NTC_TEMPLATES_DIR"] = BASE_DIR + '/utils/connect_layer/my_netmiko/templates'


def my_netmiko(*args, **kwargs):
    device_type = kwargs.get('device_type')
    if 'hillstone' == device_type:
        return HillstoneSSH(*args, **kwargs)
    elif 'hillstone_telnet' == device_type:
        return HillstoneTelnet(*args, **kwargs)
    else:
        ConnectionClass = ssh_dispatcher(device_type)
        return ConnectionClass(*args, **kwargs)
