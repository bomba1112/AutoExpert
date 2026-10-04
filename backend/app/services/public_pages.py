# ruff: noqa: E501
"""Public pages by car (product phase, stage 5), behind the public_car_pages flag: a static site
generated from the database, one page per line -> generation -> engine, e.g. "Toyota Camry XV70
2018–2024 2.5L A25A-FKS: known issues, oil & fluids, maintenance schedule, recalls", in English
(main), Russian and Azerbaijani.

Data rules are the card's (us_tech_facts.build): FACT plain, SECONDARY_NOTE marked, OWNER_REPORTS
"owners report", HIDDEN_CONFLICT never, an empty field left out. Values and the source's name only,
never quotations from manuals. Every page: title / description / canonical / hreflang for the
three languages, schema.org Vehicle + FAQPage, a link to add the car to the garage. A sitemap and
robots.txt are written next to the pages; the output folder is what goes to the web server.
"""

from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.core.english import pick
from app.models.catalog import VehicleGeneration, VehicleMake, VehicleModel
from app.models.evidence import TechnicalEvidence

LANGUAGES = ("en", "ru", "az")
FLUID_KEYS = ("engine_oil_viscosity", "engine_oil_specification", "engine_oil_oem_approval", "engine_oil_capacity_l",
              "engine_oil_capacity_drain_refill_l", "transmission_fluid", "transmission_fluid_capacity_l", "coolant",
              "coolant_capacity_l", "brake_fluid", "spark_plug", "octane_aki", "fuel_tank_l")
T = {
    "issues": ("Известные проблемы", "Məlum problemlər", "Known issues"),
    "fluids": ("Масло и жидкости", "Yağ və mayelər", "Oil & fluids"),
    "maintenance": ("Регламент ТО", "Texniki xidmət reqlamenti", "Maintenance schedule"),
    "recalls": ("Отзывные кампании", "Geri çağırma kampaniyaları", "Recalls"),
    "h1_tail": ("известные проблемы, масло и жидкости, регламент ТО, отзывные кампании",
                "məlum problemlər, yağ və mayelər, texniki xidmət, geri çağırmalar",
                "known issues, oil & fluids, maintenance schedule, recalls"),
    "versions": ("Версии", "Versiyalar", "Versions"),
    "sources": ("Источники", "Mənbələr", "Sources"),
    "secondary": ("по данным справочников", "məlumat kitabçalarına görə", "per reference sources"),
    "severe": ("тяжёлые условия", "ağır şərait", "severe conditions"),
    "years": ("годы", "illər", "years"),
    "cta_title": ("Добавьте свою машину в гараж", "Avtomobilinizi qaraja əlavə edin", "Add your car to the garage"),
    "cta_text": ("Auto Expert напомнит о замене масла и жидкостей по регламенту этой машины и сообщит о новых отзывных кампаниях.",
                 "Auto Expert bu avtomobilin reqlamentinə görə yağ və mayelərin dəyişməsini xatırladacaq və yeni geri çağırma kampaniyalarını bildirəcək.",
                 "Auto Expert reminds you about oil and fluid changes by this car's schedule and tells you about new recalls."),
    "cta_button": ("Открыть гараж", "Qarajı aç", "Open the garage"),
    "recall_note": ("Касается ли кампания конкретной машины — проверяется по VIN у дилера; ремонт бесплатный.",
                    "Kampaniyanın konkret avtomobilə aidiyyəti dilerdə VIN üzrə yoxlanılır; təmir pulsuzdur.",
                    "Whether a campaign covers a specific car is checked by VIN at a dealer; the repair is free."),
    "faq": ("Частые вопросы", "Tez-tez verilən suallar", "FAQ"),
    "q_oil": ("Какое масло нужно {car}?", "{car} üçün hansı yağ lazımdır?", "What oil does the {car} take?"),
    "q_issues": ("Какие известные проблемы у {car}?", "{car} hansı məlum problemlərə malikdir?", "What are the known issues of the {car}?"),
    "q_recalls": ("Есть ли отзывные кампании по {car}?", "{car} üzrə geri çağırma kampaniyaları varmı?", "Are there recalls for the {car}?"),
    "home": ("Машины", "Avtomobillər", "Cars"),
    "about": ("Данные — из руководств производителя и официальных баз (EPA, NHTSA); вторичные справочники помечены. Без выдуманных значений.",
              "Məlumatlar istehsalçı təlimatlarından və rəsmi bazalardan (EPA, NHTSA) götürülüb; ikinci dərəcəli mənbələr qeyd olunub. Uydurma dəyər yoxdur.",
              "Data comes from the manufacturers' manuals and official databases (EPA, NHTSA); secondary reference data is marked. No invented values."),
    "description": ("{car}: {n_issues} известных проблем, масло и жидкости, регламент ТО и {n_recalls} отзывных кампаний — по руководствам и данным NHTSA.",
                    "{car}: {n_issues} məlum problem, yağ və mayelər, texniki xidmət və {n_recalls} geri çağırma — təlimatlara və NHTSA məlumatlarına görə.",
                    "{car}: {n_issues} known issues, oil & fluids, maintenance schedule and {n_recalls} recalls — from the manuals and NHTSA data."),
}
LANG_NAMES = {"en": "English", "ru": "Русский", "az": "Azərbaycan"}


