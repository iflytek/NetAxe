# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      init_asset
   Description:
   Author:          Lijiamin
   date：           2022/9/8 16:36
-------------------------------------------------
   Change Activity:
                    2022/9/8 16:36
-------------------------------------------------
"""
import json
import os
import django
from django.core.management import BaseCommand
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'netaxe.settings')
django.setup()
from netaxe.settings import BASE_DIR
from apps.route_backend.models import NavigationProfile, NavigationSubProfile


def main():
    with open(os.path.join(BASE_DIR, 'utils', 'init_route.json'), 'r', encoding="utf-8") as load_f:
        code_list = json.load(load_f)
        for table, values in code_list.items():
            if table == 'NavigationSubProfile':
                for v in values:
                    NavigationSubProfile.objects.get_or_create(**v)
            if table == 'NavigationProfile':
                for v in values:
                    NavigationProfile.objects.get_or_create(**v)


class Command(BaseCommand):
    """
    项目初始化命令: python manage.py init_route
    """

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        print(f"正在准备初始化导航数据...")
        main()
        print("数据初始化导航数据完成！")
