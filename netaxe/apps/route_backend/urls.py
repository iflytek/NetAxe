from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt

from rest_framework import routers

from .views import DashboardChart, WebSshView, DeviceCollectView, AutomationChart, \
    DispatchManageView, JobCenterView, PeriodicTaskViewSet, IntervalScheduleViewSet

app_name = 'vue_backend'
router = routers.SimpleRouter()
router.register(r'periodic_task', PeriodicTaskViewSet)
router.register(r'interval_schedule', IntervalScheduleViewSet)

urlpatterns = [
    path(r'', include(router.urls)),
    path('dashboardChart/', DashboardChart.as_view(), name='dashboardChart'),
    path('deviceWebSsh/', WebSshView.as_view(), name='deviceWebSsh'),
    path('deviceCollect/', DeviceCollectView.as_view(), name='deviceCollect'),
    path('automationChart/', AutomationChart.as_view(), name='automationChart'),
    path('dispatch_page/', csrf_exempt(DispatchManageView.as_view()), name='dispatch_page'),
    path('jobCenter/', JobCenterView.as_view(), name='jobCenter'),
]
