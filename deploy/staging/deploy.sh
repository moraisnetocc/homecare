#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
cd /opt/homecore/staging
IMAGE="${1:?Usage: deploy.sh ghcr.io/moraisnetocc/homecare-cloud:sha-<40hex>}"
if [[ ! "$IMAGE" =~ ^ghcr\.io/moraisnetocc/homecare-cloud:sha-[a-f0-9]{40}$ ]]; then
  echo "Invalid image reference" >&2
  exit 2
fi
test -f .env || { echo "Missing .env" >&2; exit 1; }
export HOMECORE_IMAGE="$IMAGE"
docker compose --env-file .env -f compose.yaml pull
docker compose --env-file .env -f compose.yaml up -d db
docker compose --env-file .env -f compose.yaml run --rm --no-deps api python manage.py migrate --noinput
docker compose --env-file .env -f compose.yaml run --rm --no-deps api python manage.py collectstatic --noinput
docker compose --env-file .env -f compose.yaml up -d --remove-orphans
docker compose --env-file .env -f compose.yaml ps
