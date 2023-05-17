import json
import os
from datetime import date
import django_filters
from django.views import View
from django.http import JsonResponse, FileResponse, Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework import viewsets, filters
from netaxe.settings import MEDIA_ROOT
from apps.route_backend.views import LimitSet
from utils.crypt_pwd import CryptPwd
from apps.api.tools.custom_pagination import LargeResultsSetPagination
from apps.api.tools.custom_viewset_base import CustomViewBase
from apps.asset.models import Idc, AssetAccount, Vendor, Role, Category, Model, Attribute, Framework, NetworkDevice, \
    IdcModel, NetZone, Rack
from apps.asset.serializers import IdcSerializer, AssetAccountSerializer, AssetVendorSerializer, RoleSerializer, \
    CategorySerializer, ModelSerializer, AttributeSerializer, FrameworkSerializer, NetworkDeviceSerializer, \
    IdcModelSerializer, NetZoneSerializer, CmdbRackSerializer
from utils.cmdb_import import search_cmdb_vendor_id, search_cmdb_idc_id, search_cmdb_netzone_id, search_cmdb_role_id, \
    search_cmdb_idc_model_id, search_cmdb_cabinet_id, search_cmdb_category_id, search_cmdb_attribute_id, \
    search_cmdb_framework_id, returndate, csv_device_staus, pandas_read_file, old_import_parse


class ResourceManageExcelView(View):
    def post(self, request):
        file = request.FILES.get('file')
        # 获取文件位置
        filename = os.path.join(MEDIA_ROOT, 'upload', file.name)
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        with open(filename, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)
        # pandas文件内容解析
        import_content_df = pandas_read_file(filename)
        # print(import_content_df)
        import_list = []
        for i in import_content_df.values:
            import_list.append(i)

        import_res, detail = old_import_parse(import_list)
        try:
            if import_res:
                return JsonResponse({'code': 200, 'msg': '导入成功！'})
            else:
                return JsonResponse({'code': 400, 'msg': '导入失败！' + detail})
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
class IdcViewSet(CustomViewBase):
    """
    IDC 处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = Idc.objects.all().order_by('-id')
    serializer_class = IdcSerializer
    permission_classes = ()
    authentication_classes = ()
    pagination_class = LargeResultsSetPagination
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = '__all__'
    # 设置搜索的关键字
    search_fields = '__all__'


class CmdbNetzoneModelViewSet(CustomViewBase):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = NetZone.objects.all().order_by('-id')
    serializer_class = NetZoneSerializer
    permission_classes = ()
    authentication_classes = ()
    pagination_class = LargeResultsSetPagination
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = '__all__'
    # 设置搜索的关键字
    search_fields = '__all__'


class CmdbRackModelViewSet(CustomViewBase):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = Rack.objects.all().order_by('id')
    # queryset = NetZoneSerializer.setup_eager_loading(queryset)
    serializer_class = CmdbRackSerializer
    # permission_classes = (permissions.IsAuthenticated,)
    permission_classes = ()
    pagination_class = LargeResultsSetPagination
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = '__all__'


class CmdbIdcModelViewSet(CustomViewBase):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = IdcModel.objects.all().order_by('id')
    queryset = IdcModelSerializer.setup_eager_loading(queryset)
    serializer_class = IdcModelSerializer
    # permission_classes = (permissions.IsAuthenticated,)
    permission_classes = ()
    pagination_class = LargeResultsSetPagination
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = '__all__'


# asset account
class AccountList(CustomViewBase):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = AssetAccount.objects.all().order_by('id')
    serializer_class = AssetAccountSerializer
    pagination_class = LimitSet
    permission_classes = ()
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    # 如果要允许对某些字段进行过滤，可以使用filter_fields属性。
    filter_fields = '__all__'
    # 设置搜索的关键字
    search_fields = '__all__'
    # list_cache_key_func = QueryParamsKeyConstructor()


# asset vendor
class VendorViewSet(CustomViewBase):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = Vendor.objects.all().order_by('id')
    serializer_class = AssetVendorSerializer
    permission_classes = ()
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    # 如果要允许对某些字段进行过滤，可以使用filter_fields属性。
    filter_fields = '__all__'
    pagination_class = LimitSet
    # 设置搜索的关键字
    search_fields = '__all__'


# asset role
class AssetRoleViewSet(CustomViewBase):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = Role.objects.all().order_by('id')
    serializer_class = RoleSerializer
    permission_classes = ()
    authentication_classes = ()
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    # 如果要允许对某些字段进行过滤，可以使用filter_fields属性。
    filter_fields = '__all__'
    pagination_class = LimitSet
    # 设置搜索的关键字
    search_fields = '__all__'


class CategoryViewSet(CustomViewBase):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = Category.objects.all().order_by('id')
    serializer_class = CategorySerializer
    permission_classes = ()
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    # 如果要允许对某些字段进行过滤，可以使用filter_fields属性。
    filter_fields = '__all__'
    pagination_class = LimitSet
    # 设置搜索的关键字
    search_fields = '__all__'


class ModelViewSet(CustomViewBase):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = Model.objects.all().order_by('id')
    queryset = ModelSerializer.setup_eager_loading(queryset)
    serializer_class = ModelSerializer
    permission_classes = ()
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = ('vendor', 'name')
    pagination_class = LimitSet


class AttributelViewSet(CustomViewBase):
    """
    处理 设备网络属性 GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = Attribute.objects.all().order_by('id')
    serializer_class = AttributeSerializer
    permission_classes = ()
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = '__all__'
    pagination_class = LimitSet


class FrameworkViewSet(CustomViewBase):
    """
    处理 设备网络架构 GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = Framework.objects.all().order_by('id')
    serializer_class = FrameworkSerializer
    permission_classes = ()
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


class NetworkDeviceViewSet(CustomViewBase):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = NetworkDevice.objects.all().order_by('-id')
    queryset = NetworkDeviceSerializer.setup_eager_loading(queryset)
    serializer_class = NetworkDeviceSerializer
    permission_classes = ()
    authentication_classes = ()
    # authentication_classes = (authentication.JWTAuthentication,)
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    # filterset_class = NetworkDeviceFilter
    filter_fields = ('serial_num', 'manage_ip', 'bridge_mac', 'category__name', 'role__name',
                     'name', 'vendor__name', 'idc__name', 'patch_version', 'idc_model__name', 'soft_version',
                     'model__name', 'netzone__name', 'attribute__name', 'framework__name', 'rack__name',
                     'u_location', 'memo', 'status', 'ha_status')
    # pagination_class = LimitSet
    pagination_class = LargeResultsSetPagination
    # 设置搜索的关键字
    search_fields = ('serial_num', 'manage_ip', 'bridge_mac', 'category__name', 'role__name',
                     'name', 'vendor__name', 'idc__name', 'patch_version', 'idc_model__name', 'soft_version',
                     'model__name', 'netzone__name', 'attribute__name', 'framework__name', 'rack__name',
                     'u_location', 'memo', 'status', 'ha_status')

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
    # def update(self, request, *args, **kwargs):
    #     print('更新', super().update(request, *args, **kwargs))
    #     return super().update(request, *args, **kwargs)
