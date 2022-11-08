# -*- coding: utf-8 -*-
# @Time    : 2020/9/2 15:26
# @Author  : LiJiaMin
# @Site    : 
# @File    : auto_main.py
# @Software: PyCharm
import json
import os
import re
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from netmiko import NetmikoTimeoutException, NetmikoAuthenticationException
from netmiko._textfsm import _clitable as clitable
from netmiko._textfsm._clitable import CliTableError
from textfsm import TextFSM
from ttp import ttp
from netboost.settings import BASE_DIR
from utils.db.mongo_ops import MongoOps
from utils.connect_layer.my_netmiko import my_netmiko

channel_layer = get_channel_layer()
"""
    Value {{options}} {{字段名称}} （{{正则}}）
    option
    options可以为空
    Filldown 如果本条记录这个值未被识别，用前一个值的值来填充本条记录这个字段的值。
    Key 每条记录的这个字段需要全局唯一
    Required 这条记录的这个字段必须被识别出来才有效被记录
    List 这个字段是列表值（比如allow vlan等 portchannel member）
    Fillup Filldown的逆操作。
"""
os.environ["NTC_TEMPLATES_DIR"] = BASE_DIR + '/utils/connect_layer/my_netmiko/templates'


# 发送websocket消息
def send_ws_msg(channel, group_name, data):
    # group_name = "sec_device"
    print(channel, group_name, data)
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': channel,
            'message': data
        }
    )
    return


# 自动化通用mongo接口
class BatManMongo(object):
    @staticmethod
    def insert_failed_logs(hostip, device_type, info):
        my_mongo = MongoOps(db='Automation', coll='collect_failed_logs')
        tmp = my_mongo.find(query_dict=dict(ip=hostip), fileds={'_id': 0})
        if tmp:
            my_mongo.update(filter=dict(ip=hostip), update={"$set": {'device_type': device_type, 'info': info}})
        else:
            my_mongo.insert(dict(ip=hostip, device_type=device_type, info=info))
        return


# 解析器类
class BatManFsm(object):

    @staticmethod
    def _get_template_dir():
        """
        已经废弃，采用os.environ["NTC_TEMPLATES_DIR"方式全局赋值改变
        :return:
        """

        # 大家也可以把templates拷贝到指定目录，在这个函数里通过环境变量读取路径。后续可以自己维护自己的templates
        package_dir = os.path.dirname(__file__)
        template_dir = os.path.join(package_dir, "templates")
        os.environ["NTC_TEMPLATES_DIR"] = template_dir
        # template_dir = os.path.join(package_dir, "templates")
        # if not os.path.isdir(template_dir):
        #     project_dir = os.path.dirname(os.path.dirname(os.path.dirname(template_dir)))
        #     template_dir = os.path.join(project_dir, "templates")
        return template_dir

    # 解析器
    @staticmethod
    def clitable_to_dict(cli_table):
        """Converts TextFSM cli_table object to list of dictionaries."""
        objs = []
        for row in cli_table:
            temp_dict = {}
            for index, element in enumerate(row):
                temp_dict[cli_table.header[index].lower()] = element
            objs.append(temp_dict)
        return objs

    # 解析器主程序
    @staticmethod
    def get_structured_data(raw_output, platform, command):
        """Convert raw CLI output to structured data using TextFSM template."""
        template_dir = BASE_DIR + '/utils/connect_layer/my_netmiko/templates'
        index_file = os.path.join(template_dir, "index")
        textfsm_obj = clitable.CliTable(index_file, template_dir)
        attrs = {"Command": command, "Platform": platform}
        try:
            # Parse output through template
            textfsm_obj.ParseCmd(raw_output, attrs)
            structured_data = BatManFsm.clitable_to_dict(textfsm_obj)
            output = raw_output if structured_data == [] else structured_data
            return output
        except CliTableError:
            return raw_output

    # 废弃demo入口子程序
    @staticmethod
    def get_textfsm_obj(Command, Platform):
        """
        通过设备的平台和cmd去匹配index中对应的模板
        不调用处理table，从而完成对windows的彻底兼容
        但也对文件锁等细节处理不当，但是在个人PC上演示调试不会造成太大问题。
        """
        Command_re_str = ' '.join(['{}{}'.format(i, '[a-zA-Z0-9]*?') for i in Command.split()])
        re_str = r'.*?{}.*? .*?{}.*?'.format(Platform, Command_re_str)
        re_str = re_str.replace(' ', '_').lower()
        textfsm_templ_re = re.compile(re_str)
        index_file = os.path.join(os.environ["NTC_TEMPLATES_DIR"], 'index')
        with open(index_file, 'r', encoding='utf8') as f:
            index_text = f.read()
        result = textfsm_templ_re.search(index_text)
        if result:
            textfsm_templ_name = '{}.textfsm'.format(result.group())
        else:
            # raise Exception('No template found for attributes: "%s"' % attributes)
            raise Exception('No template found for attributes')
        textfsm_templ_iofile = open(os.path.join(os.environ["NTC_TEMPLATES_DIR"], textfsm_templ_name), 'r',
                                    encoding='utf8')
        return TextFSM(textfsm_templ_iofile)

    # 废弃demo入口
    @staticmethod
    def parse_output(platform=None, command=None, raw_output=None):
        """Return the structured data based on the output from a network device."""

        attrs = {"Command": command, "Platform": platform}
        fsm = BatManFsm.get_textfsm_obj(**attrs)
        structured_data = fsm.ParseTextToDicts(raw_output)
        structured_data_lower = []
        structured_data_lower = [{k.lower(): v for k, v in raw_output.items()} for raw_output in structured_data]
        # for data in structured_data:
        #     structured_data_lower.append(
        #         {k.lower():v for k,v in data.items()}
        #     )
        return structured_data_lower


