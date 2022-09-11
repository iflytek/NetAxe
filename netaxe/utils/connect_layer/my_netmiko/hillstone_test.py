#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/7/7 19:42
# @Author  : dingyifei


# !/usr/bin/env python

from utils.connect_layer.my_netmiko import my_netmiko


hs_fw1 = {
    'ip': '10.254.12.242',
    'device_type': 'hillstone',
    'username': '',
    'password': '',
}



# Show command that we execute
command = "display version"
with my_netmiko(**hs_fw1) as net_connect:
    # output = net_connect.send_command(
    #     command_string=command,
    # strip_command=False,
    # strip_prompt=False,
    # cmd_verify=False,
    # )
    output = net_connect.send_config_set(config_commands=['address zxpt_lt_bgp', 'ip 10.103.1.1/32'])
    print(output)

# Automatically cleans-up the output so that only the show output is returned
