# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      urls
   Description:
   Author:          Lijiamin
   date：           2022/7/29 10:57
-------------------------------------------------
   Change Activity:
                    2022/7/29 10:57
-------------------------------------------------
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

app_name = 'resources_manage'

router = DefaultRouter()

router.register(r'cmdb_idc', IdcViewSet)
router.register(r'cmdb_account', AccountList)
router.register(r'cmdb_vendor', VendorViewSet)
router.register(r'cmdb_role', AssetRoleViewSet)
router.register(r'cmdb_category', CategoryViewSet)
router.register(r'cmdb_model', ModelViewSet)
router.register(r'attribute', AttributelViewSet)
router.register(r'framework', FrameworkViewSet)
router.register(r'asset_networkdevice', NetworkDeviceViewSet)

urlpatterns = [
    path(r'api/', include(router.urls)),
    path('excel/', ResourceManageExcelView.as_view(), name='excel'),
]
