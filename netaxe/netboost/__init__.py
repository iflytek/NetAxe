from __future__ import absolute_import, unicode_literals
import logging
import pymysql
import threading
from .celery import app as celery_app
from utils.custom.nacos import nacos

logger = logging.getLogger('server')

# Fake PyMySQL's version and install as MySQLdb
# https://adamj.eu/tech/2020/02/04/how-to-use-pymysql-with-django/
pymysql.version_info = (1, 4, 2, "final", 0)
pymysql.install_as_MySQLdb()

# 注册服务
nacosServer = nacos(ip="10.254.2.188", port=8848)
nacosServer.registerService(serviceIp="10.254.2.188", servicePort="8001", serviceName="auth", groupName="default")
nacosServer.healthyCheck()

__all__ = ['celery_app']