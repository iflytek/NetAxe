# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      serializers
   Description:
   Author:          Lijiamin
   date：           2022/7/29 10:51
-------------------------------------------------
   Change Activity:
                    2022/7/29 10:51
-------------------------------------------------
"""
from rest_framework import serializers

from apps.asset.models import (
    Idc, NetZone, Role, IdcModel, Rack, Vendor, Category, Model,
    Attribute, Framework, AssetIpInfo, AssetAccount, NetworkDevice)


# 机房
class IdcSerializer(serializers.ModelSerializer):
    class Meta:
        model = Idc
        fields = '__all__'


# 账户表
class AssetAccountSerializer(serializers.ModelSerializer):  # 指定ModelSerializer序列化model层
    class Meta:
        model = AssetAccount  # 指定要序列化的模型
        # 指定要序列化的字段
        fields = '__all__'


# 供应商
class AssetVendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'


# 设备型号
class ModelSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)

    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary eager loading of data. """
        # select_related for "to-one" relationships
        # queryset = queryset.select_related('host')
        queryset = queryset.select_related('vendor')
        return queryset

    class Meta:
        model = Model
        fields = '__all__'


# 网络属性
class AttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = '__all__'


# 网络架构
class FrameworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Framework
        fields = '__all__'


# 设备类型
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


# 网络区域
class NetZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetZone
        fields = '__all__'


# 设备角色
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


# 机房机柜
class CmdbRackSerializer(serializers.ModelSerializer):
    idc_model_name = serializers.CharField(source='idc_model.name', read_only=True)
    idc_name = serializers.CharField(source='idc_model.idc.name', read_only=True)

    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary eager loading of data. """
        queryset = queryset.select_related('idc_model', 'idc_model__idc')
        return queryset

    class Meta:
        model = Rack
        fields = '__all__'


# 机房模块
class IdcModelSerializer(serializers.ModelSerializer):

    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary eager loading of data. """
        # select_related for "to-one" relationships
        # queryset = queryset.select_related('host')
        queryset = queryset.select_related('idc')
        return queryset

    class Meta:
        model = IdcModel
        fields = '__all__'


# 网络设备绑定IP信息
class AssetIpInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetIpInfo
        fields = '__all__'


# 网络设备
class NetworkDeviceSerializer(serializers.ModelSerializer):

    plan_name = serializers.CharField(source='plan.name', read_only=True)
    idc_name = serializers.CharField(source='idc.name', read_only=True)
    nvwa_idc_name = serializers.CharField(source='idc.nvwa_name', read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    vendor_alias = serializers.CharField(source='vendor.alias', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)
    framework_name = serializers.CharField(source='framework.name', read_only=True)
    netzone_name = serializers.CharField(source='zone.name', read_only=True)
    rack_name = serializers.CharField(source='rack.name', read_only=True)
    rack_row = serializers.CharField(source='rack.rack_row', read_only=True)
    idc_model_name = serializers.CharField(source='idc_model.name', read_only=True)
    idc_model_floor = serializers.CharField(source='idc_model.floor', read_only=True)
    idc_model_area = serializers.CharField(source='idc_model.area', read_only=True)
    # adpp_device = serializers.StringRelatedField(many=True, read_only=True)
    bind_ip = serializers.StringRelatedField(many=True, read_only=True)
    # bgbu = BgBuSerializer(many=True)
    # 针对choices的处理
    status_name = serializers.CharField(source='get_status_display', read_only=True)
    ha_status_name = serializers.CharField(source='get_ha_status_display', read_only=True)

    class Meta:
        model = NetworkDevice
        fields = '__all__'

    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary eager loading of data. """
        # select_related for "to-one" relationships
        queryset = queryset.select_related('idc_model',
                                           'model',
                                           'role',
                                           'attribute',
                                           'category',
                                           'vendor',
                                           'idc',
                                           'framework',
                                           'zone',
                                           'rack')
        queryset = queryset.prefetch_related(
            'bind_ip', 'account')
        return queryset
