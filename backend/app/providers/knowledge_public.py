# ruff: noqa: E501
"""Free, documented EPA APIs and explicitly reviewed public document locations.

No search scraping, login, CAPTCHA, paid service, or access-control workarounds.
"""

from __future__ import annotations

import io
import re
import time
from datetime import UTC, datetime
from urllib.parse import urlencode, urlsplit
from urllib.robotparser import RobotFileParser

from pypdf import PdfReader

from app.models.enums import EvidenceStatus
from app.providers.official_nhtsa import OfficialProviderUnavailable, OfficialVehicleProvider
from app.schemas.research import ProviderResult, VehicleResearchRequest

EPA = "https://www.fueleconomy.gov/ws/rest"


def menu(payload: dict) -> list[dict]:
    value = payload.get("menuItem", [])
    return [value] if isinstance(value, dict) else value


class ContextProvider(OfficialVehicleProvider):
    def fetch_context(self, request: VehicleResearchRequest, context: dict) -> ProviderResult:
        started = time.perf_counter()
        try:
            records, raw, count = self.retrieve(request, context)
            return ProviderResult(
                provider_id=self.id,
                capability=self.capability,
                status=EvidenceStatus.CONFIRMED if records else EvidenceStatus.INSUFFICIENT_DATA,
                records=records,
                raw_payload=raw,
                source_url=self.source_url(request),
                retrieved_at=datetime.now(UTC),
                api_requests=count,
                duration_ms=round((time.perf_counter() - started) * 1000),
                http_status=200,
            )
        except (OfficialProviderUnavailable, ValueError, KeyError, TypeError) as error:
            return ProviderResult(
                provider_id=self.id,
                capability=self.capability,
                status=EvidenceStatus.INSUFFICIENT_DATA,
                error=str(error),
                source_url=self.source_url(request),
                retrieved_at=datetime.now(UTC),
                api_requests=getattr(error, "api_requests", 0),
                duration_ms=round((time.perf_counter() - started) * 1000),
            )

    def _fetch(self, request, url):  # noqa: ANN001, ANN202
        return self.retrieve(request, {})


class EPAConfigurationProvider(ContextProvider):
    id = "epa_vehicle_configuration"
    capability = "fuel_economy"

    def source_url(self, request: VehicleResearchRequest) -> str:
        return f"{EPA}/vehicle/menu/model?" + urlencode(
            {"year": request.year, "make": request.make}
        )

    def retrieve(
        self, request: VehicleResearchRequest, context: dict
    ) -> tuple[list[dict], dict, int]:
        payload, calls = self.http.get_json(self.source_url(request))
        identity = context.get("identity", {})
        target_model = str(request.model).casefold()
        names = [
            row["value"]
            for row in menu(payload)
            if str(row["value"]).casefold() == target_model
            or str(row["value"]).casefold().startswith(target_model + " ")
        ]
        # A bounded shortlist; no unbounded scraping or entire-database downloads.
        if len(names) > 12:
            raise OfficialProviderUnavailable(
                "EPA model shortlist is ambiguous; refine configuration", api_requests=calls
            )
        raw, vehicles = {"menus": [], "vehicles": []}, []
        for name in names:
            url = f"{EPA}/vehicle/menu/options?" + urlencode(
                {"year": request.year, "make": request.make, "model": name}
            )
            options, count = self.http.get_json(url)
            calls += count
            raw["menus"].append({"url": url, "response": options})
            for item in menu(options):
                description = item.get("text", "")
                liters = re.search(r"(\d+(?:\.\d+)?)\s*L\b", description)
                if (
                    identity.get("displacement_l")
                    and liters
                    and abs(float(liters[1]) - float(identity["displacement_l"])) > 0.06
                ):
                    continue
                if len(vehicles) >= 20:
                    raise OfficialProviderUnavailable(
                        "EPA configuration budget exceeded", api_requests=calls
                    )
                vehicle_url = f"{EPA}/vehicle/{item['value']}"
                row, count = self.http.get_json(vehicle_url)
                calls += count
                raw["vehicles"].append({"url": vehicle_url, "response": row})
                if str(row.get("make", "")).casefold() != str(request.make).casefold() or str(
                    row.get("year")
                ) != str(request.year):
                    continue
                if str(row.get("baseModel") or row.get("model", "")).casefold() != target_model:
                    continue
                if not _matches_identity(row, identity):
                    continue
                vehicles.append({**row, "record_url": vehicle_url})
        return vehicles, raw, calls


