from django.contrib import admin
from .models import NavigationProfile, NavigationSubProfile


# Register your models here.


class AdminNavigationProfile(admin.ModelAdmin):
    """自定义设备表显示字段"""
    list_display = ['menuName', 'menuUrl', 'icon', 'parentPath', 'iconPrefix', 'showOrder']
    search_fields = ['menuName', 'menuUrl', 'icon', 'parentPath', 'iconPrefix', 'showOrder']


class AdminNavigationSubProfile(admin.ModelAdmin):
    """自定义设备表显示字段"""
    list_display = ['menuName', 'menuUrl', 'badge', 'parent', 'showOrder', 'cacheable']
    search_fields = ['menuName', 'menuUrl', 'badge', 'showOrder']


admin.site.register(NavigationProfile, AdminNavigationProfile)
admin.site.register(NavigationSubProfile, AdminNavigationSubProfile)
