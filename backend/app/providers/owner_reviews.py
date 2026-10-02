"""Owner evidence from public complaint pages; government mirrors are excluded.

The catalogue contains reviewed source locations, never facts or expected counts.
Only compact structured observations/fingerprints are persisted, not full narratives.
"""

import hashlib
import re
from contextlib import suppress
from datetime import UTC, datetime
from typing import Protocol

from bs4 import BeautifulSoup

from app.providers.public_evidence_http import PublicAccessError, PublicEvidenceHTTP
from app.schemas.common import SourceSnapshot
from app.schemas.research_evidence import (
    EvidenceProviderMetadata,
    OwnerMaterial,
    OwnerReviewResult,
    ProviderAttempt,
    ResearchState,
)
from app.services.knowledge_coverage import stable_id

CATALOGUE = {
    ("ford", "fusion", 2019): [
        "https://www.carcomplaints.com/Ford/Fusion/2019/engine/coolant_intrusion_cracked_short_block.shtml",
    ],
    ("toyota", "camry", 2019): [
        "https://www.carcomplaints.com/Toyota/Camry/2019/transmission/total_failure.shtml",
    ],
    ("hyundai", "sonata", 2019): [
        "https://www.carcomplaints.com/Hyundai/Sonata/2019/engine/high_oil_consumption.shtml",
    ],
}


class OwnerReviewProvider(Protocol):
    metadata: EvidenceProviderMetadata

    def lookup(self, target: dict) -> OwnerReviewResult: ...


def fingerprint(text: str) -> tuple[str, list[str]]:
    words = re.sub(r"\W+", " ", text.casefold()).split()
    digest = hashlib.sha256(" ".join(words).encode()).hexdigest()
    shingles = sorted({stable_id(words[i : i + 5]) for i in range(max(0, len(words) - 4))})
    return digest, shingles


def classify_topics(text: str) -> list[str]:
    vocabulary = {
        "ENGINE": r"engine|cylinder|misfire|short block|oil consumption",
        "TRANSMISSION": r"transmission|gearbox|gear shift|torque converter",
        "COOLING": r"coolant|antifreeze|overheat|radiator",
        "ELECTRICAL": r"battery|electrical|wiring|alternator",
        "SUSPENSION": r"suspension|strut|shock absorber",
        "STEERING": r"steering",
        "BRAKES": r"brake|braking",
        "BODY": r"rust|corrosion|bodywork|paint",
        "INTERIOR": r"seat|interior|cabin",
        "INFOTAINMENT": r"infotainment|touchscreen|bluetooth|stereo",
        "FUEL_ECONOMY": r"fuel economy|gas mileage|mpg",
        "MAINTENANCE": r"oil changes?|servic\w*|maintenance",
    }
    return sorted(
        k for k, pattern in vocabulary.items() if re.search(r"\b(?:" + pattern + r")\b", text, re.I)
    ) or ["RELIABILITY_GENERAL"]


def issue_key(text: str) -> str | None:
    # Shared issue vocabulary: no manufacturer/model condition in the aggregator.
    rules = {
        "coolant_intrusion": (
            r"coolant.{0,100}(?:cylinder|intrusion|short block)|"
            r"(?:intrusion|cylinder).{0,100}coolant"
        ),
        "transmission_failure": (
            r"transmission.{0,80}(?:fail|stopped|replacement)|"
            r"(?:new|replace).{0,20}transmission"
        ),
        "oil_consumption": r"oil consumption|consum.{0,15}oil|add.{0,10}oil",
    }
    return next((k for k, pattern in rules.items() if re.search(pattern, text, re.I | re.S)), None)


