# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import time
import asyncio
from datetime import datetime
from celery import shared_task
from django.template import loader
from netboost.celery import AxeTask
from netboost.settings import DEBUG
from apps.asset.model_api import get_device_info_v2
from apps.config_center.compliance import config_file_verify
from apps.config_center.config_parse.config_parse import config_file_parse
from apps.config_center.git_tools.git_proc import push_file
from apps.config_center.my_nornir import config_backup_nornir
from utils.db.mongo_ops import MongoOps
# from utils.send_email import send_mail
# from utils.wechat_api import send_msg_netops

config_mongo = MongoOps(db='netops', coll='ConfigBackupStatistics')

if DEBUG:
    CELERY_QUEUE = 'dev'
else:
    CELERY_QUEUE = 'config_backup'


@shared_task(base=AxeTask, once={'graceful': True})
def config_backup(**kwargs):
    log_time = datetime.now().strftime("%Y-%m-%d")
    start_time = time.time()
    # send_msg_netops(f"配置备份开始，时间:{log_time}")
    if kwargs:
        hosts = get_device_info_v2(**kwargs)
    else:
        hosts = get_device_info_v2()
    # 配置备份任务
    result = config_backup_nornir(hosts)
    end_time = time.time()
    time_use = int(int(end_time - start_time) / 60)
    fail_host = '\n'.join([x for x in result.failed_hosts.keys()])
    # send_msg_netops(f"配置备份完成，耗时:{time_use}分\n备份失败设备:\n{fail_host}")
    # 配置解析
    loop = asyncio.get_event_loop()
    loop.run_until_complete(config_file_parse())
    # config_file_parse()
    # 推送git
    commit, changed_files, untracked_files = push_file()
    if changed_files or untracked_files:
        html_tmp = loader.render_to_string(
            'config_center/config_backup.html',
            dict(commit=commit, changedFiles=changed_files, untracked_files=untracked_files), None, None)
        # html_res = str(html_tmp, "utf-8")
        # email_addr = ['*@*.com']
        # email_subject = '配置备份结果_' + datetime.now().strftime("%Y-%m-%d %H:%M")
        # email_text_content = html_res
        # try:
        #     send_mail(
        #         receive_email_addr=email_addr,
        #         email_subject=email_subject, content_type='html',
        #         email_text_content=email_text_content)
        # except Exception as e:
        #     pass
        # mongo_data = {
        #     "log_time": log_time,
        #     "changed_files": len(changed_files),
        #     "untracked_files": len(untracked_files),
        # }
        # config_mongo.insert(mongo_data)
    # send_msg_netops(f"配置备份推送完成\n变更配置文件数:{len(changed_files)}\n新增配置文件数:{len(untracked_files)}\ncommit:{commit}")
    # 合规性检查
    loop.run_until_complete(config_file_verify())
    return

