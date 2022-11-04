##############################################
# 基于centos7构建python3运行环境
# 进入容器：docker exec -it netops-private /bin/bash
##############################################

FROM registry.cn-hangzhou.aliyuncs.com/netaxe/netaxe-backend:1.0.5

# 更新pip版本
RUN pip3 install -i https://pypi.doubanio.com/simple/ uwsgi --upgrade pip

COPY . /home/netaxe
# 再次切换工作目录为Django主目录
WORKDIR /home/netaxe


# 安装项目所需python第三方库
# 指定setuptools的版本，必须指定，新版本有兼容问题
RUN set -ex \
    && /usr/local/python3/bin/pip3 install setuptools_scm -i https://mirrors.aliyun.com/pypi/simple/ \
    && /usr/local/python3/bin/pip3 install --upgrade pip setuptools==45.2.0 -i https://mirrors.aliyun.com/pypi/simple/ \
    &&/usr/local/python3/bin/pip3 install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ \
    && rm -rf /home/netaxe/* \
    && rm -rf /var/cache/yum/*
EXPOSE 5555
# EXPOSE 8000
EXPOSE 8001
CMD ["sh", "start.sh"]