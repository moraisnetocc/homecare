#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
[[ $# == 1 && "$1" =~ ^(staging|production)$ ]] || exit 2
environment="$1"
dir="/var/backups/homecore/$environment"
config="/etc/homecore/backup/$environment"
remote="r2:homecore-backups-$environment/postgres"
exec 9>"/run/lock/homecore-$environment-backup.lock"
flock -w 120 9
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
rc() { rclone --config "$config/rclone.conf" "$@"; }
export LC_ALL=C
shopt -s nullglob
rc lsf --files-only "$remote" > "$work/remote"
uploaded=0
for file in "$dir"/postgres-*.dump; do
  name="${file##*/}"
  [[ -f "$file" && ! -L "$file" && "$name" =~ ^postgres-[0-9]{8}T[0-9]{6}Z\.dump$ ]] || continue
  uploaded=1
  if grep -Fxq "$name.age" "$work/remote"; then
    continue
  fi
  age -R "$config/recipient.txt" -o "$work/$name.age" "$file"
  rc copyto --immutable "$work/$name.age" "$remote/$name.age"
  rc cat "$remote/$name.age" | cmp - "$work/$name.age"
  rm -- "$work/$name.age"
  echo "Uploaded and verified: $name.age"
done
[[ "$uploaded" == 1 ]] || { echo "No local backups" >&2; exit 1; }
rc lsf --files-only "$remote" > "$work/remote"
grep -E '^postgres-[0-9]{8}T[0-9]{6}Z\.dump\.age$' "$work/remote" | sort -u > "$work/sorted"
mapfile -t archives < "$work/sorted"
for ((i=0; i<${#archives[@]}-6; i++)); do
  rc deletefile "$remote/${archives[i]}"
done
echo "Offsite backup synchronization completed"