def enabled(settings=None) -> bool:
    settings = settings or get_settings()
    if settings.public_car_pages is not None:
        return bool(settings.public_car_pages)
    return settings.environment != "production"


def tt(language: str, key: str, **values) -> str:
    text = pick(language, *T[key])
    return text.format(**values) if values else text


def slug(text) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text or "").lower().replace("+", "plus")).strip("-") or "x"


def esc(text) -> str:
    return html.escape(str(text if text is not None else ""), quote=True)


# --- groups ------------------------------------------------------------------------------------
def engine_label(ident: dict, key: str) -> str:
    parts = []
    if ident.get("displacement_l"):
        parts.append(f"{ident['displacement_l']}L")
    if ident.get("engine_family_key"):
        parts.append(str(ident["engine_family_key"]))
    elif str(ident.get("aspiration") or "").upper() in ("TURBOCHARGED", "SUPERCHARGED"):
        parts.append("Turbo")
    power = "DIESEL" if "-diesel-" in key else str(ident.get("powertrain") or "").upper()
    if power and power not in ("ICE",):
        parts.append({"HEV": "Hybrid", "PHEV": "Plug-in Hybrid", "BEV": "Electric", "DIESEL": "Diesel", "MHEV": "Mild Hybrid"}.get(power, power))
    return " ".join(parts) or "Engine"


def groups(db, makes: set[str] | None = None) -> list[dict]:
    """Pages: (generation, engine) with their configurations."""
    rows = db.execute(select(TechnicalEvidence.configuration_key, TechnicalEvidence.conditions, TechnicalEvidence.year_from,
                             VehicleMake.name, VehicleModel.name, VehicleGeneration.id, VehicleGeneration.code, VehicleGeneration.name)
                      .join(VehicleGeneration, VehicleGeneration.id == TechnicalEvidence.generation_id)
                      .join(VehicleModel, VehicleModel.id == VehicleGeneration.model_id)
                      .join(VehicleMake, VehicleMake.id == VehicleModel.make_id)
                      .where(TechnicalEvidence.fact_key == "configuration")).all()
    out: dict = {}
    for key, cond, year, make, model, gen_id, code, gen_name in rows:
        if makes and make.lower() not in makes:
            continue
        ident = (cond or {}).get("identity") or {}
        engine = engine_label(ident, key or "")
        group = out.setdefault((gen_id, engine), {"make": make, "model": model, "generation": code if code and len(code) <= 12 else (gen_name or ""),
                                                  "generation_id": gen_id, "engine": engine, "configs": []})
        group["configs"].append({"key": key, "year": year, "drive": ident.get("drivetrain"), "transmission": ident.get("epa_transmission")})
    generation_years: dict = defaultdict(set)
    for g in out.values():
        generation_years[g["generation_id"]].update(c["year"] for c in g["configs"])
    for g in out.values():
        years = [c["year"] for c in g["configs"]]
        g["years"] = (min(years), max(years))
        gy = generation_years[g["generation_id"]]
        g["path"] = "/".join([slug(g["make"]), slug(g["model"]), slug(f"{g['generation']} {min(gy)}-{max(gy)}"), slug(g["engine"])])
    return sorted(out.values(), key=lambda g: (g["make"], g["model"], g["years"], g["engine"]))


# --- merging the cards of a page ---------------------------------------------------------------
def _variant(config: dict, all_configs: list[dict]) -> tuple:
    """(year, drive / gearbox) of a configuration; drive and gearbox only when the page has several."""
    rest = []
    if len({c["drive"] for c in all_configs}) > 1 and config["drive"]:
        rest.append(str(config["drive"]))
    if len({c["transmission"] for c in all_configs}) > 1 and config["transmission"]:
        rest.append(str(config["transmission"]))
    return config["year"], " · ".join(rest)


