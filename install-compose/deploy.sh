#! /bin/bash

MIN_MEMORY_KB=16000000

fail() {
    echo "错误: $*" >&2
    return 1
}

get_kernel_name() {
    if [ -n "${NETAXE_TEST_UNAME_S:-}" ]; then
        echo "${NETAXE_TEST_UNAME_S}"
    else
        uname -s
    fi
}

get_kernel_arch() {
    if [ -n "${NETAXE_TEST_UNAME_M:-}" ]; then
        echo "${NETAXE_TEST_UNAME_M}"
    else
        uname -m
    fi
}

get_mem_total_kb() {
    if [ -n "${NETAXE_TEST_MEM_TOTAL_KB:-}" ]; then
        echo "${NETAXE_TEST_MEM_TOTAL_KB}"
        return 0
    fi

    if [ ! -r /proc/meminfo ]; then
        echo 0
        return 0
    fi

    awk '/^MemTotal:/ { print $2; exit }' /proc/meminfo
}

check_linux_kernel() {
    kernel_name=$(get_kernel_name)
    if [ "${kernel_name}" != "Linux" ]; then
        fail "当前操作系统内核为 ${kernel_name}，NetAxe 部署脚本仅支持 Linux 服务器。"
        return 1
    fi
}

check_amd64_architecture() {
    kernel_arch=$(get_kernel_arch | tr '[:upper:]' '[:lower:]')
    case "${kernel_arch}" in
        x86_64|amd64)
            return 0
            ;;
        *)
            fail "当前内核架构为 ${kernel_arch}，NetAxe 容器基于 CentOS 7 x86_64 构建，仅支持 AMD64/x86_64 服务器。"
            return 1
            ;;
    esac
}

check_memory_requirement() {
    mem_total_kb=$(get_mem_total_kb)
    case "${mem_total_kb}" in
        ''|*[!0-9]*)
            fail "无法读取服务器内存配置，请确认 /proc/meminfo 可用。"
            return 1
            ;;
    esac

    if [ "${mem_total_kb}" -lt "${MIN_MEMORY_KB}" ]; then
        mem_total_gb=$((mem_total_kb / 1024 / 1024))
        fail "当前服务器内存约 ${mem_total_gb}G，小于 NetAxe 部署要求 16G。"
        return 1
    fi
}

check_required_commands() {
    missing_commands=""
    for cmd in awk curl cut find git grep htpasswd ip openssl sed ssh-keygen systemctl tr; do
        if ! command -v "${cmd}" >/dev/null 2>&1; then
            missing_commands="${missing_commands} ${cmd}"
        fi
    done

    if [ -n "${missing_commands}" ]; then
        fail "当前服务器缺少必要命令:${missing_commands}"
        return 1
    fi
}

check_docker_compose() {
    if ! command -v docker >/dev/null 2>&1; then
        fail "当前服务器未安装 Docker，请先安装 Docker 和 docker compose。"
        return 1
    fi

    if ! docker compose version >/dev/null 2>&1; then
        fail "当前服务器未安装可用的 docker compose v2，请确认 'docker compose version' 可正常执行。"
        return 1
    fi
}

run_preflight_checks() {
    echo "------------------开始部署环境检查----------------------"
    check_linux_kernel || return 1
    check_amd64_architecture || return 1
    check_memory_requirement || return 1
    check_required_commands || return 1
    check_docker_compose || return 1
    echo "------------------部署环境检查通过----------------------"
}

compose() {
    docker compose "$@"
}

prepare_host_services() {
    # SELinux may not be installed or enabled on every supported Linux host.
    if command -v setenforce >/dev/null 2>&1; then
        setenforce 0 || true
    fi

    systemctl stop firewalld
    systemctl disable firewalld
    systemctl restart docker
}

