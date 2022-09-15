##############################################
# 基于centos7构建python3运行环境
# 进入容器：docker exec -it netops-private /bin/bash
##############################################

FROM centos:centos7

# 切换国内阿里YUM源镜像
RUN set -ex \
    && yum install -y wget \
    && cp /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.bak \
    && wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo \
    && sed -i 's/gpgcheck=1/gpgcheck=0/g' /etc/yum.repos.d/CentOS-Base.repo \
    && yum clean all \
    && yum makecache \
    && yum -y update \
    && yum clean all
# 系统环境依赖配置
# 目录设置
WORKDIR /netaxe
# 从gitlab仓库拉取
COPY Python-3.9.11.tgz  /netaxe
RUN set -ex \
    # 预安装所需组件
    && yum install -y epel-release tar libmysqlclient-dev supervisor libffi-devel zlib-devel bzip2-devel openssl-devel ncurses-devel \
    sqlite-devel readline-devel tk-devel gcc make initscripts  \
    && tar -zxvf Python-3.9.11.tgz \
    && cd Python-3.9.11 \
    && ./configure prefix=/usr/local/python3 \
    && make \
    && make install \
    && make clean \
    && rm -rf /netaxe/Python-3.9.11* \
    && yum install -y python-pip \
    && yum install -y python-devel \
    && yum install -y openldap-devel \
    && yum install -y python36-devel \
    && yum install -y git
# 设置默认为python3
RUN set -ex \
    # 备份旧版本python
    && mv /usr/bin/python /usr/bin/python27 \
    && mv /usr/bin/pip /usr/bin/pip-python2.7 \
    # 配置默认为python3
    && ln -sf /usr/local/python3/bin/python3.9 /usr/bin/python3 \
    && ln -sf /usr/local/python3/bin/pip3 /usr/bin/pip3
# 环境变量
#ENV MYSQL_DATABASE_NAME netops_server
# 系统环境变量$PATH追加pythn3 shell 为export PATH=$PATH:/usr/local/python3/bin
ENV PATH /usr/local/python3/bin:$PATH
# 设置默认python为python3
RUN echo 'alias python="/usr/local/python3/bin/python3"' > /etc/profile.d/python.sh
RUN source /etc/profile.d/python.sh


# 修复因修改python版本导致yum失效问题
RUN set -ex \
    && sed -i "s#/usr/bin/python#/usr/bin/python2.7#" /usr/bin/yum \
    && sed -i "s#/usr/bin/python#/usr/bin/python2.7#" /usr/libexec/urlgrabber-ext-down \
    && yum install -y deltarpm


# 基础环境配置
RUN set -ex \
    # 修改系统时区为东八区
    && rm -rf /etc/localtime \
    && ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && mkdir -p /home/netaxe

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
EXPOSE 8000
EXPOSE 8001
EXPOSE 5555
CMD ["sh", "start.sh"]