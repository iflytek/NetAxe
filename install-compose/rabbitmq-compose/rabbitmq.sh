#!/bin/sh
set -eu

max_attempts="${RABBITMQ_INIT_MAX_ATTEMPTS:-60}"
attempt=1

while ! rabbitmq-diagnostics -q ping >/dev/null 2>&1; do
  if [ "${attempt}" -ge "${max_attempts}" ]; then
    echo "RabbitMQ is not ready after ${max_attempts} attempts" >&2
    exit 1
  fi
  attempt=$((attempt + 1))
  sleep 2
done

rabbitmqctl add_vhost netaxe >/dev/null 2>&1 || true
rabbitmqctl set_permissions -p netaxe adminnetaxe '.*' '.*' '.*'
rabbitmqctl set_user_tags adminnetaxe administrator >/dev/null 2>&1 || true
