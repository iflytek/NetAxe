# -*- coding: utf-8 -*-
'''
@Time    : 2022/9/13 20:50
@Author  : xhweng
@File    : serializers.py

'''
from django_celery_beat.models import CrontabSchedule, IntervalSchedule
from rest_framework import serializers


class CrontabSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrontabSchedule
        fields = ('minute', 'hour', 'day_of_week', 'day_of_month', 'month_of_year', 'id')


class IntervalSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntervalSchedule
        fields = ('every', 'period', 'id')