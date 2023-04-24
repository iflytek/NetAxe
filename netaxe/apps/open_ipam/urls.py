from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SubnetHostsView, AvailableIpView, SubnetAddressView, IpAmSubnetTreeView, IpAmHandleView

router = DefaultRouter()

urlpatterns = [
    path(r'', include(router.urls)),
    path('subnet_tree/', IpAmSubnetTreeView.as_view(), name='subnet_tree'),  # get_subnet_tree
    path('address_handel/', IpAmHandleView.as_view(), name='address_handle'),  # ip_addr_handle
    path('subnet/<str:subnet_id>/ip_address/', SubnetAddressView.as_view(), name='subnet_ip_address'),
    path('subnet/<str:subnet_id>/hosts/', SubnetHostsView.as_view(), name='hosts'),  # admin- ip_addr_by_subnet_id
    path('subnet/<str:subnet_id>/get-next-available-ip/', AvailableIpView.as_view(), name='get_next_available_ip'),
]
