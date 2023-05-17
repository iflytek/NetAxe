from django.shortcuts import render

# Create your views here.
import json

from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from rest_framework import viewsets, permissions, filters, pagination

from apps.api.serializers import *
from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.key_constructor.constructors import (
    DefaultKeyConstructor
)


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


class IntervalScheduleViewSet(viewsets.ModelViewSet):
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
