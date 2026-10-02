"""Bounded public listing import. HTML is data, never executable instructions."""

from __future__ import annotations

import hashlib
import http.client
import ipaddress
import json
import re
import socket
import ssl
import time
from datetime import UTC, datetime
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup

AGENT = "AutoExpert/0.7"
LIMIT = 2_000_000


class ListingUnavailable(ValueError):
    pass


def public_address(url: str) -> tuple[str, str, int, str, str]:
    p = urlsplit(url)
    if p.scheme not in {"https", "http"} or not p.hostname or p.username or p.password:
        raise ListingUnavailable("UNSAFE_URL")
    host = p.hostname.encode("idna").decode("ascii")
    port = p.port or (443 if p.scheme == "https" else 80)
    if port not in {80, 443} or host.casefold() in {"localhost", "metadata.google.internal"}:
        raise ListingUnavailable("UNSAFE_URL")
    addresses = list(
        dict.fromkeys(r[4][0] for r in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM))
    )
    if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):
        raise ListingUnavailable("UNSAFE_URL")
    return host, addresses[0], port, p.scheme, urlunsplit(("", "", p.path or "/", p.query, ""))


def fetch_public(
    url: str, *, deadline: float | None = None, redirect_policy=None
) -> tuple[int, str, bytes, str]:
    """Pin each validated DNS address to the socket; TLS still validates original host."""
    deadline = deadline or time.monotonic() + 25
    for _ in range(4):
        host, address, port, scheme, path = public_address(url)
        timeout = min(8, deadline - time.monotonic())
        if timeout <= 0:
            raise ListingUnavailable("TIMEOUT")
        conn = http.client.HTTPConnection(host, port, timeout=timeout)
        sock = socket.create_connection((address, port), timeout=timeout)
        if scheme == "https":
            try:
                sock = ssl.create_default_context().wrap_socket(sock, server_hostname=host)
            except Exception:
                sock.close()
                raise
        conn.sock = sock
        try:
            conn.request(
                "GET",
                path,
                headers={
                    "Host": host,
                    "User-Agent": AGENT,
                    "Accept": "text/html,text/plain,application/xhtml+xml",
                    "Accept-Encoding": "identity",
                },
            )
            response = conn.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                url = urljoin(url, response.getheader("Location") or "")
                if redirect_policy:
                    redirect_policy(url)
                continue
            kind = response.getheader("Content-Type", "").split(";", 1)[0].lower()
            if kind not in {"text/html", "application/xhtml+xml", "text/plain"}:
                raise ListingUnavailable("UNSUPPORTED_CONTENT")
            if int(response.getheader("Content-Length", "0")) > LIMIT:
                raise ListingUnavailable("PAGE_TOO_LARGE")
            chunks, size = [], 0
            while True:
                if time.monotonic() >= deadline:
                    raise ListingUnavailable("TIMEOUT")
                chunk = response.read(min(65536, LIMIT + 1 - size))
                if not chunk:
                    break
                size += len(chunk)
                if size > LIMIT:
                    raise ListingUnavailable("PAGE_TOO_LARGE")
                chunks.append(chunk)
            return response.status, kind, b"".join(chunks), url
        finally:
            conn.close()
    raise ListingUnavailable("TOO_MANY_REDIRECTS")


def _number(text: object) -> float | None:
    m = re.search(r"\d[\d\s\u00a0]*(?:[.,]\d+)?", str(text or ""))
    return float(re.sub(r"\s", "", m[0]).replace(",", ".")) if m else None


