# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      views
   Description:
   Author:          Lijiamin
   date：           2022/7/29 14:49
-------------------------------------------------
   Change Activity:
                    2022/7/29 14:49
-------------------------------------------------
"""
import base64
import datetime

from captcha.helpers import captcha_image_url
# from io import BytesIO
from captcha.models import CaptchaStore
from django.conf import settings
from django.contrib import admin
from django.contrib import auth
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.authtoken.models import Token
# from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response


EXPIRE_MINUTES = getattr(settings, 'REST_FRAMEWORK_TOKEN_EXPIRE_MINUTES', 1)


# class ObtainExpiringAuthToken(ObtainAuthToken):
#     """Create user token"""
#
#     def post(self, request, *args, **kwargs):
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid():
#             token, created = Token.objects.get_or_create(user=serializer.validated_data['user'])
#             time_now = datetime.datetime.now()
#             if created or token.created < time_now - datetime.timedelta(minutes=EXPIRE_MINUTES):
#                 # Update the created time of the token to keep it valid
#                 token.delete()
#                 token = Token.objects.create(user=serializer.validated_data['user'])
#                 token.created = time_now
#                 token.save()
#             return Response({'token': token.key})
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# obtain_expiring_auth_token = ObtainExpiringAuthToken.as_view()


# 覆盖默认的admin登录方法实现登录限流
# @ratelimit(key='ip', rate='5/h', block=True)
def extend_admin_login(request, extra_context=None):
    return admin.site.login(request, extra_context)

