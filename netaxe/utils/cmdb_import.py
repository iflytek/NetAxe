import time
from datetime import date

# Create your tests here.
from apps.asset.models import *


# from apps.host_management.models import *


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


# 根据设备类型字段获取设备类型ID
def search_cmdb_category_id(cmdb_category_name):
    cmdb_category_id = Rack.objects.filter(name=cmdb_category_name).values('id').first()

    if not cmdb_category_id:
        msg = "[{}] 类型不存在，请先录入类型信息！".format(cmdb_category_name)
        print(msg)
        raise Exception(msg)

    else:
        print("已完成检索，{} 类型ID为: {}".format(cmdb_category_name, cmdb_category_id['id']))
    return cmdb_category_id['id']


# # 根据机柜U位和机柜ID进行检索，若机柜位置不存在，则创建并返回创建后的机柜U位ID
# def search_cmdb_cabinetaddr_id(idc_name, idc_cabinet, cabinetaddr_name):
#     cmdb_idc_id = search_cmdb_idc_id(idc_name)
#     cmdb_cabinet_id = search_cmdb_cabinet_id(idc_cabinet, cmdb_idc_id)
#     cmdb_cabinetaddr_id = cmdb_cabinetaddr.objects.filter(name=cabinetaddr_name, cabinet=cmdb_cabinet_id).values(
#         'id').first()
#
#     if cmdb_cabinetaddr_id:
#         print("已检索完成，机柜U位ID为: {}".format(cmdb_cabinetaddr_id['id']))
#         return cmdb_cabinetaddr_id['id']
#     else:
#         try:
#             cmdb_cabinet_instance = cmdb_cabinet.objects.get(name=idc_cabinet, idc=cmdb_idc_id)
#
#             print("{} 机柜U位不存在，系统正在创建!".format(cabinetaddr_name))
#             cmdb_cabinetaddr.objects.update_or_create(name=cabinetaddr_name, cabinet=cmdb_cabinet_instance)
#             time.sleep(3)
#             print("{} 机柜U位不存在，系统已创建完成!".format(cabinetaddr_name))
#             cmdb_cabinetaddr_id = search_cmdb_cabinetaddr_id(idc_name, idc_cabinet, cabinetaddr_name)
#
#             return cmdb_cabinetaddr_id
#
#         except Exception as e:
#             print('{} 机柜不存在，请先创建此机柜！'.format(idc_cabinet))


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


