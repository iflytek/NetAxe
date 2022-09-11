# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      authentication
   Description:
   Author:          Lijiamin
   date：           2022/7/29 11:06
-------------------------------------------------
   Change Activity:
                    2022/7/29 11:06
-------------------------------------------------
"""
import datetime
from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from rest_framework import exceptions
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache

EXPIRE_MINUTES = getattr(settings, 'REST_FRAMEWORK_TOKEN_EXPIRE_MINUTES', 60)



class ExpiringTokenAuthentication(TokenAuthentication):
    """Set up token expired time"""

    def authenticate_credentials(self, key):
        # Search token in cache
        cache_user = cache.get(key)
        if cache_user:
            return (cache_user, key)

        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))

        time_now = datetime.datetime.now()

        if token.created < time_now - datetime.timedelta(minutes=EXPIRE_MINUTES):
            token.delete()
            raise exceptions.AuthenticationFailed(_('Token has expired then delete.'))

        if token:
            # Cache token
            cache.set(key, token.user, EXPIRE_MINUTES * 60)

        return (token.user, token)
