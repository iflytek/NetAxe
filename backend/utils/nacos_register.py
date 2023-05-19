# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      nacos
   Description:
   Author:          Lijiamin
   date：           2023/4/14 10:41
-------------------------------------------------
   Change Activity:
                    2023/4/14 10:41
-------------------------------------------------
"""
import logging
from confload.confload import config

logger = logging.getLogger('nacos')


def nacos_init():
    if not config.local_dev:
        metadata = {
            'queue': config.queue,
            'routing_key': config.routing_key,
            'menu': config.get_default_menu,
        }
        config.registerService(serviceIp=config.server_ip,
                               servicePort=config.server_port,
                               serviceName=config.queue, groupName="default",
                               metadata=metadata)
        config.healthyCheck()


