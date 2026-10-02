"""No real manual text is stored in these synthetic parser/network fixtures."""

from __future__ import annotations

import httpx
import pytest

from scripts.lemon_access import LemonSelectiveHTTP, fetch_explicit_page, validate_lemon_url
from scripts.lemon_selective import discover_child_links, is_target_section, parse_page

URL = (
    "https://lemon-manuals.la/Hyundai/2018/Elantra%20SE/Repair%20and%20Diagnosis/"
    "Quick%20Lookups/Fluids/"
)
HTML = b"""<!doctype html><html><head><title>Illustrative fluids</title></head><body>
<h1>Quick Lookups</h1><h2>Fluids</h2>
<p>This manual is identical to the manual for the following model variants,
except for possibly the Fluids and Tire Fitment pages:</p>
<ul><li>Elantra SEL</li><li>Elantra Limited</li></ul>
<table><caption>Fluid capacities - example</caption>
<tr><th>Fluid Type</th><th>Application</th><th>Operation</th>
<th>Standard</th><th>Metric</th><th>Fluid Spec</th><th>Note</th></tr>
<tr><td rowspan="2">Engine Oil</td><td>2.0L</td><td>Drain and Refill, with Filter</td>
<td>4.2 US QT</td><td>4.0 L</td><td>SAE 5W-20 API SN</td><td>Recommended</td></tr>
<tr><td>1.6L</td><td>Dry Fill</td><td>5.0 US QT</td><td>4.7 L</td>
<td>SAE 5W-30 API SN</td><td>* at temperature below 0C</td></tr>
<tr><td>Automatic Transmission Fluid</td><td>6AT only</td><td></td>
<td>7.5 US QT</td><td>7.1 L</td><td>ATF-A OR ATF-B</td><td></td></tr>
<tr><td>Manual Transmission Fluid</td><td>6MT only</td><td></td>
<td></td><td></td><td>MTF-C</td><td></td></tr>
</table><p>* Below 0C is a conditional alternative, not a default.</p>
</body></html>"""


def test_fluid_rows_preserve_original_units_spans_conditions_and_exceptions():
    result = parse_page(HTML, source_url=URL, retrieved_at="2026-09-24T00:00:00Z")
    assert result["publication"] == "REVIEW_REQUIRED"
    assert result["parser_version"] == "lemon-selective-html-v1"
    assert len(result["tables"]) == 1
    assert len(result["candidates"]) == 4
    assert result["manual_relationship"]["variants_named"] == [
        "Elantra SEL",
        "Elantra Limited",
    ]
    assert result["manual_relationship"]["exception_sections"] == ["fluids", "tire fitment"]
    table = result["tables"][0]
    assert table["section_path"] == ["Quick Lookups", "Fluids"]
    assert table["grid"][2][0]["origin_row"] == 1  # Actual rowspan, not inferred fill.
    assert table["notes"] == ["* Below 0C is a conditional alternative, not a default."]
    candidates = result["candidates"]
    assert candidates[0]["raw_fields"]["standard"] == "4.2 US QT"
    assert candidates[0]["raw_fields"]["operation"] == "Drain and Refill, with Filter"
    assert candidates[0]["normalized"]["standard_capacity"] == {
        "value": "4.2",
        "unit": "US_QUART",
        "original": "4.2 US QT",
    }
    assert candidates[0]["normalized"]["capacity_type"] == "SERVICE_WITH_FILTER"
    assert candidates[1]["raw_fields"]["operation"] == "Dry Fill"
    assert candidates[1]["normalized"]["capacity_type"] == "DRY_FILL"
    assert candidates[2]["raw_fields"]["specification"] == "ATF-A OR ATF-B"
    assert candidates[3]["raw_fields"]["standard"] == ""
    assert candidates[3]["normalized"]["standard_capacity"] is None
    assert all(item["applicability"] == "UNRESOLVED" for item in candidates)


def test_multilevel_header_colspan_and_blank_cells_are_not_filled():
    html = b"""<html><body><h1>Specifications</h1><table>
    <tr><th rowspan="2">Component</th><th colspan="2">Capacity</th></tr>
    <tr><th>US</th><th>Metric</th></tr>
    <tr><td>Engine coolant</td><td></td><td>7.2 L</td></tr>
    </table></body></html>"""
    table = parse_page(html, source_url=URL, retrieved_at="2026-09-24T00:00:00Z")["tables"][0]
    assert table["grid"][0][1]["text"] == "Capacity"
    assert table["grid"][0][2]["origin_col"] == 1
    assert table["grid"][1][0]["origin_row"] == 0
    assert table["grid"][2][1]["text"] == ""


