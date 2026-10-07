#!/usr/bin/env bash
# The one change to the Stories project (owner decision 2026-10-06): its Caddy (owner of 80/443)
# forwards autoexpert.77-42-27-222.sslip.io to the Auto Expert edge (172.17.0.1:8088) and gets the
# HTTPS certificate for it. Run as root:
#   bash stories_caddy_link.sh          # add the block (once), validate, reload without downtime
#   bash stories_caddy_link.sh --undo   # put the saved Caddyfile back and reload
# The file is appended / rewritten in place (same inode: the container's bind mount sees it).
set -euo pipefail
CADDYFILE=/opt/stories/deploy/production/Caddyfile
CONTAINER=stories-caddy-1
HOST=autoexpert.77-42-27-222.sslip.io
BACKUP_GLOB="$CADDYFILE.bak-autoexpert-*"
reload() {
  docker exec "$CONTAINER" caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
  docker exec "$CONTAINER" caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
}

if [ "${1:-}" = "--undo" ]; then
  backup=$(ls -1t $BACKUP_GLOB | head -1)
  cat "$backup" > "$CADDYFILE"
  reload
  echo "restored $backup"
  exit 0
fi

if grep -q "^$HOST " "$CADDYFILE"; then
  echo "already linked"
else
  cp -p "$CADDYFILE" "$CADDYFILE.bak-autoexpert-$(date -u +%Y%m%dT%H%M%SZ)"
  cat >> "$CADDYFILE" <<EOF

# Auto Expert closed staging (added $(date -u +%F)); Basic Auth and noindex are in its own Caddy.
$HOST {
    encode zstd gzip
    header Strict-Transport-Security "max-age=31536000"
    reverse_proxy 172.17.0.1:8088
}
EOF
  if ! reload; then
    echo "validation failed: restoring the saved Caddyfile" >&2
    cat "$(ls -1t $BACKUP_GLOB | head -1)" > "$CADDYFILE"
    reload
    exit 1
  fi
fi
sleep 5
echo "stories:    $(curl -s -o /dev/null -w '%{http_code}' --max-time 20 https://stories.77-42-27-222.sslip.io/health)"
echo "autoexpert: $(curl -s -o /dev/null -w '%{http_code}' --max-time 60 https://$HOST/) (401 = Basic Auth asks for the password)"
