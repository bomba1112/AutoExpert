"""English for the server-side user texts (product phase, stage 1).

The services write their texts as (ru, az) pairs; the English of each Russian text is in
en_text.json ({ru: en}), so one table serves every helper (catalog_buyer.tr, us_tech_facts.tr,
fuel_advice). A missing entry is a bug that the completeness test (tests/test_english.py) finds;
at run time it falls back to the Russian text and is logged once.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal

Language = Literal["ru", "az", "en"]
LANGUAGES = ("ru", "az", "en")
_PATH = Path(__file__).with_name("en_text.json")
_missing: set[str] = set()
log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def table() -> dict[str, str]:
    return json.loads(_PATH.read_text(encoding="utf-8")) if _PATH.exists() else {}


def english(ru: str) -> str:
    text = table().get(ru)
    if text is None:
        if ru not in _missing:
            _missing.add(ru)
            log.warning("no English for %r", ru[:80])
        return ru
    return text


def pick(language: str, ru: str, az: str, en: str | None = None) -> str:
    """The text in the language: AZ, EN (given, else from the table), RU otherwise."""
    if language == "az":
        return az
    if language == "en":
        return en if en is not None else english(ru)
    return ru