def _matches_identity(row: dict, identity: dict) -> bool:
    from app.services.vehicle_identity import dimensions_equal, epa_powertrain, powertrain_type

    kind = powertrain_type(identity)
    if kind != "UNKNOWN" and epa_powertrain(row) != kind:
        return False
    if identity.get("drive_type") and not dimensions_equal(
        "drivetrain", identity["drive_type"], row.get("drive")
    ):
        return False
    # EPA publishes a separate 'Blue' efficiency configuration; it cannot stand
    # in for a Limited/SEL VIN. No other trim is inferred from the base model.
    if (
        str(row.get("model", "")).endswith(" Hybrid Blue")
        and identity.get("trim")
        and str(identity["trim"]).casefold() != "blue"
    ):
        return False
    if (
        str(identity.get("trim") or "").casefold() == "blue"
        and row.get("atvType") == "Hybrid"
        and not str(row.get("model", "")).endswith(" Hybrid Blue")
    ):
        return False
    for key, field in (("displacement_l", "displ"), ("engine_cylinders", "cylinders")):
        if identity.get(key) and (
            not row.get(field) or abs(float(identity[key]) - float(row[field])) > 0.06
        ):
            return False
    drive = str(identity.get("drive_type") or "").casefold()
    for needle, epa in (
        ("fwd", "front-wheel"),
        ("front-wheel", "front-wheel"),
        ("awd", "all-wheel"),
        ("rwd", "rear-wheel"),
    ):
        if needle in drive and epa not in str(row.get("drive", "")).casefold():
            return False
    fuel = str(identity.get("fuel_type_primary") or "").casefold()
    # Unknown hybrid status cannot be guessed from gasoline alone; EPA alternatives
    # remain alternatives until displacement/powertrain evidence removes ambiguity.
    return not (fuel and fuel not in str(row.get("fuelType1", "")).casefold())


class EPAOwnerLogProvider(ContextProvider):
    id = "epa_my_mpg"
    capability = "owner_experience"

    def source_url(self, request: VehicleResearchRequest) -> str:
        return f"{EPA}/ympg/shared/vehicles?" + urlencode(
            {"make": request.make, "model": request.model}
        )

    def retrieve(
        self, request: VehicleResearchRequest, context: dict
    ) -> tuple[list[dict], dict, int]:
        selected = context.get("epa_vehicle")
        if not selected:
            return [], {"unavailable_reason": "EXACT_EPA_CONFIGURATION_UNRESOLVED"}, 0
        if selected.get("mpgData") != "Y":
            return (
                [],
                {"vehicle_id": selected["id"], "unavailable_reason": "NO_SHARED_OWNER_LOGS"},
                0,
            )
        url = f"{EPA}/ympg/shared/ympgDriverVehicle/{selected['id']}"
        payload, calls = self.http.get_json(url)
        rows = payload.get("yourMpgDriverVehicle") or []
        if isinstance(rows, dict):
            rows = [rows]
        return (
            [{**row, "record_url": url, "evidence_class": "PUBLIC_OWNER_LOG"} for row in rows],
            {"url": url, "response": payload},
            calls,
        )


