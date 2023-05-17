# -*- coding: utf-8 -*-
'''
@Time    : 2022/9/9 10:37
@Author  : xhweng
@File    : async_auth.py

'''

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from rest_framework.authtoken.models import Token
from rest_framework_jwt.authentication import jwt_decode_handler


def authenticate(jwt_value):
    try:
        payload = jwt_decode_handler(jwt_value)
        username = payload.get('username')
        if username:
            User = get_user_model()
            user = User.objects.get(username=username)
            return user
    except Exception:
        pass
    return AnonymousUser()


@database_sync_to_async
def get_user(headers):
    try:
        items = headers[b'cookie'].decode().split("; ")
        cookie_json = {}
        for i in items:
            splis = i.split("=")
            if len(splis) == 2:
                cookie_json[splis[0]] = splis[1]
        token = cookie_json.get("token")
        if token:
            return authenticate(token)

    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware:

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return JWTAuthMiddlewareInstance(scope, self)


class JWTAuthMiddlewareInstance:
    """
    Yeah, this is black magic:
    https://github.com/django/channels/issues/1399
    """

    def __init__(self, scope, middleware):
        self.middleware = middleware
        self.scope = dict(scope)
        self.inner = self.middleware.inner

    async def __call__(self, receive, send):
        headers = dict(self.scope['headers'])

        if b'cookie' in headers:
            user = await get_user(headers)
            if user != None:
                self.scope['user'] = user

        inner = self.inner(self.scope)
        return await inner(receive, send)


JWTAuthMiddlewareStack = lambda inner: JWTAuthMiddleware(AuthMiddlewareStack(inner))
