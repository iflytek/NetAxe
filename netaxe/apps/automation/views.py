from django.shortcuts import render

# Create your views here.
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, filters, pagination
from rest_framework_tracking.mixins import LoggingMixin

from apps.api.tools.custom_viewset_base import CustomViewBase
from apps.api.views import LimitSet
from apps.automation.models import CollectionPlan
from apps.automation.serializers import CollectionPlanSerializer


class CollectionPlanViewSet(LoggingMixin, CustomViewBase):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    logging_methods = ['POST', 'PUT', 'PATCH', 'DELETE']
    queryset = CollectionPlan.objects.all().order_by('-id')
    queryset = CollectionPlanSerializer.setup_eager_loading(queryset)
    serializer_class = CollectionPlanSerializer
    permission_classes = (permissions.IsAuthenticated,)
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = '__all__'
    pagination_class = LimitSet