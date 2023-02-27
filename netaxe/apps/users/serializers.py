# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      serializers
   Description:
   Author:          Lijiamin
   date：           2023/2/27 20:25
-------------------------------------------------
   Change Activity:
                    2023/2/27 20:25
-------------------------------------------------
"""
import json
from rest_framework import serializers
from .models import BgBu

class BgBuSerializer(serializers.ModelSerializer):
    """bgbu表，用于运营平台数据对应关系"""

    class Meta:
        model = BgBu
        fields = ('id', 'name',)

