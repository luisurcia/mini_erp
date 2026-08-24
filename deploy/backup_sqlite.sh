#!/usr/bin/env bash
# Backup of the Mini ERP SQLite database. See README.md -> Deployment ->
# Backups for the cron setup on the production server.
#
# Uses `sqlite3 <db> ".backup"` (SQLite's online backup API) instead of
# copying the file with cp/rsync: safe to run while the app is writing to
# the database at the same time, without risking a half-written copy.
#
# Manual usage:
#   ./deploy/backup_sqlite.sh

set -euo pipefail

APP_DIR="${KOMBUCHAERP_APP_DIR:-/home/titoeyzy/kombuchaerp}"
DB_PATH="${KOMBUCHAERP_DB_PATH:-$APP_DIR/instance/mini_erp.db}"
BACKUP_DIR="${KOMBUCHAERP_BACKUP_DIR:-/home/titoeyzy/backups/kombuchaerp}"
RETENTION_DAYS="${KOMBUCHAERP_BACKUP_RETENTION_DAYS:-30}"

if [ ! -f "$DB_PATH" ]; then
    echo "Database not found at $DB_PATH" >&2
    exit 1
fi

mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
DEST="$BACKUP_DIR/mini_erp_${TIMESTAMP}.db"

sqlite3 "$DB_PATH" ".backup '$DEST'"
gzip "$DEST"

echo "Backup created: ${DEST}.gz"

# Local retention (default 30 days).
find "$BACKUP_DIR" -name 'mini_erp_*.db.gz' -mtime "+${RETENTION_DAYS}" -delete

# -----------------------------------------------------------------------
# Cron setup (this is NOT configured automatically — see README.md ->
# Deployment -> Backups for the exact crontab line already in place)
# -----------------------------------------------------------------------
#
# Recommended: also sync $BACKUP_DIR periodically to off-server storage
# (rsync to another host, S3, etc.) — out of scope for this script, which
# only handles the daily local backup.
