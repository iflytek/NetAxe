# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      routing
   Description:
   Author:          Lijiamin
   date：           2022/7/29 15:03
-------------------------------------------------
   Change Activity:
                    2022/7/29 15:03
-------------------------------------------------
"""
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from apps.asset.consumers import WebSshConsumer

application = ProtocolTypeRouter({

    "websocket": AuthMiddlewareStack(
        URLRouter(
            [
                re_path(r'ws/ssh/([0-9]+)/', WebSshConsumer),
                # path('ws/ssh/1/', WebSshConsumer),
            ]
        ),
    )
})
