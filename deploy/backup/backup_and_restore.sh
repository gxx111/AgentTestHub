#!/usr/bin/env bash
# E20-05: AgentTestHub 数据库热备份与灾难恢复自动化脚本
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/agent_test_hub}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATABASE_URL="${DATABASE_URL:-sqlite:///agent_test_hub_data.db}"

mkdir -p "$BACKUP_DIR"

backup() {
    echo "[*] Starting AgentTestHub database backup to ${BACKUP_DIR}..."
    if [[ "$DATABASE_URL" == postgres* ]]; then
        BACKUP_FILE="${BACKUP_DIR}/ath_pg_backup_${TIMESTAMP}.sql.gz"
        pg_dump "$DATABASE_URL" | gzip > "$BACKUP_FILE"
        echo "[+] PostgreSQL backup completed: ${BACKUP_FILE}"
    else
        DB_PATH="${DATABASE_URL#sqlite:///}"
        BACKUP_FILE="${BACKUP_DIR}/ath_sqlite_backup_${TIMESTAMP}.db"
        sqlite3 "$DB_PATH" ".backup '${BACKUP_FILE}'"
        echo "[+] SQLite backup completed: ${BACKUP_FILE}"
    fi
}

restore() {
    RESTORE_FILE="$1"
    echo "[*] Restoring AgentTestHub database from ${RESTORE_FILE}..."
    if [[ "$RESTORE_FILE" == *.sql.gz ]]; then
        gunzip -c "$RESTORE_FILE" | psql "$DATABASE_URL"
        echo "[+] PostgreSQL restore completed."
    else
        DB_PATH="${DATABASE_URL#sqlite:///}"
        sqlite3 "$DB_PATH" ".restore '${RESTORE_FILE}'"
        echo "[+] SQLite restore completed."
    fi
}

case "${1:-backup}" in
    backup)
        backup
        ;;
    restore)
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 restore <backup_file>"
            exit 1
        fi
        restore "$2"
        ;;
    *)
        echo "Usage: $0 {backup|restore <file>}"
        exit 1
        ;;
esac
