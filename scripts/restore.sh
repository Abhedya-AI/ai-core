#!/bin/bash
# ABHEDYA Platform Restore Script
set -euo pipefail

BACKUP_FILE=${1:-""}
if [ -z "${BACKUP_FILE}" ]; then
  echo "Usage: $0 <backup_file.tar.gz>"
  exit 1
fi

echo "[$(date)] Starting restore from: ${BACKUP_FILE}"
TEMP_DIR=$(mktemp -d)
trap "rm -rf ${TEMP_DIR}" EXIT
tar -xzf "${BACKUP_FILE}" -C "${TEMP_DIR}"
BACKUP_CONTENT=$(ls "${TEMP_DIR}")

PG_DUMP=$(find "${TEMP_DIR}/${BACKUP_CONTENT}" -name "postgres_*.dump" 2>/dev/null | head -1)
if [ -n "${PG_DUMP}" ]; then
  echo "[$(date)] Restoring PostgreSQL from: ${PG_DUMP}"
  PGPASSWORD=${POSTGRES_PASSWORD:-password} pg_restore     -h ${POSTGRES_HOST:-localhost}     -U ${POSTGRES_USER:-postgres}     -d ${POSTGRES_DB:-abhedya}     --clean --if-exists -F c "${PG_DUMP}"
  echo "[$(date)] PostgreSQL restored."
fi

REDIS_RDB=$(find "${TEMP_DIR}/${BACKUP_CONTENT}" -name "redis_*.rdb" 2>/dev/null | head -1)
if [ -n "${REDIS_RDB}" ]; then
  echo "[$(date)] Restoring Redis from: ${REDIS_RDB}"
  redis-cli -h ${REDIS_HOST:-localhost} SHUTDOWN NOSAVE 2>/dev/null || true
  cp "${REDIS_RDB}" /data/dump.rdb 2>/dev/null || echo "[WARNING] Redis restore failed"
  echo "[$(date)] Redis RDB placed. Restart Redis to load."
fi

echo "[$(date)] Restore completed. Verify data integrity before enabling traffic."
