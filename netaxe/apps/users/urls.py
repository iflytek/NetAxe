from django.urls import path, include
from rest_framework import routers

from apps.users.views.user import UserViewSet
from .views import BgBuViewSet


router = routers.SimpleRouter()
router.register(r'user', UserViewSet)
router.register(r'bgbu', BgBuViewSet)

urlpatterns = [
    path(r'', include(router.urls)),
]