from django.contrib import admin
from .models import Topology
# Register your models here.


class AdminTopology(admin.ModelAdmin):
    """拓扑图总表"""
    list_display = ['name']
    search_fields = ['name']


admin.site.register(Topology, AdminTopology)