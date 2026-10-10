#!/usr/bin/env bash
# Nightly backup: database dump + n8n data folder (holds the encryption key).
# Add to crontab:  15 3 * * * /root/n8n-server/backup.sh
set -euo pipefail
cd "$(dirname "$0")"
stamp=$(date +%F)
mkdir -p backups
docker compose exec -T postgres pg_dump -U n8n n8n | gzip > "backups/db-$stamp.sql.gz"
docker run --rm -v n8n-server_n8n_data:/data -v "$PWD/backups":/out alpine \
  tar czf "/out/n8n-data-$stamp.tgz" -C /data .
find backups -type f -mtime +14 -delete
echo "backup done: $stamp"
