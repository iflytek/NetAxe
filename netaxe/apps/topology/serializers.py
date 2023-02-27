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
import json
from rest_framework import serializers
from .models import Topology


# bgbu field
class BgBuField(serializers.StringRelatedField):

    def to_internal_value(self, value):
        # print(value, type(value))
        # value = value[1:-1]
        value = json.loads(value)
        # print('解码后', value, type(value))
        # print(value, type(value))
        if isinstance(value, list):
            return value
        else:
            raise serializers.ValidationError("BGBU with name: %s not found" % value)


# 拓扑表
class TopologySerializer(serializers.ModelSerializer):
    add_datetime = serializers.DateTimeField(read_only=True, format='%Y-%m-%d %H:%M:%S')
    bgbu = BgBuField(many=True)

    class Meta:
        model = Topology
        fields = '__all__'

    def create(self, validated_data):
        """
        重写 create
        """
        bgbu = validated_data.get('bgbu')
        validated_data.pop('bgbu')
        instance = Topology.objects.create(**validated_data)
        if bgbu:
            if isinstance(bgbu[0], list) and instance:
                dev_obj = Topology.objects.get(id=instance.id)
                dev_obj.bgbu.set(bgbu[0])
        return instance

    def update(self, instance, validated_data):
        """
        重写 update
        """
        instance.name = validated_data.get('name', instance.name)
        instance.memo = validated_data.get('memo', instance.memo)
        instance.save()
        bgbu = validated_data.get('bgbu', instance.bgbu)
        if bgbu:
            if isinstance(bgbu[0], list):
                dev_obj = Topology.objects.get(id=instance.id)
                # dev_obj.bgbu.clear()
                dev_obj.bgbu.set(bgbu[0])
        return instance