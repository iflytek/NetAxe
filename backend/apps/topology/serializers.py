# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      serializers
   Description:
   Author:          Lijiamin
   date：           2023/2/27 20:24
-------------------------------------------------
   Change Activity:
                    2023/2/27 20:24
-------------------------------------------------
"""
from rest_framework import serializers
from .models import Topology


# 拓扑表
class TopologySerializer(serializers.ModelSerializer):
    add_datetime = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = Topology
        fields = '__all__'