def _applies(variants: list[tuple], all_years: set[int]) -> str | None:
    """"2018–2022 · FWD; 2020–2022 · AWD": years collapsed into ranges per drive / gearbox."""
    by_rest: dict = defaultdict(set)
    for year, rest in variants:
        by_rest[rest].add(year)
    parts = []
    for rest, years in sorted(by_rest.items(), key=lambda kv: (min(kv[1]), kv[0])):
        when = None if years == all_years and len(all_years) > 1 else _years_text(years)
        parts.append(" · ".join(x for x in (when, rest) if x))
    return "; ".join(p for p in parts if p) or None


def _years_text(years: set[int]) -> str:
    ys = sorted(years)
    runs, start = [], ys[0]
    for a, b in zip(ys, ys[1:] + [None], strict=False):
        if b != a + 1:
            runs.append(str(start) if start == a else f"{start}–{a}")
            start = b
    return ", ".join(runs)


def merge(group: dict, cards: dict[str, dict]) -> dict:
    """One page from the cards of its configurations: a value common to all is shown once, a
    different one with the versions it applies to."""
    configs = [c for c in group["configs"] if cards.get(c["key"])]
    fluids: dict = defaultdict(lambda: {"label": None, "values": {}})
    sources: dict = {}
    for c in configs:
        card = cards[c["key"]]
        for category in card["categories"]:
            for row in category["rows"]:
                if row["key"] not in FLUID_KEYS:
                    continue
                entry = fluids[row["key"]]
                entry["label"] = row["label"]
                for v in row["values"]:
                    text = v["value"] + (f" ({v['qualifier']})" if v.get("qualifier") else "")
                    slot = entry["values"].setdefault(text, {"secondary": v.get("secondary"), "variants": [], "years": set()})
                    slot["variants"].append(_variant(c, configs))
                    slot["years"].add(c["year"])
                    if v.get("source"):
                        s = v["source"]
                        sources[(s.get("title"), s.get("publisher"))] = s.get("url")
    fluid_rows = []
    for key in FLUID_KEYS:
        if key not in fluids:
            continue
        entry = fluids[key]
        values = []
        all_years = {c["year"] for c in configs}
        for text, slot in entry["values"].items():
            everywhere = len(slot["variants"]) == len(configs)
            applies = None if everywhere or len(entry["values"]) == 1 else _applies(slot["variants"], all_years)
            values.append({"value": text, "secondary": slot["secondary"], "applies": applies})
        fluid_rows.append({"key": key, "label": entry["label"], "values": values})
    maintenance: dict = {}
    for c in configs:
        for m in cards[c["key"]]["maintenance"]:
            k = (m["job"], m["action"], m.get("interval"), m.get("max_interval"), m.get("severe"), m.get("occurrence"), m.get("service"), m.get("system"))
            item = maintenance.setdefault(k, {**{f: m.get(f) for f in ("job", "action", "interval", "max_interval", "severe", "occurrence", "service", "system", "secondary")},
                                              "years": set()})
            item["years"].add(c["year"])
            if m.get("source"):
                sources[(m["source"].get("title"), m["source"].get("publisher"))] = m["source"].get("url")
    all_years = {c["year"] for c in configs}
    maintenance_rows = [{**m, "years": None if m["years"] == all_years else _years_text(m["years"])}
                        for m in sorted(maintenance.values(), key=lambda m: (m["severe"] or False, m["service"] or "", m["job"], m["interval"] or ""))
                        if m.get("interval") or m.get("system")]
    issues: dict = {}
    recalls: dict = {}
    for c in configs:
        card = cards[c["key"]]
        for w in card["weak_points"]:
            item = issues.setdefault(w["title"], {**{f: w.get(f) for f in ("title", "symptoms", "how_to_check", "note", "severity", "owner_reports")}, "years": set()})
            item["years"].add(c["year"])
        for r in card["campaigns"]:
            item = recalls.setdefault(r["number"], {**{f: r.get(f) for f in ("number", "component", "summary")}, "years": set()})
            item["years"].add(c["year"])
    return {
        "fluids": fluid_rows, "maintenance": maintenance_rows,
        "issues": [{**i, "years": None if i["years"] == all_years else _years_text(i["years"])} for i in issues.values()],
        "recalls": [{**r, "years": _years_text(r["years"])} for r in sorted(recalls.values(), key=lambda r: r["number"], reverse=True)],
        "versions": sorted({cards[c["key"]]["summary"] for c in configs}),
        "sources": sorted((t, p, u) for (t, p), u in sources.items() if t),
        "labels": next(iter(cards.values()))["labels"] if cards else {},
    }