# 方法集合
class BatManMain(object):

    @staticmethod  # 执行命令并按规则保存结果文件到media/automation
    def send_cmds(*cmds, **dev_info):
        # paths = BatManMain.send_cmds(*['display evpn route arp'], **dev_info)
        paths = []
        try:
            with my_netmiko(**dev_info) as dev_connection:
                prompt = dev_connection.find_prompt()  # 找出设备的prompt
                for cmd in cmds:
                    content = dev_connection.send_command(cmd)
                    if content:
                        filename = 'automation/' + dev_info['ip'] + '/' + '_'.join(cmd.split()) + '.txt'
                        # 判断文件是否已经存在
                        if default_storage.exists(filename):
                            # 删除已经存在的文件重新生成
                            default_storage.delete(filename)
                        path = default_storage.save(filename, ContentFile(content))
                        # automation/10.254.2.55/display_evpn_route_arp.txt
                        paths.append(path)
                dev_connection.disconnect()
        except NetmikoAuthenticationException as e:  # 认证失败报错记录
            error_text = '[Error 1] Authentication failed.{}'.format(str(e))
            print('[Error 1] Authentication failed.{}'.format(str(e)))
            BatManMongo.insert_failed_logs(hostip=dev_info['ip'], device_type=dev_info['device_type'], info=error_text)
        except NetmikoTimeoutException as e:  # 登录超时报错记录
            error_text = '[Error 2] Connection timed out.{}'.format(str(e))
            print('[Error 2] Connection timed out.{}'.format(str(e)))
            BatManMongo.insert_failed_logs(hostip=dev_info['ip'], device_type=dev_info['device_type'], info=error_text)
        except Exception as e:
            # 采集失败的记录日志
            BatManMongo.insert_failed_logs(hostip=dev_info['ip'], device_type=dev_info['device_type'], info=str(e))
            print(str(e))
            return False
        return paths

    @staticmethod
    def config_cmds(*cmds, **dev_info):
        # paths = BatManMain.send_cmds(*['display evpn route arp'], **dev_info)
        paths = []
        try:
            # dev_connection = ConnectHandler(**dev_info)
            # input = dev_connection.send_config_set(cmds)
            # print(input)
            # 进入配置模式的命令
            config_mode_command = None
            if dev_info.get('config_mode_command'):
                config_mode_command = dev_info['config_mode_command']
                dev_info.pop('config_mode_command')
            # print('config_mode_command', config_mode_command)
            with my_netmiko(**dev_info) as dev_connection:
                # prompt = dev_connection.find_prompt()  # 找出设备的prompt
                # print(prompt)
                # dev_connection.enable()
                filename = 'automation/' + dev_info['ip'] + '/' + 'config' + '.txt'
                # 判断文件是否已经存在
                if default_storage.exists(filename):
                    # 删除已经存在的文件重新生成
                    default_storage.delete(filename)
                tmp = default_storage.save(filename, ContentFile('test'))
                # netmiko自带log方法需要使用绝对路径存储
                dev_connection.open_session_log(filename=BASE_DIR + '/media/' + tmp)
                # content = dev_connection.send_config_set(config_commands=cmds,
                #                                          cmd_verify=False)
                content = dev_connection.send_config_set(config_commands=cmds, exit_config_mode=True, delay_factor=1,
                                                         max_loops=120, strip_prompt=False,
                                                         strip_command=False,
                                                         config_mode_command=config_mode_command,
                                                         cmd_verify=True, enter_config_mode=True)
                # content += dev_connection.save_config(
                #     cmd='snmp-agent trap enable', confirm=True, confirm_response='Y')
                content += dev_connection.save_config()
                # print(content)
                dev_connection.close_session_log()
                dev_connection.disconnect()
                paths.append(filename)
        #
        # except Exception as e:
        #     print(e)
        #     print(traceback.print_exc())
        except NetmikoAuthenticationException as e:  # 认证失败报错记录
            error_text = '[Error 1] Authentication failed.{}'.format(str(e))
            print('[Error 1] {} Authentication failed.{}'.format(dev_info['ip'], str(e)))
            BatManMongo.insert_failed_logs(hostip=dev_info['ip'], device_type=dev_info['device_type'], info=error_text)
        except NetmikoTimeoutException as e:  # 登录超时报错记录
            error_text = '[Error 2] Connection timed out.{}'.format(str(e))
            print('[Error 2] {} Connection timed out.{}'.format(dev_info['ip'], str(e)))
            BatManMongo.insert_failed_logs(hostip=dev_info['ip'], device_type=dev_info['device_type'], info=error_text)
        except Exception as e:  # 未知报错记录
            error_text = '[Error 3] Unknown error. {}'.format(str(e))
            print('[Error 3] {} Unknown error. {}'.format(dev_info['ip'], str(e)))
            # 采集失败的记录日志
            BatManMongo.insert_failed_logs(hostip=dev_info['ip'], device_type=dev_info['device_type'], info=error_text)
            # print(str(e))
            return False
        return paths

    @staticmethod
    def yaml_config_cmds(**kwargs):
        dev_info = kwargs['dev_info']
        room_name = kwargs['room_name']
        yaml_res = kwargs['yaml_res']
        channel = kwargs['channel']
        try:
            with my_netmiko(**dev_info) as dev_connection:
                # prompt = dev_connection.find_prompt()  # 找出设备的prompt
                # print(prompt)
                # dev_connection.enable()
                filename = 'automation/' + dev_info['ip'] + '/' + 'config' + '.txt'
                # 判断文件是否已经存在
                if default_storage.exists(filename):
                    # 删除已经存在的文件重新生成
                    default_storage.delete(filename)
                path = default_storage.save(filename, ContentFile('config'))
                # netmiko自带log方法需要使用绝对路径存储
                dev_connection.open_session_log(filename=BASE_DIR + '/media/' + path)
                for cmds in yaml_res:
                    content = dev_connection.send_config_set(cmds['lines'],
                                                             exit_config_mode=False, cmd_verify=False,
                                                             error_pattern="(Ambiguous|Unrecognized|Wrong parameter)")
                    # content = dev_connection.send_config_set(config_commands=cmds['lines'], exit_config_mode=False,
                    #                                          delay_factor=1,
                    #                                          max_loops=120, strip_prompt=False,
                    #                                          strip_command=False,
                    #                                          cmd_verify=True, enter_config_mode=True)
                    send_ws_msg(channel=channel, group_name=room_name,
                                data={'parents': cmds['parents'][0], 'content': content})
                dev_connection.save_config()
                # print(content)
                dev_connection.close_session_log()
                dev_connection.disconnect()
                return True, path
        except NetmikoAuthenticationException as e:  # 认证失败报错记录
            print('[Error 1] {} Authentication failed.{}'.format(dev_info['ip'], str(e)))
            return False, '[Error 1] {} Authentication failed.{}'.format(dev_info['ip'], str(e))
        except NetmikoTimeoutException as e:  # 登录超时报错记录
            print('[Error 2] {} Connection timed out.{}'.format(dev_info['ip'], str(e)))
            return False, '[Error 2] {} Connection timed out.{}'.format(dev_info['ip'], str(e))
        except Exception as e:  # 未知报错记录
            print('[Error 3] {} Unknown error. {}'.format(dev_info['ip'], str(e)))
            # 采集失败的记录日志
            # print(str(e))
            return False, '[Error 3] {} Unknown error. {}'.format(dev_info['ip'], str(e))

    @staticmethod  # 解析数据
    def info_fsm(path, fsm_platform):
        if default_storage.exists(path):
            tmp = path.split('/')[-1]
            _cmd = tmp.split('.')[0]
            cmd = ' '.join(_cmd.split('_'))
            _content = default_storage.open(path).read()
            _content = _content.decode('utf-8')
            # print(cmd)
            res = BatManFsm.get_structured_data(platform=fsm_platform,
                                                command=cmd,
                                                raw_output=_content)
            return res
        else:
            raise Exception("path file not found")

    @staticmethod
    def custom_fsm(path, template):
        if isinstance(path, dict):
            path = path['path']
        # 将打开的解析模板文件对象传参给TextFSM模块
        base_template = os.environ["NTC_TEMPLATES_DIR"] + '/'
        ins = TextFSM(open(base_template + template, "r", encoding='utf8'))
        _content = default_storage.open(path).read()
        _content = _content.decode('utf-8')
        # 将文本简析成字典
        result = ins.ParseTextToDicts(_content)
        return result

    @staticmethod
    def test_fsm(content, template):
        # 将打开的解析模板文件对象传参给TextFSM模块
        base_template = os.environ["NTC_TEMPLATES_DIR"] + '/'
        ins = TextFSM(open(base_template + template, "r", encoding='utf8'))
        # 将文本简析成字典
        result = ins.ParseTextToDicts(content)
        return result


