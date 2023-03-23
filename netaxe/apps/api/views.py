from django.shortcuts import render

# Create your views here.
import json

from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from rest_framework import viewsets, permissions, filters, pagination

from .serializers import PeriodicTaskSerializer
from .tools.custom_viewset_base import CustomViewBase
# from rest_framework_extensions.cache.mixins import CacheResponseMixin
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework_extensions.cache.mixins import BaseCacheResponseMixin, CacheResponseMixin
# from rest_framework_tracking.mixins import LoggingMixin
from .tools.custom_pagination import LargeResultsSetPagination
from apps.api.serializers import *
from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.key_constructor.constructors import (
    DefaultKeyConstructor
)
from datetime import date

from apps.automation.models import CollectionPlan
from apps.int_utilization.models import InterfaceUsedNew


class QueryParamsKeyConstructor(DefaultKeyConstructor):
    all_query_params = bits.QueryParamsKeyBit()


class LimitSet(pagination.LimitOffsetPagination):
    # 每页默认几条
    default_limit = 10
    # 设置传入页码数参数名
    page_query_param = "page"
    # 设置传入条数参数名
    limit_query_param = 'limit'
    # 设置传入位置参数名
    offset_query_param = 'start'
    # 最大每页显示条数
    max_limit = None


# class CategoryViewSet(viewsets.ModelViewSet):
#     """
#     处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
#     """
#     queryset = Category.objects.all().order_by('id')
#     serializer_class = CategorySerializer
#     permission_classes = (permissions.IsAuthenticated,)
#     # 配置搜索功能
#     filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
#     # 如果要允许对某些字段进行过滤，可以使用filter_fields属性。
#     filter_fields = '__all__'
#     pagination_class = LimitSet
#     # 设置搜索的关键字
#     search_fields = '__all__'
#
#
#
#
#
# class ModelViewSet(viewsets.ModelViewSet):
#     """
#     处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
#     """
#     queryset = Model.objects.all().order_by('id')
#     queryset = ModelSerializer.setup_eager_loading(queryset)
#     serializer_class = ModelSerializer
#     permission_classes = (permissions.IsAuthenticated,)
#     # 配置搜索功能
#     filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
#     filter_fields = ('vendor', 'name')
#     pagination_class = LimitSet
#
#
# class AttributelViewSet(viewsets.ModelViewSet):
#     """
#     处理 设备网络属性 GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
#     """
#     queryset = Attribute.objects.all().order_by('id')
#     serializer_class = AttributeSerializer
#     permission_classes = (permissions.IsAuthenticated,)
#     # 配置搜索功能
#     filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
#     filter_fields = '__all__'
#     pagination_class = LimitSet
#
#
# class FrameworkViewSet(viewsets.ModelViewSet):
#     """
#     处理 设备网络架构 GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
#     """
#     queryset = Framework.objects.all().order_by('id')
#     serializer_class = FrameworkSerializer
#     permission_classes = (permissions.IsAuthenticated,)
#     # 配置搜索功能
#     filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
#     filter_fields = '__all__'
#     pagination_class = LimitSet
#
#
# class NetworkDeviceFilter(django_filters.FilterSet):
#     """模糊字段过滤"""
#
#     serial_num = django_filters.CharFilter(lookup_expr='icontains')
#     manage_ip = django_filters.CharFilter(lookup_expr='icontains')
#     name = django_filters.CharFilter(lookup_expr='icontains')
#
#     class Meta:
#         model = NetworkDevice
#         fields = '__all__'
#
#
# class NetworkDeviceViewSet(LoggingMixin, viewsets.ModelViewSet):
#     """
#     处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
#     """
#     logging_methods = ['POST', 'PUT', 'PATCH', 'DELETE']
#     queryset = NetworkDevice.objects.all().order_by('-id')
#     queryset = NetworkDeviceSerializer.setup_eager_loading(queryset)
#     serializer_class = NetworkDeviceSerializer
#     permission_classes = (permissions.IsAuthenticated,)
#     # authentication_classes = (authentication.JWTAuthentication,)
#     # 配置搜索功能
#     filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
#     filterset_class = NetworkDeviceFilter
#     # filter_fields = ('asset', 'asset__idc__name', 'asset__idc_model__name', 'asset__rack__name')
#     # pagination_class = LimitSet
#     pagination_class = LargeResultsSetPagination
#     # 设置搜索的关键字
#     search_fields = ('serial_num', 'manage_ip', 'bridge_mac', 'category__name', 'role__name',
#                      'name', 'vendor__name', 'idc__name', 'patch_version', 'idc_model__name', 'soft_version',
#                      'model__name', 'netzone__name', 'attribute__name', 'framework__name', 'rack__name',
#                      'u_location', 'memo', 'status', 'ha_status')
#
#     # list_cache_key_func = QueryParamsKeyConstructor()
#
#     def get_queryset(self):
#         """
#         expires  比 expire多一个s ，用来筛选已过期的设备数据 lt 小于  gt 大于  lte小于等于  gte 大于等于
#         :return:
#         """
#         expires = self.request.query_params.get('expires', None)
#         search_host_list = self.request.query_params.get('search_host_list', None)
#         if search_host_list:
#             if search_host_list.find('-') != -1:
#                 return self.queryset.filter(manage_ip__in=search_host_list.split('-'))
#             else:
#                 return self.queryset.filter(manage_ip__in=[search_host_list])
#             # return self.queryset.filter(manage_ip__in=search_host_list)
#         if expires == '1':
#             return self.queryset.filter(expire__lt=date.today())
#         elif expires == '0':
#             return self.queryset.filter(expire__gt=date.today())
#         else:
#             return self.queryset
#
#     # 重新update方法主要用来捕获更改前的字段值并赋值给self.log
#     def update(self, request, *args, **kwargs):
#         return super().update(request, *args, **kwargs)
#
#     # 拼接log记录中data字段前后变化
#     def handle_log(self):
#         # Do some stuff before saving.
#         # print('before', self.log['data'])
#         # print(self.request)
#         if self.request.POST.get('serial_num'):
#             # print('PUT记录写入')
#             for key in self.request.POST.keys():
#                 if key == 'serial_num':
#                     continue
#                 self.log['data'][key] += " => " + str(self.request.POST[key])
#             self.log['data'].pop('serial_num')
#             if self.log['data'].get('id'):
#                 self.log['data'].pop('id')
#             if self.log['view_method'] == 'create':
#                 tmp = json.loads(self.log['response'])
#                 if isinstance(tmp['data'], dict):
#                     if 'id' in tmp['data'].keys():
#                         self.log['path'] += str(tmp['data']['id']) + '/'
#         elif self.request.data.get('serial_num'):
#             # print('PATCH记录写入')
#             for key in self.request.data.keys():
#                 if key == 'serial_num':
#                     continue
#                 self.log['data'][key] += " => " + str(self.request.data[key])
#             self.log['data'].pop('serial_num')
#         # print(self.log)
#         super(NetworkDeviceViewSet, self).handle_log()
#         # print('after', self.log['data'])
#         # Do some stuff after saving.

# 任务列表
class PeriodicTaskViewSet(viewsets.ModelViewSet):
    # queryset = PeriodicTask.objects.all().order_by('id')
    queryset = PeriodicTask.objects.exclude(task__startswith='celery').order_by('id')
    serializer_class = PeriodicTaskSerializer
    permission_classes = (permissions.IsAuthenticated,)
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    # 如果要允许对某些字段进行过滤，可以使用filter_fields属性。
    filter_fields = '__all__'
    pagination_class = LimitSet
    # 设置搜索的关键字
    search_fields = '__all__'
    # list_cache_key_func = QueryParamsKeyConstructor()


class IntervalScheduleViewSet(CacheResponseMixin, viewsets.ModelViewSet):
    queryset = IntervalSchedule.objects.all().order_by('id')
    serializer_class = IntervalScheduleSerializer
    permission_classes = (permissions.IsAuthenticated,)
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    # 如果要允许对某些字段进行过滤，可以使用filter_fields属性。
    filter_fields = '__all__'
    pagination_class = LimitSet
    # 设置搜索的关键字
    search_fields = '__all__'
    list_cache_key_func = QueryParamsKeyConstructor()
