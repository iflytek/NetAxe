# -*- coding: utf-8 -*-

"""
"""
from django.core import paginator
from django.core.paginator import Paginator as DjangoPaginator
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "limit"
    max_page_size = 999
    django_paginator_class = DjangoPaginator

    def get_paginated_response(self, data):
        res = {
            "code": 200,
            'msg': '获取成功',
            "results": data,
            "count": self.page.paginator.count,
            "limit": int(self.get_page_size(self.request)) or 10,
            "page": int(self.get_page_number(self.request, paginator)) or 1,
        }
        if not data:
            res['msg'] = "暂无数据"
            res['results'] = []
        return Response(res)


from rest_framework import pagination
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from collections import OrderedDict
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param, remove_query_param


class LargeResultsSetPagination(LimitOffsetPagination):
    # 每页默认几条
    default_limit = 10
    # 设置传入页码数参数名
    page_query_param = "page"
    # 设置传入条数参数名
    limit_query_param = 'limit'
    # 设置传入位置参数名
    offset_query_param = 'start'
    # 最大每页显示条数
    max_limit = None
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100000

    def get_paginated_response(self, data):
        code = 200
        msg = 'success'
        if not data:
            code = 404
            msg = "Data Not Found"

        return Response(OrderedDict([
            ('code', code),
            ('msg', msg),
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
        ]))


class SubnetAddressPagination(pagination.BasePagination):
    limit = 256
    start_query_param = 'start'

    def paginate_queryset(self, queryset, request, view=None):
        self.count = queryset.count()
        self.queryset = queryset
        self.request = request
        self.offset = self.get_offset(request)
        return list(queryset[self.offset: self.offset + self.limit])  # noqa

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ('next', self.get_next_link()),
                    ('previous', self.get_previous_link()),
                    ('total_count', len(data)),
                    ('used_count', len([i for i in data if i['used']])),
                    ('results', data),

                ]
            )
        )

    def get_offset(self, request):
        try:
            return self.queryset.index_of(request.query_params[self.start_query_param])
        except (KeyError, ValueError):
            return 0

    def get_next_link(self):
        if self.offset + self.limit >= self.count:
            return None
        url = self.request.build_absolute_uri()
        offset = self.offset + self.limit
        return replace_query_param(
            url, self.start_query_param, self.queryset[offset].address
        )

    def get_previous_link(self):
        if self.offset <= 0:
            return None
        url = self.request.build_absolute_uri()
        if self.offset - self.limit <= 0:
            return remove_query_param(url, self.start_query_param)
        offset = self.offset - self.limit
        return replace_query_param(
            url, self.start_query_param, self.queryset[offset].address
        )
