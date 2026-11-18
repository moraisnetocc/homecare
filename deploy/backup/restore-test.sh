#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
[[ $# -eq 2 && "$1" =~ ^(staging|production)$ ]] || { echo "Usage: $0 staging|production /path/to/archive.dump" >&2; exit 2; }
environment="$1"
archive="$(realpath -- "$2")"
[[ -f "$archive" && -s "$archive" ]] || exit 2
cd "/opt/homecore/$environment"
# A separate disposable database, never the configured application database.
testdb="homecore_restore_test_$(date -u +%Y%m%d%H%M%S)_$$"
created=0
cleanup() {
  if [[ "$created" == 1 ]]; then
    docker compose exec -T db sh -ec 'exec dropdb -U "$POSTGRES_USER" -- "$1"' sh "$testdb" || { echo "Cleanup failed: $testdb" >&2; return 1; }
  fi
}
trap cleanup EXIT
docker compose exec -T db sh -ec '
  test "$1" != "$POSTGRES_DB"
  exec createdb -U "$POSTGRES_USER" -T template0 -- "$1"
' sh "$testdb"
created=1
docker compose exec -T db sh -ec 'exec pg_restore -U "$POSTGRES_USER" -d "$1" --exit-on-error --no-owner --no-privileges' sh "$testdb" < "$archive"
docker compose exec -T db sh -ec 'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$1" -c "SELECT count(*) FROM django_migrations;"' sh "$testdb"
echo "Restore validation passed: $testdb"
