from __future__ import absolute_import, unicode_literals
import pymysql
from .celery import app as celery_app

# Fake PyMySQL's version and install as MySQLdb
# https://adamj.eu/tech/2020/02/04/how-to-use-pymysql-with-django/
pymysql.version_info = (1, 4, 2, "final", 0)
pymysql.install_as_MySQLdb()

__all__ = ['celery_app']