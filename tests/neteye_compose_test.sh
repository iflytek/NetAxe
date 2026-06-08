#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NETEYE_COMPOSE="${ROOT_DIR}/install-compose/neteye-compose/docker-compose.yml"
NETEYE_CONFIG="${ROOT_DIR}/install-compose/neteye-compose/config.yaml"
VMAGENT_CONFIG="${ROOT_DIR}/install-compose/neteye-compose/vmagent/prometheus-cluster.yml"
ALERTGATEWAY_CONFIG="${ROOT_DIR}/install-compose/alertgateway-compose/config.json"
DEPLOY_SH="${ROOT_DIR}/install-compose/deploy.sh"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

assert_file_exists() {
  local file="$1"
  [[ -f "${file}" ]] || fail "expected file to exist: ${file}"
}

assert_contains() {
  local file="$1"
  local pattern="$2"
  local message="$3"

  grep -Eq -- "${pattern}" "${file}" || fail "${message}"
}

assert_not_contains() {
  local file="$1"
  local pattern="$2"
  local message="$3"

  if grep -Eq -- "${pattern}" "${file}"; then
    fail "${message}"
  fi
}

assert_any_file_contains() {
  local pattern="$1"
  local message="$2"

  if ! find "${ROOT_DIR}/install-compose" -type f \
    \( -name 'docker-compose.yml' -o -name '*.yaml' -o -name '*.yml' \) \
    -exec grep -Eq -- "${pattern}" {} +; then
    fail "${message}"
  fi
}

test_private_registry_is_forbidden() {
  if grep -R "artifacts.iflytek.com/docker-private/netops/" "${ROOT_DIR}/install-compose" >/dev/null 2>&1; then
    fail "install-compose must not reference the private artifacts.iflytek.com registry"
  fi
}

test_required_services_exist() {
  for service in monitor-center register vmagent vmalert snmp-exporter; do
    assert_contains "${NETEYE_COMPOSE}" "^  ${service}:" "neteye-compose must define service ${service}"
  done
}

test_required_images_are_current_and_public() {
  assert_contains "${NETEYE_COMPOSE}" "image: registry.cn-hangzhou.aliyuncs.com/netaxe/neteye:3.2" "monitor-center must use the public NetAxe image"
  assert_contains "${NETEYE_COMPOSE}" "image: registry.cn-hangzhou.aliyuncs.com/netaxe/vmagent:componentized" "vmagent must use the public NetAxe componentized image"
  assert_contains "${NETEYE_COMPOSE}" "image: registry.cn-hangzhou.aliyuncs.com/netaxe/vmalert:componentized" "vmalert must use the public NetAxe componentized image"
  assert_contains "${NETEYE_COMPOSE}" "image: registry.cn-hangzhou.aliyuncs.com/netaxe/snmp_exporter:1.0" "snmp_exporter must use the public NetAxe image requested for this project"
  assert_contains "${NETEYE_COMPOSE}" "image: registry.cn-hangzhou.aliyuncs.com/netaxe/regiscenter:2.5" "register must use the public NetAxe regiscenter image"
  assert_contains "${NETEYE_COMPOSE}" "image: prom/alertmanager:v0.32.2" "alertmanager must use the current public Prometheus image"
  assert_contains "${NETEYE_COMPOSE}" "image: quay.io/prometheus/blackbox-exporter:v0.27.0" "blackbox exporter must use the current public Prometheus image"
  assert_not_contains "${NETEYE_COMPOSE}" "v1\\.102\\.0" "VictoriaMetrics images must not remain on v1.102.0"
  assert_not_contains "${NETEYE_COMPOSE}" "image: victoriametrics/(vmagent|vmalert):" "vmagent and vmalert must not fall back to upstream images without componentReporter support"
}

test_rule_directories_match_monitor_center_layout() {
  assert_contains "${NETEYE_COMPOSE}" "./rules/monitor:/build/rules/monitor" "monitor-center must mount monitor rules from rules/monitor"
  assert_contains "${NETEYE_COMPOSE}" "./rules/alarm:/build/rules/alarm" "monitor-center must mount alarm rules from rules/alarm"
  assert_contains "${NETEYE_COMPOSE}" "./rules/monitor:/etc/snmp_exporter" "snmp-exporter must read SNMP configs from rules/monitor"
  assert_contains "${NETEYE_COMPOSE}" "./vmalert-runtime:/etc/alerts" "vmalert must read the managed runtime rule file from vmalert-runtime"
  assert_file_exists "${ROOT_DIR}/install-compose/neteye-compose/vmalert-runtime/managed.yml"

  for file in snmp_h3c.yml snmp_hillstone.yml snmp_hw.yml snmp_other.yml snmp_up.yml; do
    assert_file_exists "${ROOT_DIR}/install-compose/neteye-compose/rules/monitor/${file}"
  done

  for file in blackbox_service.yml dns_probe.yml general_hardware.yml general_interface.yml general_protocol.yml mtr_rules.yml qos_rule.yml unique_gongwang.yml unique_zhuanxian.yml; do
    assert_file_exists "${ROOT_DIR}/install-compose/neteye-compose/rules/alarm/${file}"
  done
}

