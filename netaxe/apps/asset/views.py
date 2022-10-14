import json
import os
from datetime import date

import django_filters
from django.views import View
from django.http import JsonResponse, FileResponse, Http404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, permissions, filters

from netboost.settings import MEDIA_ROOT
from apps.route_backend.views import LimitSet
from utils.tools.custom_pagination import LargeResultsSetPagination
from apps.asset.models import Idc, AssetAccount, Vendor, Role, Category, Model, Attribute, Framework, NetworkDevice, \
    IdcModel, NetZone
from apps.asset.serializers import IdcSerializer, AssetAccountSerializer, AssetVendorSerializer, RoleSerializer, \
    CategorySerializer, ModelSerializer, AttributeSerializer, FrameworkSerializer, NetworkDeviceSerializer, \
    IdcModelSerializer


# asset  import export excel
class ResourceManageExcelView(View):

    def get(self, request):
        try:
            file_path = os.path.join(MEDIA_ROOT, 'cmdbExcelTemplate/import-demo.xlsx')
            response = FileResponse((open(file_path, 'rb')))
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment;filename="import-demo.xlsx"'
            return response
        except Exception:
            raise Http404


# asset IDC
class IdcViewSet(viewsets.ModelViewSet):
    """
    IDC 处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = Idc.objects.all().order_by('-id')
    serializer_class = IdcSerializer
    # permission_classes = (permissions.IsAuthenticated,)
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LargeResultsSetPagination
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = '__all__'
    # 设置搜索的关键字
    search_fields = '__all__'


class NetZoneFilter(django_filters.FilterSet):
    """模糊字段过滤"""

    # vendor = django_filters.CharFilter(lookup_expr='icontains')
    # memo = django_filters.CharFilter(lookup_expr='icontains')
    # name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = NetZone
        fields = '__all__'


class IdcModelFilter(django_filters.FilterSet):
    """模糊字段过滤"""

    # vendor = django_filters.CharFilter(lookup_expr='icontains')
    # memo = django_filters.CharFilter(lookup_expr='icontains')
    # name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = IdcModel
        fields = '__all__'


class CmdbIdcModelViewSet(viewsets.ModelViewSet):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = IdcModel.objects.all().order_by('id')
    queryset = IdcModelSerializer.setup_eager_loading(queryset)
    serializer_class = IdcModelSerializer
    # permission_classes = (permissions.IsAuthenticated,)
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LargeResultsSetPagination
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_class = IdcModelFilter
    # filter_fields = '__all__'
    # list_cache_key_func = QueryParamsKeyConstructor()


# asset account
class AccountList(viewsets.ModelViewSet):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = AssetAccount.objects.all().order_by('id')
    serializer_class = AssetAccountSerializer
    pagination_class = LimitSet
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    # 如果要允许对某些字段进行过滤，可以使用filter_fields属性。
    filter_fields = '__all__'
    # 设置搜索的关键字
    search_fields = '__all__'
    # list_cache_key_func = QueryParamsKeyConstructor()


# asset vendor
class VendorViewSet(viewsets.ModelViewSet):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = Vendor.objects.all().order_by('id')
    serializer_class = AssetVendorSerializer
    permission_classes = (permissions.IsAuthenticated,)
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    # 如果要允许对某些字段进行过滤，可以使用filter_fields属性。
    filter_fields = '__all__'
    pagination_class = LimitSet
    # 设置搜索的关键字
    search_fields = '__all__'


# asset role
class AssetRoleViewSet(viewsets.ModelViewSet):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = Role.objects.all().order_by('id')
    serializer_class = RoleSerializer
    permission_classes = (permissions.IsAuthenticated,)
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    # 如果要允许对某些字段进行过滤，可以使用filter_fields属性。
    filter_fields = '__all__'
    pagination_class = LimitSet
    # 设置搜索的关键字
    search_fields = '__all__'


class CategoryViewSet(viewsets.ModelViewSet):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    permission_classes = (permissions.IsAuthenticated,)
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    # 如果要允许对某些字段进行过滤，可以使用filter_fields属性。
    filter_fields = '__all__'
    pagination_class = LimitSet
    # 设置搜索的关键字
    search_fields = '__all__'


class ModelViewSet(viewsets.ModelViewSet):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = Model.objects.all().order_by('id')
    queryset = ModelSerializer.setup_eager_loading(queryset)
    serializer_class = ModelSerializer
    permission_classes = (permissions.IsAuthenticated,)
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = ('vendor', 'name')
    pagination_class = LimitSet


class AttributelViewSet(viewsets.ModelViewSet):
    """
    处理 设备网络属性 GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = Attribute.objects.all().order_by('id')
    serializer_class = AttributeSerializer
    permission_classes = (permissions.IsAuthenticated,)
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = '__all__'
    pagination_class = LimitSet


