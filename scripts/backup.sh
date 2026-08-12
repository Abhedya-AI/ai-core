#!/bin/bash
# ABHEDYA Platform Backup Script
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/abhedya_${TIMESTAMP}"
S3_BUCKET=${S3_BUCKET:-"s3://abhedya-backups"}

mkdir -p "${BACKUP_DIR}"
echo "[$(date)] Starting ABHEDYA backup..."

echo "[$(date)] Backing up PostgreSQL..."
PGPASSWORD=${POSTGRES_PASSWORD:-password} pg_dump   -h ${POSTGRES_HOST:-localhost}   -U ${POSTGRES_USER:-postgres}   -d ${POSTGRES_DB:-abhedya}   -F c -f "${BACKUP_DIR}/postgres_${TIMESTAMP}.dump"

echo "[$(date)] Backing up Neo4j..."
if command -v neo4j-admin &> /dev/null; then
  neo4j-admin database dump neo4j --to-path="${BACKUP_DIR}/neo4j_${TIMESTAMP}.dump" 2>/dev/null ||     echo "[WARNING] Neo4j backup failed — manual backup recommended"
fi

echo "[$(date)] Backing up Redis..."
redis-cli -h ${REDIS_HOST:-localhost} BGSAVE 2>/dev/null && sleep 5
cp /data/dump.rdb "${BACKUP_DIR}/redis_${TIMESTAMP}.rdb" 2>/dev/null ||   echo "[WARNING] Redis RDB copy failed — in-memory data may not be backed up"

tar -czf "${BACKUP_DIR}.tar.gz" -C "$(dirname ${BACKUP_DIR})" "$(basename ${BACKUP_DIR})"
rm -rf "${BACKUP_DIR}"

if command -v aws &> /dev/null && [ -n "${S3_BUCKET}" ]; then
  aws s3 cp "${BACKUP_DIR}.tar.gz" "${S3_BUCKET}/$(basename ${BACKUP_DIR}.tar.gz)"
  echo "[$(date)] Backup uploaded to ${S3_BUCKET}"
fi
echo "[$(date)] Backup completed: ${BACKUP_DIR}.tar.gz"
