from django.contrib.auth.decorators import login_required
from django.urls import path

from apps.topology.views import Topology,  IconView

app_name = 'topology'

urlpatterns = [
    path('show/', Topology.as_view(), name='show'),
    path('topology_icon/', IconView.as_view(), name='topology_icon'),
]