class FrameworkViewSet(viewsets.ModelViewSet):
    """
    处理 设备网络架构 GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = Framework.objects.all().order_by('id')
    serializer_class = FrameworkSerializer
    permission_classes = (permissions.IsAuthenticated,)
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = '__all__'
    pagination_class = LimitSet


class NetworkDeviceFilter(django_filters.FilterSet):
    """模糊字段过滤"""

    serial_num = django_filters.CharFilter(lookup_expr='icontains')
    manage_ip = django_filters.CharFilter(lookup_expr='icontains')
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = NetworkDevice
        fields = '__all__'


class NetworkDeviceViewSet(viewsets.ModelViewSet):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    logging_methods = ['POST', 'PUT', 'PATCH', 'DELETE']
    queryset = NetworkDevice.objects.all().order_by('-id')
    queryset = NetworkDeviceSerializer.setup_eager_loading(queryset)
    serializer_class = NetworkDeviceSerializer
    permission_classes = (permissions.IsAuthenticated,)
    # authentication_classes = (authentication.JWTAuthentication,)
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_class = NetworkDeviceFilter
    # filter_fields = ('asset', 'asset__idc__name', 'asset__idc_model__name', 'asset__rack__name')
    # pagination_class = LimitSet
    pagination_class = LargeResultsSetPagination
    # 设置搜索的关键字
    search_fields = ('serial_num', 'manage_ip', 'bridge_mac', 'category__name', 'role__name',
                     'name', 'vendor__name', 'idc__name', 'patch_version', 'idc_model__name', 'soft_version',
                     'model__name', 'netzone__name', 'attribute__name', 'framework__name', 'rack__name',
                     'u_location', 'memo', 'status', 'ha_status')

    # list_cache_key_func = QueryParamsKeyConstructor()

    def get_queryset(self):
        """
        expires  比 expire多一个s ，用来筛选已过期的设备数据 lt 小于  gt 大于  lte小于等于  gte 大于等于
        :return:
        """
        expires = self.request.query_params.get('expires', None)
        search_host_list = self.request.query_params.get('search_host_list', None)
        if search_host_list:
            if search_host_list.find('-') != -1:
                return self.queryset.filter(manage_ip__in=search_host_list.split('-'))
            else:
                return self.queryset.filter(manage_ip__in=[search_host_list])
            # return self.queryset.filter(manage_ip__in=search_host_list)
        if expires == '1':
            return self.queryset.filter(expire__lt=date.today())
        elif expires == '0':
            return self.queryset.filter(expire__gt=date.today())
        else:
            return self.queryset

    # 重新update方法主要用来捕获更改前的字段值并赋值给self.log
    def update(self, request, *args, **kwargs):
        print('更新', super().update(request, *args, **kwargs))
        return super().update(request, *args, **kwargs)

    # 拼接log记录中data字段前后变化
    def handle_log(self):
        # Do some stuff before saving.
        # print('before', self.log['data'])
        # print(self.request)
        if self.request.POST.get('serial_num'):
            # print('PUT记录写入')
            for key in self.request.POST.keys():
                if key == 'serial_num':
                    continue
                self.log['data'][key] += " => " + str(self.request.POST[key])
            self.log['data'].pop('serial_num')
            if self.log['data'].get('id'):
                self.log['data'].pop('id')
            if self.log['view_method'] == 'create':
                tmp = json.loads(self.log['response'])
                if isinstance(tmp['data'], dict):
                    if 'id' in tmp['data'].keys():
                        self.log['path'] += str(tmp['data']['id']) + '/'
        elif self.request.data.get('serial_num'):
            print('PATCH记录写入')
            for key in self.request.data.keys():
                if key == 'serial_num':
                    continue
                self.log['data'][key] += " => " + str(self.request.data[key])
            self.log['data'].pop('serial_num')
        super(NetworkDeviceViewSet, self).handle_log()
