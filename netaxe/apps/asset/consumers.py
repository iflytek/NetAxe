# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      consumers
   Description:
   Author:          Lijiamin
   date：           2022/9/8 17:46
-------------------------------------------------
   Change Activity:
                    2022/9/8 17:46
-------------------------------------------------
"""

import os
import time
import logging
import paramiko
import threading
from django import db
from socket import timeout
from django.conf import settings
from channels.generic.websocket import WebsocketConsumer
from apps.asset.models import NetworkDevice, AssetIpInfo, AdminRecord, AssetAccount
from apps.asset.tasks import admin_file
# 以上为了解决 Lost connection to MySQL server during query
from utils.crypt_pwd import CryptPwd
import socket
socket.gethostname()

logger = logging.getLogger('server')


class MyThread(threading.Thread):
    def __init__(self, chan):
        super(MyThread, self).__init__()
        self.chan = chan
        self._stop_event = threading.Event()
        self.start_time = time.time()
        self.current_time = time.strftime(settings.TIME_FORMAT)
        self.stdout = []

    def stop(self):
        self._stop_event.set()

    def run(self):
        while not self._stop_event.is_set() or not self.chan.chan.exit_status_ready():
            time.sleep(0.1)
            try:
                data = self.chan.chan.recv(1024)
                if data:
                    try:
                        # str_data = data.decode(encoding='GB2312')
                        # str_data = bytes.decode(data)
                        str_data = data.decode('utf-8')
                        # str_data = bytes.decode(data)  原来配置
                    except Exception as e:
                        print(data)
                        print(e)
                        try:
                            str_data = data.decode(encoding='GB2312')
                        except:
                            str_data = data.decode('ISO-8859-1')
                        # str_data = data.decode(encoding='gb18030')
                        # str_data = data.decode('ISO-8859-1')
                        # str_data = data.decode('gb18030', 'ignore')
                    self.chan.send(str_data)
                    self.stdout.append([time.time() - self.start_time, 'o', str_data])
            except timeout:
                self.chan.send('\n由于长时间没有操作，连接已断开!', close=True)
                self.stdout.append([time.time() - self.start_time, 'o', '\n由于长时间没有操作，连接已断开!'])
                break

    def record(self):
        record_path = os.path.join(settings.MEDIA_ROOT, 'admin_ssh_records', self.chan.scope['user'].username,
                                   time.strftime('%Y-%m-%d'))
        if not os.path.exists(record_path):
            os.makedirs(record_path, exist_ok=True)
        record_file_name = '{}.{}.cast'.format(self.chan.host_ip, time.strftime('%Y%m%d%H%M%S'))
        record_file_path = os.path.join(record_path, record_file_name)
        header = {
            "version": 2,
            "width": self.chan.width,
            "height": self.chan.height,
            "timestamp": round(self.start_time),
            "title": "Demo",
            "env": {
                "TERM": os.environ.get('TERM'),
                "SHELL": os.environ.get('SHELL', '/bin/bash')
            },
        }

        admin_file.delay(record_file_path, self.stdout, header)

        login_status_time = time.time() - self.start_time
        if login_status_time >= 60:
            login_status_time = '{} m'.format(round(login_status_time / 60, 2))
        elif login_status_time >= 3600:
            login_status_time = '{} h'.format(round(login_status_time / 3660, 2))
        else:
            login_status_time = '{} s'.format(round(login_status_time))

        try:
            AdminRecord.objects.create(
                admin_login_user=self.chan.scope['user'],
                admin_server=self.chan.host_ip,
                admin_remote_ip=self.chan.remote_ip,
                admin_start_time=self.current_time,
                admin_login_status_time=login_status_time,
                admin_record_file=record_file_path.split('media/')[1]
            )
        except Exception as e:
            # print(e)
            pass
            # fort_logger.error('数据库添加用户操作记录失败，原因：{}'.format(e))


class WebSshConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super(WebSshConsumer, self).__init__(*args, **kwargs)
        db.connections.close_all()
        self.ssh = paramiko.SSHClient()
        self.server = NetworkDevice.objects.get(id=self.scope['path'].split('/')[3])
        bind_ssh_ip = AssetIpInfo.objects.filter(device=self.scope['path'].split('/')[3], name='SSH').values()
        # 如果有关联SSH的IP，则使用关联SSH方式登录
        if bind_ssh_ip:
            self.host_ip = bind_ssh_ip[0]['ipaddr']
        else:
            self.host_ip = self.server.manage_ip
        self.width = 150
        self.height = 30
        self.t1 = MyThread(self)
        self.remote_ip = self.scope['query_string'].decode('utf8')
        self.chan = None
        self.account = None

    def connect(self):
        print('self.scope["user"].is_anonymous', self.scope["user"].is_anonymous)
        self.accept()
        _CryptPwd = CryptPwd()
        self.account = AssetAccount.objects.filter(
            networkdevice=self.server, networkdevice__account__protocol='ssh'
        ).values(
            "networkdevice__account__username",
            "networkdevice__account__password",
            "networkdevice__account__protocol",
            "networkdevice__account__port",
        ).first()
        port = self.account['networkdevice__account__port']
        username = self.account['networkdevice__account__username']
        password = _CryptPwd.decrypt_pwd(self.account['networkdevice__account__password'])
        try:
            # self.ssh.load_system_host_keys()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.host_ip,
                             int(port),
                             str(username).strip(),
                             str(password).strip(),
                             timeout=20,
                             allow_agent=False,
                             look_for_keys=False)
            self.send("当前使用网管账号登陆设备,用户:{}".format(username))
        except Exception as e:
            print(e)
            # fort_logger.error('用户{}通过webssh连接{}失败！原因：{}'.format(username, self.host_ip, e))
            self.send(
                '用户{}通过webssh连接{}失败！原因：{}，用户名:{},密码:{}'.format(username, self.host_ip, e, str(username).strip(),
                                                               str(password).strip()))
            self.close()
            return
        self.chan = self.ssh.invoke_shell(term='xterm', width=self.width, height=self.height)
        # 设置如果15分钟没有任何输入，就断开连接
        self.chan.settimeout(60 * 15)
        self.t1.setDaemon(True)
        self.t1.start()

    def receive(self, text_data=None, bytes_data=None):
        self.chan.send(text_data)

    def disconnect(self, close_code):
        print('close_code')
        try:
            self.t1.record()
            self.t1.stop()
        finally:
            self.ssh.close()