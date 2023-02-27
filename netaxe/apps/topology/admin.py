from django.contrib import admin
from .models import Topology
# Register your models here.


class AdminTopology(admin.ModelAdmin):
    """拓扑图总表"""
    list_display = ['name', 'bgbu_list']
    search_fields = ['name', 'bgbu_list']


admin.site.register(Topology, AdminTopology)