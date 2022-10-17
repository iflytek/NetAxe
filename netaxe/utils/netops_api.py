# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      netops_api
   Description:
   Author:          Lijiamin
   date：           2022/9/8 11:04
-------------------------------------------------
   Change Activity:
                    2022/9/8 11:04
-------------------------------------------------
"""
import os
import json
import logging
import requests
from netboost.settings import BASE_DIR

logger = logging.getLogger("celery")

USER_CONF = {}
if os.path.exists("{}/{}/{}".format(BASE_DIR, "netboost", "conf.py")):
    from netboost.conf import netops_api

    USER_CONF = netops_api


class netOpsApi():

    def __init__(self):
        self.token_url = USER_CONF.get('token_url') or None
        self.base_url = USER_CONF.get('base_url') or None
        self.resources_manage_base_url = USER_CONF.get('resources_manage_base_url') or None
        self.data = {
            'username': USER_CONF.get('username') or 'adminnetaxe',
            'password': USER_CONF.get('password') or 'netaxeadmin'
        }
        self.token = self.get_token()

        self.headers = {
            "Content-Type": "application/json;charset=UTF-8",
            'Authorization': 'Bearer ' + str(self.token)
        }

    def get_token(self):
        headers = {
            "Content-Type": "application/json;charset=UTF-8"
        }
        r = requests.post(self.token_url, data=json.dumps(self.data), headers=headers)
        try:
            return r.json().get('access')
        except Exception as e:
            try:
                r = requests.post(self.token_url, data=json.dumps(self.data), headers=headers)
                return r.json().get('access')
            except Exception as e:
                raise Exception("Can't get netops_api token {},{},{}".format(str(e), self.token_url, self.data))

    def do_something(self, get_url, params):
        """
        Simple token based authentication.

        Clients should authenticate by passing the token key in the "Authorization"
        HTTP header, prepended with the string "Token ".  For example:

            Authorization: Token 401f7ac837da42b97f613d789819ff93537bee6a
        """
        url = self.base_url + get_url

        res = requests.get(url, params=params, headers=self.headers)
        # tmpres = res.json()['results']
        # for i in tmpres:
        #     print(i)
        return res.json()['results']

    def post_something(self, url, data):
        """
        新建条目通用方法
        """
        url = self.base_url + url
        res = requests.post(url, data=json.dumps(data), headers=self.headers)
        return res

    def patch_something(self, tmp_url, pk, data):
        """
        更新条目通用方法   url example: 'nvwa_relation/'
        """
        # url = self.base_url + 'nvwa_relation/' + str(pk) + '/'
        url = self.base_url + tmp_url + str(pk) + '/'
        res = requests.patch(url, data=json.dumps(data), headers=self.headers)
        return res

    def get_cmdb_account(self, params):
        """
        查询账户和设备关联
        """
        url = self.base_url + 'asset/cmdb_account/'
        res = requests.get(url, params=params, headers=self.headers)
        return res.json()['results']
        # 获取所有网络设备信息

    def get_all_device(self, limit):
        networkdevice_url = self.base_url + 'asset/asset_networkdevice/'
        params = {
            'limit': limit,
        }
        res = requests.get(networkdevice_url, params=params, headers=self.headers)
        return res.json()['results']
