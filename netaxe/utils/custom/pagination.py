# -*- coding: utf-8 -*-

"""
@author: 猿小天

@contact: QQ:1638245306

@Created on: 2020/4/16 23:35
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