# --- rendering ---------------------------------------------------------------------------------
CSS = """*{box-sizing:border-box}body{margin:0;font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;color:#13202a;background:#f3f6f7}
header,main,footer{max-width:860px;margin:0 auto;padding:16px}header{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
header a{color:#13202a;text-decoration:none;font-weight:700}nav.lang a{margin-left:10px;font-weight:500;color:#167b80}nav.crumbs{font-size:14px;color:#64717b}
nav.crumbs a{color:#167b80}h1{font-size:28px;line-height:1.2;margin:8px 0 6px}h2{font-size:21px;margin:0 0 10px}
section{background:#fff;border:1px solid #dfddd7;border-radius:16px;padding:16px;margin:14px 0}dl{margin:0;display:grid;gap:8px}
dl div{display:grid;grid-template-columns:minmax(140px,1fr) 2fr;gap:10px}dt{color:#64717b}dd{margin:0}small.mark{color:#a85b23;font-size:12px;margin-left:4px}
small.applies{display:block;color:#64717b;font-size:12px}table{width:100%;border-collapse:collapse;font-size:14px}td,th{text-align:left;padding:6px;border-top:1px solid #eee;vertical-align:top}
ul{padding-left:20px;margin:0}li{margin:6px 0}.cta{background:#142735;color:#fff;border:0}.cta a{display:inline-block;background:#167b80;color:#fff;padding:10px 16px;border-radius:10px;text-decoration:none;font-weight:600}
.muted{color:#64717b;font-size:13px}ul.cards{list-style:none;padding:0;display:grid;gap:8px}ul.cards a{display:block;background:#fff;border:1px solid #dfddd7;border-radius:12px;padding:10px 14px;color:#13202a;text-decoration:none}
@media(max-width:560px){dl div{grid-template-columns:1fr}h1{font-size:23px}}"""


def page_url(base: str, language: str, path: str) -> str:
    return f"{base.rstrip('/')}/cars/{language}/{path}/" if path else f"{base.rstrip('/')}/cars/{language}/"


def head(language: str, title: str, description: str, base: str, path: str, ld: list[dict]) -> str:
    alternates = "".join(f'<link rel="alternate" hreflang="{lang}" href="{esc(page_url(base, lang, path))}">' for lang in LANGUAGES)
    alternates += f'<link rel="alternate" hreflang="x-default" href="{esc(page_url(base, "en", path))}">'
    scripts = "".join(f'<script type="application/ld+json">{json.dumps(item, ensure_ascii=False).replace("</", "<\\/")}</script>' for item in ld)
    return (f'<!doctype html><html lang="{language}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f"<title>{esc(title)}</title><meta name=\"description\" content=\"{esc(description)}\"><link rel=\"canonical\" href=\"{esc(page_url(base, language, path))}\">"
            f'{alternates}<link rel="stylesheet" href="/cars/assets/site.css">{scripts}</head><body>')


def top(language: str, path: str, crumbs: list[tuple[str, str]]) -> str:
    langs = "".join(f'<a href="/cars/{lang}/{path + "/" if path else ""}" hreflang="{lang}"{" aria-current=\"page\"" if lang == language else ""}>{lang.upper()}</a>' for lang in LANGUAGES)
    trail = " › ".join(f'<a href="{esc(href)}">{esc(label)}</a>' if href else esc(label) for label, href in crumbs)
    return f'<header><a href="/cars/{language}/">Auto Expert</a><nav class="lang">{langs}</nav></header><main><nav class="crumbs">{trail}</nav>'


def bottom(language: str) -> str:
    return f'</main><footer class="muted">{esc(tt(language, "about"))}</footer></body></html>'


def car_name(group: dict) -> str:
    return f"{group['make']} {group['model']} {group['generation']} {group['years'][0]}–{group['years'][1]} {group['engine']}".replace("  ", " ")


