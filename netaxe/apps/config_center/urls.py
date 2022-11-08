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
from django.urls import path, include
from rest_framework_extensions.routers import (
    ExtendedDefaultRouter as DefaultRouter
)

from apps.config_center import views

app_name = 'config_center'
router = DefaultRouter()

router.register(r'config_compliance', views.ConfigComplianceViewSet)
router.register(r'config_template', views.ConfigTemplateViewSet)
router.register(r'ttp_template', views.TTPTemplateViewSet)

urlpatterns = [
    path(r'api/', include(router.urls)),
    # 配置文件目录树
    path('git_config/', views.GitConfig.as_view(), name='git_config'),
    path('compliance_results', views.ComplianceResults.as_view(), name='compliance_results'),
    path('test_regex', views.RegexTest.as_view(), name='test_regex'),
    path('ttp_parse', views.TTPParse.as_view(), name='ttp_parse'),
    path('fsm_parse', views.TextFSMParse.as_view(), name='fsm_parse'),
    path('jinja2_parse', views.Jinja2View.as_view(), name='jinja2_parse'),
]
