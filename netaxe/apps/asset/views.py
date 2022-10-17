import json
import os
from datetime import date

import django_filters
from django.views import View
from django.http import JsonResponse, FileResponse, Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework_tracking.mixins import LoggingMixin
from rest_framework import viewsets, permissions, filters

from netboost.settings import MEDIA_ROOT
from apps.route_backend.views import LimitSet
from utils.crypt_pwd import CryptPwd
# from scripts.crypt_pwd import CryptPwd
from utils.excel2list import excel2list
# asset  import export excel
from utils.netops_api import netOpsApi
from utils.tools.custom_pagination import LargeResultsSetPagination
from apps.asset.models import Idc, AssetAccount, Vendor, Role, Category, Model, Attribute, Framework, NetworkDevice, \
    IdcModel, NetZone, Rack
from apps.asset.serializers import IdcSerializer, AssetAccountSerializer, AssetVendorSerializer, RoleSerializer, \
    CategorySerializer, ModelSerializer, AttributeSerializer, FrameworkSerializer, NetworkDeviceSerializer, \
    IdcModelSerializer, NetZoneSerializer, CmdbRackSerializer
from utils.cmdb_import import search_cmdb_vendor_id, search_cmdb_idc_id, search_cmdb_netzone_id, search_cmdb_role_id, \
    search_cmdb_idc_model_id, search_cmdb_cabinet_id, search_cmdb_category_id, search_cmdb_attribute_id, \
    search_cmdb_framework_id, returndate, csv_device_staus


class ResourceManageExcelView(View):
    def post(self, request):
        file = request.FILES.get('file')
        filename = os.path.join(MEDIA_ROOT, 'upload', file.name)
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        with open(filename, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)
        try:
            data_list = excel2list(filename)
            # print(data_list)

            for data in data_list:
                # 判断厂商是否存在，如 F5 Mellanox  华三  华为  山石网科  思科  成都数维  深信服  盛科  科来 锐捷
                cmdb_vendor_id = search_cmdb_vendor_id(data[2].strip())
                # 判断所属机房是否存在，如上海嘉定、北京鲁谷、北京大族、北京酒仙桥、广州新华园、合肥B3
                cmdb_idc_id = search_cmdb_idc_id(data[4].strip())
                # 判断网络区域是否存在，如生产公共区域、业务互联区域、IaaS网络区域、IPMI管理区域、公网区域、网络管理区域、
                cmdb_netzone_id = search_cmdb_netzone_id(data[5].strip())
                # 判断设备角色是否存在，如网络汇聚、业务互联、千兆电器接入、出口防火墙、Spine、Leaf、服务器
                cmdb_role_id = search_cmdb_role_id(data[8].strip())

                # 根据机房模块编号、机房ID进行检索，若机房模块不存在，则创建并返回机房模块ID
                cmdb_idc_model_id = search_cmdb_idc_model_id(data[9].strip(), cmdb_idc_id)

                # 根据机柜编号、机房ID进行检索，若机柜不存在，则创建并返回创建后机柜ID
                cmdb_cabinet_id = search_cmdb_cabinet_id(data[10].strip(), cmdb_idc_model_id)
                # 根据设备类型字段获取设备类型ID
                cmdb_category_id = search_cmdb_category_id(data[3].strip())
                cmdb_attribute_id = search_cmdb_attribute_id(data[6].strip())
                cmdb_framework_id = search_cmdb_framework_id(data[7].strip())
                # from apps.asset.models import AssetAccount
                # account = AssetAccount.objects.get(name='网管账户_带域名')
                # print('data[15]', data[15])
                networkdevices = {
                    "attribute": cmdb_attribute_id,
                    "framework": cmdb_framework_id,
                    'serial_num': data[0].strip(),
                    'manage_ip': data[1].strip(),
                    'vendor': cmdb_vendor_id,
                    'idc': cmdb_idc_id,
                    'zone': cmdb_netzone_id,
                    'role': cmdb_role_id,
                    'rack': int(cmdb_cabinet_id),
                    'idc_model': cmdb_idc_model_id,
                    'u_location_start': int(data[11].strip()),  # U位
                    'u_location_end': int(data[11].strip()),  # U位
                    # 'uptime': '2022-7-11',  # 上线时间必须要，默认当前日期
                    'uptime': str(returndate(data[15].strip())),  # 上线时间必须要，默认当前日期
                    'expire': '2099-01-01',  # 维保时间必须有，默认3年
                    'status': csv_device_staus(data[13].strip()),
                    'memo': data[12].strip() if data[12].strip() else data[1].strip() + "备注信息",  # memo为备注信息
                    'name': data[1].strip(),  # 系统名称必须有。用管理IP代替
                    'auto_enable': 'true',
                    'bgbu': [],
                    'category': cmdb_category_id,  # 设备类型字段
                }

                # print(networkdevices)
                device_obj = NetworkDevice.objects.filter(serial_num=data[0].strip())
                # print('查询结果', device_obj)
                if device_obj:
                    pass
                else:
                    netops_api = netOpsApi()
                    # print('请求新增数据')
                    res = netops_api.post_something(url="asset/asset_networkdevice/", data=networkdevices)
                    # print('新增设备结果', res.json())
                    if res.json().get('code', ''):
                        if res.json()['code'] == 400:
                            return JsonResponse({'code': 500, 'msg': '导入失败！{}'.format(res.json()['message'])})
            return JsonResponse({'code': 200, 'msg': '导入成功！'})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '导入失败！{}'.format(e)})

    def get(self, request):
        try:
            file_path = os.path.join(MEDIA_ROOT, 'cmdbExcelTemplate/import_template.xlsx')
            response = FileResponse((open(file_path, 'rb')))
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment;filename="import_template.xlsx"'
            return response
        except Exception:
            raise Http404


