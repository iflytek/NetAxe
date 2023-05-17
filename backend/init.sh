#!/bin/bash
#license:MIT
#Another:jmli12
#date:2023.1.4
# cd /home/netaxe && git pull
# pip3 install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
# pip3 install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
python3 manage.py migrate users
python3 manage.py migrate
python3 manage.py init_asset # 资产初始化
python3 manage.py init_collect # 采集方案初始化
#python3 manage.py init_system_menu # 系统菜单初始化

echo "cmdb init success!"
echo "starting web server!"
sh start.sh web