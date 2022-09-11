# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      wechat_api
   Description:
   Author:          Lijiamin
   date：           2022/9/1 16:19
-------------------------------------------------
   Change Activity:
                    2022/9/1 16:19
-------------------------------------------------
"""

import json
import os
import traceback
import requests
from django.core.cache import cache
from netboost.settings import BASE_DIR

# USER_CONF = {}
# if os.path.exists("{}/{}/{}".format(BASE_DIR, "netboost", "conf.py")):
#     from netboost.conf import (
#         corpid, network_info, netops_info, alarm_backup,
#         platform, alarm_analysis, syslog, sec_main,
#         dcn_controller, dev_inspect, error_packets)
#
#     USER_CONF = {
#         'corpid': corpid,
#         'network_info': network_info,
#         'netops_info': netops_info,
#         'alarm_backup': alarm_backup,
#         'platform': platform,
#         'alarm_analysis': alarm_analysis,
#         'syslog': syslog,
#         'sec_main': sec_main,
#         'dcn_controller': dcn_controller,
#         'dev_inspect': dev_inspect,
#         'error_packets': error_packets,
#     }


# class weiChatApi():
#
#     def __init__(self):
#         self.version = "1.0"
#         self.corpid = USER_CONF.get('corpid') or "wwdbb4001a9bafff7d"
#         # self.corpsecret = "0s1u1q04juUAD_gvipUjrIHg-tn9FAC8fwai2U2Hi4k"
#
#         self.get_token_url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
#         self.send_url = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
#
#         # 用于网络组所有成员通知使用
#         self.network_info = USER_CONF.get('network_info') or {
#             "touser": "@all",
#             "toparty": "3",
#             "agentid": "1000002",
#             "corpsecret": "0s1u1q04juUAD_gvipUjrIHg-tn9FAC8fwai2U2Hi4k",
#             "msgtype": "text",
#         }
#
#         # 用于网络运维开发通知使用
#         self.netops_info = USER_CONF.get('netops_info') or {
#             "touser": "@all",
#             "toparty": "2",
#             "agentid": "1000003",
#             "corpsecret": "ve1QYM_07jSCzLXOx4FnjwymnObvvbISiSYUywLKqxo",
#             "msgtype": "text",
#         }
#         # 网络告警备
#         self.alarm_backup = USER_CONF.get('alarm_backup') or {
#             "touser": "@all",
#             "toparty": "3",
#             "agentid": "1000004",
#             "corpsecret": "QxJvPIBcLrnLGMTYQqVFPLSHUb-abQinrSjfKB8fEcM",
#             "msgtype": "text",
#         }
#         # 平台运维
#         self.platform = USER_CONF.get('platform') or {
#             "touser": "@all",
#             "toparty": "2",
#             "agentid": "1000005",
#             "corpsecret": "SFnBAr1r7vH_Nd7jaFLaqWmjlWSKgWEN23MDFjKTKyk",
#             "msgtype": "text",
#         }
#         # 告警分析
#         self.alarm_analysis = USER_CONF.get('alarm_analysis') or {
#             "touser": "@all",
#             "toparty": "3",
#             "agentid": "1000006",
#             "corpsecret": "ghD1kqt1iXI5yewODauhwqhi4dtWsM5GnmzvkUzL-pA",
#             "msgtype": "text",
#         }
#         # 日志告警
#         self.syslog = USER_CONF.get('syslog') or {
#             "touser": "@all",
#             "toparty": "3",
#             "agentid": "1000007",
#             "corpsecret": "QHtm02acAtKshW5H_5qHwyfDFahKniQDXoa3StHuB3c",
#             "msgtype": "text",
#         }
#         # 安全纳管引擎
#         self.sec_main = USER_CONF.get('sec_main') or {
#             "touser": "@all",
#             "toparty": "3",
#             "agentid": "1000008",
#             "corpsecret": "IN_kGjHQj6QQQ_n4QhVlcPrySkeOhxoNneohomo40ZQ",
#             "msgtype": "text",
#         }
#         # DCN控制器
#         self.dcn_controller = USER_CONF.get('dcn_controller') or {
#             "touser": "@all",
#             "toparty": "3",
#             "agentid": "1000009",
#             "corpsecret": "ZRJ0xpeUWHyI9QhuqHuoFc5CCDcMWFqZ9Yr5DipFtw0",
#             "msgtype": "text",
#         }
#         # 巡检
#         self.dev_inspect = USER_CONF.get('dev_inspect') or {
#             "touser": "@all",
#             "toparty": "3",
#             "agentid": "1000010",
#             "corpsecret": "_1--HS3xtw8pOBrTcifvRkfQzdDOlCazCIGu_0Pohjk",
#             "msgtype": "text",
#         }
#         # 错包
#         # PsE-S1el-2SZlurSa451GF8Pgyi2syXXtrY7BYFtgYY
#         self.error_packets = USER_CONF.get('error_packets') or {
#             "touser": "@all",
#             "toparty": "3",
#             "agentid": "1000011",
#             "corpsecret": "PsE-S1el-2SZlurSa451GF8Pgyi2syXXtrY7BYFtgYY",
#             "msgtype": "text",
#         }
#
#     def get_map(self, flag):
#         app_map = {
#             "alarm_m": self.network_info,
#             "alarm_b": self.alarm_backup,
#             "netops": self.netops_info,
#         }
#         return app_map[flag] if flag in app_map.keys() else None
#
#     def get_token(self, corpId, corpsecret):
#         params = {
#             'corpId': corpId,
#             'corpsecret': corpsecret
#         }
#         try:
#             if cache.get('weichat_token' + corpsecret):
#                 return cache.get('weichat_token' + corpsecret)
#             else:
#                 token_file = requests.post(self.get_token_url, params=params, timeout=10)
#                 res = token_file.json()
#                 print('get_token', res)
#                 cache.set('weichat_token' + corpsecret, res, res['expires_in'])
#                 return res
#         except Exception as e:
#             print(traceback.print_exc())
#         return {}
#
#     # 用于网络运维全体人员消息通知
#     def send_msg_to_network(self, content):
#         send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send'
#         token = self.get_token(self.corpid, self.network_info['corpsecret'])['access_token']
#         params = {'access_token': token}
#         body = {
#             "touser": self.network_info['touser'],  # 企微中的用户账号;
#             "toparty": self.network_info['toparty'],  # 企微中的部门ID，如网络告警组ID=2；
#             "msgtype": self.network_info['msgtype'],  # 消息类型;
#             "agentid": self.network_info['agentid'],  # 企微中的应用ID，如网络告警应用ID=1000002;
#             "text": {
#                 "content": content
#             },
#             "safe": "0",
#         }
#         res = requests.post(send_url, params=params, data=json.dumps(body))
#         tmp = json.loads(res.text)
#         if tmp['errcode'] == 45009:
#             # self.send_msg_to_netops(content + '消息达到上限')
#             self.send_msg('alarm_b', content)
#         return res
#
#     # 用于网络开发消息通知
#     def send_msg_to_netops(self, content):
#         send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send'
#         token = self.get_token(self.corpid, self.netops_info['corpsecret'])['access_token']
#         params = {'access_token': token}
#         body = {
#             "touser": self.netops_info['touser'],  # 企微中的用户账号;
#             "toparty": self.netops_info['toparty'],  # 企微中的部门ID，如网络告警组ID=2；
#             "msgtype": self.netops_info['msgtype'],  # 消息类型;
#             "agentid": self.netops_info['agentid'],  # 企微中的应用ID，如网络告警应用ID=1000002;
#             "text": {
#                 "content": content,
#             },
#             "safe": "0",
#         }
#         res = requests.post(send_url, params=params, data=json.dumps(body))
#         return res
#
#     # 用户syslog日志告警
#     def send_msg_to_syslog(self, content):
#         send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send'
#         token = self.get_token(self.corpid, self.syslog['corpsecret'])['access_token']
#         params = {'access_token': token}
#         body = {
#             "touser": self.syslog['touser'],  # 企微中的用户账号;
#             "toparty": self.syslog['toparty'],  # 企微中的部门ID，如网络告警组ID=2；
#             "msgtype": self.syslog['msgtype'],  # 消息类型;
#             "agentid": self.syslog['agentid'],  # 企微中的应用ID，如网络告警应用ID=1000002;
#             "text": {
#                 "content": content,
#             },
#             "safe": "0",
#         }
#         res = requests.post(send_url, params=params, data=json.dumps(body))
#         return res
#
#     # 获取用户列表
#     def get_user_list(self):
#         send_url = 'https://qyapi.weixin.qq.com/cgi-bin/externalcontact/batch/get_by_user'
#         token = self.get_token(self.corpid, self.netops_info['corpsecret'])['access_token']
#         params = {'access_token': token}
#         body = {
#             "userid_list":
#                 [
#                     "LiJiaMin"
#                 ],
#             "cursor": "",
#             "limit": 100
#         }
#         res = requests.post(send_url, params=params, data=json.dumps(body))
#         return res.json()
#
#     def get_media_ID(self, path, token):  # 上传到临时素材  图片ID
#         img_url = "https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={}&type=image".format(token)  # 封面图片
#         files = {'image': open(path, 'rb')}
#         r1 = requests.post(img_url, files=files)  # 封面
#         re = json.loads(r1.text)
#         return re['media_id']
#
#     def post_image(self, file_name, file_path):
#         token = self.get_token(self.corpid, self.netops_info['corpsecret'])['access_token']
#         url = 'https://qyapi.weixin.qq.com/cgi-bin/media/uploadimg?access_token={}'.format(token)  # 正文图片
#
#         files = [
#             (file_name, open(file_path, 'rb')),
#         ]
#
#         r = requests.post(url, files=files)
#         res = r.json()
#         if res['errcode'] == 0:
#             return res['url']
#         else:
#             return False
#
#     def send_graph_to_network(self, path, title, content, digest):
#         """发送图文消息带正文"""
#         # print(path)
#         token = self.get_token(self.corpid, self.network_info['corpsecret'])['access_token']
#         img_id = self.get_media_ID(path, token)
#         # img_url = self.post_image(file_name=file_name, file_path=path)
#         # images = self.post_image(path,token,title)
#         send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send'
#         params = {'access_token': token}
#         body = {
#             "touser": self.network_info['touser'],  # 企微中的用户账号;
#             "toparty": self.network_info['toparty'],  # 企微中的部门ID，如网络告警组ID=2；
#             "msgtype": "mpnews",  # 消息类型; 图片image
#             "agentid": self.network_info['agentid'],  # 企微中的应用ID，如网络告警应用ID=1000002;
#             # "image": {
#             #     "media_id": img_id
#             # },
#             "mpnews": {
#                 "articles": [
#                     {
#                         "title": title,
#                         "thumb_media_id": img_id,
#                         "author": "iFLYTEK-NetOps",
#                         "content_source_url": "https://in.iflytek.com",
#                         "content": content,  # 正文 img_url + '<br>' +
#                         "digest": digest  # 描述信息
#                     }
#                 ]
#             },
#             "safe": "0",
#         }
#         res = requests.post(send_url, params=params, data=json.dumps(body))
#         tmp = json.loads(res.text)
#         if tmp['errcode'] == 45009:
#             self.send_graph_to_netops(path, title, content, digest)
#             # self.send_msg_to_netops(title + '\n' + digest + '\n消息达到上限')
#         return res
#
#     def send_graph_to_netops(self, path, title, content, digest):
#         """发送图文消息带正文"""
#         # print(path)
#         token = self.get_token(self.corpid, self.netops_info['corpsecret'])['access_token']
#         img_id = self.get_media_ID(path, token)
#         # print(img_id)
#         # img_url = self.post_image(file_name=file_name, file_path=path)
#         # images = self.post_image(path,token,title)
#         send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send'
#         params = {'access_token': token}
#         body = {
#             "touser": self.netops_info['touser'],  # 企微中的用户账号;
#             "toparty": self.netops_info['toparty'],  # 企微中的部门ID，如网络告警组ID=2；
#             "msgtype": "mpnews",  # 消息类型; 图片image
#             "agentid": self.netops_info['agentid'],  # 企微中的应用ID，如网络告警应用ID=1000002;
#             # "image": {
#             #     "media_id": img_id
#             # },
#             "mpnews": {
#                 "articles": [
#                     {
#                         "title": title,
#                         "thumb_media_id": img_id,
#                         "author": "iFLYTEK-NetOps",
#                         "content_source_url": "https://in.iflytek.com",
#                         "content": content,  # 正文 img_url + '<br>' +
#                         "digest": digest  # 描述信息
#                     }
#                 ]
#             },
#             "safe": "0",
#         }
#         res = requests.post(send_url, params=params, data=json.dumps(body))
#         return res.status_code
#
#     def send_image_to_netops(self, path):
#         ## 发送图片
#         # print(path)
#         token = self.get_token(self.corpid, self.netops_info['corpsecret'])['access_token']
#         img_id = self.get_media_ID(path, token)
#         # img_url = self.post_image(file_name=file_name, file_path=path)
#         # images = self.post_image(path,token,title)
#         send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send'
#         params = {'access_token': token}
#         body = {
#             "touser": self.netops_info['touser'],  # 企微中的用户账号;
#             "toparty": self.netops_info['toparty'],  # 企微中的部门ID，如网络告警组ID=2；
#             "msgtype": "image",  # 消息类型; 图片image
#             "agentid": self.netops_info['agentid'],  # 企微中的应用ID，如网络告警应用ID=1000002;
#             # "image": {
#             #     "media_id": img_id
#             # },
#             "image": {
#                 "media_id": img_id
#             },
#             "safe": "0",
#         }
#         res = requests.post(send_url, params=params, data=json.dumps(body))
#         # print(img_id)
#         return res.status_code
#
#     def send_image_to_network(self, path):
#         ## 发送图片
#         # print(path)
#         token = self.get_token(self.corpid, self.network_info['corpsecret'])['access_token']
#         img_id = self.get_media_ID(path, token)
#         # img_url = self.post_image(file_name=file_name, file_path=path)
#         # images = self.post_image(path,token,title)
#         send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send'
#         params = {'access_token': token}
#         body = {
#             "touser": self.network_info['touser'],  # 企微中的用户账号;
#             "toparty": self.network_info['toparty'],  # 企微中的部门ID，如网络告警组ID=2；
#             "msgtype": "image",  # 消息类型; 图片image
#             "agentid": self.network_info['agentid'],  # 企微中的应用ID，如网络告警应用ID=1000002;
#             "image": {
#                 "media_id": img_id
#             },
#             "safe": "0",
#         }
#         res = requests.post(send_url, params=params, data=json.dumps(body))
#         return res
#
#     def send_markdown_to_netops(self, content):
#         """该消息只能在企业微信中查看"""
#         # resolved_context = """
#         #         <font color=\"info\">地址访问异常已恢复</font>
#         #         >**告警详情**
#         #         >故障时间：<font color=\"info\">开会</font>
#         #         >恢复时间：@miglioguan
#         #         >故障实例：@miglioguan、@kunliu、@jamdeezhou、@kanexiong、@kisonwang
#         #         >归属机房：<font color=\"info\">广州TIT 1楼 301</font>
#         #         >业务线：<font color=\"warning\">2018年5月18日</font>
#         #         >联系人：<font color=\"comment\">上午9:00-11:00</font>
#         #         """
#         # firing_context = """
#         #                 <font color=\"warning\">地址访问异常</font>
#         #                 >**告警详情**
#         #                 >故障时间：<font color=\"info\">开会</font>
#         #                 >故障实例：@miglioguan、@kunliu、@jamdeezhou、@kanexiong、@kisonwang
#         #                 >归属机房：<font color=\"info\">广州TIT 1楼 301</font>
#         #                 >业务线：<font color=\"warning\">2018年5月18日</font>
#         #                 >联系人：<font color=\"comment\">上午9:00-11:00</font>
#         #                 """
#         token = self.get_token(self.corpid, self.netops_info['corpsecret'])['access_token']
#         send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send'
#         params = {'access_token': token}
#         body = {
#             "touser": self.netops_info['touser'],  # 企微中的用户账号;
#             "toparty": self.netops_info['toparty'],  # 企微中的部门ID，如网络告警组ID=2；
#             "msgtype": "markdown",  # 消息类型; markdown
#             "agentid": self.netops_info['agentid'],  # 企微中的应用ID，如网络告警应用ID=1000002;
#             "markdown": {
#                 "content": content
#             }}
#         res = requests.post(send_url, params=params, data=json.dumps(body))
#         return res.status_code
#
#     # 新版发布消息接口， 配合get_map
#     def send_msg(self, flag, content):
#         send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send'
#         app_instance = self.get_map(flag)
#         if app_instance:
#             token = self.get_token(self.corpid, app_instance['corpsecret'])['access_token']
#             params = {'access_token': token}
#             body = {
#                 "touser": app_instance['touser'],  # 企微中的用户账号;
#                 "toparty": app_instance['toparty'],  # 企微中的部门ID，如网络告警组ID=2；
#                 "msgtype": app_instance['msgtype'],  # 消息类型;
#                 "agentid": app_instance['agentid'],  # 企微中的应用ID，如网络告警应用ID=1000002;
#                 "text": {
#                     "content": content
#                 },
#                 "safe": "0",
#             }
#             res = requests.post(send_url, params=params, data=json.dumps(body))
#             return res
#
#     # 新版发布图形卡片消息接口
#     def send_graph(self, flag, path, title, content, digest):
#         """发送图文消息带正文"""
#         # print(path)
#         app_instance = self.get_map(flag)
#         token = self.get_token(self.corpid, app_instance['corpsecret'])['access_token']
#         img_id = self.get_media_ID(path, token)
#         # img_url = self.post_image(file_name=file_name, file_path=path)
#         # images = self.post_image(path,token,title)
#         send_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send'
#         params = {'access_token': token}
#         body = {
#             "touser": app_instance['touser'],  # 企微中的用户账号;
#             "toparty": app_instance['toparty'],  # 企微中的部门ID，如网络告警组ID=2；
#             "msgtype": "mpnews",  # 消息类型; 图片image
#             "agentid": app_instance['agentid'],  # 企微中的应用ID，如网络告警应用ID=1000002;
#             # "image": {
#             #     "media_id": img_id
#             # },
#             "mpnews": {
#                 "articles": [
#                     {
#                         "title": title,
#                         "thumb_media_id": img_id,
#                         "author": "iFLYTEK-NetOps",
#                         "content_source_url": "https://in.iflytek.com",
#                         "content": content,  # 正文 img_url + '<br>' +
#                         "digest": digest  # 描述信息
#                     }
#                 ]
#             },
#             "safe": "0",
#         }
#         res = requests.post(send_url, params=params, data=json.dumps(body))
#         tmp = json.loads(res.text)
#         if tmp['errcode'] == 45009:
#             self.send_graph_to_netops(path, title, content, digest)
#             # self.send_msg_to_netops(title + '\n' + digest + '\n消息达到上限')
#         return res


# 外部调用这个方法，里面自带消息达上限后的备份机制
def send_msg_network(msg):
    try:
        print(msg)
        # _weichat = weiChatApi()
        # tmp = _weichat.send_msg('alarm_m', msg)
        # tmp = json.loads(tmp.text)
        # if tmp['errcode'] == 45009:
        #     _weichat.send_msg('alarm_b', msg)
    except Exception as e:
        print(e)
        # _weichat = weiChatApi()
        # _weichat.send_msg_to_netops(msg)
    return

# 外部调用这个方法，里面自带消息达上限后的备份机制
def send_msg_netops(msg):
    try:
        print(msg)
        # _weichat = weiChatApi()
        # _weichat.send_msg_to_netops(msg)
        # _weichat.send_msg('platform', msg)
    except Exception as e:
        # print(traceback.print_exc())
        print(e)
    return


if __name__ == '__main__':
    pass
    # _wechat = weiChatApi()
    # _wechat.send_msg_to_netops('test')
