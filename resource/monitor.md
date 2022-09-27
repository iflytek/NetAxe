# 服务监控

## 初始化配置
```shell
# systemctl stop firewalld.service
# systemctl disable firewalld.service 
需要关闭 selinux，一定要关闭这个，开启selinux会引起一连串问题，甚至zabbix的discovery功能也不能正常使用
# sed -i "s/SELINUX=enforcing/SELINUX=disabled/g" /etc/selinux/config
确认是否修改成功
# grep SELINUX /etc/selinux/config
```
## 升级内核
CentOS7.x系统自带的3.10.x内核存在一些Bug，Docker运行不稳定，建议升级内核
```shell
#下载内核源
rpm -Uvh http://www.elrepo.org/elrepo-release-7.0-3.el7.elrepo.noarch.rpm
# 安装最新版本内核
yum --enablerepo=elrepo-kernel install -y kernel-lt
# 查看可用内核
cat /boot/grub2/grub.cfg |grep menuentry
# 设置开机从新内核启动  这里设置内核版本必须在上面的命令显示结果中
grub2-set-default "CentOS Linux (4.4.230-1.el7.elrepo.x86_64) 7 (Core)"
# 查看内核启动项
grub2-editenv list
# 重启系统使内核生效
reboot
# 查看内核版本是否生效
uname -r
```
## 初始化docker-ce
```shell
配置yum源
sudo tee /etc/yum.repos.d/docker-ce.repo <<-'EOF'
[docker-ce-stable]
name=Docker CE Stable -$basearch
baseurl=https://mirrors.aliyun.com/docker-ce/linux/centos/7/$basearch/stable
enabled=1
gpgcheck=1
gpgkey=https://mirrors.aliyun.com/docker-ce/linux/centos/gpg
EOF
#安装docker-ce
wget https://mirrors.aliyun.com/centos-vault/7.3.1611/extras/x86_64/Packages/container-selinux-2.9-4.el7.noarch.rpm
yum localinstall container-selinux-2.9-4.el7.noarch.rpm -y
yum install docker-ce -y
```

