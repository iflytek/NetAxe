# Repository Guidelines

## Project Structure & Ownership

This repository is the NetAxe deployment and installation bundle. It is not the
main backend or frontend source tree. Most tracked files are compose manifests,
runtime config templates, Nginx config, Prometheus config, example resources,
and installation scripts under `install-compose/`.

Key areas:

- `install-compose/README.md`: short deployment entrypoint documentation.
- `install-compose/deploy.sh`: full Linux host deployment script.
- `install-compose/deploy-lite.sh`: lighter deployment variant.
- `install-compose/init.sh`: APISIX route initialization script, not the first
  host initialization step.
- `install-compose/*-compose/`: one compose folder per NetAxe service or
  dependency.
- `resource/` and `readme/`: documentation images and project assets.

## Safety Rules

Do not run `install-compose/deploy.sh`, `install-compose/deploy-lite.sh`,
`install-compose/undeploy.sh`, or broad `docker compose up/down` commands unless
the user explicitly asks to deploy or tear down the stack.

The deployment scripts mutate tracked config files by replacing placeholders
such as `SERVER_IP`, `MYSQL_PASSWD`, `NACOS_PASSWORD`, `RABBITMQ_PASSWORD`,
`MONGO_PASSWORD`, `REDIS_PASSWORD`, `APISIX_ADMIN_KEY`, and
`DJANGO_INSECURE`. They also create Docker networks, pull images, start
containers, generate keys, and call local services. Treat those generated values
as environment-specific secrets and avoid committing them.

These scripts are written for a Linux server environment. They use commands such
as `setenforce`, `systemctl`, `ip route`, GNU-style `sed -i`, `htpasswd`,
`ssh-keygen`, `openssl`, Docker, and Docker Compose. On macOS, inspect or adapt
the scripts instead of running them directly.

## Development Commands

Prefer read-only checks unless deployment is the explicit task:

- `rg -n "SERVER_IP|MYSQL_PASSWD|NACOS_PASSWORD|APISIX_ADMIN_KEY" install-compose`
  checks whether templates still contain unreplaced placeholders.
- `docker compose -f install-compose/<service>-compose/docker-compose.yml config`
  validates a single compose file without starting containers.
- `git status --short --untracked-files=all` confirms scope before and after
  changes.
- `git diff --check` catches whitespace errors before handoff.

When deployment is explicitly requested, run commands from `install-compose/`,
not from the repository root, because the scripts rely on relative paths.

## Editing Guidelines

Keep changes narrow to the relevant compose folder, config template, or script.
Do not rewrite generated secrets into templates unless the task is specifically
to initialize a deployment target. If a script needs to become portable, preserve
the existing Linux deployment path and add clear guards rather than silently
changing production behavior.

For compose changes, validate the affected file with `docker compose ... config`
when Docker Compose is available. For script-only or docs-only changes, use
`git diff --check` and a targeted `rg` check.
