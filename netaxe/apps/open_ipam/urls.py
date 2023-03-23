from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework.routers import DefaultRouter

from .views import SubnetHostsView, AvailableIpView, SubnetApiViewSet, IpAddressApiViewSet, SubnetAddressView, \
    IpAmSubnetTreeView, PeriodicTaskViewSet, IpAmHandelView, IntervalScheduleViewSet

router = DefaultRouter()
#
router.register(r'subnet_list', SubnetApiViewSet)  # 获取子网段列表
router.register(r'ip_address_list', IpAddressApiViewSet)
router.register(r'periodic_task', PeriodicTaskViewSet)
router.register(r'interval_schedule', IntervalScheduleViewSet)
urlpatterns = [
    path(r'', include(router.urls)),
    path('subnet_tree/', IpAmSubnetTreeView.as_view(), name='subnet_tree'),
    path('address_handel/', csrf_exempt(IpAmHandelView.as_view()), name='address_handel'),
    path('subnet/<str:subnet_id>/ip_address/', SubnetAddressView.as_view(), name='subnet_ip_address'),
    path('subnet/<str:subnet_id>/hosts/', SubnetHostsView.as_view(), name='hosts'),
    path(
        'subnet/<str:subnet_id>/get-next-available-ip/',
        AvailableIpView.as_view(),
        name='get_next_available_ip',
    ),
]
