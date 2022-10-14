import django_filters
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, permissions, filters, pagination

from .models import InterfaceUsedNew
from .serializers import InterfaceUsedNewSerializer
from utils.tools.custom_viewset_base import CustomViewBase
from utils.tools.custom_pagination import LargeResultsSetPagination


class InterfaceUsedFilter(django_filters.FilterSet):
    log_time = django_filters.CharFilter(lookup_expr='icontains')
    host = django_filters.CharFilter(lookup_expr='icontains')
    host_ip = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = InterfaceUsedNew
        fields = '__all__'


class InterfaceUsedNewViewSet(CustomViewBase):
    """
    接口利用率--处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = InterfaceUsedNew.objects.all().order_by('-log_time')
    # queryset = InterfaceUsedNewSerializer.setup_eager_loading(queryset)
    serializer_class = InterfaceUsedNewSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LargeResultsSetPagination
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    # 如果要允许对某些字段进行过滤，可以使用filter_fields属性。
    filterset_class = InterfaceUsedFilter
    search_fields = ('host_ip', 'host')
    ordering_fields = ('log_time', 'id')

    def get_queryset(self):
        start = self.request.query_params.get('start_time', None)
        end = self.request.query_params.get('end_time', None)
        host_id = self.request.query_params.get('host_id', None)
        interface_used = self.request.query_params.get('interface_used', None)
        if start and end:
            return self.queryset.filter(log_time__range=(start, end))

        if host_id and interface_used:
            return self.queryset.filter(host_id=host_id)
        return self.queryset
