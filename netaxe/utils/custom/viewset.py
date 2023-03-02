# -*- coding: utf-8 -*-

"""
@author: 猿小天
@contact: QQ:1638245306
@Created on: 2021/6/1 001 22:57
@Remark: 自定义视图集
"""
from django.http import JsonResponse
from django_filters import rest_framework
# from drf_yasg import openapi
# from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from django_restql.mixins import QueryArgumentsMixin

from utils.custom.filters import DataLevelPermissionsFilter
from utils.custom.json_response import SuccessResponse, ErrorResponse, DetailResponse
from utils.custom.permission import CustomPermission


class CustomModelViewSet(ModelViewSet,QueryArgumentsMixin):
    """
    自定义的ModelViewSet:
    统一标准的返回格式;新增,查询,修改可使用不同序列化器
    (1)ORM性能优化, 尽可能使用values_queryset形式
    (2)xxx_serializer_class 某个方法下使用的序列化器(xxx=create|update|list|retrieve|destroy)
    (3)filterset_fields = '__all__' 默认支持全部model中的字段查询(除json字段外)
    (4)import_field_dict={} 导入时的字段字典 {model值: model的label}
    (5)export_field_label = [] 导出时的字段
    """
    values_queryset = None
    create_serializer_class = None
    update_serializer_class = None
    search_fields = ()
    ordering_fields = '__all__'
    filterset_fields = '__all__'
    extra_filter_backends = [DataLevelPermissionsFilter]
    permission_classes = [CustomPermission]
    import_field_dict = {}
    export_field_label = []

    def filter_queryset(self, queryset):
        for backend in set(set(self.filter_backends) | set(self.extra_filter_backends or [])):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get_queryset(self):
        if getattr(self, 'values_queryset', None):
            return self.values_queryset
        return super().get_queryset()

    def get_serializer_class(self):
        action_serializer_name = f"{self.action}_serializer_class"
        action_serializer_class = getattr(self, action_serializer_name, None)
        if action_serializer_class:
            return action_serializer_class
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, request=request)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return DetailResponse(data=serializer.data, msg="新增成功")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, request=request)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True, request=request)
        return SuccessResponse(data=serializer.data, msg="获取成功")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return DetailResponse(data=serializer.data, msg="获取成功")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, request=request, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        return DetailResponse(data=serializer.data, msg="更新成功")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        request_data = request.data
        soft_delete = request_data.get('soft_delete',True)
        if soft_delete:
            instance.is_deleted = True
            instance.save()
        else:
            self.perform_destroy(instance)
        return DetailResponse(data=[], msg="删除成功")


    # keys = openapi.Schema(description='主键列表',type=openapi.TYPE_ARRAY,items=openapi.TYPE_STRING)
    # @swagger_auto_schema(request_body=openapi.Schema(
    #     type=openapi.TYPE_OBJECT,
    #     required=['keys'],
    #     properties={'keys': keys}
    # ), operation_summary='批量删除')
    @action(methods=['delete'],detail=False)
    def multiple_delete(self,request,*args,**kwargs):
        '''
        批量删除接口
        '''
        request_data = request.data
        keys = request_data.get('keys',None)
        soft_delete = request_data.get('soft_delete', True)
        if keys and soft_delete:
            self.get_queryset().filter(id__in=keys).update(is_deleted=True)
            return SuccessResponse(data=[], msg="删除成功")
        elif keys and not soft_delete:
            self.get_queryset().filter(id__in=keys).delete()
        else:
            return ErrorResponse(msg="未获取到keys字段")


class CustomViewBase(viewsets.ModelViewSet):
    queryset = ''
    serializer_class = ''
    permission_classes = ()
    filter_fields = ()
    search_fields = ()
    filter_backends = (rest_framework.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        print(request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return JsonResponse(data=serializer.data, msg="success", code=201,
                            status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(data=serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse(data=serializer.data, code=200, msg="success", status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return JsonResponse(data=serializer.data, code=200, msg="success", status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return JsonResponse(data=serializer.data, msg="success", code=200, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        # return JsonResponse(data=[], code=204, msg="delete resource success", status=status.HTTP_204_NO_CONTENT)
        return JsonResponse(data=[], code=204, msg="delete resource success", status=status.HTTP_200_OK)