# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      send_email
   Description:
   Author:          Lijiamin
   date：           2022/9/1 16:08
-------------------------------------------------
   Change Activity:
                    2022/9/1 16:08
-------------------------------------------------
"""
from __future__ import unicode_literals

import os
import smtplib
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from django.conf import settings


class SendEMail(object):
    """封装发送邮件类"""

    def __init__(self):
        self.msg_from = settings.EMAIL_HOST_USER

        self.password = settings.EMAIL_HOST_PASSWORD

        self.smtp_s = smtplib.SMTP_SSL(host=settings.EMAIL_HOST, port=settings.EMAIL_PORT)

        self.smtp_s.login(user=self.msg_from, password=self.password)

        self.from_email = formataddr(pair=(settings.EMAIL_FROM_NAME, settings.EMAIL_HOST_USER))

    def send_text(self, to_user, content, subject, content_type='html'):
        """发送文本邮件

        :param to_user: 对方邮箱

        :param content: 邮件正文

        :param subject: 邮件主题

        :param content_type: 内容格式：'plain' or 'html'

        :return:"""
        msg = MIMEText(content, _subtype=content_type, _charset="utf8")

        msg["From"] = self.from_email

        # msg["To"] = to_user
        msg["To"] = Header(",".join(to_user))

        msg["subject"] = subject
        self.smtp_s.send_message(msg, from_addr=self.from_email, to_addrs=to_user)

    def send_file(self, to_user, content, subject, file_path, content_type='html'):
        """发送带文件的邮件

        :param to_user: 对方邮箱

        :param content: 邮件正文

        :param subject: 邮件主题

        :param reports_path: 文件路径

        :param filename: 邮件中显示的文件名称

        :param content_type: 内容格式"""

        filename = os.path.basename(file_path)

        file_content = open(file_path, "rb").read()

        msg = MIMEMultipart()

        text_msg = MIMEText(content, _subtype=content_type, _charset="utf8")

        msg.attach(text_msg)

        file_msg = MIMEApplication(file_content)

        file_msg.add_header('content-disposition', 'attachment', filename=filename)

        msg.attach(file_msg)

        msg["From"] = self.from_email

        msg["To"] = Header(",".join(to_user))

        msg["subject"] = subject

        self.smtp_s.send_message(msg, from_addr=self.msg_from, to_addrs=to_user)

    def send_img(self, to_user, subject, content, filename, content_type='html'):
        '''发送带图片的邮件

        :param to_user: 对方邮箱

        :param subject: 邮件主题

        :param content: 邮件正文

        :param filename: 图片路径

        :param content_type: 内容格式'''
        subject = subject

        msg = MIMEMultipart('related')  # Html正文必须包含

        msg.attach(content)

        msg['Subject'] = subject

        msg['From'] = self.msg_from

        msg['To'] = to_user

        with open(filename, "rb") as file:
            img_data = file.read()

            img = MIMEImage(img_data)

            img.add_header('Content-ID', 'imageid')

            msg.attach(img)

            self.smtp_s.sendmail(self.msg_from, to_user, msg.as_string())


def send_mail(*args, **kwargs):
    """
    发送带附件邮件函数
        parameter:
            receive_email_addr: 邮箱地址list    ['***@163.com','***@qq.com',...]
            file_path:          附件绝对路径地址
    :param args:
    :param kwargs:
    :return:
    """
    print('**************发送邮件*********************')
    e = SendEMail()
    if kwargs.get('file_path'):
        e.send_file(to_user=kwargs['receive_email_addr'], content=kwargs['email_text_content'],
                    subject=kwargs['email_subject'], file_path=kwargs['file_path'])
    else:
        e.send_text(to_user=kwargs['receive_email_addr'], content=kwargs['email_text_content'],
                    subject=kwargs['email_subject'], content_type=kwargs.get('content_type', 'html'))



