"""Owner-defined active catalogue scope, independent of verification and stored history."""

import json
from functools import lru_cache
from pathlib import Path

POLICY_PATH = Path(__file__).resolve().parents[3] / "data/manifests/az-market-priority-policy.json"


@lru_cache(maxsize=4)
def _read_scope(path, modified_ns, size):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def scope_policy():
    stat = POLICY_PATH.stat()
    return _read_scope(str(POLICY_PATH), stat.st_mtime_ns, stat.st_size)


def minimum_year(make, rules=None):
    rules = rules if rules is not None else scope_policy()
    aliases = {k.casefold(): v for k, v in rules.get("make_aliases", {}).items()}
    canonical = aliases.get(str(make).casefold(), make)
    canonical = next(
        (m for m in rules["primary_makes"] if m.casefold() == str(canonical).casefold()), None
    )
    if canonical is None or canonical in rules.get("excluded_makes", []):
        return None
    return rules.get("minimum_model_year_overrides", {}).get(
        canonical, rules.get("minimum_model_year", 2005)
    )


def in_active_scope(make, market, model_year, rules=None):
    rules = rules if rules is not None else scope_policy()
    minimum = minimum_year(make, rules)
    return bool(
        minimum is not None
        and market in rules.get("allowed_markets", ["US"])
        and isinstance(model_year, int)
        and not isinstance(model_year, bool)
        and model_year >= minimum
    )


def catalog_in_active_scope(catalog, rules=None):
    return in_active_scope(
        catalog.get("make"), catalog.get("original_market"), catalog.get("model_year"), rules
    )
