"""Registry of the US tech-database lines (prompt Appendix A) and their names per source.

One entry per line. Source names are matched with regular expressions because every
source names models differently (EPA `model`, NHTSA products, vPIC Canadian specs,
mycarusermanual.com and carmans.net slugs). Renamed models (Appendix C) are one line of
succession: GLK -> GLC, ML -> GLE, GL -> GLS, Optima -> K5, FX -> QX70, LR2 -> Discovery
Sport. Sport versions (AMG, M, RS, S, N, Type R, SRT ...) are configurations of their line
unless Appendix A lists them as a line (BMW M3, M5, X5 M, X6 M).

Names that a source uses for something that is not one of the lines (Corolla Cross, Grand
Highlander, Equinox EV, EQS SUV, Atlas Cross Sport, Rogue Sport, Range Rover Velar ...)
are excluded on purpose; they appear as proposals in the final report.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# make -> names used by each source
MAKES = {
    "hyundai": {"epa": "Hyundai", "nhtsa": "HYUNDAI", "vpic": "Hyundai", "mcum": "hyundai", "carmans": "hyundai"},
    "kia": {"epa": "Kia", "nhtsa": "KIA", "vpic": "Kia", "mcum": "kia", "carmans": "kia"},
    "toyota": {"epa": "Toyota", "nhtsa": "TOYOTA", "vpic": "Toyota", "mcum": "toyota", "carmans": "toyota"},
    "mercedes-benz": {"epa": "Mercedes-Benz", "nhtsa": "MERCEDES-BENZ", "vpic": "Mercedes-Benz", "mcum": "mercedes", "carmans": "mercedes-benz"},
    "bmw": {"epa": "BMW", "nhtsa": "BMW", "vpic": "BMW", "mcum": "bmw", "carmans": "bmw"},
    "chevrolet": {"epa": "Chevrolet", "nhtsa": "CHEVROLET", "vpic": "Chevrolet", "mcum": "chevrolet", "carmans": "chevrolet"},
    "ford": {"epa": "Ford", "nhtsa": "FORD", "vpic": "Ford", "mcum": "ford", "carmans": "ford"},
    "lexus": {"epa": "Lexus", "nhtsa": "LEXUS", "vpic": "Lexus", "mcum": None, "carmans": "lexus"},
    "honda": {"epa": "Honda", "nhtsa": "HONDA", "vpic": "Honda", "mcum": "honda", "carmans": "honda"},
    "nissan": {"epa": "Nissan", "nhtsa": "NISSAN", "vpic": "Nissan", "mcum": "nissan", "carmans": "nissan"},
    "land-rover": {"epa": "Land Rover", "nhtsa": "LAND ROVER", "vpic": "Land Rover", "mcum": "land-rover", "carmans": "land-rover"},
    "infiniti": {"epa": "Infiniti", "nhtsa": "INFINITI", "vpic": "Infiniti", "mcum": None, "carmans": "infiniti"},
    "cadillac": {"epa": "Cadillac", "nhtsa": "CADILLAC", "vpic": "Cadillac", "mcum": None, "carmans": "cadillac"},
    "jeep": {"epa": "Jeep", "nhtsa": "JEEP", "vpic": "Jeep", "mcum": "jeep", "carmans": "jeep"},
    "audi": {"epa": "Audi", "nhtsa": "AUDI", "vpic": "Audi", "mcum": "audi", "carmans": "audi"},
    "volkswagen": {"epa": "Volkswagen", "nhtsa": "VOLKSWAGEN", "vpic": "Volkswagen", "mcum": "vw", "carmans": "volkswagen"},
    "mitsubishi": {"epa": "Mitsubishi", "nhtsa": "MITSUBISHI", "vpic": "Mitsubishi", "mcum": "mitsubishi", "carmans": "mitsubishi"},
    "tesla": {"epa": "Tesla", "nhtsa": "TESLA", "vpic": "Tesla", "mcum": "tesla", "carmans": "tesla"},
}

# Owner-approved write order (2026-10-02): Hyundai, Kia, Toyota (remaining lines),
# Mercedes-Benz, BMW, Chevrolet, Ford, Lexus, Honda, Nissan, Land Rover, then the rest.
MAKE_ORDER = [
    "hyundai", "kia", "toyota", "mercedes-benz", "bmw", "chevrolet", "ford", "lexus",
    "honda", "nissan", "land-rover", "infiniti", "cadillac", "jeep", "audi", "volkswagen",
    "mitsubishi", "tesla",
]


@dataclass(frozen=True)
class Line:
    make: str
    slug: str
    name: str
    epa_base: tuple[str, ...]
    epa_include: str = r".*"
    epa_exclude: str | None = None
    nhtsa: str = ""
    vpic_ca: str = ""
    mcum: tuple[str, ...] = ()
    carmans: str = ""
    db_models: tuple[str, ...] = ()
    years: tuple[int, int] = (2014, 2026)
    notes: str = ""
    done: bool = False
    extra_epa: tuple[tuple[str, str], ...] = field(default=())

    @property
    def key(self) -> str:
        return f"{self.make}/{self.slug}"


def L(make, slug, name, epa_base, **kw) -> Line:
    if isinstance(epa_base, str):
        epa_base = (epa_base,)
    kw.setdefault("db_models", (name,))
    for k in ("mcum", "db_models"):
        if isinstance(kw.get(k), str):
            kw[k] = (kw[k],)
    return Line(make, slug, name, tuple(epa_base), **kw)


LINES: list[Line] = [
    # Hyundai
    L("hyundai", "sonata", "Sonata", "Sonata", nhtsa=r"SONATA.*", vpic_ca=r"SONATA\b.*",
      carmans=r"hyundai-sonata(-hybrid|-plug-in-hybrid|-n-line)?"),
    L("hyundai", "elantra", "Elantra", "Elantra", nhtsa=r"ELANTRA.*", vpic_ca=r"ELANTRA\b.*",
      carmans=r"hyundai-elantra(-gt|-hybrid|-n|-coupe)?"),
    L("hyundai", "tucson", "Tucson", "Tucson", epa_exclude=r"Fuel Cell", nhtsa=r"TUCSON(?! FUEL CELL).*",
      vpic_ca=r"TUCSON\b(?!.*FUEL CELL).*", mcum="tucson", carmans=r"hyundai-tucson(-hybrid|-plug-in-hybrid)?"),
    L("hyundai", "santa-fe", "Santa Fe", "Santa Fe", epa_exclude=r"^Santa Fe Sport",
      nhtsa=r"SANTA FE(?! SPORT)(?! CRUZ).*", vpic_ca=r"SANTA FE\b(?! SPORT).*", mcum="santa-fe",
      carmans=r"hyundai-santa-fe(-xl|-hybrid|-plug-in-hybrid)?"),
    L("hyundai", "santa-fe-sport", "Santa Fe Sport", "Santa Fe", epa_include=r"^Santa Fe Sport",
      nhtsa=r"SANTA FE SPORT.*", vpic_ca=r"SANTA FE SPORT.*", carmans=r"hyundai-santa-fe-sport",
      years=(2014, 2018)),
    L("hyundai", "accent", "Accent", "Accent", nhtsa=r"ACCENT.*", vpic_ca=r"ACCENT\b.*",
      carmans=r"hyundai-accent", years=(2014, 2022)),
    L("hyundai", "kona", "Kona", "Kona", nhtsa=r"KONA.*", vpic_ca=r"KONA\b.*", mcum="kona",
      carmans=r"hyundai-kona(-electric|-n)?", years=(2018, 2026)),
    # Kia
    L("kia", "optima-k5", "Optima / K5", ("Optima", "K5"), nhtsa=r"(OPTIMA|K5)\b.*",
      vpic_ca=r"(OPTIMA|K5)\b.*", carmans=r"kia-(optima|k5)(-incl-hybrid|-hybrid|-plug-in-hybrid|-phev)?",
      db_models=("Optima", "K5")),
    L("kia", "forte", "Forte", "Forte", nhtsa=r"FORTE.*", vpic_ca=r"FORTE.*",
      carmans=r"kia-forte(5|-koup|-5)?", years=(2014, 2024)),
    L("kia", "rio", "Rio", "Rio", nhtsa=r"RIO\b.*", vpic_ca=r"RIO\b.*", mcum="rio",
      carmans=r"kia-rio(5|-5)?", years=(2014, 2023)),
    L("kia", "sorento", "Sorento", "Sorento", nhtsa=r"SORENTO.*", vpic_ca=r"SORENTO.*", mcum="sorento",
      carmans=r"kia-sorento(-hybrid|-plug-in-hybrid)?"),
    L("kia", "sportage", "Sportage", "Sportage", nhtsa=r"SPORTAGE.*", vpic_ca=r"SPORTAGE.*",
      mcum="sportage", carmans=r"kia-sportage(-hybrid|-plug-in-hybrid)?"),
    # Toyota (Camry done 2026-10-02)
    L("toyota", "camry", "Camry", "Camry", nhtsa=r"CAMRY.*", vpic_ca=r"CAMRY\b.*",
      carmans=r"toyota-camry(-hybrid)?", done=True),
    L("toyota", "corolla", "Corolla", "Corolla", nhtsa=r"(GR )?COROLLA(?! CROSS).*",
      vpic_ca=r"(GR )?COROLLA\b(?! CROSS).*", mcum="corolla",
      carmans=r"toyota-corolla(-hatchback|-hybrid|-im)?"),
    # Prius Prime and RAV4 Prime (later "Plug-in Hybrid") are separate models in the owner-approved
    # storage map (data_work/toyota/SCHEMA_MAP.md section 4); their rows are excluded everywhere.
    L("toyota", "rav4", "RAV4", "RAV4", epa_exclude=r"PHEV|Prime|Plug-in", nhtsa=r"RAV4(?! PRIME)(?! PLUG).*",
      vpic_ca=r"RAV4(?! PRIME)(?!.*PHEV)(?!.*PLUG).*", mcum="rav4", carmans=r"toyota-rav4(-hybrid|-ev)?"),
    L("toyota", "highlander", "Highlander", "Highlander", nhtsa=r"HIGHLANDER(?! GRAND).*",
      vpic_ca=r"HIGHLANDER.*", carmans=r"toyota-highlander(-hybrid)?"),
    L("toyota", "prius", "Prius", ("Prius",), epa_exclude=r"^Prius c\b|PHEV|Plug-in|Prime",
      nhtsa=r"PRIUS(?! C\b)(?! V\b)(?! PRIME)(?! PLUG).*",
      vpic_ca=r"PRIUS\b(?! C\b)(?! V\b)(?! PRIME)(?!.*PLUG).*", mcum="prius", carmans=r"toyota-prius"),
    # Mercedes-Benz
    L("mercedes-benz", "c-class", "C-Class", "C-Class", nhtsa=r"(C-CLASS|C ?\d{2,3}|AMG C ?\d{2}|C\d{2} AMG).*",
      vpic_ca=r"C[ -]CLASS.*", mcum="c-class", carmans=r"mercedes-benz-c-class(-[a-z-]+)?"),
    L("mercedes-benz", "e-class", "E-Class", "E-Class", nhtsa=r"(E-CLASS|E ?\d{3}|AMG E ?\d{2}|E\d{2} AMG).*",
      vpic_ca=r"E[ -]CLASS.*", mcum="e-class", carmans=r"mercedes-benz-e-class(-[a-z-]+)?"),
    L("mercedes-benz", "s-class", "S-Class", "S-Class", nhtsa=r"(S-CLASS|S ?\d{3}|AMG S ?\d{2}|S\d{2} AMG|MAYBACH S).*",
      vpic_ca=r"(S[ -]CLASS|MAYBACH S).*", carmans=r"mercedes-benz-s-class(-[a-z-]+)?"),
    L("mercedes-benz", "gla", "GLA", "GLA-Class", db_models=("GLA-Class",), nhtsa=r"(GLA|AMG GLA).*", vpic_ca=r"GLA\b.*",
      carmans=r"mercedes-benz-gla(-class)?(-[a-z-]+)?", years=(2015, 2026)),
    L("mercedes-benz", "glb", "GLB", "GLB-Class", db_models=("GLB-Class",), nhtsa=r"(GLB|AMG GLB).*", vpic_ca=r"GLB\b.*",
      carmans=r"mercedes-benz-glb(-class)?", years=(2020, 2026)),
    L("mercedes-benz", "glc", "GLC (+GLK)", ("GLC-Class", "GLK-Class"), nhtsa=r"(GLC|GLK|AMG GLC).*",
      vpic_ca=r"(GLC|GLK)\b.*", mcum="glc-class", carmans=r"mercedes-benz-gl[ck](-class)?(-[a-z-]+)?",
      db_models=("GLC-Class", "GLK-Class")),
    L("mercedes-benz", "gle", "GLE (+ML)", ("GLE-Class", "ML-Class"), nhtsa=r"(GLE|ML\b|ML ?\d{3}|M-CLASS|AMG GLE).*",
      vpic_ca=r"(GLE|M[ -]CLASS|ML)\b.*", carmans=r"mercedes-benz-(gle|m-class|ml)(-class)?(-[a-z-]+)?",
      db_models=("GLE-Class", "ML-Class")),
    L("mercedes-benz", "gls", "GLS (+GL)", ("GLS-Class", "GL-Class"), nhtsa=r"(GLS|GL-CLASS|GL ?\d{3}|AMG GLS|MAYBACH GLS).*",
      vpic_ca=r"(GLS|GL[ -]CLASS|GL ?\d{3})\b.*", carmans=r"mercedes-benz-(gls|gl-class)(-class)?(-[a-z-]+)?",
      db_models=("GLS-Class", "GL-Class")),
    L("mercedes-benz", "cla", "CLA", "CLA-Class", db_models=("CLA-Class",), nhtsa=r"(CLA\b|CLA-CLASS|CLA ?\d{2,3}|AMG CLA).*",
      vpic_ca=r"CLA\b.*", carmans=r"mercedes-benz-cla(-class)?(-[a-z-]+)?"),
    L("mercedes-benz", "cls", "CLS", "CLS-Class", db_models=("CLS-Class",), nhtsa=r"(CLS|AMG CLS).*", vpic_ca=r"CLS\b.*",
      carmans=r"mercedes-benz-cls(-class)?(-[a-z-]+)?", years=(2014, 2023)),
    L("mercedes-benz", "cle", "CLE", "CLE-Class", db_models=("CLE-Class",), nhtsa=r"(CLE|AMG CLE).*", vpic_ca=r"CLE\b.*",
      carmans=r"mercedes-benz-cle(-class)?(-[a-z-]+)?", years=(2024, 2026)),
    L("mercedes-benz", "amg-gt-4-door", "AMG GT 4-Door", "AMG GT",
      epa_include=r"^AMG GT (43|53|63)( S)? (4matic Plus|E Performance)$",
      nhtsa=r"(AMG )?GT ?(43|53|63).*(4[- ]?DOOR|4MATIC).*|.*GT.*4[- ]DOOR.*",
      vpic_ca=r"AMG GT.*(4DR|4-DOOR|43|53|63).*", carmans=r"mercedes-(benz-)?amg-gt(-4-door)?(-[a-z-]+)?",
      years=(2019, 2026), notes="2-door AMG GT coupe/roadster is not this line"),
    L("mercedes-benz", "eqs", "EQS", "EQS", epa_exclude=r"\(SUV\)", nhtsa=r"EQS(?!.*SUV).*",
      vpic_ca=r"EQS\b(?!.*SUV).*", carmans=r"mercedes-benz-eqs(?!-suv)(-[a-z-]+)?", years=(2022, 2026),
      notes="EQS SUV excluded (separate model)"),
    L("mercedes-benz", "eqb", "EQB", "EQB", nhtsa=r"EQB.*", vpic_ca=r"EQB\b.*",
      carmans=r"mercedes-benz-eqb", years=(2022, 2025)),
    L("mercedes-benz", "v-class", "V-Class", (), nhtsa=r"V-CLASS.*", vpic_ca=r"V[ -]CLASS.*",
      notes="no V-Class in EPA/vPIC US data; Metris is the US W447 van (proposal only)"),
    # BMW
    L("bmw", "3-series", "3 Series", ("3 Series", "M"), epa_include=r"^(3\d\d|M340i|ActiveHybrid 3)",
      nhtsa=r"(3 SERIES.*|3-SERIES.*|3\d\d[A-Z]*( .*)?|M340I.*|ACTIVEHYBRID 3)",
      vpic_ca=r"3[ -]SERIES.*", mcum="3-series", carmans=r"bmw-3(-series)?(-[a-z-]+)?"),
    L("bmw", "5-series", "5 Series", ("5 Series", "M"), epa_include=r"^(5\d\d|M550i|ActiveHybrid 5)",
      nhtsa=r"(5 SERIES.*|5-SERIES.*|5\d\d[A-Z]*( .*)?|M550I.*|ACTIVEHYBRID 5)",
      vpic_ca=r"5[ -]SERIES.*", mcum="5-series", carmans=r"bmw-5(-series)?(-[a-z-]+)?"),
    L("bmw", "7-series", "7 Series", ("7 Series", "M"), epa_include=r"^(7\d\d|M760i|ActiveHybrid 7|Alpina B7)",
      nhtsa=r"(7 SERIES.*|7-SERIES.*|7\d\d[A-Z]*( .*)?|M760.*|ACTIVEHYBRID 7.*|ALPINA B7.*)",
      vpic_ca=r"7[ -]SERIES.*|ALPINA B7.*", mcum="7-series", carmans=r"bmw-7(-series)?(-[a-z-]+)?"),
    L("bmw", "x5", "X5", "X5", epa_exclude=r"^X5 M( Competition)?$", nhtsa=r"X5(?! ?M\b)(?!M).*",
      vpic_ca=r"X5(?! ?M\b)(?!M).*", mcum="x5", carmans=r"bmw-x5(?!-m)(-[a-z0-9-]+)?"),
    L("bmw", "x6", "X6", "X6", epa_exclude=r"^X6 M( Competition)?$", nhtsa=r"X6(?! ?M\b)(?!M).*",
      vpic_ca=r"X6(?! ?M\b)(?!M).*", mcum="x6", carmans=r"bmw-x6(?!-m)(-[a-z0-9-]+)?"),
    L("bmw", "x7", "X7", "X7", nhtsa=r"X7.*|ALPINA XB7.*", vpic_ca=r"X7.*|ALPINA XB7.*", mcum="x7",
      carmans=r"bmw-x7", years=(2019, 2026)),
    L("bmw", "m3", "M3", "M", epa_include=r"^M3( |$)", nhtsa=r"M3( .*)?", vpic_ca=r"M3\b.*", mcum="m3",
      carmans=r"bmw-m3", years=(2015, 2026)),
    L("bmw", "m5", "M5", "M", epa_include=r"^M5( |$)", nhtsa=r"M5( .*)?", vpic_ca=r"M5\b.*", mcum="m5",
      carmans=r"bmw-m5"),
    L("bmw", "x5-m", "X5 M", ("X5", "M"), epa_include=r"^X5 M( Competition)?$", nhtsa=r"X5 ?M( .*)?",
      vpic_ca=r"X5 ?M\b.*", carmans=r"bmw-x5-m", years=(2015, 2026)),
    L("bmw", "x6-m", "X6 M", ("X6", "M"), epa_include=r"^X6 M( Competition)?$", nhtsa=r"X6 ?M( .*)?",
      vpic_ca=r"X6 ?M\b.*", carmans=r"bmw-x6-m"),
    # Chevrolet
    L("chevrolet", "malibu", "Malibu", "Malibu", nhtsa=r"MALIBU.*", vpic_ca=r"MALIBU.*",
      carmans=r"chevrolet-malibu(-hybrid|-limited)?", years=(2014, 2025)),
    L("chevrolet", "cruze", "Cruze", "Cruze", nhtsa=r"CRUZE.*", vpic_ca=r"CRUZE.*",
      carmans=r"chevrolet-cruze(-limited)?", years=(2014, 2019)),
    L("chevrolet", "equinox", "Equinox", "Equinox", epa_exclude=r"Equinox EV", nhtsa=r"EQUINOX(?! EV).*",
      vpic_ca=r"EQUINOX(?! EV).*", carmans=r"chevrolet-equinox(?!-ev)", notes="Equinox EV excluded (separate model)"),
    L("chevrolet", "trax", "Trax", "Trax", nhtsa=r"TRAX.*", vpic_ca=r"TRAX.*", carmans=r"chevrolet-trax",
      years=(2015, 2026)),
    # Ford
    L("ford", "fusion", "Fusion", "Fusion", nhtsa=r"FUSION.*", vpic_ca=r"FUSION.*", mcum="fusion",
      carmans=r"ford-fusion(-hybrid|-energi)?", years=(2014, 2020)),
    # Lexus
    L("lexus", "es", "ES", "ES", nhtsa=r"ES ?\d{3}.*|ES\b.*", vpic_ca=r"ES ?\d{3}.*|ES\b.*",
      carmans=r"lexus-es(-?\d{3}[a-z]*)?(-hybrid)?"),
    L("lexus", "rx", "RX", "RX", nhtsa=r"RX ?\d{3}.*|RX\b.*", vpic_ca=r"RX ?\d{3}.*|RX\b.*",
      carmans=r"lexus-rx(-?\d{3}[a-z]*)?(-hybrid)?"),
    L("lexus", "nx", "NX", "NX", nhtsa=r"NX ?\d{3}.*|NX\b.*", vpic_ca=r"NX ?\d{3}.*|NX\b.*",
      carmans=r"lexus-nx(-?\d{3}[a-z]*)?(-hybrid)?", years=(2015, 2026)),
    L("lexus", "gx", "GX", "GX", nhtsa=r"GX ?\d{3}.*|GX\b.*", vpic_ca=r"GX ?\d{3}.*|GX\b.*",
      carmans=r"lexus-gx(-?\d{3})?"),
    # Honda
    L("honda", "accord", "Accord", "Accord", nhtsa=r"ACCORD(?! CROSSTOUR).*", vpic_ca=r"ACCORD\b(?!.*CROSSTOUR).*",
      mcum="accord", carmans=r"honda-accord(-hybrid|-sedan|-coupe|-plug-in-hybrid)?"),
    L("honda", "civic", "Civic", "Civic", nhtsa=r"CIVIC.*", vpic_ca=r"CIVIC.*", mcum="civic",
      carmans=r"honda-civic(-[a-z-]+)?"),
    L("honda", "cr-v", "CR-V", "CR-V", nhtsa=r"CR-V.*", vpic_ca=r"CR-V.*", mcum="cr-v",
      carmans=r"honda-cr-?v(-hybrid|-e-fcev)?"),
    # Nissan
    L("nissan", "altima", "Altima", "Altima", nhtsa=r"ALTIMA.*", vpic_ca=r"ALTIMA.*",
      carmans=r"nissan-altima(-sedan|-coupe)?"),
    L("nissan", "sentra", "Sentra", "Sentra", nhtsa=r"SENTRA.*", vpic_ca=r"SENTRA.*",
      carmans=r"nissan-sentra"),
    L("nissan", "rogue", "Rogue", "Rogue", epa_exclude=r"^Rogue Sport", nhtsa=r"ROGUE(?! SPORT).*",
      vpic_ca=r"ROGUE(?! SPORT).*", carmans=r"nissan-rogue(?!-sport)(-select|-hybrid)?",
      notes="Rogue Sport excluded (separate model, EU Qashqai)"),
    L("nissan", "pathfinder", "Pathfinder", "Pathfinder", nhtsa=r"PATHFINDER.*", vpic_ca=r"PATHFINDER.*",
      carmans=r"nissan-pathfinder(-hybrid)?"),
    # Land Rover
    L("land-rover", "range-rover", "Range Rover", "Range Rover",
      epa_include=r"^(New )?Range Rover(?! Sport)(?! Evoque)(?! Velar)",
      nhtsa=r"RANGE ROVER(?! SPORT)(?! EVOQUE)(?! VELAR).*", vpic_ca=r"RANGE ROVER(?! SPORT)(?! EVOQUE)(?! VELAR).*",
      carmans=r"land-rover-range-rover(?!-sport)(?!-evoque)(?!-velar)(-[a-z-]+)?"),
    L("land-rover", "range-rover-sport", "Range Rover Sport", "Range Rover",
      epa_include=r"^(New )?Range Rover Sport", nhtsa=r"RANGE ROVER SPORT.*", vpic_ca=r"RANGE ROVER SPORT.*",
      carmans=r"land-rover-range-rover-sport(-[a-z-]+)?"),
    L("land-rover", "range-rover-evoque", "Range Rover Evoque", ("Range Rover", "Evoque"),
      epa_include=r"^(Range Rover )?Evoque", nhtsa=r"(RANGE ROVER )?EVOQUE.*", vpic_ca=r"(RANGE ROVER )?EVOQUE.*",
      mcum=("evoque",), carmans=r"land-rover-(range-rover-)?evoque(-[a-z-]+)?"),
    L("land-rover", "discovery-sport", "Discovery Sport (+LR2)", ("Discovery", "Discovery Sport", "LR2"),
      epa_include=r"^(Discovery Sport|LR2)", nhtsa=r"(DISCOVERY SPORT|LR2).*", vpic_ca=r"(DISCOVERY SPORT|LR2).*",
      mcum="discovery-sport", carmans=r"land-rover-(discovery-sport|lr2)", db_models=("Discovery Sport", "LR2")),
    # Infiniti
    L("infiniti", "q50", "Q50", "Q50", nhtsa=r"Q50.*", vpic_ca=r"Q50.*", carmans=r"infiniti-q50",
      years=(2014, 2024)),
    L("infiniti", "qx60", "QX60 (+JX)", "QX60", nhtsa=r"(QX60|JX\d*).*", vpic_ca=r"(QX60|JX).*",
      carmans=r"infiniti-(qx60|jx\d*)(-hybrid)?", db_models=("QX60", "JX35")),
    L("infiniti", "fx-qx70", "FX / QX70", "QX70", nhtsa=r"(QX70|FX\d*).*", vpic_ca=r"(QX70|FX).*",
      carmans=r"infiniti-(qx70|fx\d*)", years=(2014, 2017), db_models=("QX70", "FX35", "FX37", "FX50")),
    # Cadillac
    L("cadillac", "cts", "CTS", ("CTS", "CTS-V"), nhtsa=r"CTS.*", vpic_ca=r"CTS.*",
      carmans=r"cadillac-cts(-v|-sedan|-coupe|-wagon)?", years=(2014, 2019)),
    L("cadillac", "srx", "SRX", "SRX", nhtsa=r"SRX.*", vpic_ca=r"SRX.*", carmans=r"cadillac-srx",
      years=(2014, 2016)),
    L("cadillac", "escalade", "Escalade", "Escalade", nhtsa=r"ESCALADE(?! IQ).*", vpic_ca=r"ESCALADE(?! IQ).*",
      carmans=r"cadillac-escalade(-esv)?", notes="Escalade IQ (EV) excluded"),
    # Jeep
    L("jeep", "grand-cherokee", "Grand Cherokee", "Grand Cherokee", nhtsa=r"GRAND CHEROKEE.*",
      vpic_ca=r"GRAND CHEROKEE.*", carmans=r"jeep-grand-cherokee(-l|-4xe|-srt|-trackhawk|-wk)?"),
    L("jeep", "cherokee", "Cherokee", "Cherokee", nhtsa=r"(?<!GRAND )CHEROKEE.*", vpic_ca=r"(?<!GRAND )CHEROKEE.*",
      mcum="cherokee", carmans=r"jeep-cherokee"),
    L("jeep", "compass", "Compass", "Compass", nhtsa=r"COMPASS.*", vpic_ca=r"COMPASS.*",
      carmans=r"jeep-compass"),
    # Audi
    L("audi", "a3", "A3", ("A3", "S3", "RS 3", "RS"), epa_include=r"^(A3|S3|RS ?3)", years=(2015, 2026),
      nhtsa=r"(A3|S3|RS ?3)\b.*", vpic_ca=r"(A3|S3|RS ?3)\b.*", mcum=("a3",), carmans=r"audi-(a3|s3|rs-?3)(-[a-z-]+)?"),
    L("audi", "a4", "A4", ("A4", "S4", "Allroad"), nhtsa=r"(A4|S4|ALLROAD)\b.*", vpic_ca=r"(A4|S4|ALLROAD)\b.*",
      mcum=("a4",), carmans=r"audi-(a4|s4)(-[a-z-]+)?", years=(2014, 2025)),
    L("audi", "a5", "A5", ("A5", "S5", "RS 5", "RS"), epa_include=r"^(A5|S5|RS ?5)",
      nhtsa=r"(A5|S5|RS ?5)\b.*", vpic_ca=r"(A5|S5|RS ?5)\b.*", mcum=("a5",), carmans=r"audi-(a5|s5|rs-?5)(-[a-z-]+)?"),
    L("audi", "a6", "A6", ("A6", "S6", "RS"), epa_include=r"^(A6|S6|RS 6)", nhtsa=r"(A6|S6|RS ?6)\b.*",
      vpic_ca=r"(A6|S6|RS ?6)\b.*", mcum=("a6",), carmans=r"audi-(a6|s6|rs-?6)(-[a-z-]+)?"),
    L("audi", "q3", "Q3", "Q3", nhtsa=r"Q3\b.*", vpic_ca=r"Q3\b.*", mcum=("q3",), carmans=r"audi-q3",
      years=(2015, 2026)),
    L("audi", "q5", "Q5", ("Q5", "SQ5"), nhtsa=r"S?Q5\b.*", vpic_ca=r"S?Q5\b.*", mcum=("q5",),
      carmans=r"audi-s?q5(-[a-z-]+)?"),
    L("audi", "q7", "Q7", ("Q7", "SQ7"), nhtsa=r"S?Q7\b.*", vpic_ca=r"S?Q7\b.*", mcum=("q7",),
      carmans=r"audi-s?q7"),
    # Volkswagen
    L("volkswagen", "jetta", "Jetta", ("Jetta", "GLI"), nhtsa=r"(JETTA|GLI)\b.*", vpic_ca=r"(JETTA|GLI)\b.*",
      mcum="jetta", carmans=r"volkswagen-jetta(-gli|-hybrid|-sportwagen)?"),
    L("volkswagen", "passat", "Passat", "Passat", nhtsa=r"PASSAT.*", vpic_ca=r"PASSAT.*", mcum="passat",
      carmans=r"volkswagen-passat", years=(2014, 2022)),
    L("volkswagen", "tiguan", "Tiguan", "Tiguan", nhtsa=r"TIGUAN.*", vpic_ca=r"TIGUAN.*", mcum="tiguan",
      carmans=r"volkswagen-tiguan(-limited)?"),
    L("volkswagen", "atlas", "Atlas", "Atlas", epa_exclude=r"Cross Sport", nhtsa=r"ATLAS(?! CROSS).*",
      vpic_ca=r"ATLAS(?! CROSS).*", mcum="atlas", carmans=r"volkswagen-atlas(?!-cross)",
      years=(2018, 2026), notes="Atlas Cross Sport excluded (separate model)"),
    L("volkswagen", "arteon", "Arteon", "Arteon", nhtsa=r"ARTEON.*", vpic_ca=r"ARTEON.*", mcum="arteon",
      carmans=r"volkswagen-arteon", years=(2019, 2024)),
    L("volkswagen", "touareg", "Touareg", "Touareg", nhtsa=r"TOUAREG.*", vpic_ca=r"TOUAREG.*", mcum="touareg",
      carmans=r"volkswagen-touareg(-hybrid)?", years=(2014, 2017)),
    # Mitsubishi
    L("mitsubishi", "outlander", "Outlander", "Outlander", epa_exclude=r"^Outlander Sport",
      nhtsa=r"OUTLANDER(?! SPORT).*", vpic_ca=r"OUTLANDER(?! SPORT).*", mcum="outlander",
      carmans=r"mitsubishi-outlander(?!-sport)(-phev)?"),
    L("mitsubishi", "outlander-sport", "Outlander Sport", "Outlander", epa_include=r"^Outlander Sport",
      nhtsa=r"OUTLANDER SPORT.*", vpic_ca=r"OUTLANDER SPORT.*", carmans=r"mitsubishi-outlander-sport"),
    # Tesla
    L("tesla", "model-3", "Model 3", "Model 3", nhtsa=r"MODEL 3.*", vpic_ca=r"MODEL 3.*", mcum="model-3",
      carmans=r"tesla-model-3", years=(2017, 2026)),
    L("tesla", "model-y", "Model Y", "Model Y", nhtsa=r"MODEL Y.*", vpic_ca=r"MODEL Y.*", mcum="model-y",
      carmans=r"tesla-model-y", years=(2020, 2026)),
    L("tesla", "model-s", "Model S", "Model S", nhtsa=r"MODEL S.*", vpic_ca=r"MODEL S.*",
      carmans=r"tesla-model-s"),
    L("tesla", "model-x", "Model X", "Model X", nhtsa=r"MODEL X.*", vpic_ca=r"MODEL X.*",
      carmans=r"tesla-model-x", years=(2016, 2026)),
]

BY_KEY = {line.key: line for line in LINES}


def lines_for(make: str | None = None, include_done: bool = False) -> list[Line]:
    order = {m: i for i, m in enumerate(MAKE_ORDER)}
    selected = [
        line
        for line in LINES
        if (make is None or line.make == make) and (include_done or not line.done)
    ]
    return sorted(selected, key=lambda line: order[line.make])


def epa_line(make: str, base_model: str, model: str) -> Line | None:
    """The line an EPA vehicles.csv row belongs to (make is the EPA make name)."""
    for line in LINES:
        if MAKES[line.make]["epa"] != make or base_model not in line.epa_base:
            continue
        if not re.search(line.epa_include, model):
            continue
        if line.epa_exclude and re.search(line.epa_exclude, model):
            continue
        return line
    return None


def _full(pattern: str, text: str) -> bool:
    return bool(pattern) and re.fullmatch(pattern, text.strip().upper(), re.I) is not None


def nhtsa_line(make_slug: str, model: str) -> Line | None:
    hits = [line for line in LINES if line.make == make_slug and _full(line.nhtsa, model)]
    # The most specific pattern wins when several match (e.g. X5 vs X5 M).
    return max(hits, key=lambda line: len(line.nhtsa)) if hits else None


def vpic_ca_line(make_slug: str, model: str) -> Line | None:
    hits = [line for line in LINES if line.make == make_slug and _full(line.vpic_ca, model)]
    return max(hits, key=lambda line: len(line.vpic_ca)) if hits else None


def carmans_line(post_slug: str) -> tuple[Line, int, str] | None:
    """carmans.net post slug like '2018-toyota-camry' or '2021-kia-optima-incl-hybrid-2'."""
    found = re.fullmatch(r"(\d{4})-([a-z0-9-]+)", post_slug)
    if not found:
        return None
    year = int(found.group(1))
    # A trailing "-2" is usually WordPress' duplicate-slug suffix, but "bmw-3" is a model.
    for rest in (found.group(2), re.sub(r"-\d$", "", found.group(2))):
        rest = re.sub(r"-incl-[a-z-]+$", "", rest)
        hits = [
            line
            for line in LINES
            if line.carmans
            and re.fullmatch(line.carmans, rest)
            and line.years[0] <= year <= line.years[1]
        ]
        if hits:
            return max(hits, key=lambda line: len(line.carmans)), year, rest
    return None