# Location/layout metadata only. Automotive facts must be extracted anew from the
# live document and retain the document hash, page, region and extracted span.
DOCUMENTS = [
    {
        "make": "Ford",
        "model": "Fusion",
        "year": 2019,
        "market": "USA",
        "url": "https://www.ford.com/content/dam/brand_ford/en_us/brand/resources/general/pdf/guides/19_Fusion_Energi_SpecLite.pdf",
        "publisher": "Ford Motor Company",
        "page": 2,
        "regions": [
            {"name": "all_variants", "box": [0.05, 0.08, 0.53, 0.91]},
            {"name": "gasoline", "box": [0.55, 0.79, 0.97, 0.91]},
        ],
    },
]


class ManufacturerSpecificationProvider(ContextProvider):
    id = "manufacturer_public_documents"
    capability = "technical_specs"

    def source_url(self, request: VehicleResearchRequest) -> str:
        match = self.document(request)
        return match["url"] if match else "urn:autoexpert:manufacturer-document-catalogue"

    @staticmethod
    def document(request: VehicleResearchRequest) -> dict | None:
        return next(
            (
                item
                for item in DOCUMENTS
                if all(
                    str(item[field]).casefold() == str(getattr(request, field)).casefold()
                    for field in ("make", "model", "year", "market")
                )
            ),
            None,
        )

    def retrieve(
        self, request: VehicleResearchRequest, context: dict
    ) -> tuple[list[dict], dict, int]:
        document = self.document(request)
        if not document:
            return [], {"unavailable_reason": "NO_REVIEWED_DOCUMENT_LOCATION"}, 0
        url = document["url"]
        parsed = urlsplit(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        robots_content, calls = self.http.get_bytes(robots_url)
        robots_text = robots_content.decode("utf-8", errors="replace")
        if "<html" in robots_text.casefold():
            raise OfficialProviderUnavailable(
                "Manufacturer access policy unavailable", api_requests=calls
            )
        robots = RobotFileParser(robots_url)
        robots.parse(robots_text.splitlines())
        if not robots.can_fetch("AutoExpert", url):
            raise OfficialProviderUnavailable(
                "Manufacturer disallows automated retrieval", api_requests=calls
            )
        delay = robots.crawl_delay("AutoExpert") or robots.crawl_delay("*") or 0
        if delay > 30:
            raise OfficialProviderUnavailable(
                "Manufacturer crawl delay exceeds interactive budget", api_requests=calls
            )
        if delay:
            time.sleep(delay)
        content, count = self.http.get_bytes(url)
        calls += count
        if not content.startswith(b"%PDF"):
            raise OfficialProviderUnavailable(
                "Manufacturer document unavailable or redirected to HTML", api_requests=calls
            )
        from hashlib import sha256

        try:
            reader = PdfReader(io.BytesIO(content))
            if len(reader.pages) > 30:
                raise ValueError("Document exceeds reviewed page budget")
            cover = reader.pages[0].extract_text()
            if (
                str(request.year) not in cover
                or str(request.model).casefold() not in cover.casefold()
            ):
                raise ValueError("Manufacturer document identity mismatch")
            page = reader.pages[document["page"] - 1]
            width, height = float(page.mediabox.width), float(page.mediabox.height)
            spans = {region["name"]: [] for region in document["regions"]}

            def visitor(text, cm, tm, font, size):  # noqa: ANN001, ANN202
                x, y = tm[4] / width, tm[5] / height
                for region in document["regions"]:
                    left, bottom, right, top = region["box"]
                    if left <= x <= right and bottom <= y <= top:
                        spans[region["name"]].append(text)

            page.extract_text(visitor_text=visitor)
            records = []
            for name, chunks in spans.items():
                text = " ".join(" ".join(chunks).split())
                scope = {key: document[key] for key in ("make", "model", "year", "market")}
                if name == "gasoline":
                    identity = context.get("identity", {})
                    if identity.get("fuel_type_primary") != "Gasoline" or identity.get(
                        "fuel_type_secondary"
                    ):
                        continue
                    # A non-hybrid EPA match is required before taking gasoline-only data.
                    epa = context.get("epa_vehicle") or {}
                    if not epa or epa.get("atvType") in {"Hybrid", "Plug-in Hybrid", "EV"}:
                        continue
                    scope["displacement"] = identity.get("displacement_l")
                    scope["powertrain_type"] = "ICE"
                    scope["drivetrain"] = epa.get("drive")
                for topic, subtopic, value, span in extract_architecture(text):
                    records.append(
                        {
                            "topic": topic,
                            "subtopic": subtopic,
                            "value": value,
                            "applicability": scope,
                            "scope": "MODEL_CONFIGURATION",
                            "record_url": url,
                            "locator": {"page": document["page"], "region": name, "span": span},
                        }
                    )
            full_text = " ".join(page.extract_text().split())
            for subtopic, pattern, multiplier in (
                ("wheelbase_mm", r'Wheelbase\s+([\d.]+)"', 25.4),
                ("length_mm", r'Length\s+([\d.]+)"', 25.4),
                ("width_mirrors_mm", r'Including mirrors\s+([\d.]+)"', 25.4),
            ):
                match = re.search(pattern, full_text)
                if match:
                    records.append(
                        {
                            "topic": "body",
                            "subtopic": subtopic,
                            "value": round(float(match[1]) * multiplier),
                            "applicability": {
                                key: document[key] for key in ("make", "model", "year", "market")
                            },
                            "record_url": url,
                            "locator": {
                                "page": document["page"],
                                "span": match[0],
                                "conversion": f"inches * {multiplier}",
                            },
                        }
                    )
            return (
                records,
                {
                    "url": url,
                    "sha256": sha256(content).hexdigest(),
                    "publisher": document["publisher"],
                    "regions": {k: "".join(v) for k, v in spans.items()},
                    "access": "ROBOTS_ALLOWED_PUBLIC_DOCUMENT",
                },
                calls,
            )
        except Exception as error:
            raise OfficialProviderUnavailable(
                f"Manufacturer document extraction failed: {type(error).__name__}",
                api_requests=calls,
            ) from error


def extract_architecture(text: str) -> list[tuple]:
    result = []
    rules = [
        (
            "suspension",
            "construction",
            "MACPHERSON_INTEGRAL_LINK",
            r"Front:\s*independent MacPherson strut;\s*rear:\s*independent integral link",
        ),
        ("brakes", "construction", "ELECTRIC_PARKING_BRAKE", r"Electric-assist parking brake"),
        ("electrical", "architecture", "TPMS", r"Individual Tire Pressure Monitoring System"),
        ("transmission", "type", "AUTOMATIC", r"\b\d+-speed automatic transmission"),
    ]
    for topic, subtopic, value, pattern in rules:
        found = re.search(pattern, text, re.I)
        if found:
            result.append((topic, subtopic, value, found[0]))
            if topic == "transmission":
                result.append((topic, "gears", int(re.search(r"\d+", found[0])[0]), found[0]))
    return result


MANUALS = [
    {
        "make": "Ford",
        "model": "Fusion",
        "year": 2019,
        "market": "USA",
        "url": "https://www.fordservicecontent.com/Ford_Content/Catalog/owner_information/2019-Ford-Fusion-Owners-Manual-version-1_om_EN-US_06_2018.pdf",
        "pages": [157, 158, 217, 328, 329, 330, 331, 332, 333, 335, 336, 337, 339, 340, 341, 482],
        "access_policy": "PUBLIC_MANUFACTURER_DOWNLOAD_ROBOTS_404",
    },
]

BULLETINS = [
    {
        "make": "Ford",
        "models": ["Fusion", "Escape"],
        "years": [2017, 2018, 2019],
        "url": "https://static.nhtsa.gov/odi/tsbs/2019/MC-10169989-0001.pdf",
    },
]


class PublicTechnicalBulletinProvider(ContextProvider):
    id = "manufacturer_public_bulletins"
    capability = "technical_bulletins"
    normalization_version = "2-case-insensitive"

    def document(self, request):
        return next(
            (
                d
                for d in BULLETINS
                if str(request.make).casefold() == d["make"].casefold()
                and str(request.model).casefold() in [m.casefold() for m in d["models"]]
                and request.year in d["years"]
            ),
            None,
        )

    def source_url(self, request):
        doc = self.document(request)
        return doc["url"] if doc else "urn:autoexpert:technical-bulletin-catalogue"

    def retrieve(self, request, context):
        from hashlib import sha256

        doc = self.document(request)
        if not doc:
            return [], {"unavailable_reason": "NO_REVIEWED_BULLETIN_LOCATION"}, 0
        content, calls = self.http.get_bytes(doc["url"])
        if not content.startswith(b"%PDF"):
            raise OfficialProviderUnavailable("Technical bulletin unavailable", api_requests=calls)
        reader = PdfReader(io.BytesIO(content))
        text = " ".join(reader.pages[0].extract_text().split())
        engine = re.search(r"Equipped with a ([\d.]+)L", text)
        years = re.search(r"(\d{4})-(\d{4}) Model Year", text)
        identity = context.get("identity", {})
        if not engine or not years or not identity.get("displacement_l"):
            return [], {"unavailable_reason": "BULLETIN_APPLICABILITY_UNRESOLVED"}, calls
        if abs(float(engine[1]) - float(identity["displacement_l"])) > 0.06 or not int(
            years[1]
        ) <= request.year <= int(years[2]):
            return [], {"unavailable_reason": "BULLETIN_VARIANT_MISMATCH"}, calls
        if "coolant intrusion into the cylinder bores" not in text:
            return [], {"unavailable_reason": "NO_RECOGNIZED_TECHNICAL_FINDING"}, calls
        program = re.search(r"Customer Satisfaction Program ([A-Z0-9]+)", text)
        record = {
            "issue_key": "coolant_intrusion",
            "topic": "engine",
            "document_id": program[1] if program else None,
            "applicability": {
                "make": request.make,
                "model": request.model,
                "year": request.year,
                "market": request.market,
                "displacement": float(engine[1]),
            },
            "conditions": ["BUILD_DATE_AND_PROGRAM_VIN_LIST"],
            "symptoms": ["COOLANT_LOSS", "EXHAUST_SMOKE", "MISFIRE"],
            "record_url": doc["url"],
            "locator": {"page": 1},
            "text": text,
            "evidence_class": "MANUFACTURER_COMMUNICATION",
            "publisher_group": str(request.make),
            "material_id": doc["url"],
            "owner_id": None,
        }
        return (
            [record],
            {"url": doc["url"], "sha256": sha256(content).hexdigest(), "page_1": text},
            calls,
        )


class ManufacturerManualProvider(ContextProvider):
    id = "manufacturer_owner_manual"
    capability = "maintenance_specs"

    def source_url(self, request: VehicleResearchRequest) -> str:
        doc = self.document(request)
        return doc["url"] if doc else "urn:autoexpert:manufacturer-manual-catalogue"

    @staticmethod
    def document(request: VehicleResearchRequest) -> dict | None:
        return next(
            (
                item
                for item in MANUALS
                if all(
                    str(item[field]).casefold() == str(getattr(request, field)).casefold()
                    for field in ("make", "model", "year", "market")
                )
            ),
            None,
        )

    def retrieve(
        self, request: VehicleResearchRequest, context: dict
    ) -> tuple[list[dict], dict, int]:
        from hashlib import sha256

        document = self.document(request)
        identity = context.get("identity", {})
        if not document:
            return [], {"unavailable_reason": "NO_REVIEWED_MANUAL_LOCATION"}, 0
        # The manufacturer exposes this PDF as a direct public download. No credentials
        # or browser emulation; ordinary HTTP failures end retrieval immediately.
        content, calls = self.http.get_bytes(document["url"])
        if not content.startswith(b"%PDF"):
            raise OfficialProviderUnavailable(
                "Owner manual unavailable or HTML challenge", api_requests=calls
            )
        reader = PdfReader(io.BytesIO(content))
        if len(reader.pages) > 800:
            raise ValueError("Owner manual exceeds document budget")
        cover = reader.pages[0].extract_text()
        if str(request.year) not in cover or str(request.model).casefold() not in cover.casefold():
            raise ValueError("Owner manual identity mismatch")
        pages = {n: " ".join(reader.pages[n - 1].extract_text().split()) for n in document["pages"]}
        scope = {key: document[key] for key in ("make", "model", "year", "market")}
        rows = []

        def add(topic, subtopic, value, page, span, *, specific=False):  # noqa: ANN001, ANN202
            rows.append(
                {
                    "topic": topic,
                    "subtopic": subtopic,
                    "value": value,
                    "applicability": {
                        **scope,
                        **(
                            {
                                "displacement": identity["displacement_l"],
                                "powertrain_type": (context.get("identity_target") or {}).get(
                                    "powertrain_type", "UNKNOWN"
                                ),
                            }
                            if specific
                            else {}
                        ),
                    },
                    "record_url": document["url"],
                    "locator": {"page": page, "span": span},
                }
            )

        displacement = identity.get("displacement_l")
        if displacement:
            for number, text in pages.items():
                header = re.search(
                    r"CAPACITIES AND SPECIFICA\s*TIONS\s*-\s*([\d.]+)L\s*([A-Za-z]+)?", text
                )
                if not header or abs(float(header[1]) - float(displacement)) > 0.06:
                    continue
                section = text + " " + pages.get(number + 1, "")
                if header[2] and header[2].casefold() not in {"capacities", "capacityitem"}:
                    add("engine", "family", header[2], number, header[0], specific=True)
                oil = re.search(
                    r"([\d.]+)\s*qt\s*\(([\d.]+)\s*L\)Engine oil \(with oil filter\)", section
                )
                if oil:
                    add("engine", "oil_capacity_l", float(oil[2]), number, oil[0], specific=True)
                spec = re.search(r"(WSS-[A-Z0-9-]+)Motor oil \(U.S.\)", section)
                grade = re.search(r"SAE\s+(\d+W-\d+)", section)
                if spec and grade:
                    add(
                        "engine",
                        "oil",
                        f"SAE {grade[1]} · {spec[1]}",
                        number,
                        spec[0] + " / " + grade[0],
                        specific=True,
                    )
                fluid = re.search(
                    r"(WSS-[A-Z0-9-]+)Automatic transmission fluid.*?(MERCON).{0,3}\s*LV", section
                )
                if fluid:
                    add(
                        "transmission",
                        "fluid",
                        f"MERCON LV · {fluid[1]}",
                        number + 1,
                        fluid[0],
                        specific=True,
                    )
        for number, text in pages.items():
            if "Your vehicle has an electric power steering system" in text:
                add(
                    "steering",
                    "construction",
                    "ELECTRIC_POWER_STEERING",
                    number,
                    "Your vehicle has an electric power steering system",
                )
            minimum = re.search(r"minimum pump \(R\+M\)/2 octane rating of (\d+)", text)
            if minimum:
                add("engine", "octane_aki", int(minimum[1]), number, minimum[0])
            belt = re.search(r"Replace timing belt \(([\d.]+)L engine\)", text)
            if belt and displacement and abs(float(belt[1]) - float(displacement)) < 0.06:
                add("engine", "timing", "TIMING_BELT", number, belt[0], specific=True)
            interval = re.search(
                r"Do not exceed one year or ([\d,]+) mi \(([\d,]+) km\) between service intervals",
                text,
            )
            if interval:
                add(
                    "engine",
                    "oil_interval",
                    {
                        "months": 12,
                        "km": int(interval[2].replace(",", "")),
                        "condition": "MAXIMUM_NORMAL_SERVICE_OIL_MONITOR",
                    },
                    number,
                    interval[0],
                )
        return (
            rows,
            {
                "url": document["url"],
                "sha256": sha256(content).hexdigest(),
                "pages": pages,
                "access": document["access_policy"],
            },
            calls,
        )
