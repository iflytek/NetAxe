#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEPLOY_SH="${ROOT_DIR}/install-compose/deploy.sh"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

assert_contains() {
  local needle="$1"
  local haystack="$2"
  local message="$3"

  if [[ "${haystack}" != *"${needle}"* ]]; then
    fail "${message}"
  fi
}

assert_success() {
  local message="$1"
  shift

  if ! "$@" >/tmp/netaxe_preflight_test.out 2>/tmp/netaxe_preflight_test.err; then
    echo "stdout:" >&2
    cat /tmp/netaxe_preflight_test.out >&2
    echo "stderr:" >&2
    cat /tmp/netaxe_preflight_test.err >&2
    fail "${message}"
  fi
}

assert_failure_contains() {
  local expected="$1"
  local message="$2"
  shift 2

  if "$@" >/tmp/netaxe_preflight_test.out 2>/tmp/netaxe_preflight_test.err; then
    fail "${message}: command unexpectedly succeeded"
  fi

  local output
  output="$(cat /tmp/netaxe_preflight_test.out /tmp/netaxe_preflight_test.err)"
  assert_contains "${expected}" "${output}" "${message}: expected output to contain '${expected}'"
}

test_lib_only_guard_exists() {
  grep -q "NETAXE_DEPLOY_LIB_ONLY" "${DEPLOY_SH}" ||
    fail "deploy.sh must support NETAXE_DEPLOY_LIB_ONLY for safe preflight tests"
}

test_preflight_runs_before_mutations() {
  local preflight_line first_mutation_line

  preflight_line="$(awk '/run_preflight_checks/ { print NR; exit }' "${DEPLOY_SH}")"
  [[ -n "${preflight_line}" ]] || fail "deploy.sh must call run_preflight_checks"

  first_mutation_line="$(
    awk '/setenforce 0|systemctl stop|systemctl disable|systemctl restart|sed -i|docker network create|compose up -d|docker compose up -d/ { print NR; exit }' "${DEPLOY_SH}"
  )"
  [[ -n "${first_mutation_line}" ]] || fail "deploy.sh mutation boundary was not found"

  if (( preflight_line >= first_mutation_line )); then
    fail "run_preflight_checks must execute before any system, config, or Docker mutation"
  fi
}

load_deploy_functions() {
  NETAXE_DEPLOY_LIB_ONLY=1 . "${DEPLOY_SH}"
}

test_linux_kernel_required() {
  load_deploy_functions

  NETAXE_TEST_UNAME_S=Linux assert_success "Linux kernel should pass" check_linux_kernel
  NETAXE_TEST_UNAME_S=Darwin assert_failure_contains "Linux" "non-Linux kernel should fail" check_linux_kernel
}

test_amd64_architecture_required() {
  load_deploy_functions

  NETAXE_TEST_UNAME_M=x86_64 assert_success "x86_64 should pass" check_amd64_architecture
  NETAXE_TEST_UNAME_M=amd64 assert_success "amd64 should pass" check_amd64_architecture
  NETAXE_TEST_UNAME_M=aarch64 assert_failure_contains "AMD64" "non-AMD64 architecture should fail" check_amd64_architecture
}

test_memory_requirement() {
  load_deploy_functions

  NETAXE_TEST_MEM_TOTAL_KB=16000000 assert_success "16G class memory should pass" check_memory_requirement
  NETAXE_TEST_MEM_TOTAL_KB=15999999 assert_failure_contains "16G" "memory below 16G should fail" check_memory_requirement
}

test_docker_compose_required() {
  load_deploy_functions

  local fake_bin
  fake_bin="$(mktemp -d)"
  cat >"${fake_bin}/docker" <<'SCRIPT'
#!/usr/bin/env bash
if [[ "$1" == "compose" && "$2" == "version" ]]; then
  echo "Docker Compose version v2.15.1"
  exit 0
fi
exit 1
SCRIPT
  chmod +x "${fake_bin}/docker"

  PATH="${fake_bin}:${PATH}" assert_success "docker compose v2 should pass" check_docker_compose

  rm -f "${fake_bin}/docker"
  cat >"${fake_bin}/docker" <<'SCRIPT'
#!/usr/bin/env bash
echo "docker compose unavailable" >&2
exit 1
SCRIPT
  chmod +x "${fake_bin}/docker"

  PATH="${fake_bin}:${PATH}" assert_failure_contains "docker compose" "missing docker compose should fail" check_docker_compose
  rm -rf "${fake_bin}"
}

main() {
  test_lib_only_guard_exists
  test_preflight_runs_before_mutations
  test_linux_kernel_required
  test_amd64_architecture_required
  test_memory_requirement
  test_docker_compose_required

  echo "deploy preflight tests passed"
}

main "$@"