class HillstoneFsm:
    # 解析器映射
    @staticmethod
    def get_map(flag):
        app_map = {
            "standard": HillstoneFsm.standard_ttp,
        }
        return app_map[flag] if flag in app_map.keys() else False

    @staticmethod
    def show_environment():
        """
        {'fan': '', 'chassis_fan': ['Fan0 Fine  Fan1 Fine'], 'fan_slot': '0', 'slot_module': 'SFM-20', 'pwr_id': '', 'pwr_status': ''}
        {'fan': '', 'chassis_fan': ['Fan None'], 'fan_slot': '1', 'slot_module': 'IOM-4XFP-100', 'pwr_id': '', 'pwr_status': ''}
        {'fan': '', 'chassis_fan': ['Fan None'], 'fan_slot': '2', 'slot_module': 'IOM-4XFP-100', 'pwr_id': '', 'pwr_status': ''}
        {'fan': '', 'chassis_fan': ['Fan None'], 'fan_slot': '7', 'slot_module': 'SSM-100', 'pwr_id': '', 'pwr_status': ''}
        {'fan': '', 'chassis_fan': ['Fan None'], 'fan_slot': '8', 'slot_module': 'SSM-100', 'pwr_id': '', 'pwr_status': ''}
        {'fan': '', 'chassis_fan': ['Fan Fine'], 'fan_slot': '12', 'slot_module': 'SCM-100(M)', 'pwr_id': '', 'pwr_status': ''}
        {'fan': '', 'chassis_fan': [], 'fan_slot': '', 'slot_module': '', 'pwr_id': '0', 'pwr_status': 'Fine'}
        {'fan': '', 'chassis_fan': [], 'fan_slot': '', 'slot_module': '', 'pwr_id': '1', 'pwr_status': 'Fine'}
        {'fan': '', 'chassis_fan': [], 'fan_slot': '', 'slot_module': '', 'pwr_id': '2', 'pwr_status': 'Absent'}
        {'fan': '', 'chassis_fan': [], 'fan_slot': '', 'slot_module': '', 'pwr_id': '3', 'pwr_status': 'Absent'}
        :return:
        """
        pass

    @staticmethod
    def dnat_proc(path):
        # 'automation/172.16.150.251/show_configuration.txt'
        res = BatManMain.custom_fsm(path=path,
                                    template='hillstone_dnat_rule.textfsm')
        if isinstance(res, list):
            return res
        else:
            return False

    @staticmethod
    def snat_proc(path):
        # 'automation/172.16.150.251/show_configuration.txt'
        res = BatManMain.custom_fsm(path=path,
                                    template='hillstone_snat_rule.textfsm')
        if isinstance(res, list):
            return res
        else:
            return False

    @staticmethod
    def service_proc(path):
        # 替换为TTP 以下是原有格式
        # 'automation/172.16.150.251/show_configuration.txt'
        # res = BatManMain.custom_fsm(path=path,
        #                             template='hillstone_service.textfsm')
        # if isinstance(res, list):
        #     return res
        # else:
        #     return False
        # 以下为替换ttp方式代码 servgroup
        data_to_parse = default_storage.open(path).read()
        data_to_parse = data_to_parse.decode('utf-8')
        # print(data_to_parse)
        ttp_template = """
<vars>
# template variable with custom regular expression:
PROTOCOL = "tcp|udp|icmp"
</vars>
<macro>
def check_data(data):
    results = []
    ## print(data) 这里可以直接打印用于方法调试
    ## print("data", data)
    ## 判断是否真正解析到服务组
    if data != [{}]:
        if isinstance(data[0]['services'], dict):
            return results
        for item in data[0]['services']:
            ## print(item)
            if isinstance(item.get('items'), dict):
                item['items'] = [item['items']]
            if "items" in item:
                results.append(item)
        return results
    return []
</macro>
<group name="services">
##{{ ignore("\s*") }}service {{ name | re("\S+|\S+udp\s\S+") |strip('"') }}
{{ ignore("\s*") }}service {{ name | strip('"') | re("\S+(\s\S+)?") }}
{{ ignore("\s*") }}description {{ description | strip('"') }}
## 带有timeout的老设备匹配
<group name="items">
{{ ignore("\s*") }}{{ protocol | re("PROTOCOL") }} dst-port {{ dst-port-min | to_int }} {{ ignore("timeout\s\d+") }}
</group>
## 不带有timeout的新设备匹配
<group name="items">
{{ ignore("\s*") }}{{ protocol | re("PROTOCOL") }} dst-port {{ dst-port-min | to_int }}
</group>
<group name="items">
{{ ignore("\s*") }}{{ protocol | re("PROTOCOL") }} dst-port {{ dst-port-min | to_int }} {{ dst-port-max | to_int }} {{ ignore("timeout\s\d+") }}
</group>
## 不带有timeout的新设备匹配
<group name="items">
{{ ignore("\s*") }}{{ protocol | re("PROTOCOL") }} dst-port {{ dst-port-min | to_int }} {{ dst-port-max | to_int }}
</group>
<group name="items">
{{ ignore("\s*") }}{{ protocol | re("PROTOCOL") }} dst-port {{ dst-port-min | to_int }} {{ dst-port-max | to_int }} src-port {{ src-port-min | to_int }} {{ ignore("timeout\s\d+") }}
</group>
<group name="items">
{{ ignore("\s*") }}{{ protocol | re("PROTOCOL") }} dst-port {{ dst-port-min | to_int }} {{ dst-port-max | to_int }} src-port {{ src-port-min | to_int }} {{ src-port-max | to_int }} {{ ignore("timeout\s\d+") }}
</group>
## dst-port 为单数字，src-port 为一对数字的情况，比如tcp dst-port 8888 src-port 0 65535 timeout 1800
<group name="items">
{{ ignore("\s*") }}{{ protocol | re("PROTOCOL") }} dst-port {{ dst-port-min | to_int }} src-port {{ src-port-min | to_int }} {{ src-port-max | to_int }} {{ ignore("timeout\s\d+") }}
</group>
<group name="items">
{{ ignore("\s*") }}{{ protocol | re("PROTOCOL") }} dst-port {{ dst-port-min | to_int }} src-port {{ src-port-min | to_int }} {{ src-port-max | to_int }}
</group>
<group name="items">
{{ ignore("\s*") }}{{ protocol | re("PROTOCOL") }} dst-port {{ dst-port-min | to_int }} {{ ignore("application\s\S+") }} {{ ignore("timeout\s\d+") }}
</group>
## 不带有timeout的新设备匹配
<group name="items">
{{ ignore("\s*") }}{{ protocol | re("PROTOCOL") }} dst-port {{ dst-port-min | to_int }} {{ dst-port-max | to_int }} src-port {{ src-port-min | to_int }}
</group>
<group name="items">
{{ ignore("\s*") }}{{ protocol | re("PROTOCOL") }} dst-port {{ dst-port-min | to_int }} {{ dst-port-max | to_int }} src-port {{ src-port-min | to_int }} {{ src-port-max | to_int }}
</group>
<group name="items">
{{ ignore("\s*") }}{{ protocol | re("PROTOCOL") }} dst-port {{ dst-port-min | to_int }} {{ ignore("application\s\S+") }}
</group>
<group name="items">
{{ ignore("\s*") }}{{ protocol | re("PROTOCOL") }} type {{ type | to_int }} {{ ignore("code\s\d\s\d") }}
</group>
<group name="items">
{{ ignore("\s*") }}{{ protocol | re("PROTOCOL") }} type {{ type }} {{ ignore("code\s\d\s\d\stimeout\s\d") }}
</group>
exit{{_end_}}
</group>
<output macro="check_data"/>
"""
        parser = ttp(data=data_to_parse, template=ttp_template)
        parser.parse()
        # print result in JSON format
        results = parser.result(format='json')[0]
        # print(type(results))
        # print(results)
        res = json.loads(results)
        # print('res', res)
        #
        return res

    @staticmethod
    def servgroup_proc(path):
        # 替换为TTP 以下是原有格式
        # 'automation/172.16.150.251/show_configuration.txt'
        # res = BatManMain.custom_fsm(path=path,
        #                             template='hillstone_servgroup.textfsm')
        # if isinstance(res, list):
        #     return res
        # else:
        #     return False
        # 以下为替换ttp方式代码 servgroup
        data_to_parse = default_storage.open(path).read()
        data_to_parse = data_to_parse.decode('utf-8')
        # print(data_to_parse)
        ttp_template = """
<macro>
def check_data(data):
    results = []
    ## print(data) 这里可以直接打印用于方法调试
    ## print("data", data)
    ## 判断是否真正解析到服务组
    if data != [{}]:
        if isinstance(data[0]['servgroup'], dict):
            return results
        for item in data[0]['servgroup']:
            ## print(item)
            if isinstance(item.get('services'), dict):
                item['services'] = [item['services']]
            if "services" in item:
                results.append(item)
        return results
    return []
</macro>
<group name="servgroup">
{{ ignore("\s*") }}servgroup {{ servgroup | strip('"') }}
<group name="services">
{{ ignore(" ") }} service {{ service | strip('"') }}
</group>
exit{{_end_}}
</group>
<output macro="check_data"/>
        """
        parser = ttp(data=data_to_parse, template=ttp_template)
        parser.parse()
        # print result in JSON format
        results = parser.result(format='json')[0]
        # print(type(results))
        # print(results)
        res = json.loads(results)
        # print('res', res)
        # {'servgroup': '智慧城市', 'services': [{'service': '1723'}, {'service': '47'}]}
        return res

    @staticmethod
    def slb_server_proc(path):
        # 'automation/172.16.150.251/show_configuration.txt'
        res = BatManMain.custom_fsm(path=path,
                                    template='hillstone_slb-server-pool.textfsm')
        if isinstance(res, list):
            return res
        else:
            return False

    @staticmethod
    def address_group(path):
        # 转ttp解析 原解析如下：
        # 'automation/172.16.150.251/show_configuration.txt'
        # res = BatManMain.custom_fsm(path=path,
        #                             template='hillstone_address.textfsm')
        # if isinstance(res, list):
        #     return res
        # else:
        #     return False
        # 更换TTP解析如下
        data_to_parse = default_storage.open(path).read()
        data_to_parse = data_to_parse.decode('utf-8')
        # print(data_to_parse)
        ttp_template = """
<vars>
default_values = {
    "id": "",
    "name": "",
    "description": "",
}
</vars>
<macro>
def check_ip(data):
    results = []
    ##  print(data) #这里可以直接打印用于方法调试
    if data != [{}]:
        if isinstance(data[0]['address_set']['address'], dict):
            data[0]['address_set']['address'] = [data[0]['address_set']['address']]
        for item in data[0]['address_set']['address']:
            ## print(item)
            if isinstance(item.get('ip'), dict):
                item['ip'] = [item['ip']]
            if isinstance(item.get('range'), dict):
                item['range'] = [item['range']]
            if isinstance(item.get('memeber'), dict):
                item['memeber'] = [item['memeber']]
            if isinstance(item.get('host'), dict):
                item['host'] = [item['host']]
            if isinstance(item.get('exclude_range'), dict):
                item['exclude_range'] = [item['exclude_range']]
            if isinstance(item.get('exclude_ip'), dict):
                item['exclude_ip'] = [item['exclude_ip']]
            if "ip" in item or "range" in item or "memeber" in item or "exclude_range" in item or "exclude_ip" in item or "host" in item:
                results.append(item)  # 必要条件，必须包含内容，插入空数据结构无意义,包括定义的空地址对象
        return results
    return []
</macro>
<group name="address_set">
<group name="address" default="default_values">
address {{ ignore("(id\s\d+\s*)?") }}{{ name | strip('"') }}
{{ ignore(" ") }} description {{ description | strip('"') }}
<group name="ip">
{{ ignore(" ") }} ip {{ ip }}
</group>
<group name="member">
{{ ignore(" ") }} member {{ member }}
</group>
<group name="host">
{{ ignore(" ") }} host {{ host | strip('"') }}{{ ignore("\svr\s\S+") }}
</group>
<group name="host">
{{ ignore(" ") }} host {{ host | strip('"') }}
</group>
<group name="range">
##{{ ignore(" ") }} range {{ range | re("\S+\s\S+") }}
{{ ignore(" ") }} range {{ start }} {{ end }}
</group>
<group name="exclude_range">
##{{ ignore(" ") }} exclude range {{ range | re("\S+\s\S+") }}
{{ ignore(" ") }} exclude range {{ start }} {{ end }}
</group>
<group name="exclude_ip">
{{ ignore(" ") }} exclude ip {{ ip }}
</group>
exit{{_end_}}
</group>
</group>
<output macro="check_ip"/>
"""
        # create parser object and parse data using template:
        parser = ttp(data=data_to_parse, template=ttp_template)
        parser.parse()
        # print result in JSON format
        results = parser.result(format='json')[0]
        # print(type(results))
        # print(results)
        res = json.loads(results)
        # print('res', res)
        return res

    @staticmethod
    def aggr_group(path):
        # 'automation/172.16.150.251/show_configuration.txt'
        res = BatManMain.custom_fsm(path=path,
                                    template='hillstone_aggregate.textfsm')
        if isinstance(res, list):
            return res
        else:
            return False

    # 安全策略
    @staticmethod
    def sec_policy(path):
        data_to_parse = default_storage.open(path).read()
        data_to_parse = data_to_parse.decode('utf-8')
        # print(data_to_parse)
        ttp_template = """
<vars>
pattern_var = "\s*"
</vars>
<macro>
def check_data(data):
    results = []
    ## print(data)
    if data != [{}]:
        for item in data[0]['sec_policy']:
            ## print(item)
            if isinstance(item.get('src_addr'), dict):
                item['src_addr'] = [item['src_addr']]
            if isinstance(item.get('dst_addr'), dict):
                item['dst_addr'] = [item['dst_addr']]
            if isinstance(item.get('service'), dict):
                item['service'] = [item['service']]
        return data
    return []
</macro>
<group name="sec_policy">
rule id {{ id }}
  disable {{ disable | set(True) }}
{{ ignore(" ") }} action {{ action }}
<group name = "logs">
{{ ignore(" ") }} log {{ log }}
</group>
  src-zone "{{ src-zone }}"
  dst-zone "{{ dst-zone }}"
<group name = "src_addr">
{{ ignore(" ") }} src-ip {{ ip }}
</group>
<group name = "src_addr">
{{ ignore(" ") }} src-range {{ range | re("\S+\s\S+") }}
</group>
<group name = "dst_addr">
{{ ignore(" ") }} dst-ip {{ ip }}
</group>
<group name = "dst_addr">
{{ ignore(" ") }} dst-range {{ range | re("\S+\s\S+") }}
</group>
<group name = "dst_addr">
  dst-addr "{{ object }}"
</group>
<group name = "src_addr">
  src-addr "{{ object }}"
</group>
## 解析包含有前导空格的字符
<group name = "service">
{{ ignore(" ") }} service "{{ object }}"
</group>
  description "{{ description }}"
  name "{{ name }}"
  url "{{ url }}"
exit{{_end_}}
</group>
<output macro="check_data"/>
        """
        # create parser object and parse data using template:
        parser = ttp(data=data_to_parse, template=ttp_template)
        parser.parse()
        # print result in JSON format
        results = parser.result(format='json')[0]
        # print(type(results))
        # print(results)
        res = json.loads(results)
        if res:
            if 'sec_policy' in res[0].keys():
                if isinstance(res[0]['sec_policy'], dict):
                    return [res[0]['sec_policy']]
                return res[0]['sec_policy']
        else:
            return []

    # 系统预定义服务
    @staticmethod
    def service_predefined(path):
        """
<group name="range">
                          {{ Protocol }}         {{ dst_port | unrange(rangechar='-', joinchar=',') }}                 {{ src_port }}        {{ timeout }}
                          {{ Protocol }}         {{ dst_port | re("\d+") | re("Any")}}                {{ src_port }}        {{ timeout }}
</group>
        :param path:
        :return:
        """
        data_to_parse = default_storage.open(path).read()
        data_to_parse = data_to_parse.decode('utf-8')
        # print(data_to_parse)
        ttp_template = """
<group name="service_predefined">
##Total configured:{{ _start_ | print }}
{{ name | re("\S+") | re("\s+") }}                               {{ Protocol }}               {{ dst_port | re("\d+") | re("Any")}}               {{ src_port }}        {{ timeout }}
</group>
"""
        # create parser object and parse data using template:
        parser = ttp(data=data_to_parse, template=ttp_template)
        parser.parse()
        # print result in JSON format
        results = parser.result(format='json')[0]
        # print(type(results))
        # print(results)
        res = json.loads(results)
        if 'service_predefined' in res[0].keys():
            return res[0]['service_predefined']
        else:
            return []

    # 新建安全策略校验
    @staticmethod
    def config_sec_policy(path):
        # print(path)
        data_to_parse = default_storage.open(path).read()
        data_to_parse = data_to_parse.decode('utf-8')
        print(data_to_parse)
        ttp_template = """
<vars>
pattern_var = ".*"
</vars>
<group name = "results">
Error: Error: {{ error | re(".*") }}
Warning: {{ error | re(".*") }}
<group name = "unrecognized">
{{ ignore(" ") }} ^-----unrecognized keyword {{ unrecognized | re("\S+") }}
</group>
<group name = "create">
{{ ignore(" ") }}Rule id {{ rule_id }} is created
</group>
</group>
"""
        # create parser object and parse data using template:
        parser = ttp(data=data_to_parse, template=ttp_template)
        parser.parse()
        # print result in JSON format
        results = parser.result(format='json')[0]
        # print(type(results))
        # print(results)
        res = json.loads(results)
        if 'results' in res[0].keys():
            if isinstance(res[0]['results'], dict):
                return res[0]['results']
            return res[0]['results']
        else:
            return []

    # 输出DNAT下发前的rule校验
    @staticmethod
    def check_dnat_config_before(rule_id, path):
        data_to_parse = default_storage.open(path).read()
        data_to_parse = data_to_parse.decode('utf-8')
        # print(data_to_parse)
        ttp_template = """
<macro>
## 调用这个方法的目的是为了嵌套一层列表结构，默认不返回外层results的key
def check(data):
    print(data) ## 这里可以直接打印用于方法调试
    #for _data in data:
        #print(_data)
    return data
</macro>
<group name = "results">
{{ ignore("\s*") }}{{ command | re("dnatrule id %s\s.*") }}
</group>
<output macro="check"/>
        """ % rule_id
        # create parser object and parse data using template:
        parser = ttp(data=data_to_parse, template=ttp_template)
        parser.parse()
        # print result in JSON format
        results = parser.result(format='json')[0]
        # print(type(results))
        res = json.loads(results)
        # print(res)
        # 必须返回字典，调用根据字典包含key判断是否匹配到结果
        if 'results' in res[0].keys():
            if isinstance(res[0]['results'], dict):
                return res[0]['results']
            return res[0]['results']
        else:
            return {}

    # 输出SNAT下发前的rule校验
    @staticmethod
    def check_snat_config_before(rule_id, path):
        data_to_parse = default_storage.open(path).read()
        data_to_parse = data_to_parse.decode('utf-8')
        # print(data_to_parse)
        ttp_template = """
<macro>
## 调用这个方法的目的是为了嵌套一层列表结构，默认不返回外层results的key
def check(data):
    print(data) ## 这里可以直接打印用于方法调试
    #for _data in data:
        #print(_data)
    return data
</macro>
<group name = "results">
{{ ignore("\s*") }}{{ command | re("snatrule id %s\s.*") }}
</group>
<output macro="check"/>
        """ % rule_id
        # create parser object and parse data using template:
        parser = ttp(data=data_to_parse, template=ttp_template)
        parser.parse()
        # print result in JSON format
        results = parser.result(format='json')[0]
        # print(type(results))
        res = json.loads(results)
        # print(res)
        # 必须返回字典，调用根据字典包含key判断是否匹配到结果
        if 'results' in res[0].keys():
            if isinstance(res[0]['results'], dict):
                return res[0]['results']
            return res[0]['results']
        else:
            return {}

    # 输出安全策略下发前的rule校验
    @staticmethod
    def check_sec_policy_config_before(rule_id, path):
        data_to_parse = default_storage.open(path).read()
        data_to_parse = data_to_parse.decode('utf-8')
        # print(data_to_parse)
        ttp_template = """
<macro>
## 调用这个方法的目的是为了嵌套一层列表结构，默认不返回外层results的key
def check(data):
    print(data) ## 这里可以直接打印用于方法调试
    ##for _data in data[0]['results']:
        ##print(_data)
    return data
</macro>
<group name = "results">
rule id {{ rule_id | re("%s") }} {{ _start_ }}
{{ before_config | lstrip() | to_list | _line_ | joinmatches }}
exit {{ _end_ }}
</group>
<output macro="check"/>""" % rule_id
        # create parser object and parse data using template:
        parser = ttp(data=data_to_parse, template=ttp_template)
        parser.parse()
        # print result in JSON format
        results = parser.result(format='json')[0]
        # print(type(results))
        res = json.loads(results)
        # print(res)
        result = {}
        # 必须返回字典，调用根据字典包含key判断是否匹配到结果
        if 'results' in res[0].keys():
            result = res[0]['results']
            if 'before_config' in result.keys():
                return [x.replace('"', '') for x in result['before_config']]
            return result
        else:
            return result

    # 新建和编辑DNAT, 用来校验配置下发结果
    @staticmethod
    def config_dnat(path):
        data_to_parse = default_storage.open(path).read()
        data_to_parse = data_to_parse.decode('utf-8')
        print(data_to_parse)
        ttp_template = """
<group name = "results">
<group name = "errors">
Error: Error: {{ error | re(".*") }}
</group>
<group name = "warning">
Warning: {{ error | re(".*") }}
</group>
<group name = "unrecognized">
{{ ignore(" ") }} ^-----unrecognized keyword {{ unrecognized | re("\S+") }}
</group>
<group name = "config">
{{ ignore("\s*") }}rule ID={{ rule_id }}
</group>
</group>
"""
        # create parser object and parse data using template:
        parser = ttp(data=data_to_parse, template=ttp_template)
        parser.parse()
        # print result in JSON format
        results = parser.result(format='json')[0]
        # print(type(results))
        res = json.loads(results)
        # print(res)
        if 'results' in res[0].keys():
            if isinstance(res[0]['results'], dict):
                return res[0]['results']
            return res[0]['results']
        else:
            return []

    # slb配置下发前的校验
    @staticmethod
    def check_slb_config_before(slb_name, path):
        data_to_parse = default_storage.open(path).read()
        data_to_parse = data_to_parse.decode('utf-8')
        # print(data_to_parse)
        ttp_template = """
<macro>
## 调用这个方法的目的是为了嵌套一层列表结构，默认不返回外层results的key
def check(data):
    print(data) ## 这里可以直接打印用于方法调试
    return data
</macro>
<group name = "results">
{{ ignore("\s*") }}slb-server-pool "{{ name | re("%s") | _start_ }}" 
{{ before_config | lstrip() | to_list | _line_ | joinmatches }}
exit {{ _end_ }}
</group>
<output macro="check"/>
""" % slb_name
        # create parser object and parse data using template:
        parser = ttp(data=data_to_parse, template=ttp_template)
        parser.parse()
        # print result in JSON format
        results = parser.result(format='json')[0]
        # print(type(results))
        res = json.loads(results)
        # print(res)
        """
        {'before_config': [
        'monitor threshold 99', 
        'server ip 1.1.1.1/30 port 80 weight-per-server 1 max-connection-per-server 655350', 
        'server ip-range 2.2.2.1 2.2.2.5 port 443 weight-per-server 1 max-connection-per-server 655350', 
        'monitor track-ping interval 10 threshold 3 weight 1'
        ], 
        'name': 'jmli12test'}
        """
        if 'results' in res[0].keys():
            if isinstance(res[0]['results'], dict):
                return res[0]['results']
            return res[0]['results']
        else:
            return {}

    # 通用校验
    @staticmethod
    def standard_ttp(path):
        # print(path)
        data_to_parse = default_storage.open(path).read()
        data_to_parse = data_to_parse.decode('utf-8')
        # print(data_to_parse)
        ttp_template = """
<group name = "results">
<group name = "errors">
Error: {{ error | re(".*") }}
</group>
<group name = "warning">
Warning: {{ error | re(".*") }}
</group>
<group name = "unrecognized">
{{ ignore(" ") }} ^-----unrecognized keyword {{ unrecognized | re("\S+") }}
</group>
<group name = "incomplete">
{{ ignore(" ") }} ^-----incomplete command {{ incomplete | re(".*") }}
</group>
<group name = "unrecognized">
{{ ignore(" ") }} ^-----contains unsupported characters {{ unrecognized | re("\S+") }}
</group>
<group name = "unrecognized">
{{ ignore(" ") }} ^-----无法识别的关键字: {{ unrecognized | re("\S+") }}
</group>
</group>
"""
        # create parser object and parse data using template:
        parser = ttp(data=data_to_parse, template=ttp_template)
        parser.parse()
        # print result in JSON format
        results = parser.result(format='json')[0]
        # print(type(results))
        # print(results)
        res = json.loads(results)
        if 'results' in res[0].keys():
            if isinstance(res[0]['results'], dict):
                return res[0]['results']
            return res[0]['results']
        else:
            return []


