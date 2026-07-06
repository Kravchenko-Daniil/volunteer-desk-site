#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?Set the target DATABASE_URL}"
: "${CONFIRM_RESTORE:?Set CONFIRM_RESTORE=YES after checking the target database}"

if [[ "$CONFIRM_RESTORE" != "YES" ]]; then
  echo "Restore cancelled: CONFIRM_RESTORE must be YES" >&2
  exit 1
fi

backup_file="${1:?Usage: restore_postgres.sh path/to/postgresql.dump}"
pg_restore --list "$backup_file" >/dev/null
pg_restore --clean --if-exists --no-owner --dbname="$DATABASE_URL" "$backup_file"
echo "Restore completed: $backup_file"
