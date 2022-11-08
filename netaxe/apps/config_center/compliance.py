# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      compliance
   Description:    合规性校验主程序
   Author:          Lijiamin
   date：           2022/7/13 16:29
-------------------------------------------------
   Change Activity:
                    2022/7/13 16:29
-------------------------------------------------
"""
import asyncio
import copy
import os
import re
from datetime import datetime, date, timedelta

from django.core.cache import cache

from netboost.settings import BASE_DIR
from apps.config_center.models import ConfigCompliance
from utils.db.mongo_ops import MongoOps, MongoNetOps
from utils.wechat_api import send_msg_netops

CONFIG_PATH = BASE_DIR + '/media/device_config/current-configuration/'
vendor_map = {
    'hp_comware': 'H3C',
    'huawei': 'HUAWEI',
}
compliance_mongo = MongoOps(db='Automation', coll='ConfigCompliance')


async def sub_file_proc(_dir: str, host: str, log_time: datetime, rules: list):
    # print("{}{}/{}".format(CONFIG_PATH, _dir, host))
    with open("{}{}/{}".format(CONFIG_PATH, _dir, host), 'r', encoding='utf8') as f:
        # print(f.read())
        # regex = r"^#\nuser-group system\n"
        # regex = r"clock protocol"
        # 扫描整个目标文本，返回所有与规则匹配的子串组成的列表，如果没有匹配的返回空列表
        # 修整正则再匹配
        # _res = re.compile(pattern=regex, flags=re.M).findall(string=f.read())
        # if _res:
        #     print('匹配成功')
        #     print(_res)
        # print(re.compile(pattern=regex, flags=re.M).findall(string=f.read()))
        vendor, host_ip = host.split('-')
        host_ip = host_ip.strip('.txt')

        content = copy.deepcopy(f.read())
        for rule in rules:
            # print(rule)
            # regex = r"^#\nuser-group system\n"
            _regex = rule['regex']
            _pattern = rule['pattern']  # match-compliance  mismatch-compliance
            _res = re.compile(pattern=_regex, flags=re.M).findall(string=content)
            # print(_res)
            host_name = cache.get('cmdb_' + host_ip)
            _data = {
                'compliance': '',
                'hostip': host_ip,
                'hostname': host_name if host_name else '',
                'vendor': vendor_map[vendor],
                'log_time': log_time,
                'rule': rule['name'],
                'regex': rule['regex'],
            }
            # 匹配-合规 反之 不匹配-不合规
            if _pattern == 'match-compliance':
                _data['compliance'] = '合规' if _res else '不合规'
            # 不匹配-合规 反之 匹配-不合规
            elif _pattern == 'mismatch-compliance':
                _data['compliance'] = '不合规' if _res else '合规'
            # if _res:
            #     print('匹配成功')
            MongoNetOps.compliance_ops(**_data)
    return


async def config_file_verify():
    # 清理30天之前的数据 start
    today = date.today()
    oneday = timedelta(days=30)
    yesterday = today - oneday
    yesterday = datetime.strptime(str(yesterday), '%Y-%m-%d')
    compliance_mongo.delete_many({"log_time": {"$lte": yesterday}})
    # 清理30天之前的数据 end
    dir_list = os.listdir(CONFIG_PATH)
    rules = ConfigCompliance.objects.all().values()
    log_time = datetime.now()
    for _dir in dir_list:
        if os.path.isdir(CONFIG_PATH + _dir):
            device_file_list = os.listdir(CONFIG_PATH + _dir)
            # print(device_file_list)
            for host in device_file_list:
                print(host)
                if host[-4:] == '.txt':
                    vendor = host.split('-')[0]
                    if vendor in vendor_map.keys():
                        rules = [x for x in rules if x['vendor'] == vendor_map[vendor]]
                        # host_file = host[:-4]
                        await sub_file_proc(_dir, host, log_time, rules)
    # 重建索引
    MongoNetOps.compliance_reindex()
    send_msg_netops("合规性检查完成\n{}".format(log_time.strftime("%Y-%m-%d %H:%M:%S")))
    return


if __name__ == '__main__':
    # import asyncio
    # from apps.config_center.compliance import config_file_verify
    loop = asyncio.get_event_loop()
    loop.run_until_complete(config_file_verify())