## docker集群初始化
可以把下面的内容放到一个shell脚本中，注意修改hostname 和 docker网卡IP，每个服务器应不同
```shell
hostnamectl set-hostname swarm01-7.97
sed -i "s/SELINUX=enforcing/SELINUX=disabled/g" /etc/selinux/config
grep SELINUX /etc/selinux/config
echo 备份当前的yum源
mv /etc/yum.repos.d /etc/yum.repos.d.backup4comex
mkdir /etc/yum.repos.d
wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
yum clean all
yum makecache
yum install -y net-tools vim lrzsz tree screen lsof tcp wget tcpdump nc mtr nmap openssl-devel ntpdate
systemctl stop firewalld
systemctl stop NetworkManager
systemctl disable firewalld
systemctl disable NetworkManager
sudo tee /etc/resolv.conf <<-'EOF'
nameserver 114.114.114.114
EOF
echo 使用tables键的时候补全systemctl命令
yum install -y epel-release  container-selinux bash-completion psmisc

tee /etc/yum.repos.d/docker-ce.repo <<-'EOF'
[docker-ce-stable]
name=Docker CE Stable -$basearch
baseurl=https://mirrors.aliyun.com/docker-ce/linux/centos/7/$basearch/stable
enabled=1
gpgcheck=1
gpgkey=https://mirrors.aliyun.com/docker-ce/linux/centos/gpg
EOF

wget https://mirrors.aliyun.com/centos-vault/7.3.1611/extras/x86_64/Packages/container-selinux-2.9-4.el7.noarch.rpm
yum localinstall container-selinux-2.9-4.el7.noarch.rpm -y
yum install docker-ce -y

systemctl start docker 
systemctl stop docker 
sudo ip link set dev docker0 down
yum install -y bridge-utils 
sudo brctl delbr docker0
sudo iptables -t nat -F POSTROUTING
brctl addbr docker0
ip addr add 1.1.134.1/24 dev docker0
ip link set dev docker0 up

systemctl start docker

docker network create --subnet 1.134.1.0/20 --gateway 1.134.1.1 -o com.docker.network.bridge.enable_icc=false  -o com.docker.network.bridge.name=docker_gwbridge  docker_gwbridge

sudo tee /etc/docker/daemon.json <<-'EOF'
{
    "bip":"1.1.134.1/24",
    "registry-mirrors": ["http://hub-mirror.c.163.com"]
}
EOF

sudo tee /etc/sysconfig/docker <<-'EOF'
OPTIONS='-H tcp://0.0.0.0:2375 -H fd:// --containerd=/run/containerd/containerd.sock'
EOF

echo 设置打开文件描述符的数量
echo "* hard nofile 65536" >> /etc/security/limits.conf
echo "* soft nofile 65536" >> /etc/security/limits.conf

echo 设置记录历史命令的格式
echo 'export HISTTIMEFORMAT=" %F %T `whoami` "' >> /etc/profile
source /etc/profile
echo 使用tables键的时候补全systemctl命令
yum install -y bash-completion
echo 安装killall命令
yum install -y psmisc  
echo 内核参数优化
tee /etc/sysctl.conf <<-'EOF'
net.ipv4.ip_forward = 1
fs.file-max=131072 
net.ipv4.tcp_syncookies=1
net.ipv4.tcp_tw_reuse=1
net.ipv4.tcp_tw_recycle=1
net.ipv4.tcp_fin_timeout=30
# net.ipv4.tcp_timestsmps=0
net.ipv4.tcp_keepalive_time=1200
net.ipv4.ip_local_port_range=1024 65535
net.ipv4.tcp_max_syn_backlog=8192
net.ipv4.tcp_max_tw_buckets=5000
net.core.somaxconn=32768
net.core.wmem_default=8388608
net.core.rmem_default=8388608
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.ipv4.tcp_synack_retries= 2
net.ipv4.tcp_syn_retries= 2
net.ipv4.tcp_wmem= 8192 436600 873200
net.ipv4.tcp_rmem = 32768 436600 873200
net.ipv4.tcp_mem= 94500000 91500000 92700000
net.ipv4.tcp_max_orphans= 3276800
fs.nr_open=1100000
EOF
sysctl -p

vi /usr/lib/systemd/system/docker.service
注释掉原来的ExecStart
[Service]
EnvironmentFile=/etc/sysconfig/docker
ExecStart=/usr/bin/dockerd $OPTIONS

systemctl daemon-reload
systemctl restart docker
systemctl enable docker

# 时间同步，如果没有内网时间同步可以使用公网的
crontab -e
*/5 * * * * /usr/sbin/ntpdate time1.aliyun.com
systemctl restart crond.service 
```
## 集群的master上执行
```shell
下面要填入master物理网卡的ip，表面master将以这个网卡地址启动
docker swarm init --advertise-addr 1.1.1.1

将会有如下显示
docker swarm join --token SWMTKN-1-3yccusxwi29oxrpgfszx8b3v5yo3glt5notowwwjb06dzc49rm-6jh46zylg198hqnu3a2muu9 1.1.1.1:2377
```

## 集群slave 配置  
```shell
执行master上的显示内容
docker swarm join --token SWMTKN-1-3yccusxwi29oxrpgfszx8b3v5yo3glt5notowwwjb06dzc49rm-6jh46zylg198hqnu3a2muu9 1.1.1.1:2377
```

## 集群master点执行
```shell
查看节点数
docker node ls
```

## 启动portainer的平台端(可以不装在集群服务器中，比如其它现有服务器中部署)
```shell
docker pull portainer/portainer-ce
新建一个docker-compose.yml  内容如下，目录路径随意
version: '3'
services:
  portainer:
    image: portainer/portainer-ce:latest
    container_name: portainer
    ports:
      - 9000:9000
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock 
      - ./portainer_data:/data
      - /usr/share/zoneinfo/Asia/Shanghai:/etc/localtime
    networks:
      - portna
networks:
  portna:
    driver: bridge
    ipam:
      config:
        - subnet: 11.11.11.0/24
启动服务
docker-compose up -d
```

## portainer-agent-stack.yml 配置  
在Master中 进行本节配置
用来向管理平台进行agent服务注册
这里示例以 /home/portainer 作为agent目录
```shell
mkdir -p /home/portainer
cd /home/portainer

portainer-agent-stack.yml 内容如下
version: '3.2'
services:
  agent:
    image: portainer/agent:latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /var/lib/docker/volumes:/var/lib/docker/volumes
    networks:
      - agent_network
    ports:
      - "9001:9001"
    deploy:
      mode: global
      placement:
        constraints: [node.platform.os == linux]
networks:
  agent_network:
    driver: overlay
    attachable: true

执行部署
docker stack deploy --compose-file=portainer-agent-stack.yml portainer
```