def test_link_discovery_stays_within_observed_child_tree_and_skips_bulk_paths():
    html = b"""<html><body>
    <a href="Repair%20and%20Diagnosis/Quick%20Lookups/Fluids/">Fluids</a>
    <a href="Repair%20and%20Diagnosis/Quick%20Lookups/Fluids/">Duplicate</a>
    <a href="Repair%20and%20Diagnosis/Labor%20Times/">Labor</a>
    <a href="/bundle/manual.zip">Bundle</a>
    <a href="https://internal.invalid/private">Other host</a>
    <a href="https://lemon-manuals.la:invalid/Hyundai/">Bad port</a>
    <a href="../Other/">Sibling</a>
    </body></html>"""
    base = "https://lemon-manuals.la/Hyundai/2018/Elantra%20SE/"
    links = discover_child_links(html, page_url=base)
    assert len(links) == 1
    assert links[0]["source_label"] == "Fluids"
    assert is_target_section(links[0]["url"])


@pytest.mark.parametrize(
    "bad_url",
    [
        "http://lemon-manuals.la/Hyundai/",
        "https://lemon-manuals.la@internal.invalid/Hyundai/",
        "https://lemon-manuals.la/bundle/manual.zip",
        "https://lemon-manuals.la/Hyundai/%2e%2e/private/",
        "https://lemon-manuals.la/Hyundai/?download=1",
        "https://lemon-manuals.la:444/Hyundai/",
        "https://lemon-manuals.la:invalid/Hyundai/",
    ],
)
def test_url_guard_rejects_nonselective_or_cross_domain_targets(bad_url):
    with pytest.raises(ValueError, match="LEMON_URL_NOT_ALLOWED"):
        validate_lemon_url(bad_url)


def test_parser_rejects_source_urls_with_unreviewed_query():
    with pytest.raises(ValueError, match="LEMON_SOURCE_URL_REQUIRED"):
        parse_page(HTML, source_url=URL + "?token=private", retrieved_at="2026-09-24T00:00:00Z")


def test_existing_http_gate_robots_cache_and_idempotent_private_fetch(tmp_path):
    requests = []

    def respond(request):
        requests.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(200, headers={"content-type": "text/html"}, content=HTML)

    http = LemonSelectiveHTTP(
        explicit_urls={URL},
        transport=httpx.MockTransport(respond),
        min_interval_seconds=0,
    )
    try:
        first, first_meta = fetch_explicit_page(http, URL, cache_root=tmp_path)
        second, second_meta = fetch_explicit_page(http, URL, cache_root=tmp_path)
    finally:
        http.close()
    assert first == second == HTML
    assert first_meta["network_requests"] == 2
    assert not first_meta["cache_hit"]
    assert second_meta["network_requests"] == 0
    assert second_meta["cache_hit"]
    assert len(requests) == 2


@pytest.mark.parametrize("status", [403, 429])
def test_access_restriction_stops_without_retries_or_page_cache(tmp_path, status):
    requests = []

    def respond(request):
        requests.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(status, text="unavailable")

    http = LemonSelectiveHTTP(
        explicit_urls={URL},
        transport=httpx.MockTransport(respond),
        min_interval_seconds=0,
    )
    try:
        content, receipt = fetch_explicit_page(http, URL, cache_root=tmp_path)
    finally:
        http.close()
    assert content == b""
    assert receipt["http_status"] == status
    assert receipt["status"] == f"HTTP_{status}"
    assert len(requests) == 2
    assert not list(tmp_path.glob("*.html"))


def test_robots_disallow_never_fetches_target(tmp_path):
    requests = []

    def respond(request):
        requests.append(str(request.url))
        return httpx.Response(200, text="User-agent: *\nDisallow: /Hyundai/\n")

    http = LemonSelectiveHTTP(
        explicit_urls={URL},
        transport=httpx.MockTransport(respond),
        min_interval_seconds=0,
    )
    try:
        content, receipt = fetch_explicit_page(http, URL, cache_root=tmp_path)
    finally:
        http.close()
    assert content == b""
    assert receipt["status"] == "ROBOTS_DISALLOW"
    assert requests == ["https://lemon-manuals.la/robots.txt"]


def test_unreviewed_redirect_does_not_fetch_second_path(tmp_path):
    requests = []

    def respond(request):
        requests.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        return httpx.Response(302, headers={"location": "/bundle/all.zip"})

    http = LemonSelectiveHTTP(
        explicit_urls={URL},
        transport=httpx.MockTransport(respond),
        min_interval_seconds=0,
    )
    try:
        with pytest.raises(ValueError, match="LEMON_URL_NOT_ALLOWED"):
            fetch_explicit_page(http, URL, cache_root=tmp_path)
    finally:
        http.close()
    assert len(requests) == 2
