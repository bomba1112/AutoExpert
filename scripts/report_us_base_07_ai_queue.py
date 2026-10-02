"""Name AI/EPA review scopes without promoting hypotheses to catalogue facts."""

# ruff: noqa: E501

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/VerifiedData/us-base-catalog-07"
SOURCE = OUT / "ai-work/ai-to-epa-comparison.jsonl"


def main():
    comparisons = [
        json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line
    ]
    grouped = defaultdict(lambda: {"years": set(), "draft_ids": set(), "epa_ids": set()})
    for row in comparisons:
        key = row["make"], row["model"], row["status"]
        grouped[key]["years"].add(row["model_year"])
        grouped[key]["draft_ids"].add(row["draft_id"])
        grouped[key]["epa_ids"].update(row["candidate_ids"])
    records = [
        {
            "make": make,
            "model": model,
            "comparison_status": status,
            "model_years": sorted(value["years"]),
            "annual_hypotheses": sum(
                row["make"] == make and row["model"] == model and row["status"] == status
                for row in comparisons
            ),
            "draft_groups": len(value["draft_ids"]),
            "epa_candidate_ids": sorted(value["epa_ids"]),
            "publication_eligible": False,
            "reason": (
                "EPA paired-field difference requires independent manufacturer review"
                if status == "EPA_PAIR_DIFFERENCE_REVIEW"
                else "EPA cannot resolve this annual hypothesis"
                if status == "EPA_INSUFFICIENT"
                else "EPA partially corroborates fields but cannot verify exact factory joint applicability"
            ),
        }
        for (make, model, status), value in sorted(grouped.items())
    ]
    (OUT / "mass-scale-ai-queue.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# AI draft and EPA comparison queue",
        "",
        "These are research hypotheses, not product vehicles. EPA paired rows alone do not establish OEM generation, trim, body or engine/transmission applicability. Some model-years already have separately published source-backed subsets; the hypotheses below still need independent tuple-level verification.",
        "",
        "| Make | Model | Target US MY | Annual hypotheses | EPA comparison | Reason |",
        "|---|---|---|---:|---|---|",
    ]
    for row in records:
        lines.append(
            f"| {row['make']} | {row['model']} | {', '.join(map(str, row['model_years']))} | "
            f"{row['annual_hypotheses']} | {row['comparison_status']} | {row['reason']} |"
        )
    (OUT / "mass-scale-ai-queue.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "annual_hypotheses": len(comparisons),
                "named_queue_groups": len(records),
                "publication_eligible": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
