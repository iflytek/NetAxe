from __future__ import absolute_import, unicode_literals

import sys

import pymysql

from utils.custom.nacos import nacos
from . import settings
from .celery import app as celery_app

# Fake PyMySQL's version and install as MySQLdb
# https://adamj.eu/tech/2020/02/04/how-to-use-pymysql-with-django/
pymysql.version_info = (1, 4, 2, "final", 0)
pymysql.install_as_MySQLdb()

__all__ = ['celery_app']
if sys.argv[1] not in ["makemigrations", "migrate"]:
    # 注册服务
    nacosServer = nacos(ip=settings.SERVERIP, port=8848)
    nacosServer.registerService(serviceIp=settings.SERVERIP, servicePort=settings.SERVERPORT, serviceName="auth", groupName="default")
    nacosServer.healthyCheck()