def parse_complaints(html: str, url: str, target: dict, retrieved_at: datetime):
    soup = BeautifulSoup(html, "html.parser")
    if "About These NHTSA Complaints" in soup.get_text(" ", strip=True):
        return [], [{"url": url, "reason": "OFFICIAL_COMPLAINT_MIRROR"}]
    source_id = "owner-source-" + stable_id(url)
    results, excluded = [], []
    for node in soup.select(".complaint"):
        number = node.select_one(".pnum")
        header, body = node.select_one(".cheader"), node.select_one(".comments")
        if not number or not header or not body:
            continue
        author_node = node.select_one(".userinfo strong")
        author = author_node.get_text(strip=True) if author_node else None
        location_node = node.select_one(".userinfo span")
        location = location_node.get_text(strip=True) if location_node else ""
        for unwanted in body.select("script, .ad, .userinfo, blockquote"):
            unwanted.decompose()
        text = body.get_text(" ", strip=True)
        vehicle_title = header.select_one(".ptitle").get_text(" ", strip=True)
        # Engine data must describe this author's vehicle, not a quoted bulletin.
        liters = re.search(r"\b(\d\.\d)\s*(?:L|liter|litre)\b", vehicle_title, re.I)
        cylinders = re.search(
            r"\b(?:[IV-]+\s*([3468])|([3468])\s*(?:cyl|cylinder))", vehicle_title, re.I
        )
        scope = {k: target[k] for k in ("make", "model", "year")}
        if re.search(r"\b(?:US|USA|United States)$", location):
            scope["market"] = "USA"
        scope["displacement"] = float(liters[1]) if liters else None
        if cylinders:
            scope["cylinders"] = int(cylinders[1] or cylinders[2])
        scope["powertrain"] = (
            "PHEV"
            if re.search(r"plug.in|phev|energi", vehicle_title, re.I)
            else "HYBRID"
            if re.search(r"hybrid", vehicle_title, re.I)
            else None
        )
        if "Automatic transmission" in header.get_text():
            scope["transmission"] = "AUTOMATIC"
        if "Manual transmission" in header.get_text():
            scope["transmission"] = "MANUAL"
        url_identity = url + "#" + number.get("name", node.get("id", ""))
        date_node = header.select_one(".pdate")
        observed = None
        if date_node:
            with suppress(ValueError):
                observed = datetime.strptime(date_node.get_text(" ", strip=True), "%b %d %Y").date()
        described_year = re.search(
            r"\b(?:my|our|daughter'?s|son'?s|wife'?s)\s+(20\d{2})\s+(?:"
            + re.escape(target["make"])
            + r"\s+)?"
            + re.escape(target["model"]),
            text,
            re.I,
        )
        if described_year:
            scope["year"] = int(described_year[1])
        if len(text) < 20:
            excluded.append({"url": url_identity, "reason": "NO_ORIGINAL_OWNER_NARRATIVE"})
            continue
        miles = re.search(r"([\d,]+) miles", header.get_text(" ", strip=True))
        content_hash, shingles = fingerprint(text)
        material_id = "owner-" + stable_id(url_identity)
        results.append(
            OwnerMaterial(
                material_id=material_id,
                evidence_class="REPAIR_EXPERIENCE",
                canonical_url=url_identity,
                publisher_group="AUTOBEEF",
                owner_id=("AUTOBEEF:" + stable_id(author.casefold()) if author else None),
                observed_at=observed,
                retrieved_at=retrieved_at,
                applicability=scope,
                mileage=int(miles[1].replace(",", "")) if miles else None,
                mileage_unit="mi" if miles else None,
                topics=classify_topics(text),
                sentiment="NEGATIVE",
                issue_key=issue_key(text),
                content_hash=content_hash,
                text_fingerprint=shingles,
                source_ids=[source_id],
                evidence_ids=[material_id],
                provenance={
                    "url": url_identity,
                    "locator": f".complaint#{node.get('id')}",
                    "page_sha256": hashlib.sha256(html.encode()).hexdigest(),
                    "vehicle_title": vehicle_title,
                    "method": "public-owner-narrative-v1",
                    "selection_bias": "PROBLEM_SPECIFIC_PAGES",
                    "narrative_stored": False,
                },
            )
        )
    return results, excluded


class CarComplaintsOwnerProvider:
    metadata = EvidenceProviderMetadata(
        id="carcomplaints_owner",
        name="CarComplaints — owner submissions",
        capabilities=["REPAIR_EXPERIENCE", "OWNER_TOPICS"],
        priority=10,
        commercial_usage_status="FACTUAL_SUMMARY_ONLY",
        policy_url="https://www.carcomplaints.com/termsofuse.shtml",
    )

    def __init__(self, http=None, catalogue=None):
        self.http = http or PublicEvidenceHTTP()
        self.catalogue = catalogue if catalogue is not None else CATALOGUE

    def lookup(self, target: dict) -> OwnerReviewResult:
        now = datetime.now(UTC)
        urls = self.catalogue.get(
            (target["make"].casefold(), target["model"].casefold(), target["year"]), []
        )
        rows, sources, excluded, failures = [], [], [], []
        for url in urls:
            try:
                r = self.http.get(url, allowed_hosts={"www.carcomplaints.com"})
                materials, rejects = parse_complaints(r.text, url, target, now)
                excluded.extend(rejects)
                if not materials and not rejects:
                    failures.append({"url": url, "reason": "PARSER_NO_MATERIALS"})
                    continue
                rows.extend(materials)
                sources.append(
                    SourceSnapshot(
                        id="owner-source-" + stable_id(url),
                        title="CarComplaints owner submissions",
                        publisher="CarComplaints / Autobeef",
                        url=url,
                        source_type="REPAIR_EXPERIENCE",
                        source_tier="C",
                        retrieved_at=now.isoformat(),
                        confidence="MEDIUM",
                        data_origin="REAL",
                        is_demo=False,
                    )
                )
            except PublicAccessError as error:
                failures.append(
                    {
                        "url": error.url,
                        "state": error.state,
                        "reason": error.reason,
                        "http_status": error.http_status,
                    }
                )
        state = ResearchState.PARTIAL if rows else ResearchState.PROVIDER_UNAVAILABLE
        return OwnerReviewResult(
            attempt=ProviderAttempt(
                provider=self.metadata,
                state=state,
                checked_at=now,
                query=target,
                scope="Public owner submission pages; problem-selected sample, not a survey",
                reason="LIMITED_PAGE_CATALOGUE" if rows else "NO_ACCESSIBLE_REVIEWED_MATERIALS",
                query_completed=bool(urls) and not failures,
                provenance={
                    "pages": urls,
                    "requests": self.http.audit,
                    "failures": failures,
                    "policy_reviewed_at": "2026-09-18",
                    "full_text_republished": False,
                },
            ),
            sources=sources,
            materials=rows,
            excluded=excluded,
        )