class HuaweiS:
    @staticmethod
    def eth_trunk(path):
        res = BatManMain.custom_fsm(path=path,
                                    template='huaweis_eth_trunk.textfsm')
        if isinstance(res, list):
            return res
        else:
            return False

    @staticmethod
    def interface(path):
        res = BatManMain.custom_fsm(path=path,
                                    template='huaweis_interface.textfsm')
        if isinstance(res, list):
            return res
        else:
            return False

    @staticmethod
    def lldp(path):
        res = BatManMain.custom_fsm(path=path,
                                    template='huawei_vrp_display_lldp_neighbor.textfsm')
        if isinstance(res, list):
            return res
        else:
            return False



if __name__ == '__main__':
    # Logging section ##############
    import logging

    # logging.basicConfig(filename="test.log", level=logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("netmiko")
    # Logging section ##############
    # res = BatManMain.info_fsm(path='automation/10.1.1.2/show_mac-address-table.txt', fsm_platform='cisco_ios')
    # res = BatManMain.info_fsm(path='automation/10.1.1.2/show_interfaces.txt', fsm_platform='cisco_ios')
    # res = BatManMain.info_fsm(path='automation/192.168.10.1/show_cdp_neighbors_detail.txt', fsm_platform='cisco_ios')
    res = BatManMain.info_fsm(path='automation/172.17.1.1/show_interfaces.txt', fsm_platform='cisco_ios')
    # res = BatManMain.info_fsm(path='automation/10.1.1.2/show_lldp_neighbors_detail.txt', fsm_platform='cisco_ios')
    if isinstance(res, list):
        for i in res:
            print(i)
    else:
        print(res)