def render_page(group: dict, data: dict, language: str, base: str, app_url: str) -> str:
    car = car_name(group)
    labels = data["labels"] or {}
    secondary = labels.get("secondary") or tt(language, "secondary")
    title = f"{car}: {tt(language, 'h1_tail')}"
    description = tt(language, "description", car=car, n_issues=len(data["issues"]), n_recalls=len(data["recalls"]))
    faq = []
    oil = [r for r in data["fluids"] if r["key"].startswith("engine_oil")]
    if oil:
        faq.append((tt(language, "q_oil", car=car), "; ".join(f"{r['label']}: {', '.join(v['value'] for v in r['values'])}" for r in oil)))
    if data["issues"]:
        faq.append((tt(language, "q_issues", car=car), "; ".join(i["title"] for i in data["issues"][:8])))
    if data["recalls"]:
        faq.append((tt(language, "q_recalls", car=car), "; ".join(f"{r['number']} — {r['component'] or ''}" for r in data["recalls"][:10])))
    ld = [{"@context": "https://schema.org", "@type": "Vehicle", "name": car, "brand": {"@type": "Brand", "name": group["make"]},
           "model": group["model"], "vehicleModelDate": f"{group['years'][0]}", "productionDate": f"{group['years'][0]}/{group['years'][1]}",
           "vehicleEngine": {"@type": "EngineSpecification", "name": group["engine"]}, "url": page_url(base, language, group["path"])}]
    if faq:
        ld.append({"@context": "https://schema.org", "@type": "FAQPage",
                   "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
    parts = [head(language, title, description, base, group["path"], ld),
             top(language, group["path"], [(tt(language, "home"), f"/cars/{language}/"), (group["make"], f"/cars/{language}/{slug(group['make'])}/"),
                                           (group["model"], f"/cars/{language}/{slug(group['make'])}/{slug(group['model'])}/"), (f"{group['generation']} · {group['engine']}", None)]),
             f"<h1>{esc(car)}</h1><p class=\"muted\">{esc(tt(language, 'versions'))}: {esc('; '.join(data['versions']))}</p>"]
    if data["issues"]:
        items = []
        for i in data["issues"]:
            mark = f'<small class="mark">{esc(i["note"])}</small>' if i.get("note") else ""
            years = f'<small class="applies">{esc(tt(language, "years"))}: {esc(i["years"])}</small>' if i.get("years") else ""
            extra = (f"<br>{esc('; '.join(i['symptoms'][:4]))}" if i.get("symptoms") else "") + (f"<br><span class=\"muted\">{esc(i['how_to_check'])}</span>" if i.get("how_to_check") else "")
            items.append(f"<li><strong>{esc(i['title'])}</strong>{mark}{years}{extra}</li>")
        parts.append(f'<section id="issues"><h2>{esc(tt(language, "issues"))}</h2><ul>{"".join(items)}</ul></section>')
    if data["fluids"]:
        rows = []
        for r in data["fluids"]:
            values = "".join(f"<div>{esc(v['value'])}{f'<small class=\"mark\">{esc(secondary)}</small>' if v.get('secondary') else ''}"
                             f"{f'<small class=\"applies\">{esc(v['applies'])}</small>' if v.get('applies') else ''}</div>" for v in r["values"])
            rows.append(f"<div><dt>{esc(r['label'])}</dt><dd>{values}</dd></div>")
        parts.append(f'<section id="fluids"><h2>{esc(tt(language, "fluids"))}</h2><dl>{"".join(rows)}</dl></section>')
    if data["maintenance"]:
        rows = []
        for m in data["maintenance"]:
            what = " · ".join(str(x) for x in (m["job"], m["action"], m.get("occurrence"), m.get("service")) if x)
            when = " · ".join(str(x) for x in (m.get("interval"), m.get("max_interval") and f"≤ {m['max_interval']}", m.get("system")) if x)
            notes = " · ".join(x for x in (tt(language, "severe") if m.get("severe") else None, m.get("years"), secondary if m.get("secondary") else None) if x)
            rows.append(f"<tr><td>{esc(what)}</td><td>{esc(when)}{f'<small class=\"applies\">{esc(notes)}</small>' if notes else ''}</td></tr>")
        parts.append(f'<section id="maintenance"><h2>{esc(tt(language, "maintenance"))}</h2><table><tbody>{"".join(rows)}</tbody></table></section>')
    if data["recalls"]:
        items = "".join(_recall_item(r) for r in data["recalls"])
        parts.append(f'<section id="recalls"><h2>{esc(tt(language, "recalls"))}</h2><ul>{items}</ul><p class="muted">{esc(tt(language, "recall_note"))}</p></section>')
    if faq:
        parts.append(f'<section id="faq"><h2>{esc(tt(language, "faq"))}</h2>' + "".join(f"<h3>{esc(q)}</h3><p>{esc(a)}</p>" for q, a in faq) + "</section>")
    parts.append(f'<section class="cta"><h2>{esc(tt(language, "cta_title"))}</h2><p>{esc(tt(language, "cta_text"))}</p>'
                 f'<a href="{esc(app_url.rstrip("/") + "/#/garage-add")}">{esc(tt(language, "cta_button"))}</a></section>')
    if data["sources"]:
        parts.append(f'<section id="sources"><h2>{esc(tt(language, "sources"))}</h2><ul class="muted">'
                     + "".join(f"<li>{esc(t)}{' · ' + esc(p) if p else ''}</li>" for t, p, _u in data["sources"]) + "</ul></section>")
    parts.append(bottom(language))
    return "".join(parts)


def _recall_item(r: dict) -> str:
    summary = f'<br><span class="muted">{esc(r["summary"])}</span>' if r.get("summary") else ""
    return f'<li><strong>{esc(r["number"])}</strong> · {esc(r["component"] or "")} <small class="applies">{esc(r["years"])}</small>{summary}</li>'


def render_index(language: str, base: str, path: str, title: str, crumbs: list, links: list[tuple[str, str]]) -> str:
    items = "".join(f'<li><a href="{esc(href)}">{esc(label)}</a></li>' for label, href in links)
    return head(language, f"{title} — Auto Expert", title, base, path, []) + top(language, path, crumbs) + f'<h1>{esc(title)}</h1><ul class="cards">{items}</ul>' + bottom(language)


def write_site(out: Path, pages: list[tuple[dict, dict[str, dict]]], base: str, app_url: str) -> dict:
    """pages: (group, {language: merged data}). Writes the pages, indexes, sitemap and robots."""
    (out / "cars" / "assets").mkdir(parents=True, exist_ok=True)
    (out / "cars" / "assets" / "site.css").write_text(CSS, encoding="utf-8")
    urls = []
    tree: dict = defaultdict(lambda: defaultdict(list))
    written = 0
    for group, by_language in pages:
        if not any(by_language[lang][k] for lang in by_language for k in ("issues", "fluids", "maintenance", "recalls")):
            continue  # nothing to show: no page
        for language, data in by_language.items():
            target = out / "cars" / language / group["path"] / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(render_page(group, data, language, base, app_url), encoding="utf-8")
            written += 1
        urls.append(group["path"])
        tree[group["make"]][group["model"]].append(group)
    for language in LANGUAGES:
        home = tt(language, "home")
        makes = sorted(tree)
        (out / "cars" / language).mkdir(parents=True, exist_ok=True)
        (out / "cars" / language / "index.html").write_text(render_index(language, base, "", home, [(home, None)],
                                                                          [(m, f"/cars/{language}/{slug(m)}/") for m in makes]), encoding="utf-8")
        for make in makes:
            path = slug(make)
            (out / "cars" / language / path).mkdir(parents=True, exist_ok=True)
            (out / "cars" / language / path / "index.html").write_text(render_index(
                language, base, path, make, [(home, f"/cars/{language}/"), (make, None)],
                [(model, f"/cars/{language}/{path}/{slug(model)}/") for model in sorted(tree[make])]), encoding="utf-8")
            for model, groups_ in tree[make].items():
                mpath = f"{path}/{slug(model)}"
                (out / "cars" / language / mpath).mkdir(parents=True, exist_ok=True)
                (out / "cars" / language / mpath / "index.html").write_text(render_index(
                    language, base, mpath, f"{make} {model}", [(home, f"/cars/{language}/"), (make, f"/cars/{language}/{path}/"), (model, None)],
                    [(car_name(g), f"/cars/{language}/{g['path']}/") for g in sorted(groups_, key=lambda g: (g["years"], g["engine"]))]), encoding="utf-8")
                urls.append(mpath)
            urls.append(path)
    urls.append("")
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for path in urls:
        alts = "".join(f'<xhtml:link rel="alternate" hreflang="{lang}" href="{esc(page_url(base, lang, path))}"/>' for lang in LANGUAGES)
        for language in LANGUAGES:
            sitemap.append(f"<url><loc>{esc(page_url(base, language, path))}</loc>{alts}</url>")
    sitemap.append("</urlset>")
    (out / "cars" / "sitemap.xml").write_text("\n".join(sitemap), encoding="utf-8")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /cars/\nSitemap: {base.rstrip('/')}/cars/sitemap.xml\n", encoding="utf-8")
    return {"pages": written, "urls": len(urls) * len(LANGUAGES)}
