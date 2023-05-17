# -*- coding: utf-8 -*-
'''
@Time    : 2022/9/14 9:35
@Author  : xhweng
@File    : tasks.py

'''
import json

from celery import shared_task, current_app
from netaxe.celery import AxeTask


@shared_task(base=AxeTask, once={'graceful': True})
def get_tasks():
    celery_app = current_app
    # celery_tasks = [task for task in celery_app.tasks if not task.startswith('celery.')]
    res = list(sorted(name for name in celery_app.tasks
                      if not name.startswith('celery.')))
    return json.dumps({'result': res})