# # 根据设备型号、厂商ID、设备类型等信息进行检索，若设备型号不存在，则创建并返回创建后设备型号ID
# def search_cmdb_model_id(cmdb_model_name, cmdb_category_id, cmdb_vendor_id):
#     cmdb_model_id = cmdb_model.objects.filter(name=cmdb_model_name,
#                                               category__id=cmdb_category_id,
#                                               devicevendor__id=cmdb_vendor_id).values('id').first()
#
#     if cmdb_model_id:
#         print("已完成检索，{} 设备型号ID为: {}".format(cmdb_model_name, cmdb_model_id['id']))
#         return cmdb_model_id['id']
#     else:
#         print("{} 设备型号不存在，系统正在创建！".format(cmdb_model_name))
#         cmdb_model.objects.update_or_create(name=cmdb_model_name, category_id=cmdb_category_id,
#                                             devicevendor_id=cmdb_vendor_id)
#         time.sleep(3)
#         print("{} 设备型号不存在，系统已创建完成！".format(cmdb_model_name))
#         cmdb_model_id = search_cmdb_model_id(cmdb_model_name, cmdb_category_id, cmdb_vendor_id)
#
#         return cmdb_model_id
#
#
# def search_int_utilization(csv_sn, int_used, int_unused, utilization):
#     networkdevice_sn = networkdevice.objects.filter(Serialnumber=csv_sn).values('Serialnumber').first()
#     if not networkdevice_sn:
#         print("{} 设备不在CMDB中，请先创建此设备！".format(csv_sn))
#     else:
#         int_utilization_id = utilization_int.objects.filter(host_id=networkdevice_sn['Serialnumber']).values(
#             'host_id').first()
#         # print(search_int_utilization['id'])
#         if int_utilization_id:
#             print("{} 设备接口使用率已存在！".format(csv_sn, int_utilization_id['host_id']))
#             return int_utilization_id['host_id']
#         else:
#             pass
#             print("{} 接口使用率不存在，系统正在创建！".format(csv_sn))
#             utilization_int.objects.update_or_create(host_id=csv_sn, int_used=int_used, int_unused=int_unused,
#                                                      utilization=utilization)
#             time.sleep(3)
#             print("{} 接口使用率不存在，系统已创建完成！".format(csv_sn))
#             return
#
#
# # 根据业务类型进行检索，若业务类型不存在，则创建并返回创建后的业务类型ID
# def search_business(csv_business_name):
#     business_name_id = business.objects.filter(name=csv_business_name).values('id').first()
#
#     if business_name_id:
#         print("已完成检索，{} 业务ID为: {}".format(csv_business_name, business_name_id['id']))
#         return business_name_id['id']
#     else:
#         print("{} 业务不存在，系统正在创建！".format(csv_business_name))
#         business.objects.update_or_create(name=csv_business_name)
#         time.sleep(3)
#         print("{} 业务不存在，系统已创建完成！".format(csv_business_name))
#         business_name_id = search_business(csv_business_name)
#         return business_name_id
#
#
# def search_networkdevice_id(csv_sn):
#     networkdevice_sn = networkdevice.objects.filter(Serialnumber=csv_sn).values('Serialnumber').first()
#     if networkdevice_sn:
#         print("已完成检索，{} 设备ID为: {}".format(csv_sn, networkdevice_sn['Serialnumber']))
#         return networkdevice_sn['Serialnumber']
#     else:
#         print("{} 设备不在CMDB中，请先创建此设备！".format(csv_sn))
#         return
#
#
# def search_idc_model_id(csv_idc_model, csv_idc_name):
#     idc_model_id = cmdb_idc_model.objects.filter(name=csv_idc_model, idc__name=csv_idc_name).values('id').first()
#     # print(idc_model_id)
#     if idc_model_id:
#         print("已完成检索，{} 机房模块ID为: {}".format(csv_idc_model, idc_model_id['id']))
#         return idc_model_id['id']
#     else:
#         print("{} 机房模块不在CMDB中，请先创建此机房模块！".format(csv_idc_model))
#         return
#
#
# # 根据设备SN进行检索账户信息，若不存在账户信息与设备关联，则创建设备与账户信息关联关系；
# def search_account2networkdevice(csv_sn, csv_idc_name):
#     account2net_id = account2networkdevice.objects.filter(device=csv_sn.strip()).values('id').first()
#
#     # 先在后台cmdb_account中创建好账号信息，然后在此手动指定机房与账户ID对应关系
#     account_name = {
#         '上海嘉定': '1',
#         '北京酒仙桥': '4',
#         '广州华新园': '6',
#         '北京鲁谷': '8',
#         '合肥B3': '13',
#         '北京大族': '21',
#         '合肥A2': '26'
#
#     }
#     account_id = cmdb_account.objects.get(id=account_name[csv_idc_name])
#
#     try:
#         device_id = networkdevice.objects.get(Serialnumber=csv_sn.strip())
#         if device_id:
#             if account2net_id:
#                 print("已完成检索，通用账号ID为: {}".format(account2net_id['id']))
#                 return account2net_id['id']
#             else:
#                 print("{} 通用账号不存在，系统正在创建！".format(csv_sn))
#                 account2networkdevice.objects.update_or_create(device=device_id, account=account_id)
#                 time.sleep(3)
#                 print("{} 通用账号不存在，系统已创建完成！".format(csv_sn))
#                 account2net_id = search_account2networkdevice(csv_sn, csv_idc_name)
#
#                 return account2net_id
#
#     except Exception as e:
#         print('{} 设备不存在，请先创建此设备！'.format(csv_sn))
#
#
# # 读取CSV文件，根据机房及设备SN编码信息，进行更新设备账户与设备对应关系表
# def update_account2networkdevice(filename):
#     csv_filename = filename
#
#     with open(csv_filename, 'r') as f:
#         reader = csv.DictReader(f)
#         for row in reader:
#             if '上海嘉定' in row['机房'] and '在线' in row['使用状态']:
#                 search_account2networkdevice(row['SN编码'].strip(), row['机房'])
#             elif '北京酒仙桥' in row['机房'] and '在线' in row['使用状态']:
#                 search_account2networkdevice(row['SN编码'].strip(), row['机房'])
#             elif '广州华新园' in row['机房'] and '在线' in row['使用状态']:
#                 search_account2networkdevice(row['SN编码'].strip(), row['机房'])
#             elif '合肥B3' in row['机房'] and '在线' in row['使用状态']:
#                 search_account2networkdevice(row['SN编码'].strip(), row['机房'])
#             elif '北京鲁谷' in row['机房'] and '在线' in row['使用状态']:
#                 search_account2networkdevice(row['SN编码'].strip(), row['机房'])
#             elif '北京大族' in row['机房'] and '在线' in row['使用状态']:
#                 search_account2networkdevice(row['SN编码'].strip(), row['机房'])
#             elif '合肥A2' in row['机房'] and '在线' in row['使用状态']:
#                 search_account2networkdevice(row['SN编码'].strip(), row['机房'])
#
#
# # 机柜和U位信息更新入品
# def update_cabinetaddr_new(filename):
#     csv_filename = filename
#
#     with open(csv_filename, 'r') as f:
#         reader = csv.DictReader(f)
#         for row in reader:
#             if '上海嘉定' in row['机房'] and '在线' in row['使用状态']:
#                 cmdb_idc_id = search_cmdb_idc_id(row['机房'].strip())
#                 cmdb_cabinet_id = search_cmdb_cabinet_id(row['机架'].strip(), cmdb_idc_id)
#                 networkdevice.objects.filter(Serialnumber=row['SN编码'].strip()).update(location=row['机柜'].strip(),
#                                                                                       cabinet_id=cmdb_cabinet_id)
#                 print('{} 设备机柜信息已更新，机柜为：{}'.format(row['SN编码'].strip(), row['机柜']))
#
#             elif '北京酒仙桥' in row['机房'] and '在线' in row['使用状态']:
#                 cmdb_idc_id = search_cmdb_idc_id(row['机房'].strip())
#                 cmdb_cabinet_id = search_cmdb_cabinet_id(row['机架'].strip(), cmdb_idc_id)
#                 networkdevice.objects.filter(Serialnumber=row['SN编码'].strip()).update(location=row['机柜'].strip(),
#                                                                                       cabinet_id=cmdb_cabinet_id)
#                 print('{} 设备机柜信息已更新，机柜为：{}'.format(row['SN编码'].strip(), row['机柜']))
#
#             elif '广州华新园' in row['机房'] and '在线' in row['使用状态']:
#                 cmdb_idc_id = search_cmdb_idc_id(row['机房'].strip())
#                 cmdb_cabinet_id = search_cmdb_cabinet_id(row['机架'].strip(), cmdb_idc_id)
#                 networkdevice.objects.filter(Serialnumber=row['SN编码'].strip()).update(location=row['机柜'].strip(),
#                                                                                       cabinet_id=cmdb_cabinet_id)
#                 print('{} 设备机柜信息已更新，机柜为：{}'.format(row['SN编码'].strip(), row['机柜']))
#
#
# # 平台业务线更新
# def update_platform_business(filename):
#     csv_filename = filename
#
#     with open(csv_filename, 'r') as f:
#         reader = csv.DictReader(f)
#         for row in reader:
#             if '北京大族' in row['机房'] and '在线' in row['使用状态']:
#                 networkdevice.objects.filter(Serialnumber=row['SN编码'].strip()).update(
#                     platform_business=row['平台业务线'].strip())
#                 print('{} 设备平台业务线信息已更新，平台业务线为：{}'.format(row['SN编码'].strip(), row['平台业务线']))
#             if '合肥A2' in row['机房'] and '在线' in row['使用状态']:
#                 networkdevice.objects.filter(Serialnumber=row['SN编码'].strip()).update(
#                     platform_business=row['平台业务线'].strip())
#                 print('{} 设备平台业务线信息已更新，平台业务线为：{}'.format(row['SN编码'].strip(), row['平台业务线']))
#             if '广州华新园' in row['机房'] and '在线' in row['使用状态']:
#                 networkdevice.objects.filter(Serialnumber=row['SN编码'].strip()).update(
#                     platform_business=row['平台业务线'].strip())
#                 print('{} 设备平台业务线信息已更新，平台业务线为：{}'.format(row['SN编码'].strip(), row['平台业务线']))
#             if '北京鲁谷' in row['机房'] and '在线' in row['使用状态']:
#                 networkdevice.objects.filter(Serialnumber=row['SN编码'].strip()).update(
#                     platform_business=row['平台业务线'].strip())
#                 print('{} 设备平台业务线信息已更新，平台业务线为：{}'.format(row['SN编码'].strip(), row['平台业务线']))
#             if '北京酒仙桥' in row['机房'] and '在线' in row['使用状态']:
#                 networkdevice.objects.filter(Serialnumber=row['SN编码'].strip()).update(
#                     platform_business=row['平台业务线'].strip())
#                 print('{} 设备平台业务线信息已更新，平台业务线为：{}'.format(row['SN编码'].strip(), row['平台业务线']))
#             if '上海嘉定' in row['机房'] and '在线' in row['使用状态']:
#                 networkdevice.objects.filter(Serialnumber=row['SN编码'].strip()).update(
#                     platform_business=row['平台业务线'].strip())
#                 print('{} 设备平台业务线信息已更新，平台业务线为：{}'.format(row['SN编码'].strip(), row['平台业务线']))
#             if '合肥B3' in row['机房'] and '在线' in row['使用状态']:
#                 networkdevice.objects.filter(Serialnumber=row['SN编码'].strip()).update(
#                     platform_business=row['平台业务线'].strip())
#                 print('{} 设备平台业务线信息已更新，平台业务线为：{}'.format(row['SN编码'].strip(), row['平台业务线']))
#
#
# def main(filename):
#     csv_filename = filename
#
#     with open(csv_filename, 'r') as f:
#
#         reader = csv.DictReader(f)
#         for row in reader:
#             if '合肥A2' in row['机房'] and '在线' in row['使用状态']:
#                 # print(row)
#                 cmdb_sn = networkdevice.objects.filter(Serialnumber=row['SN编码'].strip()).values('Serialnumber').first()
#                 if cmdb_sn:
#                     print("\n{} 设备已存在".format(row['SN编码'].strip()))
#                 else:
#                     print("\n{} 设备不存在，系统正在创建".format(row['SN编码'].strip()))
#
#                     # 判断厂商是否存在，如思科、华三、华为、锐捷、F5、Mellanox、深信服
#                     cmdb_vendor_id = search_cmdb_vendor_id(row['品牌'].strip())
#
#                     # 判断设备类型是否存在，如交换机、路由器、防火墙、负载均衡、服务器
#                     cmdb_category_id = search_cmdb_category_id(row['设备类型'].strip(), cmdb_vendor_id)
#
#                     # 根据设备型号、厂商ID、设备类型等信息进行检索，若设备型号不存在，则创建并返回创建后设备型号ID
#                     cmdb_model_id = search_cmdb_model_id(row['型号'].strip(), cmdb_category_id, cmdb_vendor_id)
#
#                     # 判断所属机房是否存在，如上海嘉定、北京鲁谷、北京大族、北京酒仙桥、广州新华园、合肥B3
#                     cmdb_idc_id = search_cmdb_idc_id(row['机房'].strip())
#
#                     # 判断网络区域是否存在，如生产公共区域、业务互联区域、IaaS网络区域、IPMI管理区域、公网区域、网络管理区域、
#                     cmdb_netzone_id = search_cmdb_netzone_id(row['网络区域'].strip(), cmdb_idc_id, row['网络属性'].strip(),
#                                                              row['网络架构'].strip())
#
#                     # 判断设备角色是否存在，如网络汇聚、业务互联、千兆电器接入、出口防火墙、Spine、Leaf、服务器
#                     cmdb_role_id = search_cmdb_role_id(row['设备角色'].strip(), cmdb_netzone_id)
#
#                     # 根据机柜编号、机房ID进行检索，若机柜不存在，则创建并返回创建后机柜ID
#                     cmdb_cabinet_id = search_cmdb_cabinet_id(row['机架'].strip(), cmdb_idc_id)
#
#                     # 根据机房模块编号、机房ID进行检索，若机房模块不存在，则创建并返回机房模块ID
#                     cmdb_idc_model_id = search_cmdb_idc_model_id(row['模块'].strip(), cmdb_idc_id)
#
#                     networkdevice.objects.create(Serialnumber=row['SN编码'].strip(),
#                                                  Managentip=row['管理IP'].strip(),
#                                                  softwareversion=row['软件版本'].strip(),
#                                                  systemname=row['主机名'].strip(),
#                                                  deviceuptime=str2time(row['上架时间'].strip()),
#                                                  maintenancedate=str2time(row['维保时间'].strip()),
#                                                  memo=row['备注'].strip(),  # memo为备注信息
#                                                  status=csv_device_staus(row['使用状态'].strip()),
#                                                  category_id=cmdb_category_id,
#                                                  devicemodel_id=cmdb_model_id,
#                                                  devicevendor_id=cmdb_vendor_id,
#                                                  idc_id=cmdb_idc_id,
#                                                  idc_model_id=cmdb_idc_model_id,
#                                                  loopbackip_id='',
#                                                  netzone_id=cmdb_netzone_id,
#                                                  role_id=cmdb_role_id,
#                                                  cabinet_id=cmdb_cabinet_id,
#                                                  location=row['机柜'].strip(),
#                                                  platform_business=row['平台业务线'].strip()
#                                                  )
#                     time.sleep(3)
#
#                     cmdb_sn = networkdevice.objects.filter(Serialnumber=row['SN编码'].strip()).values(
#                         'Serialnumber').first()
#                     if cmdb_sn:
#                         print("{} 设备，系统已创建完成！".format(row['SN编码']))
#
#                 # break


if __name__ == "__main__":
    import django
    import os
    import sys

    sys.path.insert(0, '../../')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'NetOpsV1.settings'  # 设置项目的配置文件
    django.setup()
    b = date.today().replace(year=date.today().year + 3)
    print(b)
