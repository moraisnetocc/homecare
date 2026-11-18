#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
exec 9>/run/lock/homecore-staging-deploy.lock
flock -n 9 || { echo "Another deployment is running" >&2; exit 1; }
[[ $# -eq 1 ]] || exit 2
cd /opt/homecore/staging
IMAGE="${1:?Usage: deploy.sh ghcr.io/moraisnetocc/homecare-cloud@sha256:<64hex>}"
if [[ ! "$IMAGE" =~ ^ghcr\.io/moraisnetocc/homecare-cloud@sha256:[a-f0-9]{64}$ ]]; then
  echo "Invalid image reference" >&2
  exit 2
fi
test -f .env || { echo "Missing .env" >&2; exit 1; }
export HOMECORE_IMAGE="$IMAGE"
docker compose --env-file .env -f compose.yaml pull
docker compose --env-file .env -f compose.yaml up -d --wait --wait-timeout 120 db
docker compose --env-file .env -f compose.yaml run --rm --no-deps api python manage.py migrate --noinput
docker compose --env-file .env -f compose.yaml run --rm --no-deps api python manage.py collectstatic --noinput
docker compose --env-file .env -f compose.yaml up -d --remove-orphans
docker compose --env-file .env -f compose.yaml ps
DOMAIN="$(sed -n 's/^HOMECORE_DOMAIN=//p' .env)"
[[ "$DOMAIN" =~ ^[a-zA-Z0-9.-]+$ ]] || exit 2
for attempt in {1..30}; do
  if curl --fail --silent --show-error --max-time 10 "https://$DOMAIN/api/health/" | python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get("status")=="ok" and d.get("service")=="homecore-cloud" else 1)'; then
    tmp="$(mktemp .env.XXXXXX)"
    trap 'rm -f "$tmp"' EXIT
    sed "s|^HOMECORE_IMAGE=.*|HOMECORE_IMAGE=$IMAGE|" .env > "$tmp"
    mv -f "$tmp" .env
    echo "Deployment validated: $IMAGE"
    exit 0
  fi
  sleep 5
done
echo "Health check failed; deployment may be running. Inspect logs before retrying." >&2
exit 1
