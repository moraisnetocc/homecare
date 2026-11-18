#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
[[ $# -eq 1 && "$1" =~ ^(staging|production)$ ]] || { echo "Usage: $0 staging|production" >&2; exit 2; }
ENVIRONMENT="$1"
cd "/opt/homecore/$ENVIRONMENT"
DIR="/var/backups/homecore/$ENVIRONMENT"
install -d -m 700 -o root -g root "$DIR"
exec 9>"/run/lock/homecore-$ENVIRONMENT-backup.lock"
flock -n 9 || { echo "Backup already running" >&2; exit 1; }
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="$DIR/postgres-$stamp.dump"
tmp="$(mktemp "$DIR/.partial.XXXXXX")"
trap 'rm -f "$tmp"' EXIT
docker compose exec -T db sh -ec 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc --no-owner --no-privileges' > "$tmp"
test -s "$tmp"
docker compose exec -T db pg_restore --list < "$tmp" > /dev/null
mv -T -- "$tmp" "$target"
# Retention only after a validated archive has been written.
find "$DIR" -maxdepth 1 -type f -name 'postgres-*.dump' -mmin +10080 -delete
echo "Backup completed: $target"
