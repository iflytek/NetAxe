# Create your views here.
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from utils.tools.custom_pagination import LargeResultsSetPagination
from .models import BgBu
from .serializers import BgBuSerializer


class BgBuViewSet(viewsets.ModelViewSet):
    """
    BgBu表---处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = BgBu.objects.all().order_by('name')
    serializer_class = BgBuSerializer
    permission_classes = (permissions.IsAuthenticated,)
    # pagination_class = LimitSet
    pagination_class = LargeResultsSetPagination
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    # 如果要允许对某些字段进行过滤，可以使用filter_fields属性。
    # filterset_class = DeviceBackupConfigFilter
    filter_fields = '__all__'