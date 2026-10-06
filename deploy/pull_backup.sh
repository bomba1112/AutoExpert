#!/usr/bin/env bash
# Download the latest server backup to the laptop and prove it restores (deploy prompt, stage
# D.2–D.3): until a Storage Box / S3 is configured this is the copy outside the server.
#   deploy/pull_backup.sh            # download + restore into a scratch database + compare rows
#   deploy/pull_backup.sh --no-restore
set -euo pipefail
SERVER=${SERVER:-deploy@77.42.27.222}
PG_BIN=${PG_BIN:-"/c/Program Files/PostgreSQL/16/bin"}
LOCAL=${LOCAL:-"-h localhost -p 5433 -U autoexpert"}
DEST=/c/AutoExpertData/server_backups
mkdir -p "$DEST"
latest=$(ssh "$SERVER" 'ls -1t /srv/autoexpert/backups/autoexpert-*.dump | head -1')
base=$(basename "$latest" .dump)
scp "$SERVER:/srv/autoexpert/backups/$base.dump" "$SERVER:/srv/autoexpert/backups/$base.counts" \
    "$SERVER:/srv/autoexpert/backups/$base.sha256" "$DEST/"
(cd "$DEST" && sha256sum -c --ignore-missing "$base.sha256")
ls -1t "$DEST"/autoexpert-*.dump | tail -n +15 | xargs -r rm -f   # keep 14 on the laptop
[ "${1:-}" = "--no-restore" ] && exit 0

COUNTS_SQL="SELECT table_name, (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from public.%I', table_name), false, true, '')))[1]::text FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY 1"
"$PG_BIN/psql" $LOCAL -d postgres -qc "DROP DATABASE IF EXISTS autoexpert_restore_check" -c "CREATE DATABASE autoexpert_restore_check"
"$PG_BIN/pg_restore" $LOCAL -d autoexpert_restore_check --no-owner --no-privileges "$DEST/$base.dump"
"$PG_BIN/psql" $LOCAL -d autoexpert_restore_check -At -F ' ' -c "$COUNTS_SQL" > "$DEST/$base.restored.counts"
if diff -u "$DEST/$base.counts" "$DEST/$base.restored.counts"; then
  echo "restore OK: $base — rows per table equal ($(wc -l < "$DEST/$base.counts") tables)"
else
  echo "RESTORE CHECK FAILED for $base" >&2; exit 1
fi
