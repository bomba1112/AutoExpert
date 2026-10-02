"""Resolve a source-specific lookup label against vPIC and the same-year EPA source row."""

from app.services.knowledge_import import normalized


def source_model(make, family, year, models, catalog):
    values = [r for r in models if normalized(r.get("Make_Name", "")) == normalized(make)]
    same_year = [
        c
        for c in catalog
        if normalized(c["make"]) == normalized(make)
        and normalized(c["model"]) == normalized(family)
        and c["model_year"] == year
        and c["original_market"] == "US"
    ]
    direct = [r for r in values if normalized(r.get("Model_Name", "")) == normalized(family)]
    if direct:
        return {
            "make": direct[0]["Make_Name"],
            "model": direct[0]["Model_Name"],
            "basis": "EXACT_OFFICIAL_MODEL_NAME",
            "catalog_external_key": None,
        }
    candidates = []
    for c in same_year:
        label = normalized(c["configuration"])
        for r in values:
            model = normalized(r.get("Model_Name", ""))
            if model and (label == model or label.startswith(model + " ")):
                candidates.append((-len(model), c["external_key"], r))
    if not candidates:
        return None
    _, key, matched = sorted(candidates, key=lambda x: (x[0], x[1]))[0]
    return {
        "make": matched["Make_Name"],
        "model": matched["Model_Name"],
        "basis": "VPIC_LABEL_PRESENT_IN_SAME_YEAR_OFFICIAL_CONFIGURATION",
        "catalog_external_key": key,
    }
