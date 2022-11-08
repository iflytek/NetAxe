# -*- coding: utf-8 -*-
# @Time    : 2022/6/21 15:26
# @Author  : LiJiaMin
# @Site    :
# @File    : config_parse.py
# @Software: PyCharm
import os
import time
from pathlib import Path

from netboost.settings import BASE_DIR
from apps.config_center.config_parse.hp_comware.ttp_parse import H3cParse

CONFIG_PATH = BASE_DIR + '/media/device_config/current-configuration/'

vendor_map = {
    'hp_comware': H3cParse
}


async def sub_file_proc(host_file, _dir, host):
    with open("{}{}/{}".format(CONFIG_PATH, _dir, host), 'r', encoding='utf8') as f:
        vendor_host = host_file.split('-')
        vendor = vendor_host[0]
        host = vendor_host[1]
        data_to_parse = f.read()
        try:
            if vendor in vendor_map.keys():
                _Parse = vendor_map[vendor](host, _dir)
                _Parse.parse(data_to_parse)
                _Parse.get_yaml()
        except Exception as e:
            print(e)
    return


# 配置文件解析主调度任务，负责解析配置，并按指标拆分具体功能
async def config_file_parse():
    dir_list = os.listdir(CONFIG_PATH)
    for _dir in dir_list:
        if os.path.isdir(CONFIG_PATH + _dir):
            device_file_list = os.listdir(CONFIG_PATH + _dir)
            for host in device_file_list:
                if host[-4:] == '.txt':
                    host_file = host[:-4]
                    await sub_file_proc(host_file, _dir, host)


# 生成配置文件目录树
def config_file_path_tree():
    p = Path(BASE_DIR + '/media/device_config/')
    pit = p.iterdir()
    for _p in pit:
        print(_p.name)


class ConfigTree:
    def __init__(self):
        self.tree_data = {}
        self.tree_final = []
        self.pathname = Path(BASE_DIR + '/media/device_config/')
        self.tree_str = ''
        self.key = 0
        self.root_path = 'device_config/'

    def _second_path(self, root_name, pathname):
        self.key += 1
        data = {
            'id': self.key,
            'key': root_name + '/' + pathname.name + '/',
            'children': [],
            'label': pathname.name,
        }
        if pathname.is_dir():
            for cp in pathname.iterdir():
                self.key += 1
                sub_data = {
                    'id': self.key,
                    'key': data['key'] + cp.name,
                    'label': cp.name,
                }
                data['children'].append(sub_data)
        self.tree_data[root_name]['children'].append(data)

    def root_tree(self):
        black_list = ['.git', '__pycache__']
        # 遍历根目录下所有文件
        for root in self.pathname.iterdir():
            if root.name not in black_list:
                self.key += 1
                data = {
                    'id': self.key,
                    'key': self.key,
                    'children': [],
                    'label': root.name,
                }
                self.tree_data[root.name] = data
                if root.is_dir():
                    for cp in root.iterdir():
                        self._second_path(root.name, cp)

    def produce_tree(self):
        self.root_tree()
        self.tree_final = [self.tree_data[k] for k in self.tree_data.keys()]


class FSMTree:
    def __init__(self):
        self.tree_data = {}
        self.tree_final = []
        self.pathname = Path(BASE_DIR + '/utils/connect_layer/my_netmiko/templates/')
        self.tree_str = ''
        self.key = 0
        self.root_path = 'templates/'

    def _second_path(self, root_name, pathname):
        self.key += 1
        data = {
            'id': self.key,
            'key': root_name + '/' + pathname.name + '/',
            'children': [],
            'label': pathname.name,
        }
        if pathname.is_dir():
            for cp in pathname.iterdir():
                self.key += 1
                sub_data = {
                    'id': self.key,
                    'key': data['key'] + cp.name,
                    'label': cp.name,
                }
                data['children'].append(sub_data)
        self.tree_data[root_name]['children'].append(data)

    def root_tree(self):
        black_list = ['.git', '__pycache__']
        # 遍历根目录下所有文件
        for root in self.pathname.iterdir():
            if root.name not in black_list:
                self.key += 1
                data = {
                    'id': self.key,
                    'key': root.name,
                    'label': root.name,
                }
                self.tree_data[root.name] = data
                if root.is_dir():
                    for cp in root.iterdir():
                        self._second_path(root.name, cp)

    def produce_tree(self):
        self.root_tree()
        self.tree_final = [self.tree_data[k] for k in self.tree_data.keys()]


def test_push():
    import asyncio
    start_time = time.time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(config_file_parse())
    print(int(time.time() - start_time))


if __name__ == "__main__":
    import asyncio
    start_time = time.time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(config_file_parse())
    print(int(time.time() - start_time))
    # config_file_parse()
    # _tree = ConfigTree()
    # _tree.produce_tree()
    # for i in _tree.tree_final:
    #     print(i)
