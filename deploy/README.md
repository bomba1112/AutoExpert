# Auto Expert local delivery / deployment preparation

**READY_NOT_DEPLOYED. Hetzner deployment is explicitly deferred by the owner.**
No host, DNS, firewall, remote service, paid product or other project was changed.

Current data checkpoint: [US base catalogue batch07](../docs/CHECKPOINT_US_BASE_CATALOG.md).
The archive contains source/manifests, not the published live DB or private document cache.
Existing-local-DB replay is idempotent; fresh deployment requires document acquisition,
RawDocument/revision ID remapping and review. Existing APK was not rebuilt by this batch.
Batch07 is published over batch06 and the retained batch05 completion correction; see
[BATCH07_VALIDATION](../docs/BATCH07_VALIDATION.md). Batch05 has a retained superseded preparation. Use the final
scopes described in [BATCH05_VALIDATION](../docs/BATCH05_VALIDATION.md); do not replay the
failed parent Toyota job as a final verified state. Historical portable exports are not
a current verified database restore and are not updated by this catalogue batch.

This package extends the existing FastAPI application and working WebView client.
Local runtime: SQLite. Prepared target: separate Compose project `autoexpert`, PostgreSQL 16,
API, import worker, Caddy and private knowledge storage. Docker/PostgreSQL execution must be
validated on the target before any live claim. The current computer has no Docker CLI.
Dependencies are exported from uv.lock to deploy/requirements.lock and installed with pip
--require-hashes. API and worker share the queue-enabled setting in the prepared configuration.

## Operator preparation (future authorized stage)

1. Inventory the existing host, reverse proxy, ports, backups, disk and memory. Do not replace
   existing projects, change tariffs, open public ports or buy volumes without authorization.
2. Copy source package into an isolated release directory owned by a dedicated service account.
3. Copy `.env.example` to `.env`, permission 0600. Supply a random secret (at least 32 chars),
   database password and URL-encoded database URL. Keep provider keys in the secret store only.
4. Run `docker compose --env-file .env config --quiet` (never print expanded config with secrets),
   `docker compose --env-file .env build`, then start on loopback 8088 for staging validation.
5. Register the operator in the app, then explicitly grant that existing account via
   `docker compose exec api python scripts/knowledge_admin.py grant-admin --email OPERATOR_EMAIL`.
   Registration does not confer admin rights, even for the configured admin email.
6. Check `/api/v1/health`, `/api/v1/meta/client-config`, anonymous catalogue, private report
   ownership, source rights, payment simulation, import pause/restart, logs and backup/restore.
7. For an approved domain, integrate with the existing host reverse proxy. If Caddy owns TLS,
   configure the actual domain and only then its approved 80/443 mappings. The default package
   intentionally binds **127.0.0.1:8088**. There is no guessed domain or public exposure.

## Data and rights gates

The local EPA catalogue is a research edition. Commercial reuse is **not** approved by this
implementation. Production queries exclude sources without documented commercial rights;
production imports fail closed. Do not toggle the registry flag without the underlying licence.
The data volume includes raw source files, revisions and images. Private originals are not served.
Image approval requires rights and matching generation/body/market/year applicability. Generated
images require an explicit editor review and are never published automatically.

Concept prices 7 / +10 / 17 AZN are inactive configuration. Existing prices are preserved.
Payments remain mock; no paid provider, subscription or live charging was enabled.

## Backup / restore

`backup.sh /private/existing/directory` pauses only this project's API/worker, creates a consistent
`pg_dump -Fc`, archives the knowledge volume, records hashes, and restarts the services.
The database contains private reports and account data: restrict permissions and encrypt any
off-host backup using the operator's existing vault. Do not attach backups to public deliverables.
Secrets are excluded; back them up in the vault separately. Retention: start with 7 daily and
4 weekly copies after measuring actual size, then define the policy with the operator.

Restore rehearsal: use a **new** isolated Compose project/database/volume, verify SHA256SUMS,
restore with `pg_restore --exit-on-error --no-owner --no-acl`, restore the knowledge tree with
path-safe extraction, run Alembic head and compare counts, raw/assets checksums, health and
ownership checks. Never test restore over the live database. Promote only after verification.
The local executable rehearsal is `python scripts/local_backup_restore.py`; its evidence is
`deliverables/MasterLocal/backup-restore.json`. PostgreSQL rehearsal is a separate target check.

Hetzner server backups/snapshots do not replace backups of attached volumes. Include database,
raw archive, assets, manifests, publication metadata and private configuration in the recovery plan.

## Sizing, updates and rollback

Measure database/raw/rendition growth, peak RSS, importer queue lag and restore time before choosing
capacity. A guessed 40–60 GB is not evidence. Worker uses bounded batches and persistent cursors.
Failed acquisition requires explicit retry; source pause stops updates without erasing published
facts. Version publication is atomic and editor-locked variants cannot be overwritten. Rollback is
an authenticated audited API action; saved reports retain their original factual snapshots.
Database downgrade removes operational metadata: use a verified backup for a full release rollback.

Official references checked 2026-09-19:
- [Compose readiness](https://docs.docker.com/compose/how-tos/startup-order/)
- [PostgreSQL pg_dump](https://www.postgresql.org/docs/16/app-pgdump.html)
- [Caddy automatic HTTPS](https://caddyserver.com/docs/automatic-https)
- [Hetzner snapshots and backups](https://docs.hetzner.com/cloud/servers/backups-snapshots/overview/)
