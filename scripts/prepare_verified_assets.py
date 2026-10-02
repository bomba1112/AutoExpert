"""Licensed candidates through existing asset upload, never approve; resumable cache."""
# ruff: noqa: E501

import asyncio
import html
import json
import sys
from pathlib import Path
from urllib.parse import urlencode, urlparse

from acquire_verified_documents import acquire

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.api.routes.knowledge import upload_asset  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.knowledge_ops import VehicleAsset  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.catalog_buyer import records  # noqa: E402
from app.services.knowledge_import import private_path  # noqa: E402
from sqlalchemy import select  # noqa: E402
from starlette.requests import Request  # noqa: E402


async def main():
    manifest = json.loads((ROOT / "data/manifests/vehicle-image-candidates.json").read_text())
    candidates = manifest["candidates"]
    cache = ROOT / ".localdata/verified-source-documents"
    output = ROOT / "deliverables/VerifiedData/image-review"
    output.mkdir(parents=True, exist_ok=True)
    items = []
    with SessionLocal() as db:
        actor = db.scalar(select(User).where(User.email == "catalog-review@local.invalid"))
        if not actor:
            raise ValueError("EXISTING_LOCAL_REVIEW_ACTOR_REQUIRED")
        published = records(db)
        for c in candidates:
            item = {**c, "status": "PENDING_REVIEW", "human_approved": False}
            items.append(item)
            # Exact public original-file links were read on the attribution pages.
            # Do not retry blocked HTML, change identity, authenticate or bypass a challenge.
            if not c.get("rights_read_at") or not c.get("rights_evidence"):
                item.update(status="RIGHTS_RECHECK_REQUIRED")
                continue
            url = c["original_url"]
            if urlparse(url).hostname != "upload.wikimedia.org":
                item.update(status="IMAGE_HOST_NOT_ALLOWED")
                continue
            result = acquire(
                {
                    "allowed_hosts": ["upload.wikimedia.org"],
                    "documents": [{"url": url, "cost": "FREE", "storage": "OPEN_LICENSE"}],
                }
            )[0]
            if result.get("http_status") != 200:
                item.update(status="DOWNLOAD_BLOCKED", reason=result.get("error", "HTTP_FAILURE"))
                continue
            ids = [
                v.id
                for v, cat in published
                if cat["make"].casefold() == c["make"].casefold()
                and cat["model"].casefold() == c["model"].casefold()
                and cat["model_year"] == c["year"]
                and cat["original_market"] == c["market"]
            ]
            if not ids:
                item.update(status="CATALOG_YEAR_GAP")
                continue
            reference = f"{c['author']} · {c['license']} · {c['license_url']}; local resized WebP; no endorsement"
            metadata = {
                k: c[k] for k in ("make", "model", "market", "generation", "facelift", "body")
            }
            metadata.update(
                variant_ids=ids,
                year_from=c["year"],
                year_to=c["year"],
                source_url=c["page"],
                rights_reference=reference,
                commercial_reuse=True,
                generated=False,
            )
            content = (cache / result["sha256"]).read_bytes()

            async def receive(content=content):
                return {"type": "http.request", "body": content, "more_body": False}

            request = Request(
                {
                    "type": "http",
                    "query_string": urlencode({"metadata": json.dumps(metadata)}).encode(),
                },
                receive,
            )
            stored = await upload_asset(request, db, actor)
            asset = db.get(VehicleAsset, stored["id"])
            # This is a candidate identity claim, not an approved catalogue mutation.
            item.update(
                asset_id=asset.id,
                database_state=asset.state,
                sha256=asset.sha256,
                candidate_variant_ids=ids,
                reason="Generation/body/trim require factory evidence and human review",
            )
            local = output / (asset.sha256 + ".webp")
            local.write_bytes(private_path(asset.renditions["hero"]).read_bytes())
            item["preview_file"] = local.name
    (output / "candidates.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    blocks = []
    for c in items:
        e = html.escape
        picture = (
            f'<img src="{e(c["preview_file"])}" alt="{e(c["make"] + " " + c["model"])}">'
            if c.get("preview_file")
            else ""
        )
        blocks.append(
            f"<article>{picture}<h2>{e(c['make'] + ' ' + c['model'])} · {c['year']} · {e(c['market'])}</h2>"
            f"<b>{e(c['status'])}</b><p>Claim: {e(c['generation'])} / {e(c['body'])} / {e(c['facelift'] or 'pre-facelift')}</p>"
            f'<p>{e(c["author"])} · <a href="{e(c["license_url"])}">{e(c["license"])}</a>; resized WebP, same image licence.</p>'
            f'<p><a href="{e(c["page"])}">Original description / rights</a></p><p>{e(c.get("reason", "Manual review required"))}</p></article>'
        )
    (output / "contact-sheet.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Auto Expert · Image source review index</title>'
        "<style>body{font:16px system-ui;background:#eef3fa;color:#15253d;margin:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px}article{background:white;padding:20px;border-radius:16px}img{width:100%;height:240px;object-fit:contain}a{color:#0059dd}</style>"
        "<h1>Image source review index · Не утверждено / Təsdiqlənməyib</h1><p>DOWNLOAD_BLOCKED means no stored image and no photographic contact sheet for that item. Source caption is a candidate claim. Factory applicability and a real human approval event are still required. No photograph proves damage or VIN history.</p><main>"
        + "".join(blocks)
        + "</main>",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"candidates": len(items), "stored": sum("asset_id" in i for i in items), "approved": 0}
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
