#!/usr/bin/env bash
# Build a release on the laptop and put it on the server (deploy prompt, stage C). Heavy builds
# (Flutter web, the public site, vPIC) are made on the laptop; the server gets files and builds
# only the small backend image.
#   deploy/release.sh            # build + upload + switch + start
#   deploy/release.sh --dry-run  # build the archive only
# Needs: committed code (git archive HEAD), C:/AutoExpertData/public_site_staging (generator),
# apps/client/build/web (flutter build web) — optional, SSH key access as deploy@SERVER.
set -euo pipefail
SERVER=${SERVER:-deploy@77.42.27.222}
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SITE_DIR=${SITE_DIR:-/c/AutoExpertData/public_site_staging}
FLUTTER_WEB="$ROOT/apps/client/build/web"
STAMP=$(date -u +%Y%m%d%H%M%S)-$(git -C "$ROOT" rev-parse --short HEAD)
BUILD=/c/AutoExpertData/deploy_build/$STAMP
mkdir -p "$BUILD/web/preview" "$BUILD/site"

echo "== code (committed HEAD)"
git -C "$ROOT" archive HEAD backend data/manifests scripts/garage_recall_job.py scripts/manage_users.py \
  scripts/knowledge_admin.py pyproject.toml deploy | tar -x -C "$BUILD"
rm -rf "$BUILD/backend/tests"

echo "== web application"
(cd "$ROOT/apps/web_preview" && tar --exclude=tests --exclude=node_modules -cf - .) | tar -x -C "$BUILD/web/preview"
if [ -d "$FLUTTER_WEB" ]; then mkdir -p "$BUILD/web/app" && cp -r "$FLUTTER_WEB"/. "$BUILD/web/app/"; fi
printf 'User-agent: *\nDisallow: /\n' > "$BUILD/web/robots.txt"

echo "== public site"
[ -d "$SITE_DIR/cars" ] || { echo "no generated site in $SITE_DIR"; exit 1; }
cp -r "$SITE_DIR/cars" "$BUILD/site/"
printf 'User-agent: *\nDisallow: /\n' > "$BUILD/site/robots.txt"   # staging: noindex

echo "$STAMP" > "$BUILD/RELEASE"
ARCHIVE=/c/AutoExpertData/deploy_build/autoexpert-$STAMP.tar.gz
tar -C "$BUILD" -czf "$ARCHIVE" .
echo "archive: $ARCHIVE ($(du -h "$ARCHIVE" | cut -f1))"
[ "${1:-}" = "--dry-run" ] && exit 0

echo "== upload and switch"
scp "$ARCHIVE" "$SERVER:/srv/autoexpert/releases/"
ssh "$SERVER" "set -euo pipefail
  cd /srv/autoexpert/releases
  mkdir -p $STAMP && tar -xzf autoexpert-$STAMP.tar.gz -C $STAMP && rm autoexpert-$STAMP.tar.gz
  ln -sfn /srv/autoexpert/releases/$STAMP /srv/autoexpert/current
  cd /srv/autoexpert/current/deploy
  RELEASE=$STAMP docker compose --env-file /srv/autoexpert/shared/.env up -d --build --remove-orphans
  # bind mounts through the current symlink are resolved when a container starts: the static
  # services and the proxy must start again to serve the new release's files and Caddyfile
  RELEASE=$STAMP docker compose --env-file /srv/autoexpert/shared/.env up -d --force-recreate --no-deps web site caddy
  ls -1dt /srv/autoexpert/releases/*/ | tail -n +6 | xargs -r rm -rf   # keep 5 releases
  docker image prune -f >/dev/null"
echo "released $STAMP"
