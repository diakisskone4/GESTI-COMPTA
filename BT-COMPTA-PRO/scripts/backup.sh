#!/bin/sh
# Sauvegarde PostgreSQL compressée, avec rotation. Utilisé par le service « backup » de docker-compose.
set -e
STAMP=$(date +%Y%m%d-%H%M%S)
FILE="/backups/bt_compta_pro-$STAMP.sql.gz"
pg_dump --no-owner --format=plain | gzip > "$FILE"
echo "$(date) sauvegarde créée : $FILE"
find /backups -name 'bt_compta_pro-*.sql.gz' -mtime +"${BACKUP_KEEP_DAYS:-14}" -delete
