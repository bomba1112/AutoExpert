"""Name AI-queue model-years with no confirmed published US configuration."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/VerifiedData/us-base-catalog-07"


def main():
    cumulative = json.loads((OUT / "mass-scale-cumulative.json").read_text(encoding="utf-8"))
    published = {
        (row["make"], row["model"], year)
        for row in cumulative
        for year in row["model_years"]
    }
    comparisons = [
        json.loads(line)
        for line in (OUT / "ai-work/ai-to-epa-comparison.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line
    ]
    bucket = defaultdict(lambda: {"years": set(), "statuses": set(), "hypotheses": 0})
    for row in comparisons:
        key = (row["make"], row["model"], row["model_year"])
        if key in published:
            continue
        item = bucket[(row["make"], row["model"])]
        item["years"].add(row["model_year"])
        item["statuses"].add(row["status"])
        item["hypotheses"] += 1
    gaps = [
        {
            "make": make,
            "model": model,
            "model_years_without_base_ready": sorted(value["years"]),
            "ai_hypotheses_in_these_years": value["hypotheses"],
            "epa_comparison_statuses": sorted(value["statuses"]),
            "publication_eligible": False,
            "reason": "AI target year; exact factory applicability remains unverified",
        }
        for (make, model), value in sorted(bucket.items())
    ]
    (OUT / "mass-scale-year-gaps.json").write_text(
        json.dumps(gaps, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# US base catalog 07 — remaining AI target years without BASE_READY",
        "",
        (
            "These are AI research target years with no confirmed published configuration. "
            "They are not promised model availability; exact annual manufacturer evidence "
            "is still required."
        ),
        "",
        "| Make | Model | Target US model years | Annual hypotheses | EPA comparison states |",
        "|---|---|---|---:|---|",
    ]
    for row in gaps:
        lines.append(
            f"| {row['make']} | {row['model']} | "
            f"{', '.join(map(str, row['model_years_without_base_ready']))} | "
            f"{row['ai_hypotheses_in_these_years']} | "
            f"{', '.join(row['epa_comparison_statuses'])} |"
        )
    (ROOT / "docs/US_BASE_CATALOG_07_YEAR_GAPS.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "named_model_gap_groups": len(gaps),
                "unpublished_model_year_scopes": sum(
                    len(row["model_years_without_base_ready"]) for row in gaps
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
