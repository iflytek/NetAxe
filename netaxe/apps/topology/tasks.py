# -*- coding: utf-8 -*-
# @Time    : 2021/12/21 16:02
# @Author  : jmli12
# @Site    :
# @File    : tasks.py
# @Software: PyCharm
# redis-json more : https://github.com/RedisJSON/redisjson-py

from __future__ import absolute_import, unicode_literals
import math
from apps.topology.models import Topology
from utils.db.mongo_ops import MongoOps, MongoNetOps

# import json

# graph_mongo = MongoOps(db='Topology', coll='graph')
lldp_mongo = MongoOps(db='Automation', coll='LLDPTable')
interface_mongo = MongoOps(db='Automation', coll='layer2interface')
layer3int_mongo = MongoOps(db='Automation', coll='layer3interface')
cmdb_mongo = MongoOps(db='XunMiData', coll='networkdevice')
lagg_mongo = MongoOps(db='Automation', coll='AggreTable')


# 拓扑数据生成
class TopologyTask:
    def __init__(self, name):
        # 初始化待处理的数据模型
        self.topology = Topology.objects.get(name=name)
        self.host_q = MongoNetOps.get_topology(self.topology.name)
        self.NODE_HIERARCHY = [
            ('^.*.AS..*', "1", "AC.png"),
            ('^.*.AR..*', "4", "L3.png")
        ]
        self.speed_map = {
            "1G": 1,
            "10G": 10,
            "25G": 25,
            "40G": 40,
            "100G": 100,
        }

    # 获取拓扑
    def get_graph(self):
        return MongoNetOps.get_topology(self.topology.name)

    # 删除拓扑
    def del_graph(self):
        self.topology.delete()
        MongoNetOps.del_topology(self.topology.name)
        return

    # 保存拓扑
    def save_graph(self, obj):
        MongoNetOps.topology_ops(**obj)

    # 根据设备IP和接口返回接口速率
    def foo_speed(self, hostip, interface_name):
        tmp = interface_mongo.find(query_dict={"hostip": hostip, "interface": interface_name}, fileds={"_id": 0})
        speed = tmp[0]['speed'] if tmp else '1G'
        return self.speed_map[speed] if speed in self.speed_map.keys() else 1

    # 根据IP 和接口返回当前接口三层IP信息
    def foo_layer3_ip(self, hostip, interface_name):
        tmp = layer3int_mongo.find(query_dict={"hostip": hostip, "interface": interface_name}, fileds={"_id": 0})
        # 如果没有IP，则查询是否聚合口，再查聚合口IP
        if not tmp:
            tmp_1 = lagg_mongo.find(query_dict={"hostip": hostip, "memberports": {"$in": [interface_name]}},
                                    fileds={"_id": 0, "aggregroup": 1})
            if tmp:
                aggre_interface = tmp_1[0]['aggregroup']
                tmp_2 = layer3int_mongo.find(query_dict={"hostip": hostip, "interface": aggre_interface},
                                             fileds={"_id": 0})
                if tmp_2:
                    return aggre_interface + ' ' + tmp_2[0]['ipaddress'] + '/' + tmp_2[0]['ipmask'] if tmp else ''
        # print('tmp', tmp)
        try:
            return tmp[0]['ipaddress'] + '/' + tmp[0]['ipmask'] if tmp else ''
        except Exception as e:
            return tmp[0]['ipaddress'] + '/32'

    # 生成连线
    def foo_link(self, nodes, manual_links, strict=True):
        """
        {
            "highest_utilization": 0,
            "source": "B3.MG.OB.DS.X01S",
            "source_interfaces": [
                "Ten-GigabitEthernet1/0/1"
            ],
            "source_interfaces_indes": [
                1
            ],
            "speed": "10",
            "target": "B3.MG.OB.AS.G12A",
            "target_interfaces": [
                "Ten-GigabitEthernet1/0/52",
                "Ten-GigabitEthernet1/0/51"
            ],
            "target_interfaces_indes": [
                52,
                51
            ]
        },
        :return:
        """

        # 排除重复连线
        def is_duplicate(links):
            tmp_result = []
            for a in links:
                source = a['source_manage_ip'] + a['source_interfaces']
                target = a['target_manage_ip'] + a['target_interfaces']
                # 正向和反向都去重
                if source + '-' + target not in [x['name'] for x in tmp_result] \
                        and target + '-' + source not in [x['name'] for x in tmp_result]:
                    a['name'] = source + '-' + target
                    tmp_result.append(a)
            # 节点信息补充多条连线信息 需要验证测试两个节点的数据
            # 计算两个节点之间的连线总数
            # 假设到这一步，已经不存在A-B B-A的重复连线数据
            result = []  # 最终数据
            for out_link in tmp_result:
                # 两个节点之间的连线总数
                out_link['sameTotal'] = 0
                out_link['sameIndex'] = 0
                for in_link in tmp_result:
                    if in_link['source_manage_ip'] == out_link['source_manage_ip'] and in_link['target_manage_ip'] == \
                            out_link['target_manage_ip']:
                        out_link['sameTotal'] += 1
                tmp_index = [x['sameIndex'] for x in result
                             if x['source_manage_ip'] == out_link['source_manage_ip']
                             and x['target_manage_ip'] == out_link['target_manage_ip']]
                if tmp_index:
                    out_link['sameIndex'] = max(tmp_index) + 1
                else:
                    out_link['sameIndex'] += 1

                out_link['sameTotalHalf'] = out_link['sameTotal'] / 2
                out_link['sameUneven'] = True if out_link['sameTotal'] % 2 else False
                out_link['sameMiddleLink'] = out_link['sameUneven'] and math.ceil(out_link['sameTotal']) == out_link[
                    'sameIndex']
                out_link['sameLowerHalf'] = out_link['sameIndex'] <= out_link['sameTotalHalf']
                out_link['sameArcDirection'] = 0 if out_link['sameLowerHalf'] else 1
                out_link['sameIndexCorrected'] = out_link['sameIndex'] \
                    if out_link['sameLowerHalf'] else out_link['sameIndex'] - math.ceil(out_link['sameTotalHalf'])
                result.append(out_link)
            return result

        links = []
        # 遍历节点
        for node in nodes:
            neighbor_q = lldp_mongo.find(query_dict={"hostip": node['manage_ip']}, fileds={"_id": 0})
            if neighbor_q:
                # 遍历节点的LLDP信息
                for _neighbor in neighbor_q:
                    if strict:  # 严格模式 只计算相关
                        # 排除自己连接自己
                        if _neighbor['neighbor_ip'] == node['manage_ip']:
                            continue
                        if _neighbor['neighbor_ip'] in [x['manage_ip'] for x in nodes]:
                            data = {
                                "highest_utilization": 0,
                                "source": node['id'],
                                "source_manage_ip": node['manage_ip'],
                                "source_interface_ip": self.foo_layer3_ip(node['manage_ip'],
                                                                          _neighbor['local_interface']),
                                "source_interfaces": _neighbor['local_interface'],
                                "source_interfaces_indes": '',
                                "speed": self.foo_speed(node['manage_ip'], _neighbor['local_interface']),
                                "target": _neighbor['neighborsysname'],
                                "target_manage_ip": _neighbor['neighbor_ip'],
                                "target_interfaces": _neighbor['neighbor_port'],
                                "target_interfaces_indes": '',
                                "target_interface_ip": self.foo_layer3_ip(_neighbor['neighbor_ip'],
                                                                          _neighbor['neighbor_port']),
                                "method": "auto"  # 自动计算标识  手动添加的连线为 manual
                            }
                            links.append(data)
                    else:  # 开放模式  计算不相关
                        data = {
                            "highest_utilization": 0,
                            "source": node['id'],
                            "source_manage_ip": node['manage_ip'],
                            "source_interfaces": '',
                            "source_interfaces_indes": '',
                            "speed": self.foo_speed(node['manage_ip'], _neighbor['local_interface']),
                            "target": _neighbor['neighborsysname'],
                            "target_manage_ip": _neighbor['neighbor_ip'],
                            "target_interfaces": _neighbor['neighbor_port'],
                            "target_interfaces_indes": '',
                            "method": "auto"  # 自动计算标识  手动添加的连线为 manual
                        }
                        links.append(data)
        return is_duplicate(links + manual_links)

    # 排除重复的设备和接口
    def is_link_duplicate(self, source_ip, source_interface, target_ip, target_interface):
        for link in self.host_q['links']:
            if source_ip == link['source_manage_ip'] and source_interface == link['source_interfaces']:
                return False
            elif source_ip == link['target_manage_ip'] and source_interface == link['target_interfaces']:
                return False
            elif target_ip == link['source_manage_ip'] and target_interface == link['source_interfaces']:
                return False
            elif target_ip == link['target_manage_ip'] and target_interface == link['target_interfaces']:
                return False
        return True

    # 增加手动连线
    def add_manual_link(self, source_ip, source_name, source_interface, target_ip, target_name, target_interface):
        result = {
            "links": self.host_q['links'],
            "nodes": self.host_q['nodes'],
            "name": self.topology.name,
            "cmdb": '',
            "interface": []
        }
        if self.is_link_duplicate(source_ip, source_interface, target_ip, target_interface):
            data = {
                "highest_utilization": 0,
                "source": source_name,
                "source_manage_ip": source_ip,
                "source_interface_ip": self.foo_layer3_ip(source_ip, source_interface),
                "source_interfaces": source_interface,
                "source_interfaces_indes": '',
                "speed": self.foo_speed(source_ip, source_interface),
                "target": target_name,
                "target_manage_ip": target_ip,
                "target_interfaces": target_interface,
                "target_interfaces_indes": '',
                "target_interface_ip": self.foo_layer3_ip(target_ip, target_interface),
                "method": "manual"  # 自动计算标识  手动添加的连线为 manual
            }
            result['links'].append(data)
            # 严格模式，只匹配相关的连线， strict 用来开关严格模式， strict=False则是开放模式
            result['links'] = self.foo_link(result['nodes'], result['links'], strict=True)
            # 存储拓扑计算结果
            MongoNetOps.topology_ops(**result)
            return True
        return False

    # 本地计算生成拓扑
    def local_graph(self):
        # 最终结果格式
        result = {
            "links": [],
            "nodes": self.host_q['nodes'],
            "name": self.topology.name,
            "cmdb": '',
            "interface": []
        }
        # 保留手动连线
        if self.host_q['links']:
            for link in self.host_q['links']:
                if link['method'] == 'manual':
                    result['links'].append(link)
        # 完善/更新节点信息
        for host in self.host_q['nodes']:
            host['image'] = "AC.png"
            tmp_info = cmdb_mongo.find(query_dict={"manage_ip": host['manage_ip']}, fileds={"_id": 0})
            if tmp_info:
                tmp_info = tmp_info[0]
                host['name'] = tmp_info['name']
                host['id'] = tmp_info['name']
                host['device_id'] = tmp_info['id']
                host['serial_num'] = tmp_info['serial_num']
                host['location'] = tmp_info['idc_name'] + '_' + tmp_info['idc_model_name'] + '_' + tmp_info[
                    'rack_name'] + '_' + str(tmp_info['u_location_start']) + '_' + str(tmp_info['u_location_end'])
                host['vendor_model'] = tmp_info['vendor_name'] + '_' + tmp_info.get('model_name', ' ')
                host['expire'] = tmp_info['expire']
            # tmp_node = {
            #     "id": host.name,  # 设备名
            #     "manage_ip": host.host,  # 设备IP
            #     "image": self.hostname_to_image(host.name)  # 设备图标
            # }

        result['links'] += self.foo_link(result['nodes'], result['links'], strict=True)

        MongoNetOps.topology_ops(**result)

        self.topology.save()
        return result

    # 增加节点
    def add_node(self, add_nodes: list):
        # 先把原有的node变成IP为key的列表用于判断是否重复
        node_ip_dict = dict()
        if self.host_q is not None and isinstance(self.host_q, dict):
            # if 'nodes' in self.host_q.keys():
            node_ip_dict = {x['manage_ip']: x for x in self.host_q['nodes']}
        else:
            self.host_q = {
                "links": [],
                "nodes": [],
                "name": self.topology.name,
                "cmdb": '',
                "interface": []
            }
        # 开始添加新节点，并判断去重
        for node in add_nodes:
            if node['manage_ip'] not in node_ip_dict.keys():
                self.host_q['nodes'] += [node]
        # 重新计算
        self.local_graph()
        return

    # 删除节点
    def del_node(self, del_nodes: list):
        for del_node in del_nodes:
            for node in self.host_q['nodes']:
                if del_node['manage_ip'] == node['manage_ip']:
                    self.host_q['nodes'].remove(node)
        # 重新计算
        self.local_graph()

    # 删除连线 只能删除手动连线
    def del_link(self, del_link: dict):
        links = [x for x in self.host_q['links'] if x['method'] == 'manual']
        for link in links:
            if del_link['source_manage_ip'] == link['source_manage_ip'] \
                    and del_link['source_interfaces'] == link['source_interfaces'] \
                    and del_link['target_manage_ip'] == link['target_manage_ip'] \
                    and del_link['target_interfaces'] == link['target_interfaces']:
                self.host_q['links'].remove(link)
        # 重新计算
        self.local_graph()

