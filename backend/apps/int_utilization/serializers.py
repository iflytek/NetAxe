from rest_framework import serializers

from .models import InterfaceUsedNew


class InterfaceUsedNewSerializer(serializers.ModelSerializer):
    """接口利用率序列化"""
    log_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    class Meta:
        model = InterfaceUsedNew
        fields = '__all__'
