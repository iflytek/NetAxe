# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      conf
   Description:
   Author:          Lijiamin
   date：           2022/7/28 14:59
-------------------------------------------------
   Change Activity:
                    2022/7/28 14:59
-------------------------------------------------
"""
# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases
DATABASES = {
    'default': {
        'NAME': 'netaxe',
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '{SERVERIP}',
        'USER': 'root',
        'PASSWORD': 'root_devnet@2022',
        'PORT': '3306',
        'CONN_MAX_AGE': 21600,
        'ATOMIC_REQUESTS': True,
        'TEST_CHARSET': 'utf8mb4',
        'TEST_COLLATION': 'utf8mb4_general_ci',
        'TEST': {'NAME': 'net_axe_test',
                 'CHARTSET': 'utf8mb4',
                 'COLLATION': 'utf8mb4_general_ci'},
        'OPTIONS': {
            'charset': 'utf8mb4',
        }
    },
}

REDIS_URL = "redis://:dade0f2a65237a56b79277e6dd27351d2854df033e0ad4b4f90abec229cd64df@redis-cache:6379/"
CACHE_PWD = 'dade0f2a65237a56b79277e6dd27351d2854df033e0ad4b4f90abec229cd64df'
mongo_db_conf = {
    "host": '{SERVERIP}',
    "port": 27017,
    "username": "root",
    "password": "70uUceCVL1gf"
}
netops_api = {
    "token_url": 'http://{SERVERIP}:9999/api/token/',
    "base_url": 'http://{SERVERIP}:9999/api/',
    'username': 'adminnetaxe',
    'password': 'netaxeadmin',
}