class DeviceAccountView(APIView):
    def post(self, request):
        post_params = request.POST.dict()
        device = NetworkDevice.objects.get(id=post_params['asset_id'])
        account_list = json.loads(post_params['account'])

        device.account.set(account_list)
        return JsonResponse({'code': 200, 'message': '关联管理账户成功'})

    def get(self, request):
        get_params = request.GET.dict()
        device = NetworkDevice.objects.get(serial_num=get_params['serial_num'])
        account_query = device.account.all()
        serializer_data = AssetAccountSerializer(account_query, many=True)
        account_list = []
        _CryptPwd = CryptPwd()
        for i in serializer_data.data:
            account_dict = {
                'name': i['name'],
                'username': i['username'],
                'protocol': i['protocol'],
                'port': i['port'],
                'password': _CryptPwd.decrypt_pwd(i['password'])
            }
            account_list.append(account_dict)
        # serializer_data = AssetAccountSerializer(account_query, many=True)

        return JsonResponse({'code': 200, 'message': '获取账户信息成功', 'results': account_list})


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


class CmdbNetzoneModelViewSet(viewsets.ModelViewSet):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = NetZone.objects.all().order_by('id')
    # queryset = NetZoneSerializer.setup_eager_loading(queryset)
    serializer_class = NetZoneSerializer
    # permission_classes = (permissions.IsAuthenticated,)
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LargeResultsSetPagination
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_class = NetZoneFilter
    # filter_fields = '__all__'
    # list_cache_key_func = QueryParamsKeyConstructor()


class RackFilter(django_filters.FilterSet):
    """模糊字段过滤"""

    # vendor = django_filters.CharFilter(lookup_expr='icontains')
    # memo = django_filters.CharFilter(lookup_expr='icontains')
    # name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Rack
        fields = '__all__'


class CmdbRackModelViewSet(viewsets.ModelViewSet):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = Rack.objects.all().order_by('id')
    # queryset = NetZoneSerializer.setup_eager_loading(queryset)
    serializer_class = CmdbRackSerializer
    # permission_classes = (permissions.IsAuthenticated,)
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LargeResultsSetPagination
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_class = RackFilter
    # filter_fields = '__all__'
    # list_cache_key_func = QueryParamsKeyConstructor()


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


class NetworkDeviceViewSet(LoggingMixin, viewsets.ModelViewSet):
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
        print('before', self.log['data'])
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
