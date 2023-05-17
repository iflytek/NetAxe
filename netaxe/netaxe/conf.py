# -*- coding: utf-8 -*-

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases
NACOSIP = 'nacos.netaxe.svc'
NACOSPORT = '8848'
SERVERIP = '10.254.12.169'
SERVERPORT = "31118"
DATABASES = {
    'default': {
        'NAME': 'netaxe',
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'mysql.a642146275df-mysql.svc.hfa.ipaas.cn',
        # 'HOST': '10.103.45.207',
        'USER': 'netops',
        'PASSWORD': 'Netops@2019',
        'PORT': '8066',
        # 'CONN_MAX_AGE': 21600,
        'ATOMIC_REQUESTS': True,
        'TEST_CHARSET': 'utf8mb4',
        'TEST_COLLATION': 'utf8mb4_general_ci',
        'TEST': {'NAME': 'net_axe_test',
                 'CHARTSET': 'utf8mb4',
                 'COLLATION': 'utf8mb4_general_ci'},
        'OPTIONS': {
            # 'charset': 'utf8mb4',
            "init_command": "SET default_storage_engine='INNODB'",
        }
    },
}

# REDIS_URL = "redis://:dade0f2a65237a56b79277e6dd27351d2854df033e0ad4b4f90abec229cd64df@{10.254.2.219}:6379/"
# REDIS_URL = "redis://:blsYHvXbMB@{}:32279/".format('10.254.12.169')
REDIS_URL = "redis://127.0.0.1:6379"

CACHE_PWD = ''
mongo_db_conf = {
    "host": '10.254.2.219',
    "port": 27017,
    "username": "root",
    "password": "70uUceCVL1gf"
}
netops_api = {
    "token_url": 'http://{}:8001/base_platform/token/'.format(SERVERIP),
    "base_url": 'http://{}:8001/base_platform/'.format(SERVERIP),
    "resources_manage_base_url": 'http://{}:9999/resources_manage/api/'.format(SERVERIP),
    'username': 'adminnetaxe',
    'password': 'netaxeadmin',
}