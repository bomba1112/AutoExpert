"""One-time transcription of reviewed annual manufacturer drive matrices.

Running this script freezes an explicit catalog-key-to-publisher assertion in
the manifest. Each drive below is transcribed from the named annual source,
not read from the candidate catalogue or its EPA observation.
"""

import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifests/commercial-manufacturer-drivetrain-01.json"
REVIEW = ROOT / "deliverables/VerifiedData/commercial-fact-overlay-01/factory-agent-review.jsonl"

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
exceptions = [json.loads(line) for line in REVIEW.read_text(encoding="utf-8").splitlines()]
available = collections.defaultdict(list)
for row in exceptions:
    if row["reason_codes"] == ["MISSING_SAFE_DRIVETRAIN"]:
        available[(row["make"], row["model"], row["model_year"])].append(row["catalog_key"])
documents = {(d["make"], d["model"], d["model_year"]): d for d in manifest["documents"]}
for document in manifest["documents"]:
    document["rows"] = []


def add(scope, suffix, official_variant, official_drive_term, drivetrain, locator):
    matches = [key for key in available[scope] if key.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError((scope, suffix, matches))
    documents[scope]["rows"].append(
        {
            "catalog_key": matches[0],
            "official_variant": official_variant,
            "official_drive_term": official_drive_term,
            "drivetrain": drivetrain,
            "locator": locator,
        }
    )


# BMW Technical Data has a Drive type entry below each named model column.
bmw = {
    2017: [
        ("530i-rwd-8at-RWD", "530i", "RWD"),
        ("530i-xdrive-awd-8at-AWD", "530i xDrive", "AWD"),
        ("540i-rwd-8at-RWD", "540i", "RWD"),
        ("540i-xdrive-awd-8at-AWD", "540i xDrive", "AWD"),
    ],
    2018: [
        ("530i-rwd-8at-RWD", "530i", "RWD"),
        ("530i-xdrive-awd-8at-AWD", "530i xDrive", "AWD"),
        ("540i-rwd-8at-RWD", "540i", "RWD"),
        ("540i-xdrive-awd-8at-AWD", "540i xDrive", "AWD"),
        ("m550i-xdrive-awd-8at-AWD", "M550i xDrive", "AWD"),
        ("530e-rwd-8at-RWD", "530e", "RWD"),
        ("530e-xdrive-awd-8at-AWD", "530e xDrive", "AWD"),
    ],
}
for year, entries in bmw.items():
    page = 18 if year == 2017 else 1
    for suffix, variant, drive in entries:
        add(
            ("BMW", "5 Series", year),
            f"-{year}-{suffix}-{year}",
            variant,
            f"Drive type: {drive}",
            drive,
            f"PDF p{page}, Technical Data, {variant} column, Drive type row",
        )

# Honda Facts Guide p7 enumerates 2WD and AWD model codes for every CR-V trim;
# p68 identifies Honda's two-wheel-drive trucks as front-wheel drive.
for trim, slug in [
    ("LX", "lx"),
    ("EX", "ex"),
    ("EX-L", "ex-l"),
    ("EX-L Navi", "ex-l-navi"),
    ("Touring", "touring"),
]:
    for source_term, drive in [("2WD", "FWD"), ("AWD", "AWD")]:
        add(
            ("Honda", "CR-V", 2017),
            f"-2017-{slug}-{drive.lower()}-{drive}-2017",
            f"{source_term} {trim}",
            source_term,
            drive,
            f"PDF p7, CR-V Model Lineup, {source_term} {trim} model-code row; "
            "p68 Front-Wheel Drive",
        )

# Jeep fleet pp1-3 explicitly restrict the gearbox to 4x2/FWD or 4x4 and
# identify which trim columns offer each combination.
jeep = [
    (
        "sport-fwd-mt6-FWD",
        "Sport / 6-speed manual / 4x2",
        "FWD",
        "PDF pp1-3, 6-speed manual 4x2, Sport column",
    ),
    (
        "sport-4wd-mt6-4WD",
        "Sport / 6-speed manual / 4x4",
        "4WD",
        "PDF pp1-3, 6-speed manual 4x4, Sport column",
    ),
    (
        "latitude-4wd-mt6-4WD",
        "Latitude / 6-speed manual / 4x4",
        "4WD",
        "PDF p3, manual standard on Latitude 4x4",
    ),
    (
        "sport-fwd-at6-FWD",
        "Sport / 6-speed automatic / FWD",
        "FWD",
        "PDF pp2-3, 6-speed automatic FWD-only, Sport column",
    ),
    (
        "latitude-fwd-at6-FWD",
        "Latitude / 6-speed automatic / FWD",
        "FWD",
        "PDF pp2-3, 6-speed automatic FWD-only, Latitude column",
    ),
    (
        "limited-fwd-at6-FWD",
        "Limited / 6-speed automatic / FWD",
        "FWD",
        "PDF pp2-3, 6-speed automatic FWD-only, Limited column",
    ),
    (
        "sport-4wd-at9-4WD",
        "Sport / 9-speed automatic / 4x4",
        "4WD",
        "PDF pp1-3, 9-speed automatic 4x4, Sport column",
    ),
    (
        "latitude-4wd-at9-4WD",
        "Latitude / 9-speed automatic / 4x4",
        "4WD",
        "PDF pp1-3, 9-speed automatic 4x4, Latitude column",
    ),
    (
        "trailhawk-4wd-at9-4WD",
        "Trailhawk / 9-speed automatic / 4x4",
        "4WD",
        "PDF pp1-3, 9-speed automatic 4x4, Trailhawk column",
    ),
    (
        "limited-4wd-at9-4WD",
        "Limited / 9-speed automatic / 4x4",
        "4WD",
        "PDF pp1-3, 9-speed automatic 4x4, Limited column",
    ),
]
for suffix, variant, drive, locator in jeep:
    add(
        ("Jeep", "Compass", 2019),
        f"-2019-{suffix}-2019",
        variant,
        "Four-Wheel Drive" if drive == "4WD" else "Front-Wheel Drive",
        drive,
        locator,
    )

# Lexus press releases directly name the following RX/drive combinations.
lexus = {
    2016: [
        ("rx-350-fwd-at8-FWD", "RX 350 FWD", "front-wheel drive", "FWD"),
        ("rx-350-awd-at8-AWD", "RX 350 AWD", "all-weather drive (AWD)", "AWD"),
        (
            "rx-350-f-sport-awd-at8-AWD",
            "RX 350 F SPORT AWD",
            "F SPORT available for RX 350 AWD",
            "AWD",
        ),
    ],
    2017: [
        ("rx-350-fwd-at8-FWD", "RX 350 FWD", "front-wheel drive", "FWD"),
        ("rx-350-awd-at8-AWD", "RX 350 AWD", "Dynamic Torque Control AWD", "AWD"),
        ("rx-350-f-sport-fwd-at8-FWD", "RX 350 F SPORT FWD", "new F SPORT FWD model", "FWD"),
        ("rx-350-f-sport-awd-at8-AWD", "RX 350 F SPORT AWD", "joining the AWD model", "AWD"),
        ("rx-450h-awd-ecvt-AWD", "RX 450h AWD", "available AWD with rear electric motor", "AWD"),
    ],
}
for year, entries in lexus.items():
    for suffix, variant, term, drive in entries:
        add(
            ("Lexus", "RX", year),
            f"-{year}-{suffix}-{year}",
            variant,
            term,
            drive,
            f"Press release, {variant} availability and Vehicle Details/Drivetrain",
        )

# Mercedes annual quick-reference At a Glance table has exact model columns
# and a Drive Config row, including AMG and the MY2020 plug-in hybrid.
mercedes = {
    2020: [
        ("amg-glc-43-awd", "AMG GLC 43", "AWD", "AMG Performance 4MATIC"),
        ("amg-glc-63-awd", "AMG GLC 63", "AWD", "AMG Performance 4MATIC+"),
        ("glc-300-rwd", "GLC 300", "RWD", "Rear-Wheel Drive"),
        ("glc-300-4matic-awd", "GLC 300 4MATIC", "AWD", "4MATIC: All-Wheel Drive"),
        ("glc-350e-4matic-awd", "GLC 350e 4MATIC", "AWD", "4MATIC: All-Wheel Drive"),
    ],
    2021: [
        ("amg-glc-43-awd", "AMG GLC 43", "AWD", "AMG Performance 4MATIC"),
        ("amg-glc-63-awd", "AMG GLC 63", "AWD", "AMG Performance 4MATIC+"),
        ("glc-300-rwd", "GLC 300", "RWD", "Rear-Wheel Drive"),
        ("glc-300-4matic-awd", "GLC 300 4MATIC", "AWD", "4MATIC: All-Wheel Drive"),
    ],
}
for year, entries in mercedes.items():
    for suffix, variant, drive, term in entries:
        add(
            ("Mercedes-Benz", "GLC-Class", year),
            f"-{year}-{suffix}-{drive}-{year}",
            variant,
            term,
            drive,
            f"At a Glance, {variant} model column, Drive Config row",
        )

# Nissan press-kit pricing sections print eight complete grade/drive rows per
# year; engine and transmission applicability is printed with the MY2021 rows
# and across the MY2022 VC-Turbo lineup.
for year, engine in [(2021, "2.5 Liter I4 Xtronic"), (2022, "1.5-liter VC-Turbo across lineup")]:
    for trim in ("S", "SV", "SL", "Platinum"):
        for drive in ("FWD", "AWD"):
            add(
                ("Nissan", "Rogue", year),
                f"-{year}-{trim.lower()}-{drive.lower()}-cvt-{drive}-{year}",
                f"Rogue {trim} {drive}",
                f"{trim} {drive}",
                drive,
                f"Annual Rogue pricing/MSRP, {trim} {drive} row; {engine}",
            )

# Toyota Highlander gas/hybrid grade columns have a standard FWD row, and
# separate option rows for conventional, dynamic-torque, and electronic AWD.
for year, gas, hybrid in [
    (2020, ("L", "LE", "XLE", "Limited", "Platinum"), ("LE", "XLE", "Limited", "Platinum")),
    (2021, ("L", "LE", "XLE", "XSE", "Limited", "Platinum"), ("LE", "XLE", "Limited", "Platinum")),
]:
    page = 30 if year == 2020 else 20
    for powertrain, grades, transmission in (("gas", gas, "at8"), ("hybrid", hybrid, "ecvt")):
        for grade in grades:
            for drive in ("FWD", "AWD"):
                if drive == "FWD":
                    term = "Front-Wheel Drive: Standard"
                elif powertrain == "hybrid":
                    term = "Electronic On-Demand AWD: Available"
                elif grade in (
                    ("Limited", "Platinum") if year == 2020 else ("XSE", "Limited", "Platinum")
                ):
                    term = "Dynamic Torque Vectoring AWD: Available"
                else:
                    term = "All-Wheel Drive: Available"
                add(
                    ("Toyota", "Highlander", year),
                    f"-{year}-{'hybrid-' if powertrain == 'hybrid' else ''}"
                    f"{grade.lower()}-{drive.lower()}-{transmission}-{drive}-{year}",
                    f"Highlander {powertrain} {grade} {drive}",
                    term,
                    drive,
                    f"PDF p{page}, {powertrain} {grade} column, DRIVETRAIN {term} row",
                )

manifest["scope_note"] = (
    "Each exact catalog key has an independently reviewed model/grade/drive "
    "assertion from its annual manufacturer document. Candidate EPA drive "
    "is checked only for agreement and never chooses a claim value."
)
manifest["held_catalog_keys"] = [
    {
        "catalog_key": next(
            key
            for key in available[("Lexus", "RX", 2017)]
            if key.endswith("-2017-rx-450h-f-sport-awd-ecvt-AWD-2017")
        ),
        "reason": (
            "The pressroom release does not state RX 450h F SPORT AWD as a single "
            "exact combination; the additional brochure needs its own source record."
        ),
    }
]
for document in manifest["documents"]:
    document["rows"].sort(key=lambda row: row["catalog_key"])
    keys = [row["catalog_key"] for row in document["rows"]]
    if len(keys) != len(set(keys)):
        raise ValueError("DUPLICATE_REVIEWED_KEY")
    document["expected_rows"] = len(keys)
    document["drive_counts"] = dict(
        collections.Counter(row["drivetrain"] for row in document["rows"])
    )
    document["keyset_sha256"] = hashlib.sha256("\n".join(keys).encode()).hexdigest()
if sum(len(document["rows"]) for document in manifest["documents"]) != 102:
    raise ValueError("REVIEWED_SCOPE_CHANGED")
MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
