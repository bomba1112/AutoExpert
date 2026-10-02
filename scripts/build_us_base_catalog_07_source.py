"""Stage reviewed Corolla/Jetta US tuples; no published DB or shared-ledger writes."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/manifests/us-base-catalog-07-source-toyota-vw.json"
WORK = ROOT / "deliverables/VerifiedData/us-base-catalog-07/source-work"
EPA_DOC = "761a077a-3298-4796-aaa3-755f7763d69e"


def fact(value, unit=None):
    return {"value": value, "unit": unit} if unit else value


def document(url, registry, publisher, first, last, locator, fmt="pdf"):
    return {
        "url": url,
        "source_id": registry,
        "publisher": publisher,
        "market": "US",
        "year_from": first,
        "year_to": last,
        "locator": locator,
        "format": fmt,
    }


def family(ident, make, model, generation, code, first, last, annual, generation_docs):
    return {
        "id": ident,
        "make": make,
        "model": model,
        "generation": generation,
        "generation_code": code,
        "market": "US",
        "year_from": first,
        "year_to": last,
        "local_relevance_tier": 1,
        "local_generation_year_priority": 1,
        "source_availability_rank": 1,
        "annual_documents": annual,
        "generation_documents": generation_docs,
        "scope_note": "US annual manufacturer engine/transmission/drive matrix only; body and trim are scoped; no adjacent-year extrapolation.",
        "exclude": ["Other model years", "Other markets", "Unlisted engines, transmissions, bodies or trims"],
        "facts": {},
        "groups": [],
    }


def group(ident, year, description, trim, drive, fields, locator, epa_match=None):
    value = {
        "id": ident,
        "year_from": year,
        "year_to": year,
        "configuration": description,
        "allowed_drives": [drive],
        "factory_combinations": [{"drivetrain": drive}],
        "locator": locator,
        "facts": {**({"trim": trim} if trim else {}), **fields},
    }
    if epa_match:
        value["epa_drive_match"] = epa_match
    return value


manifest = {
    "version": "basic-catalog-07-independent-source-candidate-1",
    "batch_id": "us-base-catalog-07-source-toyota-vw",
    "state": "REVIEWED_LOCAL_NOT_PUBLISHED",
    "selection_status": "OWNER_MASTER_LIST_INDEPENDENT_MANUFACTURER_US_TABLES",
    "epa_document_id": EPA_DOC,
    "documents": {},
    "families": [],
}
docs = manifest["documents"]

for year, matrix in ((2017, "PDF p25"), (2018, "PDF p21"), (2019, "PDF p22")):
    docs[f"corolla-{year}-source07"] = document(
        f"https://www.auto-brochures.com/makes/Toyota/Corolla/Toyota_US%20Corolla_{year}.pdf",
        "factory-toyota-us",
        "Toyota manufacturer-authored US annual brochure",
        year,
        year,
        f"{matrix}: same-column trim×engine×transmission×FWD matrix; earlier model page and seat description; no other MY inheritance.",
    )
docs["corolla-xi-generation-source07"] = document(
    "https://pressroom.toyota.com/toyota-reveals-next-generation-corolla-june6/",
    "factory-toyota-us",
    "Toyota USA Newsroom",
    2017,
    2019,
    "June 2013 launch identifies all-new 2014 sedan as eleventh generation. Generation lineage only; no 2014 technical fact transferred.",
    "html",
)
docs["corolla-xii-boundary-source07"] = document(
    "https://pressroom.toyota.com/all-new-2020-toyota-corolla-sedan-greater-than-ever/",
    "factory-toyota-us",
    "Toyota USA Newsroom",
    2017,
    2019,
    "April 2019 release identifies all-new MY2020 successor sedan. Generation boundary only; no 2020 technical fact transferred.",
    "html",
)

corolla = family(
    "toyota-corolla-xi-us-2017-2019-source07", "Toyota", "Corolla",
    "XI sedan (US 2014 redesign)", "XI", 2017, 2019,
    {str(y): [f"corolla-{y}-source07"] for y in (2017, 2018, 2019)},
    ["corolla-xi-generation-source07", "corolla-xii-boundary-source07"],
)
corolla["facts"] = {
    "body": "SEDAN",
    "powertrain": "ICE",
    "fuel": "GASOLINE",
    "seats": 5,
    "engine_displacement": fact(1.8, "L"),
    "cylinders": 4,
    "aspiration": "NATURALLY_ASPIRATED",
}
for year, matrix in ((2017, "p25"), (2018, "p21"), (2019, "p22")):
    trims = ["L", "LE", "XLE", "LE Eco", "SE 6MT", "SE CVT", "XSE"]
    if year == 2017:
        trims.insert(-1, "50th Anniversary Special Edition")
    for trim in trims:
        eco = trim == "LE Eco"
        manual = trim == "SE 6MT"
        transmission = "6-speed manual" if manual else "CVTi-S continuously variable transmission"
        fields = {
            "engine_description": "1.8L DOHC inline-4 Valvematic" if eco else "1.8L DOHC inline-4 Dual VVT-i",
            "power_hp": 140 if eco else 132,
            "torque_lb_ft": fact(126 if eco else 128, "lb-ft"),
            "transmission_family": "MANUAL" if manual else "CVT",
            "transmission_description": transmission,
        }
        if manual:
            fields["gears"] = 6
        ident = trim.lower().replace(" ", "-").replace("/", "-") + f"-{year}"
        locator = (
            f"Toyota Corolla MY{year} US brochure PDF {matrix}, same trim column: "
            f"{trim} = {'Valvematic 140 hp' if eco else 'Dual VVT-i 132 hp'} / "
            f"{transmission} / FWD. Body and five seats on earlier annual pages."
        )
        corolla["groups"].append(
            group(ident, year, f"Corolla {trim} 1.8 / {transmission} / FWD", trim, "FWD", fields, locator)
        )
manifest["families"].append(corolla)

docs["jetta-2016-source07"] = document(
    "https://www.auto-brochures.com/makes/Volkswagen/Jetta/VW_US%20Jetta_2016.pdf",
    "factory-vw-us", "Volkswagen manufacturer-authored US brochure", 2016, 2016,
    "PDF p10 performance inventory: 1.4 TSI, 1.8 TSI, 5MT and 6AT; EPA complete tuples separately verify exact engine×transmission×FWD linkage; sedan body illustrated/described.",
)
docs["jetta-vi-generation-source07"] = document(
    "https://www.volkswagen-newsroom.com/en/international-driving-presentation-of-the-new-jetta-2292/the-new-jetta-body-styling-and-function-2302",
    "factory-vw-us", "Volkswagen Newsroom", 2016, 2016,
    "Manufacturer identifies sixth-generation Jetta body lineage; paired with annual US MY2016 sedan and EPA tuples. Identity only.",
    "html",
)
jetta16 = family(
    "vw-jetta-vi-us-2016-source07", "Volkswagen", "Jetta", "VI sedan", "VI", 2016, 2016,
    {"2016": ["jetta-2016-source07"]}, ["jetta-vi-generation-source07"],
)
jetta16["facts"] = {"body": "SEDAN", "powertrain": "ICE", "fuel": "GASOLINE", "cylinders": 4, "aspiration": "TURBO"}
for displacement, hp in ((1.4, 150), (1.8, 170)):
    for manual in (True, False):
        trans = "5-speed manual" if manual else "6-speed Tiptronic automatic"
        epa_trans = "Manual 5-spd" if manual else "Automatic (S6)"
        desc = f"Jetta {displacement} TSI / {trans} / FWD"
        jetta16["groups"].append(group(
            f"{str(displacement).replace('.', '-')}-{'5mt' if manual else '6at'}-2016",
            2016, desc, None, "FWD",
            {
                "engine_description": f"{displacement} TSI turbo direct-injection inline-4",
                "engine_displacement": fact(displacement, "L"),
                "power_hp": hp,
                "torque_lb_ft": fact(184, "lb-ft"),
                "transmission_family": "MANUAL" if manual else "AT",
                "transmission_description": trans,
                "gears": 5 if manual else 6,
            },
            f"VW MY2016 Jetta US brochure PDF p10 engine/transmission inventory; EPA vehicles.csv exact complete Jetta MY2016 {displacement}L/{epa_trans}/FWD tuple. No trim or GLI claim.",
            {"model": ["Jetta"], "displ": [str(displacement)], "trany": [epa_trans]},
        ))
manifest["families"].append(jetta16)

docs["jetta-2019-order-source07"] = document(
    "https://www.auto-brochures.com/makes/Volkswagen/Jetta/VW_US%20Jetta_2019-og.pdf",
    "factory-vw-us", "Volkswagen of America MY2019 order guide", 2019, 2019,
    "PDF p4 performance matrix, S/SE/R-Line/SEL/SEL Premium columns: 1.4T 147 hp, S6MT or optional8AT, other trims8AT, FWD all. Document dated Dec2019; trim scope only.",
)
docs["jetta-vii-generation-source07"] = document(
    "https://www.volkswagen-newsroom.com/en/press-releases/world-premiere-of-the-completely-new-jetta-in-detroit-580",
    "factory-vw-us", "Volkswagen Newsroom", 2019, 2019,
    "Jan2018 press release names seventh-generation new Jetta for US and four-door sedan body; identity only. Annual MY2019 order guide proves technical tuples.",
    "html",
)
jetta19 = family(
    "vw-jetta-vii-us-2019-source07", "Volkswagen", "Jetta", "VII sedan (MQB)", "VII", 2019, 2019,
    {"2019": ["jetta-2019-order-source07"]}, ["jetta-vii-generation-source07"],
)
jetta19["facts"] = {
    "body": "SEDAN", "powertrain": "ICE", "fuel": "GASOLINE",
    "engine_description": "1.4L TSI turbocharged direct-injection inline-4",
    "engine_displacement": fact(1.4, "L"), "cylinders": 4, "aspiration": "TURBO",
    "power_hp": 147, "torque_lb_ft": fact(184, "lb-ft"),
}
for trim in ("S", "SE", "R-Line", "SEL", "SEL Premium"):
    transmissions = ("6MT", "8AT") if trim == "S" else ("8AT",)
    for transmission in transmissions:
        manual = transmission == "6MT"
        jetta19["groups"].append(group(
            trim.lower().replace(" ", "-") + "-" + transmission.lower() + "-2019",
            2019, f"Jetta {trim} 1.4 TSI / {transmission} / FWD", trim, "FWD",
            {
                "transmission_family": "MANUAL" if manual else "AT",
                "transmission_description": "6-speed manual" if manual else "8-speed Tiptronic automatic",
                "gears": 6 if manual else 8,
            },
            f"VW of America MY2019 Jetta order guide PDF p4, {trim} column: 1.4 TSI 147 hp, {transmission}, FWD. S8AT optional; other four trims8AT standard. GLI excluded.",
        ))
manifest["families"].append(jetta19)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
summary = {
    "state": "SOURCE_CANDIDATE_UNPUBLISHED",
    "families": [
        {"make": item["make"], "model": item["model"], "generation": item["generation"],
         "model_years": list(range(item["year_from"], item["year_to"] + 1)),
         "annual_configurations": sum(g["year_to"] - g["year_from"] + 1 for g in item["groups"])}
        for item in manifest["families"]
    ],
    "candidate_annual_configurations": sum(len(f["groups"]) for f in manifest["families"]),
    "exact_us_source_documents": len(docs),
    "ai_draft_publication": 0,
    "db_writes": 0,
}
WORK.mkdir(parents=True, exist_ok=True)
(WORK / "source-candidate-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))
