from django.contrib import admin
from .models import Topology, TopologyHost
# Register your models here.


class AdminTopologyHost(admin.ModelAdmin):
    """拓扑图子表"""
    list_display = ['name', 'host']
    search_fields = ['name', 'host']


class AdminTopology(admin.ModelAdmin):
    """拓扑图总表"""
    list_display = ['name', 'bgbu_list', 'add_datetime']
    search_fields = ['name', 'bgbu_list', 'add_datetime']


admin.site.register(TopologyHost, AdminTopologyHost)
admin.site.register(Topology, AdminTopology)