from django.contrib import admin

# Register your models here.
from apps.system.models import Menu, Role, Dept


class MenuAdmin(admin.ModelAdmin):
    """自定义设备表显示字段"""
    list_display = ['parent', 'name', 'web_path']
    search_fields = ['parent', 'name', 'web_path']


admin.site.register(Menu, MenuAdmin)

admin.site.register(Role)
admin.site.register(Dept)
