#!/bin/bash
#license:MIT
#Another:jmli12
#date:2022.09.7
cd /home/netaxe && git pull
pip3 install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/
pip3 install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

web(){
    mkdir -p /home/netaxe/logs/celery_logs
    mkdir -p /var/log/supervisor
    rm -rf /home/netaxe/logs/celery_logs/w*.log
    rm -rf *.pid
    echo 'uwsgi done'
    supervisord -n -c /home/netaxe/supervisord_prd.conf
}
default(){
    sleep 10
    celery -A netboost worker -Q default -c 10  -l info -n default
}
config(){
    sleep 10
    celery -A netboost worker -Q config -c 10 -l info -n config
}
case "$1" in
web)
web
;;
default)
default
;;
config)
config
;;
*)
echo "Usage: $1 {web|default|config}"
;;
esac
echo "start running!"