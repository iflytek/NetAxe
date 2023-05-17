# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      urls
   Description:
   Author:          Lijiamin
   date：           2022/7/29 10:44
-------------------------------------------------
   Change Activity:
                    2022/7/29 10:44
-------------------------------------------------
"""
from django.urls import path, include
from apps.api import views
from rest_framework_extensions.routers import (
    ExtendedDefaultRouter as DefaultRouter
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView, TokenVerifyView
)
router = DefaultRouter()
#
#
#
# router.register(r'cmdb_category', views.CategoryViewSet)
# router.register(r'cmdb_model', views.ModelViewSet)
# router.register(r'attribute', views.AttributelViewSet)
# router.register(r'framework', views.FrameworkViewSet)
# router.register(r'asset_networkdevice', views.NetworkDeviceViewSet)
router.register(r'periodic_task', views.PeriodicTaskViewSet)
router.register(r'interval_schedule', views.IntervalScheduleViewSet)
app_name = 'api'

urlpatterns = [
    # 主机列表
    path(r'', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='get_jwt_token'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh_jwt_token'),
    path('verify/', TokenVerifyView.as_view(), name='token_jwt_verify'),
]
