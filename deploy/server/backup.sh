#!/usr/bin/env bash
# Daily backup of the Auto Expert database (deploy prompt, stage D.1–D.2); run by
# autoexpert-backup.timer. Consistent pg_dump (custom format, compressed) without stopping the
# service; the club photos as a tar.gz; the last 7 of each kept; then a copy outside the server
# when BACKUP_OFFSITE is set in /srv/autoexpert/shared/.env (storagebox | s3).
set -euo pipefail
ENV_FILE=/srv/autoexpert/shared/.env
DIR=/srv/autoexpert/backups
COMPOSE=(docker compose --env-file "$ENV_FILE" -f /srv/autoexpert/current/deploy/compose.yaml)
KEEP=7
COUNTS_SQL="SELECT table_name, (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from public.%I', table_name), false, true, '')))[1]::text FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY 1"
env_value() { sed -n "s/^$1=//p" "$ENV_FILE" | tail -1 | sed -e "s/^'//" -e "s/'\$//"; }
POSTGRES_USER=$(env_value POSTGRES_USER); POSTGRES_DB=$(env_value POSTGRES_DB)
BACKUP_OFFSITE=$(env_value BACKUP_OFFSITE)
STORAGEBOX_USER=$(env_value STORAGEBOX_USER); STORAGEBOX_HOST=$(env_value STORAGEBOX_HOST); STORAGEBOX_PATH=$(env_value STORAGEBOX_PATH)
S3_ENDPOINT=$(env_value S3_ENDPOINT); S3_BUCKET=$(env_value S3_BUCKET); S3_ACCESS_KEY=$(env_value S3_ACCESS_KEY); S3_SECRET_KEY=$(env_value S3_SECRET_KEY)
umask 077
stamp=$(date -u +%Y%m%dT%H%M%SZ)
dump="autoexpert-$stamp.dump"

"${COMPOSE[@]}" exec -T postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --compress=6 > "$DIR/$dump.part"
"${COMPOSE[@]}" exec -T postgres pg_restore --list < "$DIR/$dump.part" > /dev/null   # the archive is readable
mv "$DIR/$dump.part" "$DIR/$dump"
# rows per table at dump time: deploy/pull_backup.sh compares a restore with these
"${COMPOSE[@]}" exec -T postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -F ' ' -c "$COUNTS_SQL" > "$DIR/autoexpert-$stamp.counts"
tar -C /srv/autoexpert -czf "$DIR/media-$stamp.tar.gz" media
(cd "$DIR" && sha256sum "$dump" "media-$stamp.tar.gz" "autoexpert-$stamp.counts" > "autoexpert-$stamp.sha256")

# keep the last $KEEP of each kind
for pattern in 'autoexpert-*.dump' 'media-*.tar.gz' 'autoexpert-*.sha256' 'autoexpert-*.counts'; do
  ls -1t "$DIR"/$pattern 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -f
done

case "${BACKUP_OFFSITE:-none}" in
  storagebox)   # Hetzner Storage Box over SSH (port 23); key /srv/autoexpert/shared/storagebox_key
    rsync -a -e "ssh -p 23 -i /srv/autoexpert/shared/storagebox_key -o StrictHostKeyChecking=accept-new" \
      "$DIR/$dump" "$DIR/media-$stamp.tar.gz" "$DIR/autoexpert-$stamp.sha256" "$DIR/autoexpert-$stamp.counts" \
      "${STORAGEBOX_USER}@${STORAGEBOX_HOST}:${STORAGEBOX_PATH:-autoexpert-backups}/"
    ;;
  s3)           # any S3-compatible storage, through the rclone image (nothing installed on the host)
    docker run --rm -v "$DIR":/backups:ro \
      -e RCLONE_CONFIG_OFFSITE_TYPE=s3 -e RCLONE_CONFIG_OFFSITE_PROVIDER=Other \
      -e RCLONE_CONFIG_OFFSITE_ENDPOINT="$S3_ENDPOINT" \
      -e RCLONE_CONFIG_OFFSITE_ACCESS_KEY_ID="$S3_ACCESS_KEY" -e RCLONE_CONFIG_OFFSITE_SECRET_ACCESS_KEY="$S3_SECRET_KEY" \
      rclone/rclone:1 copy /backups "offsite:${S3_BUCKET}/autoexpert" \
      --include "$dump" --include "media-$stamp.tar.gz" --include "autoexpert-$stamp.sha256" --include "autoexpert-$stamp.counts"
    ;;
  *) echo "offsite copy: not configured (BACKUP_OFFSITE=none) — download with deploy/pull_backup.sh" ;;
esac
echo "$(date -u +%FT%TZ) backup ok $dump $(du -h "$DIR/$dump" | cut -f1)" >> /srv/autoexpert/logs/backup.log
