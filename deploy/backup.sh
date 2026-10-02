#!/bin/sh
# Run from deploy/ against this isolated Compose project only.
set -eu
umask 077
destination=${1:?Provide an existing private backup directory}
[ -d "$destination" ] || { echo "Backup directory must exist" >&2; exit 1; }
stamp=$(date -u +%Y%m%dT%H%M%SZ)
target="$destination/autoexpert-$stamp"
mkdir "$target"
docker compose --env-file .env stop api worker
trap 'docker compose --env-file .env start api worker >/dev/null' EXIT HUP INT TERM
docker compose --env-file .env exec -T db pg_dump -U autoexpert -d autoexpert --format=custom > "$target/database.dump"
docker compose --env-file .env run --rm --no-deps -T api python -c 'import sys,tarfile; t=tarfile.open(fileobj=sys.stdout.buffer,mode="w|gz"); t.add("/data",arcname="knowledge"); t.close()' > "$target/knowledge.tar.gz"
cp compose.yaml Caddyfile "$target/"
# Secrets are deliberately excluded; back them up separately using the operator's vault.
(cd "$target" && sha256sum database.dump knowledge.tar.gz compose.yaml Caddyfile > SHA256SUMS)
echo "Private backup created. Verify a restore before rotating older backups."
