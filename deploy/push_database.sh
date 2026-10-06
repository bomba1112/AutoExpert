#!/usr/bin/env bash
# Copy the database from the laptop's PostgreSQL (already transferred from SQLite and checked by
# scripts/sqlite_to_postgres.py) to the server (deploy prompt, stage C.3): pg_dump -> upload ->
# pg_restore while the backend is stopped -> rows per table compared on both sides.
#   deploy/push_database.sh
set -euo pipefail
SERVER=${SERVER:-deploy@77.42.27.222}
LOCAL_URL=${LOCAL_URL:-postgresql://autoexpert@localhost:5433/autoexpert}
PG_BIN=${PG_BIN:-"/c/Program Files/PostgreSQL/16/bin"}
DUMP=/c/AutoExpertData/deploy_build/autoexpert-db-$(date -u +%Y%m%d%H%M%S).dump
COUNTS_SQL="SELECT table_name, (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from public.%I', table_name), false, true, '')))[1]::text FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY 1"
mkdir -p "$(dirname "$DUMP")"

"$PG_BIN/pg_dump" --format=custom --compress=6 --no-owner --no-privileges --file "$DUMP" "$LOCAL_URL"
"$PG_BIN/psql" -At -F ' ' -c "$COUNTS_SQL" "$LOCAL_URL" > "$DUMP.counts"
echo "dump: $DUMP ($(du -h "$DUMP" | cut -f1))"
scp "$DUMP" "$SERVER:/srv/autoexpert/backups/initial.dump"
ssh "$SERVER" "set -euo pipefail
  cd /srv/autoexpert/current/deploy
  C='docker compose --env-file /srv/autoexpert/shared/.env'
  U=\$(sed -n \"s/^POSTGRES_USER=//p\" /srv/autoexpert/shared/.env | tr -d \"'\")
  D=\$(sed -n \"s/^POSTGRES_DB=//p\" /srv/autoexpert/shared/.env | tr -d \"'\")
  \$C stop backend caddy
  \$C exec -T postgres pg_restore -U \$U -d \$D --clean --if-exists --no-owner --no-privileges < /srv/autoexpert/backups/initial.dump
  \$C exec -T postgres psql -U \$U -d \$D -c 'ANALYZE'
  \$C exec -T postgres psql -U \$U -d \$D -At -F ' ' -c \"$COUNTS_SQL\" > /srv/autoexpert/backups/initial.counts
  \$C up -d backend caddy"
scp "$SERVER:/srv/autoexpert/backups/initial.counts" "$DUMP.server.counts"
if diff -u "$DUMP.counts" "$DUMP.server.counts"; then
  echo "rows per table: equal on the laptop and the server ($(wc -l < "$DUMP.counts") tables)"
else
  echo "ROW COUNTS DIFFER" >&2; exit 1
fi
