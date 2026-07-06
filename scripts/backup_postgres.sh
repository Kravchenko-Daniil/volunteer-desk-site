#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?Set DATABASE_URL, for example postgresql://user:password@host/database}"

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
MEDIA_DIR="${MEDIA_DIR:-./media}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
database_backup="$BACKUP_DIR/postgresql-$timestamp.dump"

umask 077
mkdir -p "$BACKUP_DIR"
pg_dump --format=custom --file="$database_backup.tmp" "$DATABASE_URL"
mv "$database_backup.tmp" "$database_backup"
pg_restore --list "$database_backup" >/dev/null

if [[ -d "$MEDIA_DIR" ]]; then
  tar -czf "$BACKUP_DIR/media-$timestamp.tar.gz" "$MEDIA_DIR"
fi

find "$BACKUP_DIR" -type f -mtime "+$RETENTION_DAYS" -delete
echo "Backup verified: $database_backup"
