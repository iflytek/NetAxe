from django.contrib import admin

# Register your models here.

# class AdminUserProfileModel(admin.ModelAdmin):
#     """自定义机房表显示字段"""
#     list_display = ['name', 'floor', 'area', 'idc']
#     search_fields = ['name', 'floor', 'area', 'idc__name']
from apps.users.models import UserProfile

admin.site.register(UserProfile)
