# -*- coding: utf-8 -*-
# @Time    : 2020/11/12 18:26
# @Author  : LiJiaMin
# @Site    : 
# @File    : custom_pagination.py
# @Software: PyCharm

from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from collections import OrderedDict
from rest_framework.response import Response


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


# class LargeResultsSetPagination(PageNumberPagination):
#     """
#
#     """
#     def get_paginated_response(self, data):
#         code = 200
#         msg = 'success'
#         if not data:
#             code = 404
#             msg = "Data Not Found"
#         return Response(OrderedDict([
#             ('code', code),
#             ('msg', msg),
#             ('count', self.page.paginator.count),
#             ('next', self.get_next_link()),
#             ('previous', self.get_previous_link()),
#             ('results', data)
#         ]))