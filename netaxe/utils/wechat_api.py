# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      wechat_api
   Description:
   Author:          Lijiaminn
   date：           2022/9/1 16:19
-------------------------------------------------
   Change Activity:
                    2022/9/1 16:19
-------------------------------------------------
"""

import json
import os
import traceback
import requests
from django.core.cache import cache
from netaxe.settings import BASE_DIR


def send_msg_network(msg):
    try:
        print(msg)
        # _weichat = weiChatApi()
        # tmp = _weichat.send_msg('alarm_m', msg)
        # tmp = json.loads(tmp.text)
        # if tmp['errcode'] == 45009:
        #     _weichat.send_msg('alarm_b', msg)
    except Exception as e:
        print(e)
        # _weichat = weiChatApi()
        # _weichat.send_msg_to_netops(msg)
    return

# 外部调用这个方法，里面自带消息达上限后的备份机制
def send_msg_netops(msg):
    try:
        print(msg)
        # _weichat = weiChatApi()
        # _weichat.send_msg_to_netops(msg)
        # _weichat.send_msg('platform', msg)
    except Exception as e:
        # print(traceback.print_exc())
        print(e)
    return


if __name__ == '__main__':
    pass
    # _wechat = weiChatApi()
    # _wechat.send_msg_to_netops('test')
