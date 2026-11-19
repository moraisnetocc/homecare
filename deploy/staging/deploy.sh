#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
exec 9>/run/lock/homecore-staging-deploy.lock
flock -n 9 || { echo "Another deployment is running" >&2; exit 1; }
[[ $# -eq 1 ]] || exit 2
cd /opt/homecore/staging
valid_image() { [[ "$1" =~ ^ghcr\.io/moraisnetocc/homecare-cloud@sha256:[a-f0-9]{64}$ ]]; }
IMAGE="$1"
valid_image "$IMAGE" || exit 2
test -f .env
PREVIOUS="$(sed -n 's/^HOMECORE_IMAGE=//p' .env)"
DOMAIN="$(sed -n 's/^HOMECORE_DOMAIN=//p' .env)"
[[ "$DOMAIN" =~ ^[a-zA-Z0-9.-]+$ ]] || exit 2
valid_image "$PREVIOUS" || { echo "No valid previous image; bootstrap manually" >&2; exit 1; }
export HOMECORE_IMAGE="$PREVIOUS"
dc() { docker compose --env-file .env -f compose.yaml "$@"; }
health() {
  local expected="$1" attempts="${2:-30}" cid response
  for ((attempt=1; attempt<=attempts; attempt++)); do
    if cid="$(dc ps -q api)" &&
       [[ -n "$cid" ]] &&
       [[ "$(docker inspect --format '{{.Config.Image}} {{.State.Running}}' "$cid")" == "$expected true" ]] &&
       response="$(curl --fail --silent --show-error --max-time 10 --resolve "$DOMAIN:443:127.0.0.1" "https://$DOMAIN/api/health/")" &&
       printf '%s' "$response" | python3 -c 'import json,sys
try:
    d=json.load(sys.stdin)
    sys.exit(0 if isinstance(d,dict) and d.get("status")=="ok" and d.get("service")=="homecore-cloud" else 1)
except (ValueError, TypeError):
    sys.exit(1)'; then
      return 0
    fi
    echo "Waiting for HTTPS health ($attempt/$attempts)"
    sleep 5
  done
  return 1
}
db_check() {
  dc exec -T api python manage.py shell -c 'from django.db import connection; connection.ensure_connection()'
}
health "$PREVIOUS" 3 && db_check || { echo "Previous version is not healthy; refusing deployment" >&2; exit 1; }
docker image inspect "$PREVIOUS" >/dev/null
export HOMECORE_IMAGE="$IMAGE"
# Pull only application image; infrastructure updates are separate.
dc pull api
tmp=""
rollback() {
  local status="$1"
  trap - ERR
  set +e
  [[ -z "$tmp" ]] || rm -f -- "$tmp"
  echo "Deployment failed ($status); restoring $PREVIOUS" >&2
  export HOMECORE_IMAGE="$PREVIOUS"
  if dc run --rm --no-deps api python manage.py collectstatic --noinput &&
     dc up -d --no-deps --force-recreate api &&
     health "$PREVIOUS" && db_check; then
    echo "ROLLBACK_SUCCEEDED: $PREVIOUS" >&2
  else
    echo "ROLLBACK_FAILED: manual intervention required; inspect migrations and containers" >&2
  fi
  exit 1
}
trap 'rollback "$?"' ERR
dc run --rm --no-deps api python manage.py migrate --noinput
dc run --rm --no-deps api python manage.py collectstatic --noinput
dc up -d --no-deps --force-recreate api
health "$IMAGE"
db_check
tmp="$(mktemp .env.XXXXXX)"
sed "s|^HOMECORE_IMAGE=.*|HOMECORE_IMAGE=$IMAGE|" .env > "$tmp"
mv -f "$tmp" .env
trap - ERR
echo "Deployment validated: $IMAGE"
