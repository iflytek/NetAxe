from django.urls import path, include
from rest_framework import routers

from apps.users.views.user import UserViewSet


router = routers.SimpleRouter()
router.register(r'user', UserViewSet)

urlpatterns = [
    path(r'', include(router.urls)),
]