wait_for_container_healthy() {
    container_name="$1"
    timeout_seconds="${2:-120}"
    elapsed_seconds=0

    echo "等待 ${container_name} 容器健康..."
    while [ "${elapsed_seconds}" -lt "${timeout_seconds}" ]; do
        health_status=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "${container_name}" 2>/dev/null || true)
        if [ "${health_status}" = "healthy" ]; then
            echo "${container_name} 容器健康检查通过"
            return 0
        fi

        sleep 2
        elapsed_seconds=$((elapsed_seconds + 2))
    done

    fail "${container_name} 容器在 ${timeout_seconds}s 内未进入 healthy 状态"
    return 1
}

main() {
    current_path="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

    run_preflight_checks || exit 1

    # 关闭selinux和firewalld
    prepare_host_services

    cd "${current_path}" || exit 1

    # 默认key设置
    default_key=$(openssl rand -hex 8)
    nacos_key=$(openssl rand -base64 32)
    x_api_key=$(openssl rand -base64 32)
    # 生成 Prometheus Web 认证密码
    prometheus_password_hash=$(htpasswd -nbB admin "${default_key}" | cut -d: -f2)

    if [ $# -eq 0 ]; then
      # 如果没有传入参数，则使用默认网卡的IP地址
      default_iface=$(ip route show default | awk '/default/ {print $5}')
      iface_ip=$(ip addr show dev "${default_iface}" | awk '/inet / {print $2}' | cut -d '/' -f 1)
    else
      # 如果传入了参数，则使用用户输入的IP地址
      iface_ip=$1
    fi

    echo "开始进行初始化操作，本操作将一次性生成各个配置文件的秘钥"
    echo "Using IP: ${iface_ip}"
    echo "Using key: ${default_key}"
    echo "Using nacos_key: ${nacos_key}"


    # 遍历当前目录的所有子目录，查找 config.json 文件并修改其中的 server_ip 字段
    find . -type f -name "config.json" -exec sed -i "s|SERVER_IP|${iface_ip}|g" {} \;
    find . -type f -name "config.yaml" -exec sed -i "s|SERVER_IP|${iface_ip}|g" {} \;
    find . -type f -name "config.json" -exec sed -i "s|X-API-KEY|${x_api_key}|g" {} \;
    find . -type f -name "config.yaml" -exec sed -i "s|X-API-KEY|${x_api_key}|g" {} \;
    find . -type f \( -name "*.yml" -o -name "*.yaml" \) -exec sed -i "s|X-API-KEY|${x_api_key}|g" {} \;
    find . -type f -name "config.json" -exec sed -i "s|MYSQL_PASSWD|${default_key}|g" {} \;
    find . -type f -name "config.json" -exec sed -i "s|MYSQL_PASSWORD|${default_key}|g" {} \;
    find . -type f -name "config.yaml" -exec sed -i "s|MYSQL_PASSWD|${default_key}|g" {} \;
    find . -type f -name "config.json" -exec sed -i "s|REDIS_PASSWORD|${default_key}|g" {} \;
    find . -type f -name "config.json" -exec sed -i "s|MONGO_PASSWORD|${default_key}|g" {} \;
    find . -type f -name "config.json" -exec sed -i "s|RABBITMQ_PASSWORD|${default_key}|g" {} \;
    find . -type f -name "config.json" -exec sed -i "s|DJANGO_INSECURE|${default_key}|g" {} \;
    find . -type f -name "config.json" -exec sed -i "s|NACOS_PASSWORD|${default_key}|g" {} \;
    find . -type f -name "config.yaml" -exec sed -i "s|REGIS_PASSWORD|${default_key}|g" {} \;
    find . -type f \( -name "*.yml" -o -name "*.yaml" \) -exec sed -i "s|REGIS_PASSWORD|${default_key}|g" {} \;
    find . -type f \( -name "*.yml" -o -name "*.yaml" \) -exec sed -i "s|NETAXE_ALERT_WEBHOOK|${default_key}|g" {} \;

    #find ./apisix-compose -type f -name "config.yaml" -exec sed -i "s|APISIX_ADMIN_KEY|${default_key}|g" {} \;
    #find ./apisix-compose -type f -name "conf.yaml" -exec sed -i "s|APISIX_ADMIN_PASSWORD|${default_key}|g" {} \;
    #find ./apisix-compose -type f -name "config.yaml" -exec sed -i "s|NACOS_PASSWORD|${default_key}|g" {} \;
    find ./redis-compose -type f -name "docker-compose.yml" -exec sed -i "s|REDIS_PASSWORD|${default_key}|g" {} \;
    find ./mongo-compose -type f -name "docker-compose.yml" -exec sed -i "s|MONGO_PASSWORD|${default_key}|g" {} \;
    find ./rabbitmq-compose -type f -name "docker-compose.yml" -exec sed -i "s|RABBITMQ_PASSWORD|${default_key}|g" {} \;
    find ./alertgateway-compose -type f -name "docker-compose.yml" -exec sed -i "s|PROMETHEUS_PASSWORD|${default_key}|g" {} \;


    sed -i "s|MYSQL_PASSWD|${default_key}|g" ./mysql-compose/init/netaxe.sql
    sed -i "s|MYSQL_PASSWD|${default_key}|g" ./neteye-compose/config.yaml
    sed -i "s|MYSQL_PASSWD|${default_key}|g" ./mysql-compose/docker-compose.yml
    sed -i "s|NACOS_PASSWORD|${default_key}|g" ./nacos-compose/docker-compose.yml
    sed -i "s|NACOS_KEY|${nacos_key}|g" ./nacos-compose/docker-compose.yml
    sed -i "s|APISIX_ADMIN_KEY|${default_key}|g" ./init.sh
    sed -i "s|DJANGO_INSECURE|${default_key}|g" ./init.sh
    sed -i "s|REGIS_PASSWORD|${default_key}|g" ./prometheus-compose/prometheus.yml
    sed -i "s|SERVER_IP|${iface_ip}|g" ./prometheus-compose/prometheus.yml
    sed -i "s|REGIS_PASSWORD|${prometheus_password_hash}|g" ./prometheus-compose/prometheus_web.yml

    # 创建docker_netaxe网络
    docker network create  --subnet=1.1.38.0/24 --ip-range=1.1.38.0/24 --gateway=1.1.38.254 docker_netaxe


    # 安装mysql和mongo
    echo "------------------开始mysql和mongo部署------------"
    cd "${current_path}" || exit 1
    cd mysql-compose || exit 1
    compose up -d
    sleep 10
    echo "------------------mysql状态----------------------"
    compose ps

    cd "${current_path}" || exit 1
    cd mongo-compose || exit 1
    compose up -d
    sleep 10
    echo "------------------mongo状态----------------------"
    compose ps


    # 安装redis
    echo "------------------开始redis部署-----------------"
    cd "${current_path}" || exit 1
    cd redis-compose || exit 1
    compose up -d
    echo "------------------redis状态------------------"
    compose ps


    # 安装rabbitmq
    echo "------------------开始rabbitmq部署-----------------"
    cd "${current_path}" || exit 1
    cd rabbitmq-compose || exit 1
    compose up -d
    wait_for_container_healthy rabbitmq 180 || exit 1
    echo "------------------rabbitmq状态------------------"
    compose ps


    # 安装nacos
    # 安装nacos
    echo "------------------开始nacos部署-------------------"
    cd "${current_path}" || exit 1
    cd nacos-compose || exit 1
    compose up -d
    echo "------------------nacos状态----------------------"
    compose ps

    # 增加延迟，等待 Nacos 启动完成
    echo "等待 Nacos 启动完成..."
    sleep 30  # 等待 30 秒，可以根据实际情况调整时间

    # 部署服务得时候需要注册nacos，需要重置后得密码信息
    echo "------------------准备初始化nacos密码完成----------------------"
    curl -X POST 'http://127.0.0.1:8848/nacos/v1/auth/users/admin' -d "password=${default_key}"
    echo "------------------初始化nacos密码完成----------------------"


    # 安装main和rbac
    echo "------------------开始权限中心部署--------------"
    cd "${current_path}" || exit 1
    cd abac-compose || exit 1
    compose pull
    compose  up -d
    echo "------------------权限中心状态------------------"
    compose ps
    sleep 10

    # 安装基础平台
    echo "------------------开始管控平台部署--------------"
    cd "${current_path}" || exit 1
    cd baseplatform-compose || exit 1
    git clone -b dev https://gitee.com/NetAxeClub/base-platform.git
    mv config.json base-platform/config/
    mkdir base-platform/backend/media/device_config/current-configuration
    mkdir base-platform/backend/media/device_config/startup-configuration
    mkdir base-platform/backend/plugins/extensibles
    compose pull
    compose  up -d
    echo "------------------管控平台状态------------------"
    compose ps
    sleep 10

    # 安装消息网关
    echo "------------------开始消息网关部署--------------"
    cd "${current_path}" || exit 1
    cd msggateway-compose || exit 1
    compose pull
    compose  up -d
    echo "------------------消息网关状态------------------"
    compose ps
    sleep 10

    # 安装告警中心
    echo "------------------开始告警中心部署--------------"
    cd "${current_path}" || exit 1
    cd alertgateway-compose || exit 1
    compose pull
    compose  up -d
    echo "------------------告警中心状态------------------"
    compose  ps
    sleep 10

    # 安装工作台
    echo "------------------开始工作台部署--------------"
    cd "${current_path}" || exit 1
    cd workbench-compose || exit 1
    compose pull
    compose  up -d
    echo "------------------工作台状态------------------"
    compose  ps
    sleep 10

    # 安装地址管理IPAM
    echo "------------------开始地址管理IPAM部署--------------"
    cd "${current_path}" || exit 1
    cd ipam-compose || exit 1
    compose pull
    compose  up -d
    echo "------------------地址管理IPAM状态------------------"
    compose  ps
    sleep 10


    # 安装监控中心
    echo "------------------开始监控中心部署--------------"
    cd "${current_path}" || exit 1
    cd neteye-compose || exit 1
    compose pull
    compose  up -d
    echo "------------------监控中心状态------------------"
    compose  ps
    sleep 10

    # 安装grafana
    echo "------------------开始grafana部署--------------"
    cd "${current_path}" || exit 1
    cd grafana-compose || exit 1
    docker volume create grafana-data
    compose pull
    ssh-keygen -t rsa -b 4096 -m PEM -f grafana.key -N ""
    openssl rsa -in grafana.key -pubout -outform PEM -out public-key.pem
    compose  up -d
    echo "------------------grafana状态------------------"
    compose  ps
    sleep 10

    echo "------------------部署完成------------------------"

    # 安装前端服务
    echo "------------------开始前端服务部署--------------"
    cd "${current_path}" || exit 1
    cd main-compose || exit 1
    compose pull
    compose  up -d
    echo "------------------前端服务状态------------------"
    compose ps
    sleep 10

    # 初始化监控中心 icmp_15s、tcp_connect_15s、tcp_connect_all
    echo "-----------监控中心初始化创建空服务--------------"
    curl -X PUT http://127.0.0.1:31468/regis/servers  -H "Content-Type: application/json"  -u admin:"${default_key}"  -d  '{"name":"icmp_15s"}'
    curl -X PUT http://127.0.0.1:31468/regis/servers  -H "Content-Type: application/json"  -u admin:"${default_key}"  -d  '{"name":"tcp_connect_15s"}'
    curl -X PUT http://127.0.0.1:31468/regis/servers  -H "Content-Type: application/json"  -u admin:"${default_key}"  -d  '{"name":"tcp_connect_all"}'
    echo "----------监控中心初始化创建空服务成功------------"


    echo "------------------刷新权限------------------"
    curl "http://127.0.0.1:31104/abac-api/authority/auth_policy/?reload=1"
    echo "------------------刷新权限成功------------------"
    sleep 10
    curl "http://127.0.0.1:31104/abac-api/authority/auth_policy/?reload=1"
}

if [ "${NETAXE_DEPLOY_LIB_ONLY:-0}" = "1" ]; then
    return 0 2>/dev/null || exit 0
fi

main "$@"
