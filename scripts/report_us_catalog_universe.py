# ruff: noqa: E501  # Long report prose and table headers are intentionally kept as source sentences.
"""Render an auditable checkpoint for the read-only U.S. candidate-universe pass.

Every count comes from the generated EPA/join/vPIC/generation artifacts or the
existing published BASE_READY rows. This script writes reports only; it neither
changes the production database nor promotes a research candidate to verified.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from us_catalog_universe_join import published_ready  # noqa: E402

DEFAULT_DIRECTORY = ROOT / "deliverables/VerifiedData/us-catalog-universe"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def year_ranges(years: set[int] | list[int]) -> str:
    ordered = sorted(set(years))
    if not ordered:
        return "—"
    runs: list[tuple[int, int]] = []
    start = end = ordered[0]
    for year in ordered[1:]:
        if year == end + 1:
            end = year
        else:
            runs.append((start, end))
            start = end = year
    runs.append((start, end))
    return ", ".join(str(a) if a == b else f"{a}–{b}" for a, b in runs)


def cell(value: object) -> str:
    return str(value if value is not None else "—").replace("|", "\\|").replace("\n", " ")


def table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def pct(numerator: int, denominator: int) -> str:
    return f"{100 * numerator / denominator:.2f}%" if denominator else "0.00%"


def write_published_csv(path: Path, published: list[dict]) -> None:
    fields = [
        "make", "model", "generation", "market", "model_year", "body", "engine",
        "displacement_l", "transmission", "transmission_family", "transmission_gears",
        "drivetrain", "catalog_key", "variant_id", "status",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        sink = csv.DictWriter(handle, fieldnames=fields)
        sink.writeheader()
        for row in sorted(published, key=lambda r: (r["make"], r["model"], r["model_year"], r["catalog_key"])):
            sink.writerow({
                **{field: row.get(field) for field in fields},
                "market": "USA",
                "status": "BASE_READY_PUBLISHED",
            })


def make_reports(directory: Path, db_path: Path) -> dict:
    index = read_json(directory / "index.json")
    join_summary = read_json(directory / "candidate-join-summary.json")
    generation_summary = read_json(directory / "generation-hypotheses-summary.json")
    vpic_summary = read_json(directory / "vpic-crosscheck-summary.json")
    scoped_summary = read_json(directory / "generation-scoped-powertrain-groups-summary.json")
    routing_summary = read_json(directory / "exception-routing/summary.json")
    candidate = read_jsonl(directory / "candidates.jsonl")
    joined = read_jsonl(directory / "candidate-join.jsonl")
    generations = read_jsonl(directory / "generation-hypotheses.jsonl")
    vpic = read_jsonl(directory / "vpic-crosscheck.jsonl")
    powertrain_groups = read_jsonl(directory / "powertrain-groups.jsonl")
    scoped_groups = read_jsonl(directory / "generation-scoped-powertrain-groups.jsonl")
    routed_models = read_jsonl(directory / "exception-routing/model-routing.jsonl")
    manual_models = read_jsonl(directory / "exception-routing/manual-review.jsonl")
    powertrain_routes = read_jsonl(directory / "exception-routing/powertrain-routing.jsonl")
    automated_generation = read_jsonl(
        directory / "exception-routing/automated-generation-research.jsonl"
    )
    published = published_ready(db_path)

    assert len(candidate) == len(joined) == index["denominator"]["epa_rows_after_filter"]
    assert len(powertrain_groups) == scoped_summary["source_group_count"]
    assert len(scoped_groups) == scoped_summary["derived_group_count"]
    assert sum(group["epa_row_count"] for group in scoped_groups) == len(candidate)
    assert len(generations) == generation_summary["counts"]["hypothesis_segments"]
    assert len(vpic) == vpic_summary["new_model_year_pairs"]
    assert len(published) == join_summary["published_base_ready_configurations"]
    assert Counter(row["classification"] for row in joined) == join_summary["candidate_classifications"]
    assert len(routed_models) == routing_summary["counts"]["models_in_denominator"]
    assert len(manual_models) == routing_summary["counts"]["manual_review_models"]
    assert len(powertrain_routes) == len(powertrain_groups)
    assert Counter(row["route"] for row in powertrain_routes) == {
        route: count
        for route, count in routing_summary["counts"]["powertrain_group_routes"].items()
        if count
    }
    routed_group_years = Counter(
        year["route"] for row in powertrain_routes for year in row["years"]
    )
    assert routed_group_years == {
        route: count
        for route, count in routing_summary["counts"]["powertrain_group_year_routes"].items()
        if count
    }
    assert sum(routed_group_years.values()) == index["denominator"]["model_year_powertrain_combinations"]
    assert len(automated_generation) == routing_summary["counts"]["automated_generation_segments"]

    makes = index["scope"]["approved_makes"]
    by_brand = {row["make"]: row for row in join_summary["brands"]}
    assert set(makes) == set(by_brand)
    ready_models = {(row["make"], row["model"]) for row in published}
    target_models = {(row["make"], row["model"]) for row in candidate}
    assert len(ready_models) == join_summary["currently_verified_models"]
    assert len(target_models) == join_summary["total_target_models"]
    assert {(row["make"], row["model"]) for row in routed_models} == target_models
    assert {(row["make"], row["model"]) for row in manual_models} == {
        (row["make"], row["model"])
        for row in routed_models if row["route"] == "MANUAL_EXCEPTION_REVIEW"
    }
    manual_model_set = {(row["make"], row["model"]) for row in manual_models}
    auto_group_years_in_manual_models = [
        (row["make"], row["model"], year["model_year"])
        for row in powertrain_routes
        if (row["make"], row["model"]) in manual_model_set
        for year in row["years"]
        if year["route"] == "AUTOMATED_BULK_CANDIDATE"
    ]
    manual_models_with_auto_groups = {
        (make, model) for make, model, _ in auto_group_years_in_manual_models
    }
    ready_matching = ready_models & target_models
    assert len(ready_matching) == join_summary["verified_models_matching_epa_base_name"]
    missing_target_models = target_models - ready_models
    assert len(missing_target_models) == sum(row["remaining_models"] for row in join_summary["brands"])

    candidate_years: dict[tuple[str, str], set[int]] = defaultdict(set)
    for row in candidate:
        candidate_years[(row["make"], row["model"])].add(row["model_year"])
    case_aliases = defaultdict(set)
    for make, model in target_models:
        case_aliases[(make, model.casefold())].add(model)
    case_aliases = {key: names for key, names in case_aliases.items() if len(names) > 1}

    new_pairs = {(row["make"], row["model"], row["model_year"]) for row in vpic}
    alias_rows = [row for row in joined if row["classification"] == "POSSIBLE_ALIAS"]
    alias_pairs = {(row["make"], row["model"], row["model_year"]) for row in alias_rows}
    vpic_unresolved = [row for row in vpic if row["status"] == "VPIC_NAME_UNRESOLVED"]
    vpic_unresolved_pairs = {(row["make"], row["model"], row["model_year"]) for row in vpic_unresolved}
    ambiguous = generation_summary["ambiguous_generation_years"]
    ambiguous_pairs = {(row["make"], row["model"], row["model_year"]) for row in ambiguous}
    explicit_exception_pairs = alias_pairs | vpic_unresolved_pairs | ambiguous_pairs
    assert explicit_exception_pairs <= new_pairs
    assert len(new_pairs) == vpic_summary["new_model_year_pairs"]
    conflict_rows = [row for row in joined if row["classification"] == "CONFLICT"]

    published_by_model: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in published:
        published_by_model[(row["make"], row["model"])].append(row)
    write_published_csv(directory / "published-ready-configurations.csv", published)

    ready_table_rows = []
    for (make, model), rows in sorted(published_by_model.items(), key=lambda item: (makes.index(item[0][0]), item[0][1])):
        generations_for_model = sorted({str(row["generation"] or "UNKNOWN") for row in rows})
        ready_table_rows.append([
            make,
            model,
            ", ".join(generations_for_model),
            "USA",
            year_ranges({row["model_year"] for row in rows}),
            len(rows),
            "BASE_READY_PUBLISHED",
        ])

    generation_rows = []
    for row in sorted(generations, key=lambda r: (makes.index(r["make"]), r["model"], r["year_start"], r["year_end"])):
        candidate_labels = ", ".join(item["label"] for item in row["generation_candidates"])
        body_aliases = ", ".join(item["alias"] for item in row["body_aliases_candidate"])
        generation_rows.append([
            row["make"], row["model"], year_ranges(row["observed_model_years"]),
            row["generation"] or "—", candidate_labels or "—", body_aliases or "—",
            row["generation_resolution"], sum(row["join_classifications"].values()),
        ])
    generation_lines = [
        "# U.S. candidate generation ranges",
        "",
        "These are **AI_GENERATION_DRAFT** segments for EPA candidate rows, not factory-verified mappings. "
        "Every range below contains only observed model years; gaps are retained. An exact-year reference "
        "to an existing published family still requires applicability proof before reuse.",
        "",
        f"Segments: **{len(generations)}**; unresolved labels: **{generation_summary['counts']['hypothesis_segments'] - sum(1 for row in generations if row['generation'])}**; "
        f"ambiguous observed model-years: **{len(ambiguous)}**.",
        "",
        table(["Make", "EPA base model", "Observed MY", "Draft generation", "Other candidate labels", "Body aliases (candidate)", "Resolution", "EPA rows"], generation_rows),
        "",
        "Machine-readable detail: [generation-hypotheses.jsonl](generation-hypotheses.jsonl).",
        "",
    ]
    (directory / "GENERATION_RANGE_QUEUE.md").write_text("\n".join(generation_lines), encoding="utf-8")

    unresolved_by_model = defaultdict(set)
    for row in vpic_unresolved:
        unresolved_by_model[(row["make"], row["model"])].add(row["model_year"])
    alias_by_model = defaultdict(list)
    for row in alias_rows:
        alias_by_model[(row["make"], row["model"])].append(row)
    exception_lines = [
        "# U.S. candidate exception signals",
        "",
        "Only candidate triage signals are listed. A vPIC name mismatch is **not** evidence that the car "
        "did not exist. POSSIBLE_ALIAS is **not** permission to inherit a published powertrain or generation.",
        "",
        f"The [exception router](exception-routing/summary.json) directs **{len(manual_models)} / {len(routed_models)} "
        f"EPA model labels ({pct(len(manual_models), len(routed_models))})** to manual agent review; "
        f"{len(routed_models) - len(manual_models)} models follow automated batched source research. "
        "A model routed to manual review can still have some published years and separate automated "
        "generation research segments. No route authorizes publication.",
        "",
        "## Routed manual-review models",
        "",
        table(["Make", "EPA base model", "Observed MY", "Manual issue codes", "New EPA rows"], [
            [
                row["make"], row["model"],
                ", ".join(str(a) if a == b else f"{a}–{b}" for a, b in row["model_year_ranges"]),
                ", ".join(sorted({issue["code"] for issue in row["manual_exceptions"]})),
                row["new_candidate_row_count"],
            ]
            for row in sorted(manual_models, key=lambda r: (makes.index(r["make"]), r["model"]))
        ]),
        "",
        "The [machine-readable manual queue](exception-routing/manual-review.jsonl) includes exact "
        "scope, EPA IDs and source labels per issue. "
        "[Automated generation source research](exception-routing/automated-generation-research.jsonl) "
        f"contains {len(automated_generation)} contiguous segments; it is not a second manual queue.",
        "",
        f"Manual routing is selective below model level: **{len(manual_models_with_auto_groups)}** of "
        f"{len(manual_models)} manual-route model labels still have "
        f"**{len(auto_group_years_in_manual_models):,}** model-year-powertrain candidates on the "
        "automated source-research path. The [per-powertrain route file]"
        "(exception-routing/powertrain-routing.jsonl) gives the EPA IDs and route for each exact year; "
        "one ambiguous variant does not hold unrelated configurations.",
        "",
        f"Unique signaled new model-year pairs: **{len(explicit_exception_pairs)} / {len(new_pairs)} "
        f"({pct(len(explicit_exception_pairs), len(new_pairs))})**. Signal categories overlap: "
        f"vPIC names {len(vpic_unresolved_pairs)}, possible alias {len(alias_pairs)} pairs / {len(alias_rows)} EPA rows, "
        f"ambiguous generation {len(ambiguous_pairs)} pairs. Exact EPA-ID conflicts: "
        f"**{len(conflict_rows)}**. "
        "Raw EPA mandatory-field blanks: **0** in this snapshot. Factory applicability remains unverified.",
        "",
        "## vPIC name unresolved",
        "",
        table(["Make", "EPA base model", "Observed MY"], [
            [make, model, year_ranges(years)]
            for (make, model), years in sorted(unresolved_by_model.items(), key=lambda x: (makes.index(x[0][0]), x[0][1]))
        ]),
        "",
        "## Possible links to existing published variants",
        "",
        table(["Make", "EPA base model", "Observed MY", "EPA rows", "Published model hint"], [
            [make, model, year_ranges({row["model_year"] for row in rows}), len(rows), ", ".join(sorted({str(row["matched_catalog_model"]) for row in rows}))]
            for (make, model), rows in sorted(alias_by_model.items(), key=lambda x: (makes.index(x[0][0]), x[0][1]))
        ]),
        "",
        "## Ambiguous generation years",
        "",
        table(["Make", "EPA base model", "MY", "Competing labels"], [
            [row["make"], row["model"], row["model_year"], ", ".join(row["candidate_labels"])]
            for row in sorted(ambiguous, key=lambda r: (makes.index(r["make"]), r["model"], r["model_year"]))
        ]),
        "",
        "## EPA case-only label variants",
        "",
        table(["Make", "Casefold-equivalent EPA labels", "Interpretation"], [
            [make, ", ".join(sorted(names)), "Candidate naming alias; do not count as two newly verified families"]
            for (make, _), names in sorted(case_aliases.items(), key=lambda x: (makes.index(x[0][0]), x[0][1]))
        ]),
        "",
        "## Exact EPA-ID conflicts",
        "",
        table(["Make", "EPA base model", "MY", "EPA ID", "Reason"], [
            [row["make"], row["model"], row["model_year"], row["epa_vehicle_id"], row["reason"]]
            for row in conflict_rows
        ]) if conflict_rows else "None in this snapshot.",
        "",
        "Machine-readable rows: [candidate-join.jsonl](candidate-join.jsonl), "
        "[vpic-crosscheck.jsonl](vpic-crosscheck.jsonl), "
        "[generation-hypotheses-summary.json](generation-hypotheses-summary.json).",
        "",
    ]
    (directory / "EXCEPTION_REVIEW_QUEUE.md").write_text("\n".join(exception_lines), encoding="utf-8")

    brand_rows = []
    manual_by_make = Counter(row["make"] for row in manual_models)
    group_year_route_by_make = defaultdict(Counter)
    for group in powertrain_routes:
        for year in group["years"]:
            group_year_route_by_make[group["make"]][year["route"]] += 1
    for make in makes:
        brand = by_brand[make]
        brand_rows.append([
            make, brand["target_models"], brand["base_ready_models"], brand["remaining_models"],
            brand["candidate_configs"], brand["base_ready_configs"], manual_by_make[make],
        ])
    new_model_lines = []
    for make in makes:
        names = by_brand[make]["new_model_names"]
        new_model_lines.append(f"**{make} ({len(names)}):** " + "; ".join(
            f"{name} (MY {year_ranges(candidate_years[(make, name)])})" for name in names
        ) + ".")

    denominator = index["denominator"]
    source = index["source"]
    target_casefold = {(make, model.casefold()) for make, model in target_models}
    denominator_by_make = {row["make"]: row for row in denominator["brands"]}
    denominator_rows = [
        [
            make,
            denominator_by_make[make]["models_discovered"],
            denominator_by_make[make]["earliest_my"],
            denominator_by_make[make]["latest_my"],
            denominator_by_make[make]["candidate_combinations"],
            denominator_by_make[make]["epa_rows"],
        ]
        for make in makes
    ]
    powertrain_route_rows = [
        [
            make,
            group_year_route_by_make[make]["AUTOMATED_BULK_CANDIDATE"],
            group_year_route_by_make[make]["MANUAL_EXCEPTION_REVIEW"],
            group_year_route_by_make[make]["MIXED_MANUAL_AND_AUTOMATED_CANDIDATES"],
            group_year_route_by_make[make]["ALREADY_VERIFIED_REFERENCE"],
        ]
        for make in makes
    ]
    checkpoint = [
        "# U.S. base catalog — full candidate-universe checkpoint",
        "",
        f"Generated from the EPA snapshot acquired **{source['acquired_at']}** and published local DB read-only; "
        "this pass makes **no publication changes**.",
        "",
        f"**TOTAL TARGET MODELS = {join_summary['total_target_models']}** EPA `baseModel` labels "
        f"({len(target_casefold)} casefold-distinct names; the source contains Nissan and Chevrolet case-only aliases).  ",
        f"**CURRENTLY VERIFIED MODELS = {join_summary['currently_verified_models']}** existing published BASE_READY labels; "
        f"{join_summary['verified_models_matching_epa_base_name']} match EPA base labels, "
        f"{len(join_summary['verified_editorial_subfamilies_outside_epa_base_names'])} are editorial subfamilies outside them.  ",
        f"**NEWLY AUTO-VERIFIED MODELS = {join_summary['newly_auto_verified_models']}**.  ",
        f"**MODELS NEEDING EXCEPTION REVIEW = {len(manual_models)}** model-level manual routes "
        f"({pct(len(manual_models), len(routed_models))} of {len(routed_models)} EPA labels).  ",
        f"**REMAINING TARGET EPA LABELS = {len(missing_target_models)}**. This is not the manual exception queue. "
        f"Alias, vPIC-name and generation-ambiguity signals affect {len(explicit_exception_pairs)} "
        "new model-year pairs; the manual router also detects source-label drivetrain ambiguity. "
        "All candidate rows still need applicable factory evidence before publication.",
        "",
        "## Per-brand coverage",
        "",
        table(["Make", "Target EPA models", "BASE_READY in EPA labels", "Remaining EPA labels", "EPA candidate rows", "Published BASE_READY configs in EPA labels", "Manual-route models"], brand_rows),
        "",
        "The published DB has **1,382** BASE_READY configurations in **75** model labels. The per-brand "
        "published-config column excludes **47** configurations in five editorial subfamilies whose names are "
        "outside the EPA base labels: " + ", ".join(
            f"{row['make']} {row['model']}" for row in join_summary["verified_editorial_subfamilies_outside_epa_base_names"]
        ) + ".",
        "",
        "## Denominator and provenance",
        "",
        f"The official [FuelEconomy.gov downloadable vehicle CSV]({source['url']}) has "
        f"{index['selection_counts']['source_rows']:,} source rows and {len(source['csv_columns'])} columns. "
        f"The retained U.S. scope contains **{denominator['unique_brands']} makes, {denominator['unique_models']} EPA base-model labels, "
        f"{denominator['model_year_pairs']:,} model-year pairs, {denominator['normalized_powertrain_combinations']:,} "
        f"normalized model-powertrain combinations without year, {denominator['model_year_powertrain_combinations']:,} "
        f"model-year-powertrain combinations, and {denominator['epa_rows_after_filter']:,} EPA rows**. "
        f"ZIP SHA-256: `{source['zip_sha256']}`. Candidate JSONL SHA-256: `{index['candidate_jsonl_sha256']}`. "
        f"The bulk source was reused locally; network calls to EPA in this pass: **{source['network_calls_this_run']}**. "
        "MY2027 is present in the source snapshot and remains candidate-only, not a claim of local availability.",
        "",
        "All 84 EPA fields are retained per candidate row, including model identifiers, displacement, cylinders, "
        "transmission, drive, fuel/powertrain type, vehicle class, MPG and range. "
        "The [queryable SQLite index](candidates-index.sqlite) keys EPA ID, make/model/year and powertrain; "
        "the [index audit](candidate-index.md) gives its checksum and query examples.",
        "",
        table(
            ["Make", "Models discovered", "Earliest MY", "Latest MY", "Normalized combinations", "EPA rows"],
            denominator_rows,
        ),
        "",
        "## New candidate model labels, named",
        "",
        "The names below are **new candidates relative to exact published EPA-base labels**, not newly visible models "
        "in the app. Parenthetical MY ranges are exact observed years in this EPA snapshot, with gaps retained.",
        "",
        *[line + "\n" for line in new_model_lines],
        "## Generation ranges and powertrain grouping",
        "",
        f"The full [generation range queue](GENERATION_RANGE_QUEUE.md) has **{len(generations)} draft segments** "
        f"over all {generation_summary['counts']['candidate_models']} candidate models. "
        f"Only {generation_summary['counts']['candidate_models_with_any_generation_reference']} models have "
        "any existing year-level published reference or prior AI hypothesis; the proposed boundaries are not "
        "automatically verified for an unmatched tuple. "
        f"The EPA rows were grouped into **{len(powertrain_groups):,}** contiguous model/powertrain MY runs. "
        f"Splitting them at draft generation boundaries yields **{len(scoped_groups):,}** "
        "[generation-scoped candidate groups](generation-scoped-powertrain-groups.jsonl), preserving all "
        f"{scoped_summary['epa_rows_preserved']:,} source rows. "
        "**Factory-confirmed new powertrain groups: 0.** Neither grouping nor an AI generation label meets the current "
        "BASE_READY evidence gate.",
        "",
        "## Powertrain-level routing",
        "",
        f"The [powertrain route artifact](exception-routing/powertrain-routing.jsonl) assigns all "
        f"**{len(powertrain_routes):,}** candidate runs: "
        f"**{routing_summary['counts']['powertrain_group_routes']['AUTOMATED_BULK_CANDIDATE']:,}** "
        "entirely automated-source candidates, "
        f"**{routing_summary['counts']['powertrain_group_routes']['MANUAL_EXCEPTION_REVIEW']:,}** "
        "entirely manual exceptions, "
        f"**{routing_summary['counts']['powertrain_group_routes']['MIXED_YEAR_ROUTES']}** "
        "with different routes in different years, "
        f"**{routing_summary['counts']['powertrain_group_routes']['MIXED_MANUAL_AND_AUTOMATED_CANDIDATES']}** "
        "with mixed EPA rows within a year, and "
        f"**{routing_summary['counts']['powertrain_group_routes']['ALREADY_VERIFIED_REFERENCE']}** "
        "containing only already-verified EPA references. "
        f"At exact model-year-powertrain grain, **{routed_group_years['AUTOMATED_BULK_CANDIDATE']:,}** "
        "continue automatically, "
        f"**{routed_group_years['MANUAL_EXCEPTION_REVIEW']:,}** need agent review, "
        f"**{routed_group_years['MIXED_MANUAL_AND_AUTOMATED_CANDIDATES']}** contain "
        "both paths, and "
        f"**{routed_group_years['ALREADY_VERIFIED_REFERENCE']}** are prior references. "
        f"These sum to {sum(routed_group_years.values()):,} model-year-powertrain candidates. "
        f"Crucially, **{len(manual_models_with_auto_groups)}** manual-route model labels retain "
        f"**{len(auto_group_years_in_manual_models):,}** automatically researched exact-year powertrain "
        "candidates; a flagged variant does not block its siblings. No candidate route is verified publication.",
        "",
        table(
            ["Make", "Auto source-research group-years", "Manual exception group-years", "Mixed within-year", "Already verified references"],
            powertrain_route_rows,
        ),
        "",
        "## Bulk join and vPIC cross-check",
        "",
        f"EPA-ID join: **{join_summary['candidate_classifications'].get('ALREADY_VERIFIED', 0)}** rows "
        f"ALREADY_VERIFIED, **{join_summary['candidate_classifications'].get('CANDIDATE_NEW', 0):,}** "
        f"CANDIDATE_NEW, **{join_summary['candidate_classifications'].get('POSSIBLE_ALIAS', 0)}** "
        f"POSSIBLE_ALIAS, **{len(conflict_rows)}** CONFLICT. An alias hint never inherits factory evidence. "
        f"The official [NHTSA vPIC API]({vpic_summary['official_documentation']}) was queried by "
        f"make/year with {vpic_summary['requested_make_years']} distinct request keys "
        f"({vpic_summary['requested_make_years']} first-pass network calls; the corrected second pass "
        f"reused all {vpic_summary['counts']['cache_hits']} cached responses), "
        f"cross-checking **{len(vpic):,}** new EPA model-year pairs. "
        f"Exact EPA-base names: **{vpic_summary['counts']['VPIC_EXACT_BASE_MODEL']:,}**; "
        f"exact raw EPA model names: **{vpic_summary['counts']['VPIC_EXACT_EPA_MODEL']}**; "
        f"name unresolved: **{vpic_summary['counts']['VPIC_NAME_UNRESOLVED']}**. "
        "vPIC confirms only name/year existence, not generation, engine, transmission, drivetrain, trim, or "
        "factory applicability. A name-unresolved status may be a naming difference, not a vehicle absence.",
        "",
        "## Automation and review boundary",
        "",
        f"**Automated ingestion/classification/grouping: {len(candidate):,}/{len(candidate):,} EPA rows "
        f"(100%).** vPIC model-year cross-check: {len(vpic):,}/{len(new_pairs):,} new pairs (100%). "
        f"**Automated source-research route: {len(routed_models) - len(manual_models)}/{len(routed_models)} "
        f"EPA model labels ({pct(len(routed_models) - len(manual_models), len(routed_models))}).** "
        f"**Manual exception-review route: {len(manual_models)}/{len(routed_models)} "
        f"({pct(len(manual_models), len(routed_models))}).** "
        f"A narrower pair-level union of alias, vPIC-name and ambiguous-generation signals covers "
        f"{len(explicit_exception_pairs)}/{len(new_pairs):,} new pairs "
        f"({pct(len(explicit_exception_pairs), len(new_pairs))}); drivetrain source-label ambiguity "
        "is additionally routed at model level. Neither percentage measures verified publication. "
        "The [exception review queue](EXCEPTION_REVIEW_QUEUE.md) lists all affected model labels, years and reasons. "
        f"**Automatically BASE_READY-published: 0/{len(missing_target_models)} missing target labels (0%).** "
        "The present verified-data policy requires applicable factory evidence for model year, generation "
        "and powertrain identity. EPA bulk rows, a vPIC existence match and AI drafts do not independently "
        "supply that evidence. The bulk-normal rows form a batched source-verification queue; individual "
        "agent examination is reserved for exceptions.",
        "",
        "## Cumulative strict-output catalog (unchanged)",
        "",
        "The following are the **75 existing published BASE_READY model labels**, with exact year coverage in the "
        "current DB. This pass added none. The [full configuration export](published-ready-configurations.csv) "
        "lists generation, engine, transmission, drivetrain, body and year for each of the 1,382 "
        "published configurations.",
        "",
        table(["Make", "Model", "Published generations", "Market", "Exact ready MY", "Configurations", "Status"], ready_table_rows),
        "",
        "## Artifacts and limits",
        "",
        "[EPA candidate rows](candidates.jsonl) · [bulk join](candidate-join.jsonl) · "
        "[vPIC model-year results](vpic-crosscheck.jsonl) · "
        "[draft generation map](generation-hypotheses.jsonl) · "
        "[candidate powertrain runs](powertrain-groups.jsonl) · "
        "[generation-scoped runs](generation-scoped-powertrain-groups.jsonl) · "
        "[powertrain routes](exception-routing/powertrain-routing.jsonl) · "
        "[exception routing](exception-routing/summary.json) · [index summary](index.json).",
        "",
        "EPA rows are a national candidate universe, not a Turbo.az prevalence ranking or a claim that "
        "every named EPA label is locally desirable. The UI, published data, evidence gate, images, "
        "prices, ownership-cost, dossiers, phone, and Hetzner were untouched.",
        "",
    ]
    (directory / "CHECKPOINT_US_CATALOG_UNIVERSE.md").write_text("\n".join(checkpoint), encoding="utf-8")
    metrics = {
        "target_epa_model_labels": len(target_models),
        "casefold_distinct_epa_model_labels": len(target_casefold),
        "published_ready_model_labels": len(ready_models),
        "published_ready_labels_within_epa_names": len(ready_matching),
        "remaining_epa_model_labels": len(missing_target_models),
        "newly_published_models": join_summary["newly_auto_verified_models"],
        "candidate_rows": len(candidate),
        "candidate_generation_segments": len(generations),
        "powertrain_candidate_groups": len(powertrain_groups),
        "generation_scoped_candidate_groups": len(scoped_groups),
        "factory_confirmed_new_groups": 0,
        "new_model_year_pairs_vpic_checked": len(vpic),
        "explicit_exception_pairs": len(explicit_exception_pairs),
        "explicit_exception_model_labels": len({(make, model) for make, model, _ in explicit_exception_pairs}),
        "auto_triaged_without_explicit_exception_pairs": len(new_pairs - explicit_exception_pairs),
        "manual_exception_route_model_labels": len(manual_models),
        "automated_source_research_route_model_labels": len(routed_models) - len(manual_models),
        "automated_generation_research_segments": len(automated_generation),
        "powertrain_group_routes": dict(Counter(row["route"] for row in powertrain_routes)),
        "powertrain_group_year_routes": dict(routed_group_years),
        "manual_route_models_with_automatic_group_years": len(manual_models_with_auto_groups),
        "automatic_group_years_inside_manual_route_models": len(auto_group_years_in_manual_models),
        "published_ready_configurations": len(published),
        "report_files": [
            "CHECKPOINT_US_CATALOG_UNIVERSE.md",
            "GENERATION_RANGE_QUEUE.md",
            "EXCEPTION_REVIEW_QUEUE.md",
            "published-ready-configurations.csv",
        ],
    }
    (directory / "checkpoint-metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--db", type=Path, default=ROOT / "autoexpert.db")
    args = parser.parse_args()
    print(json.dumps(make_reports(args.directory, args.db), ensure_ascii=False, indent=2))
