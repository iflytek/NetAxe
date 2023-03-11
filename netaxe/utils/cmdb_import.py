import time
import os
from datetime import date, datetime
from apps.asset.models import *
import pandas as pd
from utils.netops_api import netOpsApi


def returndate(strdate):
    # 如果日期为空，则默认填写为当前时间
    if not strdate:
        # print(4,'日期为空，默认当前日期')
        res_date = date.today()
    else:
        # print(5,'日期不为空，将日期转换为达特，datetime.date格式')
        tmp_date = strdate.split('-')  # '2019-11-25'-->['2019', '11', '25']
        res_date = date(int(tmp_date[0]), int(tmp_date[1]), int(tmp_date[2]))
    return res_date


def str2time(str):
    if not str:
        csv_time = time.strftime("%Y-%m-%d", time.localtime())
        return csv_time
    else:
        str = str.replace('/', '-')
        csv_time = time.strftime("%Y-%m-%d", time.strptime(str, "%Y-%m-%d"))

        return csv_time


def csv_device_staus(device_staus):
    device_staus_dict = {
        '在线': 0,
        '已下线': 1,
        '未知': 2,
        '故障': 3,
        '备用': 4,
    }
    return device_staus_dict[device_staus]


def csv_attribute(attribute):
    attribute_dict = {
        '其它': 0,
        '研测网络': 1,
        '研发网络': 2,
        '生产网络': 3,
        '骨干网络': 4,
        '公网网络': 5,
    }
    return attribute_dict[attribute]


def csv_framework(framework):
    framework_dict = {
        '其它': '0',
        '大二层': '1',
        '三层': '2',
        '二层': '3',
    }
    return framework_dict[framework]


# 根据机柜编号、机房ID进行检索，若机柜不存在，则创建并返回创建后机柜ID
def search_cmdb_cabinet_id(cmdb_cabinet_name, cmdb_idc_model_id):
    cmdb_cabinet_id = Rack.objects.filter(name=cmdb_cabinet_name, idc_model__id=cmdb_idc_model_id).values(
        'id').first()

    if not cmdb_cabinet_id:
        msg = "[{}] 机柜不存在，请先录入机柜信息！".format(cmdb_cabinet_name)
        print(msg)
        raise Exception(msg)

    else:
        print("已完成检索，{} 机柜ID为: {}".format(cmdb_cabinet_name, cmdb_cabinet_id['id']))
    return cmdb_cabinet_id['id']


# 根据机房模块编号、机房ID进行检索，若机房模块不存在，则创建并返回机房模块ID
def search_cmdb_idc_model_id(cmdb_idc_model_name, cmdb_idc_id):
    cmdb_idc_model_id = IdcModel.objects.filter(name=cmdb_idc_model_name, idc__id=cmdb_idc_id).values('id').first()

    if not cmdb_idc_model_id:
        msg = "[{}] 机房模块不存在，请先录入机房模块信息！".format(cmdb_idc_model_name)
        print(msg)
        raise Exception(msg)

    else:
        print("已完成检索，{} 机房模块ID为: {}".format(cmdb_idc_model_name, cmdb_idc_model_id['id']))
    return cmdb_idc_model_id['id']


# 根据网络区域名称、机房ID、网络属性、网络架构等信息进行检索，若网络区域不存在，则创建并返回网络区域ID
def search_cmdb_netzone_id(cmdb_netzone_name):
    cmdb_netzone_id = NetZone.objects.filter(name=cmdb_netzone_name).values('id').first()
    if not cmdb_netzone_id:
        msg = "[{}] 网络区域不存在，请先录入网络区域信息！".format(cmdb_netzone_name)
        print(msg)
        raise Exception(msg)

    else:
        print("已完成检索，{} 网络区域ID为: {}".format(cmdb_netzone_name, cmdb_netzone_id['id']))
    return cmdb_netzone_id['id']


# 根据设备角色名称、网络区域ID等信息进行检索，若设备角色不存在，则创建并返回设备角色ID
def search_cmdb_role_id(cmdb_role_name):
    cmdb_role_id = Role.objects.filter(name=cmdb_role_name).values('id').first()

    if not cmdb_role_id:
        msg = "[{}] 设备角色不存在，请先录入设备角色信息！".format(cmdb_role_name)
        print(msg)
        raise Exception(msg)

    else:
        print("已完成检索，{} 设备角色ID为: {}".format(cmdb_role_name, cmdb_role_id['id']))
    return cmdb_role_id['id']


# 根据机房名称进行检索，若机房不存在，则创建并返回机房ID
def search_cmdb_idc_id(cmdb_idc_name):
    cmdb_idc_id = Idc.objects.filter(name=cmdb_idc_name).values('id').first()

    if not cmdb_idc_id:
        msg = "[{}] 机房不存在，请先录入机房信息！".format(cmdb_idc_name)
        print(msg)
        raise Exception(msg)

    else:
        print("已完成检索，{} 机房ID为: {}".format(cmdb_idc_name, cmdb_idc_id['id']))
    return cmdb_idc_id['id']


# 根据设备型号、厂商名称进行检索，若设备型号不存在，则创建并返回设备型号ID
def search_cmdb_category_id(cmdb_category_name):
    cmdb_category_id = Category.objects.filter(name=cmdb_category_name).values('id').first()
    if cmdb_category_id:
        print("已完成检索，{} 设备型号ID为: {}".format(cmdb_category_name, cmdb_category_id['id']))
        return cmdb_category_id['id']

    else:
        print("{} 设备型号不存在，系统正在创建!".format(cmdb_category_name))
        Category.objects.update_or_create(name=cmdb_category_name)
        time.sleep(3)
        print("{} 设备型号不存在，系统已创建完成!".format(cmdb_category_name))
        cmdb_category_id = search_cmdb_category_id(cmdb_category_name)

        return cmdb_category_id