def parse_listing(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    meta = {x.get("property") or x.get("name"): x.get("content", "") for x in soup.find_all("meta")}
    out = {"title": meta.get("og:title"), "description": meta.get("og:description"), "photos": []}
    rows = {}
    if urlsplit(url).hostname in {"turbo.az", "ru.turbo.az", "en.turbo.az", "www.turbo.az"}:
        for item in soup.select(".product-properties__i"):
            k, v = (
                item.select_one(".product-properties__i-name"),
                item.select_one(".product-properties__i-value"),
            )
            if k and v:
                rows[k.get_text(" ", strip=True)] = v.get_text(" ", strip=True)
        mapping = {
            "make": ["Marka", "Марка"],
            "model": ["Model", "Модель"],
            "year": ["Buraxılış ili", "Год выпуска"],
            "engine": ["Mühərrik", "Двигатель"],
            "transmission": ["Sürətlər qutusu", "Коробка передач"],
            "drivetrain": ["Ötürücü", "Привод"],
            "color": ["Rəng", "Цвет"],
            "mileage_km": ["Yürüş", "Пробег"],
            "city": ["Şəhər", "Город"],
            "body": ["Ban növü", "Тип кузова"],
            "market_claim": ["Hansı bazar üçün yığılıb", "Рынок"],
            "condition_claim": ["Vəziyyəti", "Состояние"],
            "trim": ["Komplektasiya", "Комплектация"],
        }
        for key, names in mapping.items():
            out[key] = next((rows[n] for n in names if n in rows), None)
        price = soup.select_one(".product-price__i, .product-price")
        price_text = (
            price.get_text(" ", strip=True)
            if price
            else str(out.get("title") or "").split("qiyməti")[-1]
        )
        price_text = price_text.replace("₼", "AZN").replace("$", "USD").replace("€", "EUR")
        out.update(
            price=_number(price_text),
            currency=next((c for c in ("AZN", "USD", "EUR") if c in price_text), None),
            adapter="turbo.az",
        )
        for img in soup.select(".product-photos img, .product-photos__slider img"):
            value = img.get("data-src") or img.get("src")
            if value:
                out["photos"].append(value)
    # Shared Schema.org path for public sites that expose vehicle metadata.
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            doc = json.loads(script.string or script.get_text())
        except (ValueError, TypeError):
            continue
        stack = doc if isinstance(doc, list) else [doc]
        while stack:
            item = stack.pop()
            if not isinstance(item, dict):
                continue
            stack.extend(item.get("@graph", []))
            if not set(
                [item.get("@type")] if isinstance(item.get("@type"), str) else item.get("@type", [])
            ) & {"Car", "Vehicle", "Product"}:
                continue
            for key, field in {
                "make": "brand",
                "model": "model",
                "year": "vehicleModelDate",
                "vin": "vehicleIdentificationNumber",
                "color": "color",
                "transmission": "vehicleTransmission",
                "fuel": "fuelType",
                "description": "description",
                "trim": "vehicleConfiguration",
            }.items():
                val = item.get(field)
                if isinstance(val, dict):
                    val = val.get("name") or val.get("value")
                if isinstance(val, (str, int, float)) and val:
                    out[key] = val
            offer = item.get("offers") or {}
            if isinstance(offer, dict):
                out.update(
                    price=_number(offer.get("price")) or out.get("price"),
                    currency=offer.get("priceCurrency") or out.get("currency"),
                )
            miles = item.get("mileageFromOdometer")
            if isinstance(miles, dict) and miles.get("unitCode") in {"KMT", "km"}:
                out["mileage_km"] = _number(miles.get("value"))
            photos = item.get("image") or []
            out["photos"].extend(
                [photos] if isinstance(photos, str) else photos if isinstance(photos, list) else []
            )
            out.setdefault("adapter", "schema.org")
    if meta.get("og:image"):
        out["photos"].insert(0, meta["og:image"])
    photos, photo_keys = [], set()
    for photo in out["photos"]:
        if not isinstance(photo, str):
            continue
        photo = urljoin(url, photo)
        p = urlsplit(photo)
        identity = (
            re.sub(r"/uploads/(?:full|thumbnail|f\d+x\d+)/", "/uploads/", photo)
            if p.hostname == "turbo.azstatic.com"
            else photo
        )
        if identity in photo_keys:
            continue
        if p.scheme == "https" and p.hostname and not p.username and photo not in photos:
            try:
                public_address(photo)
            except (ValueError, OSError):
                continue
            photos.append(photo)
            photo_keys.add(identity)
    out["photos"] = [
        {
            "url": p,
            "type": "LISTING",
            "caption": "Photo from the listing",
            "source_url": url,
            "pdf_permission": "NOT_ESTABLISHED",
        }
        for p in photos[:30]
    ]
    for key in ("year", "mileage_km"):
        val = _number(out.get(key))
        out[key] = int(val) if val is not None else None
    vin = str(out.get("vin") or "").upper()
    out["vin"] = vin if re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", vin) else None
    out["description"] = str(out.get("description") or "")[:12000]
    out["claim_type"] = "SELLER_CLAIM"
    return out


def import_listing(url: str) -> dict:
    result = {
        "source_url": url,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "status": "UNAVAILABLE",
        "reason": None,
        "http_status": None,
        "data": {},
    }
    try:
        public_address(url)
        p = urlsplit(url)
        robots_url = urlunsplit((p.scheme, p.netloc, "/robots.txt", "", ""))
        status, _, body, _ = fetch_public(robots_url)
        parser = None
        if status == 200:
            parser = RobotFileParser()
            parser.parse(body.decode("utf-8", errors="replace").splitlines())
            if not parser.can_fetch(AGENT, url):
                raise ListingUnavailable("SOURCE_RESTRICTED")
        elif status not in {404, 410}:
            raise ListingUnavailable("SOURCE_RESTRICTED")

        def allowed_redirect(target):
            if urlsplit(target).netloc != p.netloc:
                raise ListingUnavailable("CROSS_SITE_REDIRECT")
            if parser and not parser.can_fetch(AGENT, target):
                raise ListingUnavailable("SOURCE_RESTRICTED")

        status, kind, body, final_url = fetch_public(url, redirect_policy=allowed_redirect)
        result["http_status"] = status
        if status != 200:
            raise ListingUnavailable(
                "SOURCE_RESTRICTED" if status in {401, 403, 429} else "PAGE_UNAVAILABLE"
            )
        if kind not in {"text/html", "application/xhtml+xml"}:
            raise ListingUnavailable("UNSUPPORTED_CONTENT")
        if urlsplit(final_url).netloc != p.netloc:
            raise ListingUnavailable("CROSS_SITE_REDIRECT")
        data = parse_listing(body.decode("utf-8", errors="replace"), final_url)
        result.update(data=data, page_sha256=hashlib.sha256(body).hexdigest())
        if not all(data.get(k) for k in ("make", "model", "year")):
            raise ListingUnavailable("VEHICLE_METADATA_NOT_FOUND")
        result.update(status="IMPORTED", reason=None)
    except (ValueError, OSError, http.client.HTTPException) as error:
        result["reason"] = (
            str(error) if isinstance(error, ListingUnavailable) else "NETWORK_UNAVAILABLE"
        )
    return result
