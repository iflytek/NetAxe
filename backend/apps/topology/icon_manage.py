# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      icon_manage
   Description:
   Author:          Lijiamin
   date：           2022/11/21 20:19
-------------------------------------------------
   Change Activity:
                    2022/11/21 20:19
-------------------------------------------------
"""
from pathlib import Path

from netaxe.settings import BASE_DIR

ICON_PATH = BASE_DIR + '/media/topology/img/'


class IconTree:
    def __init__(self):
        self.tree_data = {}
        self.tree_final = []
        self.pathname = Path(BASE_DIR + '/media/topology/img/')
        self.tree_str = ''
        self.key = 0
        self.root_path = 'img/'

    def _second_path(self, root_name, pathname):
        # self.tree_data[root_name]['children'] = []
        self.key += 1
        data = {
            'id': self.key,
            'key': root_name + '/' + pathname.name,
            # 'children': [],
            'label': pathname.name,
        }
        if pathname.is_dir():
            data['children'] = []
            for cp in pathname.iterdir():
                self.key += 1
                if cp.name.endswith('.png'):
                    sub_data = {
                        'id': self.key,
                        'key': data['key'] + cp.name,
                        'label': cp.name,
                    }
                    data['children'].append(sub_data)
        self.tree_data[root_name]['children'].append(data)

    def root_tree(self):
        black_list = ['.git', '__pycache__', 'favicon.ico', '.DS_Store', 'background.css']
        # 遍历根目录下所有文件
        for root in self.pathname.iterdir():
            if root.name not in black_list:
                self.key += 1
                data = {
                    'id': self.key,
                    'key': root.name,
                    # 'children': [],
                    'label': root.name,
                }
                self.tree_data[root.name] = data
                if root.is_dir():
                    self.tree_data[root.name]['children'] = []
                    for cp in root.iterdir():
                        if cp.name.endswith('.png'):
                            self._second_path(root.name, cp)

    def produce_tree(self):
        self.root_tree()
        self.tree_final = [self.tree_data[k] for k in self.tree_data.keys()]
