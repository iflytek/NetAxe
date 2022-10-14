# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      urls
   Description:
   Author:          Lijiamin
   date：           2022/9/1 16:53
-------------------------------------------------
   Change Activity:
                    2022/9/1 16:53
-------------------------------------------------
"""
from django.urls import path

from apps.config_center import views

app_name = 'config_center'

urlpatterns = [
    # 配置文件目录树
    path('git_config/', views.GitConfig.as_view(), name='git_config'),
]
