from django.contrib.auth.decorators import login_required
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import *

app_name = 'topology'
router = DefaultRouter()


router.register(r'index', TopologyViewSet)


urlpatterns = [
    path('show/', TopologyShow.as_view(), name='show'),
    path('topology_icon/', IconView.as_view(), name='topology_icon'),
]
