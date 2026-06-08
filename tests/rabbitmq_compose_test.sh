#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RABBITMQ_COMPOSE="${ROOT_DIR}/install-compose/rabbitmq-compose/docker-compose.yml"
RABBITMQ_INIT="${ROOT_DIR}/install-compose/rabbitmq-compose/rabbitmq.sh"
DEPLOY_SH="${ROOT_DIR}/install-compose/deploy.sh"

fail() {
  echo "FAIL: $*" >&2
  exit 1
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

test_compose_initializes_netaxe_vhost() {
  assert_contains "${RABBITMQ_COMPOSE}" "RABBITMQ_DEFAULT_VHOST=netaxe" "rabbitmq must create the netaxe vhost during first boot"
  assert_contains "${RABBITMQ_COMPOSE}" "healthcheck:" "rabbitmq compose must expose a healthcheck"
  assert_contains "${RABBITMQ_COMPOSE}" "rabbitmq-diagnostics -q ping" "rabbitmq healthcheck must wait for a responsive node"
  assert_not_contains "${RABBITMQ_COMPOSE}" "rabbitmq\\.sh:/etc/rabbitmq/rabbitmq\\.sh" "first boot must not depend on externally exec-ing rabbitmq.sh"
}

test_init_script_is_idempotent_when_used_manually() {
  assert_not_contains "${RABBITMQ_INIT}" "rabbitmqctl reset" "rabbitmq.sh must not reset broker state"
  assert_not_contains "${RABBITMQ_INIT}" "rabbitmqctl stop_app" "rabbitmq.sh must not stop the broker during initialization"
  assert_contains "${RABBITMQ_INIT}" "rabbitmq-diagnostics -q ping" "rabbitmq.sh must wait for RabbitMQ readiness before mutating state"
  assert_contains "${RABBITMQ_INIT}" "add_vhost netaxe" "rabbitmq.sh must ensure the netaxe vhost exists"
  assert_contains "${RABBITMQ_INIT}" "set_permissions -p netaxe adminnetaxe" "rabbitmq.sh must ensure adminnetaxe permissions on netaxe"
}

test_deploy_waits_for_health_instead_of_execing_init() {
  assert_not_contains "${DEPLOY_SH}" "docker exec rabbitmq.*/etc/rabbitmq/rabbitmq\\.sh" "deploy.sh must not run rabbitmq.sh before first startup is ready"
  assert_contains "${DEPLOY_SH}" "wait_for_container_healthy rabbitmq" "deploy.sh must wait for rabbitmq health before continuing"
}

main() {
  test_compose_initializes_netaxe_vhost
  test_init_script_is_idempotent_when_used_manually
  test_deploy_waits_for_health_instead_of_execing_init

  echo "rabbitmq compose tests passed"
}

main "$@"
