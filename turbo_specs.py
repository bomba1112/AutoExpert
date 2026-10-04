#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
turbo.az -> техническая таблица по китайским авто (Auto Expert)

Проходит по ссылкам объявлений и собирает:
  марка, модель, год, цена (в AZN), пробег,
  объём двигателя, ёмкость батареи (кВт·ч), мощность (л.с.),
  тип силовой установки (бензин / гибрид / plug-in гибрид / электро),
  коробка, привод, кузов, рынок сборки, ссылка.

Результат: turbo_specs.csv (открывается в Excel) и turbo_specs.json
Запуск:    python turbo_specs.py
"""

from __future__ import annotations

import csv
import json
import re
import time

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ------------------------------- НАСТРОЙКИ -----------------------------------
BUDGET_AZN = 44000
USD_TO_AZN = 1.70      # манат привязан к доллару
EUR_TO_AZN = 1.95      # приблизительно, при необходимости поправь
REQUEST_DELAY = 1.5
TIMEOUT = 20
OUT_CSV = "turbo_specs.csv"
OUT_JSON = "turbo_specs.json"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

URLS = """
https://turbo.az/autos/10612950-changan-cs-75-pro
https://turbo.az/autos/10536975-changan-cs-75-plus
https://turbo.az/autos/10323535-lynk-co-900
https://turbo.az/autos/10440730-zeekr-001
https://turbo.az/autos/10650770-changan-cs-55-plus
https://turbo.az/autos/10588616-changan-qiyuan-q07
https://turbo.az/autos/10744031-changan-uni-v
https://turbo.az/autos/10741004-byd-leopard-7
https://turbo.az/autos/10017220-byd-destroyer-05
https://turbo.az/autos/10738747-byd-qin-plus
https://turbo.az/autos/10604255-byd-qin-plus
https://turbo.az/autos/10652522-byd-song-plus-dm-i
https://turbo.az/autos/10724400-changan-qiyuan-a05
https://turbo.az/autos/10743833-changan-eado
https://turbo.az/autos/10730684-changan-qiyuan-a06
https://turbo.az/autos/10747015-changan-deepal-s07
https://turbo.az/autos/10736390-changan-nevo-a05
https://turbo.az/autos/10076984-changan-deepal-s07
https://turbo.az/autos/10315170-changan-qiyuan-a06r
https://turbo.az/autos/9741620-changan-deepal-s09
https://turbo.az/autos/10727942-changan-nevo-q06
https://turbo.az/autos/10675073-changan-qiyuan-q07
https://turbo.az/autos/10738355-changan-uni-z
https://turbo.az/autos/10547402-zeekr-8x
https://turbo.az/autos/10330527-zeekr-x
https://turbo.az/autos/10482266-toyota-corolla-cross
https://turbo.az/autos/10603959-changan-cs-55-plus
https://turbo.az/autos/10667087-changan-cs-75-plus
"""

# Подписи полей на turbo.az (азербайджанский) -> ключ в таблице
LABELS = {
    "Şəhər": "city",
    "Marka": "make",
    "Model": "model",
    "Buraxılış ili": "year",
    "Ban növü": "body",
    "Rəng": "color",
    "Mühərrik": "engine_raw",
    "Yürüş": "mileage_raw",
    "Sürətlər qutusu": "gearbox",
    "Ötürücü": "drive",
    "Yeni": "is_new",
    "Vəziyyəti": "condition",
    "Hansı bazar üçün yığılıb": "market",
}

# Перевод значений на русский (для удобства чтения)
FUEL_RU = {
    "Benzin": "Бензин", "Dizel": "Дизель", "Hibrid": "Гибрид",
    "Plug-in Hibrid": "Plug-in гибрид (PHEV)", "Elektro": "Электро",
    "Qaz": "Газ",
}
GEARBOX_RU = {
    "Avtomat": "Автомат", "Mexaniki": "Механика", "Robotlaşdırılmış": "Робот",
    "Variator": "Вариатор/E-CVT", "Reduktor": "Редуктор",
}
DRIVE_RU = {"Ön": "Передний", "Arxa": "Задний", "Tam": "Полный"}
MARKET_RU = {"Çin": "Китай", "Amerika": "США", "Avropa": "Европа",
             "Koreya": "Корея", "Yaponiya": "Япония", "Rəsmi diler": "Официальный дилер",
             "Rusiya": "Россия", "BƏƏ": "ОАЭ", "Digər": "Другое"}

PRICE_RE = re.compile(r"qiyməti\s*([\d\s]+?)\s*(AZN|USD|EUR)", re.IGNORECASE)
PRICE_FALLBACK_RE = re.compile(r"([\d][\d\s]{2,})\s*(₼|AZN|\$|USD|€|EUR)")


# ------------------------------- ЛОГИКА --------------------------------------
def make_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=1.5,
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=["GET"])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": UA, "Accept-Language": "az,ru;q=0.8"})
    return s


def unique_urls(block: str) -> list[str]:
    seen, out = set(), []
    for line in block.split():
        u = line.strip()
        if u.startswith("http") and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def parse_engine(raw: str) -> dict:
    """'1.5 L / 18.3 kWh / 331 a.g. / Plug-in Hibrid' -> поля"""
    res = {"engine_l": None, "battery_kwh": None, "hp": None, "fuel": None}
    if not raw:
        return res
    for part in [p.strip() for p in raw.split("/")]:
        if m := re.fullmatch(r"([\d.]+)\s*L", part):
            res["engine_l"] = float(m.group(1))
        elif m := re.fullmatch(r"([\d.]+)\s*kWh", part, re.IGNORECASE):
            res["battery_kwh"] = float(m.group(1))
        elif m := re.fullmatch(r"(\d+)\s*a\.?\s*g\.?", part):
            res["hp"] = int(m.group(1))
        elif part:
            res["fuel"] = part
    return res


def parse_price(title: str, page_text: str) -> tuple[int | None, str | None]:
    m = PRICE_RE.search(title or "") or PRICE_FALLBACK_RE.search(page_text or "")
    if not m:
        return None, None
    amount = int(re.sub(r"\s", "", m.group(1)))
    cur = {"₼": "AZN", "$": "USD", "€": "EUR"}.get(m.group(2), m.group(2).upper())
    return amount, cur


def to_azn(amount: int | None, cur: str | None) -> int | None:
    if amount is None:
        return None
    rate = {"AZN": 1, "USD": USD_TO_AZN, "EUR": EUR_TO_AZN}.get(cur, 1)
    return int(round(amount * rate))


def extract_props(soup: BeautifulSoup) -> dict:
    props: dict[str, str] = {}
    # 1) Основная разметка turbo.az
    for item in soup.select(".product-properties__i"):
        name = item.select_one(".product-properties__i-name")
        val = item.select_one(".product-properties__i-value")
        if name and val:
            label = name.get_text(" ", strip=True)
            if label in LABELS:
                props[LABELS[label]] = val.get_text(" ", strip=True)
    if len(props) >= 5:
        return props
    # 2) Запасной вариант: ищем подпись и берём соседний элемент
    for s in soup.find_all(string=True):
        label = s.strip()
        key = LABELS.get(label)
        if not key or key in props:
            continue
        el = s.parent
        sib = el.find_next_sibling()
        value = sib.get_text(" ", strip=True) if sib else ""
        if not value and el.parent:
            value = el.parent.get_text(" ", strip=True).replace(label, "", 1).strip()
        if value:
            props[key] = value
    return props


def scrape(session: requests.Session, url: str) -> dict:
    r = session.get(url, timeout=TIMEOUT)
    if r.status_code == 404:
        return {"url": url, "error": "объявление удалено"}
    r.raise_for_status()
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, "lxml")

    title = soup.title.get_text(strip=True) if soup.title else ""
    h1 = soup.find("h1")
    props = extract_props(soup)
    eng = parse_engine(props.get("engine_raw", ""))
    amount, cur = parse_price(title, soup.get_text(" ", strip=True))
    price_azn = to_azn(amount, cur)
    mileage = re.sub(r"\D", "", props.get("mileage_raw", "")) or None

    return {
        "make": props.get("make"),
        "model": props.get("model"),
        "title": h1.get_text(" ", strip=True) if h1 else title,
        "year": int(props["year"]) if props.get("year", "").isdigit() else None,
        "price": amount,
        "currency": cur,
        "price_azn": price_azn,
        "under_budget": (price_azn is not None and price_azn <= BUDGET_AZN),
        "mileage_km": int(mileage) if mileage else None,
        "engine_l": eng["engine_l"],
        "battery_kwh": eng["battery_kwh"],
        "hp": eng["hp"],
        "fuel": FUEL_RU.get(eng["fuel"], eng["fuel"]),
        "gearbox": GEARBOX_RU.get(props.get("gearbox"), props.get("gearbox")),
        "drive": DRIVE_RU.get(props.get("drive"), props.get("drive")),
        "body": props.get("body"),
        "market": MARKET_RU.get(props.get("market"), props.get("market")),
        "engine_raw": props.get("engine_raw"),
        "url": url,
    }


def main():
    session = make_session()
    urls = unique_urls(URLS)
    rows = []
    for i, url in enumerate(urls, 1):
        try:
            row = scrape(session, url)
        except Exception as e:
            row = {"url": url, "error": str(e)}
        rows.append(row)
        print(f"[{i}/{len(urls)}] {row.get('make') or ''} {row.get('model') or ''} "
              f"| {row.get('price_azn') or row.get('error', '?')}")
        time.sleep(REQUEST_DELAY)

    ok = [r for r in rows if "error" not in r]
    ok.sort(key=lambda r: (not r["under_budget"], r["price_azn"] or 10**9))
    failed = [r for r in rows if "error" in r]

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(ok + failed, f, ensure_ascii=False, indent=2)

    cols = [("До 44k", "under_budget"), ("Марка", "make"), ("Модель", "model"),
            ("Год", "year"), ("Цена AZN", "price_azn"), ("Пробег км", "mileage_km"),
            ("Тип", "fuel"), ("Двигатель л", "engine_l"), ("Батарея кВт·ч", "battery_kwh"),
            ("Мощность л.с.", "hp"), ("Коробка", "gearbox"), ("Привод", "drive"),
            ("Кузов", "body"), ("Рынок сборки", "market"), ("Ссылка", "url")]
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")   # ';' — Excel в RU/AZ локали откроет по колонкам
        w.writerow([c[0] for c in cols])
        for r in ok:
            budget_mark = "ДА" if r["under_budget"] else ""
            w.writerow([budget_mark] +
                       [("" if r.get(k) is None else r.get(k)) for _, k in cols[1:]])
        for r in failed:
            w.writerow(["ОШИБКА"] + [""] * (len(cols) - 2) + [r["url"]])

    under = sum(1 for r in ok if r["under_budget"])
    print(f"\nГотово: {len(ok)} объявлений, из них до {BUDGET_AZN} AZN: {under}. "
          f"Ошибок: {len(failed)} -> {OUT_CSV}")


if __name__ == "__main__":
    main()
