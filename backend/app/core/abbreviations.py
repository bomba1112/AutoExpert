from __future__ import annotations

from dataclasses import dataclass, field

EXPLANATIONS = {
    "VIN": {
        "ru": "идентификационный номер автомобиля",
        "az": "avtomobilin identifikasiya nömrəsi",
        "en": "vehicle identification number",
    },
    "8AT": {
        "ru": "8-ступенчатая автоматическая коробка передач",
        "az": "8 pilləli avtomatik sürətlər qutusu",
        "en": "8-speed automatic transmission",
    },
    "FWD": {
        "ru": "передний привод",
        "az": "ön ötürücü",
        "en": "front-wheel drive",
    },
    "TSB": {
        "ru": "технический бюллетень производителя",
        "az": "istehsalçının texniki bülleteni",
        "en": "manufacturer technical service bulletin",
    },
    "A25A-FKS": {
        "ru": "заводской код двигателя Toyota 2.5",
        "az": "Toyota 2.5 mühərrikinin zavod kodu",
        "en": "Toyota factory code for the 2.5 engine",
    },
}


@dataclass
class AbbreviationExplainer:
    language: str
    seen: set[str] = field(default_factory=set)

    def render(self, abbreviation: str) -> str:
        if abbreviation in self.seen:
            return abbreviation
        self.seen.add(abbreviation)
        explanation = EXPLANATIONS.get(abbreviation, {}).get(self.language)
        return f"{abbreviation} — {explanation}" if explanation else abbreviation