# 根据设备属性名称查询设备属性ID
def search_cmdb_attribute_id(attribute_name):
    attribute_id_info = Attribute.objects.filter(name=attribute_name).values('id').first()
    if attribute_id_info:
        print("已完成检索，{} 设备属性ID为: {}".format(attribute_name, attribute_id_info['id']))
        return attribute_id_info['id']

    else:
        print("{} 设备属性不存在，系统正在创建!".format(attribute_name))
        Attribute.objects.update_or_create(name=attribute_name)
        time.sleep(3)
        print("{} 设备属性不存在，系统已创建完成!".format(attribute_name))
        attribute_id = search_cmdb_attribute_id(attribute_name)

        return attribute_id


# 根据设备架构名称查询设备架构ID
def search_cmdb_framework_id(framework_name):
    framework_id_info = Framework.objects.filter(name=framework_name).values('id').first()
    if framework_id_info:
        print("已完成检索，{} 设备架构ID为: {}".format(framework_name, framework_id_info['id']))
        return framework_id_info['id']

    else:
        print("{} 设备架构不存在，系统正在创建!".format(framework_name))
        Framework.objects.update_or_create(name=framework_name)
        time.sleep(3)
        print("{} 设备结构不存在，系统已创建完成!".format(framework_name))
        framework_id = search_cmdb_framework_id(framework_name)

        return framework_id


# 根据厂商名称进行检索，若厂商不存在，则抛出msg
def search_cmdb_vendor_id(cmdb_vendor_name):
    cmdb_vendor_id = Vendor.objects.filter(name=cmdb_vendor_name).values('id').first()

    if not cmdb_vendor_id:
        msg = "[{}] 厂商不存在，请先录入厂商信息！".format(cmdb_vendor_name)
        print(msg)
        raise Exception(msg)

    else:
        print("已完成检索，{} 厂商ID为: {}".format(cmdb_vendor_name, cmdb_vendor_id['id']))
    return cmdb_vendor_id['id']


def old_import_parse(import_list):
    # data_list = excel2list(filename)
    data_list = import_list
    # print(data_list)

    for data in data_list:
        # 判断厂商是否存在，如 F5 Mellanox  华三  华为  山石网科  思科  成都数维  深信服  盛科  科来 锐捷
        cmdb_vendor_id = search_cmdb_vendor_id(data[2])
        cmdb_idc_id = search_cmdb_idc_id(data[4])
        cmdb_netzone_id = search_cmdb_netzone_id(data[5])
        cmdb_role_id = search_cmdb_role_id(data[8])
        cmdb_idc_model_id = search_cmdb_idc_model_id(data[9], cmdb_idc_id)
        cmdb_cabinet_id = search_cmdb_cabinet_id(data[10], cmdb_idc_model_id)
        cmdb_category_id = search_cmdb_category_id(data[3])
        cmdb_attribute_id = search_cmdb_attribute_id(data[6])
        cmdb_framework_id = search_cmdb_framework_id(data[7])
        # from apps.asset.models import AssetAccount
        # account = AssetAccount.objects.get(name='网管账户_带域名')
        # print('data[15]', data[15])
        networkdevices = {
            "attribute": cmdb_attribute_id,
            "framework": cmdb_framework_id,
            'serial_num': data[0],
            'manage_ip': data[1],
            'vendor': cmdb_vendor_id,
            'idc': cmdb_idc_id,
            'zone': cmdb_netzone_id,
            'role': cmdb_role_id,
            'rack': int(cmdb_cabinet_id),
            'idc_model': cmdb_idc_model_id,
            'u_location_start': int(data[11].split("到")[0]),  # U位
            'u_location_end': int(data[11].split("到")[1]),  # U位
            'uptime': datetime.now().strftime('%Y-%m-%d'),  # 上线时间必须要，默认当前日期
            'expire': '2099-01-01',  # 维保时间必须有，默认3年
            'status': csv_device_staus(data[13]),
            'memo': "备注信息",  # memo为备注信息
            'name': data[1].strip(),  # 系统名称必须有。用管理IP代替
            'auto_enable': 'true',
            'category': cmdb_category_id,  # 设备类型字段
        }

        # print(networkdevices)
        device_obj = NetworkDevice.objects.filter(serial_num=data[0].strip())
        if device_obj:
            return False, '已经存在相同SN设备'
        else:
            # print('新建')
            try:
                netops_api = netOpsApi()
                # print('请求新增数据')
                res = netops_api.post_something(url="asset/asset_networkdevice/", data=networkdevices)
                # print(res.json())
                if res.json().get('code', ''):
                    if res.json()['code'] == 400:
                        return False, res.json(['msg'])
                    else:
                        return True, '导入成功'
                return True, '导入成功'
            except Exception as e:
                # print(e)
                return False, e


def pandas_read_file(filename, **kwargs):
    """Read file with **kwargs; files supported: xls, xlsx, csv, csv.gz, pkl"""

    read_map = {'xls': pd.read_excel, 'xlsx': pd.read_excel, 'csv': pd.read_csv,
                'gz': pd.read_csv, 'pkl': pd.read_pickle}

    ext = os.path.splitext(filename)[1].lower()[1:]
    assert ext in read_map, "Input file not in correct format, must be xls, xlsx, csv, csv.gz, pkl; current format '{0}'".format(
        ext)
    assert os.path.isfile(filename), "File Not Found Exception '{0}'.".format(filename)

    return read_map[ext](filename, engine='openpyxl')


if __name__ == "__main__":
    pass
