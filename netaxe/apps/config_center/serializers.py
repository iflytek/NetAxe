# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      serializers
   Description:
   Author:          Lijiamin
   date：           2022/10/1 13:16
-------------------------------------------------
   Change Activity:
                    2022/10/1 13:16
-------------------------------------------------
"""
from rest_framework import serializers

from .models import (
    ConfigCompliance, ConfigTemplate, TTPTemplate
)


# 配置合规表
class ConfigComplianceSerializer(serializers.ModelSerializer):
    datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary eager loading of data. """
        # select_related for "to-one" relationships
        # prefetch_related for "to-many" relationships
        # queryset = queryset.select_related('config_set')
        # queryset = queryset.prefetch_related(
        #     'part')
        #
        # # Prefetch for subsets of relationships
        # queryset = queryset.prefetch_related(
        #     Prefetch('unaffiliated_attendees',
        #              queryset=NetworkDevice.objects.filter(organization__isnull=True))
        # )
        return queryset

    class Meta:
        model = ConfigCompliance
        fields = '__all__'


# 配置模板表
class ConfigTemplateSerializer(serializers.ModelSerializer):
    """配置模板表"""
    datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    class Meta:
        model = ConfigTemplate
        fields = '__all__'


# TTP模板表
class TTPTemplateSerializer(serializers.ModelSerializer):
    """TTP模板表"""
    datetime = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    class Meta:
        model = TTPTemplate
        fields = '__all__'
