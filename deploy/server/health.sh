#!/usr/bin/env bash
# Is the service alive (every 5 minutes, autoexpert-health.timer) — deploy prompt, stage D.4.
# Checks the proxy (401 = Caddy answers behind Basic Auth), the backend health endpoint inside its
# container, the containers' state and the disk (> 80 % warns). Problems go to
# /srv/autoexpert/logs/health.log and to the system journal (journalctl -t autoexpert).
set -uo pipefail
ENV_FILE=/srv/autoexpert/shared/.env
COMPOSE=(docker compose --env-file "$ENV_FILE" -f /srv/autoexpert/current/deploy/compose.yaml)
LOG=/srv/autoexpert/logs/health.log
problems=()

EDGE_URL=${EDGE_URL:-http://172.17.0.1:8088/}
code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$EDGE_URL" || echo 000)
[ "$code" = "401" ] || [ "$code" = "200" ] || [ "$code" = "302" ] || problems+=("proxy answered $code")
"${COMPOSE[@]}" exec -T backend curl -fsS --max-time 10 http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1 \
  || problems+=("backend health failed")
for service in postgres backend web site caddy; do
  state=$("${COMPOSE[@]}" ps --format '{{.State}}' "$service" 2>/dev/null | head -1)
  [ "$state" = "running" ] || problems+=("$service is ${state:-missing}")
done
used=$(df --output=pcent / | tail -1 | tr -dc '0-9')
[ "${used:-0}" -le 80 ] || problems+=("disk ${used}% full")

if [ ${#problems[@]} -gt 0 ]; then
  message="$(date -u +%FT%TZ) PROBLEM: ${problems[*]}"
  echo "$message" >> "$LOG"
  logger -t autoexpert -p user.warning "$message"
  exit 1
fi
# one line an hour when everything is fine (a heartbeat in the log)
[ "$(date +%M)" -lt 5 ] && echo "$(date -u +%FT%TZ) ok disk ${used}%" >> "$LOG"
exit 0
