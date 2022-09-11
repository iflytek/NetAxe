# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      custom_exception
   Description:
   Author:          Lijiamin
   date：           2022/7/29 11:05
-------------------------------------------------
   Change Activity:
                    2022/7/29 11:05
-------------------------------------------------
"""
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    # 这个循环是取第一个错误的提示用于渲染
    # print(response.data)
    message = ''
    if response is None:
        return response
    for index, value in enumerate(response.data):
        if index == 0:
            key = value
            value = response.data[key]
            # print('value', value, type(value[0]))
            if isinstance(value, str):
                message = value
            else:
                message = key + value[0]
    # Now add the HTTP status code to the response.
    if response is not None:
        # print("response.data", response.data, type(response.data))
        # print("response", response, type(response))
        # print(str(response.data))
        response.data.clear()
        if not response.status_code:
            response.status_code = 200
        response.data['code'] = response.status_code
        response.data['data'] = []
        if response.status_code == 404:
            try:
                # response.data['message'] = response.data.pop('detail')
                response.data['message'] = "Not found"
            except KeyError:
                response.data['message'] = "Not found"

        if response.status_code == 400:

            # response.data['message'] = 'Input error'
            response.data['message'] = message

        elif response.status_code == 401:
            response.data['message'] = "Auth failed"

        elif response.status_code >= 500:
            response.data['message'] = "Internal service errors"

        elif response.status_code == 403:
            response.data['message'] = "Access denied"

        elif response.status_code == 405:
            response.data['message'] = 'Request method error'
        response.code = response.status_code
        response.status_code = 200
    return response