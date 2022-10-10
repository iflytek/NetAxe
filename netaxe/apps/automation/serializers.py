# 自动化设备数据采集方案清单
from rest_framework import serializers

from apps.automation.models import CollectionPlan


class CollectionPlanSerializer(serializers.ModelSerializer):

    @staticmethod
    def setup_eager_loading(queryset):
        """ Perform necessary eager loading of data. """
        # queryset = queryset.prefetch_related('relate_device')

        return queryset

    class Meta:
        model = CollectionPlan
        fields = '__all__'