test_neteye_config_matches_component_layout() {
  assert_contains "${NETEYE_CONFIG}" "regiscenter:" "monitor-center config must include regiscenter target settings"
  assert_contains "${NETEYE_CONFIG}" "endpoint: \"http://register:4168\"" "monitor-center must target the local register service"
  assert_contains "${NETEYE_CONFIG}" "password: REGIS_PASSWORD" "register password must stay as deployment placeholder before deploy.sh runs"
  assert_contains "${NETEYE_CONFIG}" "component_id: vmagent-neteye-compose" "monitor-center config must authorize the vmagent component"
  assert_contains "${NETEYE_CONFIG}" "component_id: vmalert-neteye-compose" "monitor-center config must authorize the vmalert component"
  assert_contains "${NETEYE_CONFIG}" "key: X-API-KEY" "component API keys must use the deployment-generated API key placeholder"
}

test_component_reporters_are_enabled() {
  for component_id in vmagent-neteye-compose vmalert-neteye-compose; do
    assert_contains "${NETEYE_COMPOSE}" "--componentReporter.componentID=${component_id}" "componentReporter must set component id ${component_id}"
  done
  assert_contains "${NETEYE_COMPOSE}" "--componentReporter.enabled" "componentReporter must be enabled"
  assert_contains "${NETEYE_COMPOSE}" "--componentReporter.registerURL=http://monitor-center:8000/monitor/components/register" "componentReporter must register against monitor-center"
  assert_contains "${NETEYE_COMPOSE}" "--componentReporter.heartbeatURL=http://monitor-center:8000/monitor/components/heartbeat" "componentReporter must heartbeat against monitor-center"
  assert_contains "${NETEYE_COMPOSE}" "--componentReporter.apiKey=X-API-KEY" "componentReporter must use the deployment-generated API key"
  assert_contains "${NETEYE_COMPOSE}" "--componentReporter.configURL=http://monitor-center:8000/monitor/components/vmalert-neteye-compose/config" "vmalert must pull managed rules through monitor-center"
  assert_contains "${NETEYE_COMPOSE}" "--componentReporter.managedConfigFile=/etc/alerts/managed.yml" "vmalert must atomically replace the managed runtime rule file"
  assert_contains "${NETEYE_COMPOSE}" "--componentReporter.currentConfigVersionFile=/var/lib/vmalert/current-config-version" "vmalert must persist applied config version"
}

test_vmagent_uses_register_sd_and_blackbox() {
  assert_contains "${VMAGENT_CONFIG}" "http://register:4168/regis/services" "vmagent must discover blackbox targets from the local register service"
  assert_contains "${VMAGENT_CONFIG}" "password: REGIS_PASSWORD" "vmagent register password must stay as deployment placeholder before deploy.sh runs"
  assert_contains "${VMAGENT_CONFIG}" "replacement: blackbox-exporter:9115" "vmagent must scrape blackbox through the neteye-compose blackbox service"
}

test_alertgateway_queries_victoriametrics() {
  assert_contains "${ALERTGATEWAY_CONFIG}" '"prometheus": "vmauth:8427/select/0/prometheus"' "alertgateway must query VictoriaMetrics through vmauth after prometheus-compose is removed"
}

test_deploy_uses_neteye_compose_without_prometheus_conflict() {
  assert_contains "${DEPLOY_SH}" "cd neteye-compose" "deploy.sh must actively deploy neteye-compose"
  assert_contains "${DEPLOY_SH}" "监控中心状态" "deploy.sh must print neteye-compose status"
  assert_not_contains "${DEPLOY_SH}" "cd prometheus-compose" "deploy.sh must not deploy the old prometheus-compose when neteye-compose owns register and blackbox"
  assert_contains "${DEPLOY_SH}" "-name \"\\*.yml\"" "deploy.sh must replace placeholders in neteye-compose yml configs"
  assert_contains "${DEPLOY_SH}" "-name \"\\*.yml\".*s\\|X-API-KEY\\|" "deploy.sh must replace componentReporter API key placeholders in yml configs"
}

main() {
  test_private_registry_is_forbidden
  test_required_services_exist
  test_required_images_are_current_and_public
  test_rule_directories_match_monitor_center_layout
  test_neteye_config_matches_component_layout
  test_component_reporters_are_enabled
  test_vmagent_uses_register_sd_and_blackbox
  test_alertgateway_queries_victoriametrics
  test_deploy_uses_neteye_compose_without_prometheus_conflict
  assert_any_file_contains "registry.cn-hangzhou.aliyuncs.com/netaxe/snmp_exporter:1.0" "snmp_exporter public image reference must be present"

  echo "neteye compose tests passed"
}

main "$@"
