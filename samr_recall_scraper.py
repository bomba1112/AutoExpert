#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAMR vehicle-recall scraper for Auto Expert
Источник: https://www.samr.gov.cn/zlfzj/qxcpzh/zhdt/  (召回动态 — лента отзывов)
Официально, бесплатно, HTML отдаётся сервером, без API-ключа.

Собирает отзывные кампании по КИТАЙСКИМ легковым брендам:
  производитель + модели (из заголовка), номер(а) отзыва, кол-во машин,
  описание дефекта, дата публикации, ссылка на первоисточник.

Результат: samr_recalls.json (UTF-8) и samr_recalls.csv

Установка (один раз):
    pip install requests beautifulsoup4 lxml
Запуск:
    python samr_recall_scraper.py
"""

from __future__ import annotations

import csv
import json
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ------------------------------- НАСТРОЙКИ -----------------------------------
BASE = "https://www.samr.gov.cn"
# 缺陷产品召回 — список последних отзывов отдаётся прямо в HTML.
# (Страница zhdt/index.html грузит список через JavaScript — её не используем.)
LIST_PATH = "/zlfzj/qxcpzh/index.html"
PAGES = 1              # у этой страницы нет пагинации index_N
FETCH_DETAILS = True   # открывать карточку отзыва (номер / кол-во / текст дефекта)
KEEP_COMMERCIAL = False  # False = только легковые (грузовики/автобусы/мото отбрасываем)
REQUEST_DELAY = 1.0    # пауза между запросами, сек (вежливость к серверу)
TIMEOUT = 20
OUT_JSON = "samr_recalls.json"
OUT_CSV = "samr_recalls.csv"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Китайское имя (суб)бренда -> латиница. Заголовок матчится по ключам.
TARGET_BRANDS = {
    "比亚迪": "BYD", "腾势": "Denza", "仰望": "Yangwang", "方程豹": "Fangchengbao",
    "吉利": "Geely", "领克": "Lynk & Co", "极氪": "Zeekr", "银河": "Geely Galaxy",
    "奇瑞": "Chery", "捷途": "Jetour", "星途": "Exeed", "欧萌达": "OMODA",
    "iCAR": "iCAR", "风云": "Chery Fengyun",
    "长城": "Great Wall", "哈弗": "Haval", "坦克": "Tank", "欧拉": "Ora", "魏牌": "Wey",
    "长安": "Changan", "深蓝": "Deepal", "启源": "Qiyuan", "阿维塔": "Avatr", "欧尚": "Oshan",
    "江淮": "JAC",
    "名爵": "MG", "荣威": "Roewe", "上汽": "SAIC", "大通": "Maxus",
    "广汽": "GAC", "传祺": "Trumpchi", "埃安": "Aion",
    "东风": "Dongfeng", "岚图": "Voyah",
    "蔚来": "NIO", "小鹏": "XPeng", "理想": "Li Auto", "零跑": "Leapmotor",
    "哪吒": "Neta", "小米": "Xiaomi", "五菱": "Wuling", "宝骏": "Baojun",
}

COMMERCIAL_MARKERS = ("货车", "客车", "运输车", "自卸", "商用车", "牵引车", "专用车", "挂车")
MOTORCYCLE_MARKERS = ("摩托车",)

# Совместные предприятия с иностранцами: это НЕ китайские бренды
# (上汽通用 = Cadillac/Buick/Chevrolet, 广汽丰田 = Toyota и т.д.).
# Префикс вырезается из заголовка ДО поиска бренда, поэтому
# 上汽通用五菱 -> остаётся 五菱 -> Wuling (корректно, это китайский бренд).
JV_PREFIXES = (
    "上汽通用", "上汽大众", "上汽斯柯达",
    "广汽丰田", "广汽本田", "广汽三菱", "广汽菲克", "广汽讴歌",
    "东风日产", "东风本田", "东风悦达起亚", "东风标致", "东风雪铁龙", "东风英菲尼迪",
    "长安福特", "长安马自达", "长安铃木",
)

RECALL_NO_RE = re.compile(r"召回编号[:：]?\s*([A-Z0-9]+)")
# Варианты SAMR: 共计58026辆 / 共390,435辆 / 合计1.2万辆 / 涉及车辆686台 / 共计约3万余辆
UNITS_RE = re.compile(
    r"(?:共计|合计|总计|涉及车辆|涉及|共)\s*约?\s*([\d][\d,，.]*)\s*(万)?\s*余?\s*(?:辆|台)"
)
DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})")

BODY_SELECTORS = [
    "div.article", "div#content", "div.content", "div.view",
    "div.TRS_Editor", "div.trs_editor_view", "div#zoom", "div.article-content",
]


# ------------------------------- ЛОГИКА --------------------------------------
def make_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=1.5,
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=["GET"])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"})
    return s


def get_soup(session: requests.Session, url: str) -> BeautifulSoup:
    r = session.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    r.encoding = "utf-8"
    return BeautifulSoup(r.text, "lxml")


def parse_units(text: str) -> int | None:
    total = 0
    for num, wan in UNITS_RE.findall(text):
        n = num.replace(",", "").replace("，", "").rstrip(".")
        try:
            val = float(n) * (10000 if wan else 1)
        except ValueError:
            continue
        total += int(round(val))
    return total or None


def classify(title: str):
    clean = title
    for jv in JV_PREFIXES:
        clean = clean.replace(jv, "")
    brands = sorted({latin for cn, latin in TARGET_BRANDS.items() if cn in clean})
    if "进口" in title and "国产" in title:
        origin = "both"
    elif "进口" in title:
        origin = "import"
    elif "国产" in title:
        origin = "domestic"
    else:
        origin = "unknown"
    is_moto = any(m in title for m in MOTORCYCLE_MARKERS)
    is_comm = any(m in title for m in COMMERCIAL_MARKERS)
    return brands, origin, is_moto, is_comm


def list_urls(pages: int):
    urls = [urljoin(BASE, LIST_PATH)]
    base_dir = LIST_PATH.rsplit("/", 1)[0]          # /zlfzj/qxcpzh/zhdt
    for i in range(1, pages):
        urls.append(urljoin(BASE, f"{base_dir}/index_{i}.html"))
    return urls


def find_date_near(a) -> str | None:
    li = a.find_parent("li")
    if li:
        m = DATE_RE.search(li.get_text(" ", strip=True))
        if m:
            return m.group(1)
        nxt = li.find_next_sibling()
        if nxt:
            m = DATE_RE.search(nxt.get_text(" ", strip=True))
            if m:
                return m.group(1)
    return None


def scrape_list(session: requests.Session, pages: int):
    items: dict[str, dict] = {}
    for url in list_urls(pages):
        try:
            soup = get_soup(session, url)
        except Exception as e:
            print(f"[skip] {url}: {e}")
            continue
        before = len(items)
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            text = a.get_text(strip=True)
            full = urljoin(url, href)
            if "/zhdt/art/" not in full or not text or "召回" not in text:
                continue
            items.setdefault(full, {
                "title": text, "url": full, "list_date": find_date_near(a),
            })
        print(f"[list] {url}: +{len(items) - before} (всего {len(items)})")
        time.sleep(REQUEST_DELAY)
    return list(items.values())


def meta(soup: BeautifulSoup, name: str) -> str | None:
    tag = soup.find("meta", attrs={"name": name})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return None


def extract_body(soup: BeautifulSoup) -> str | None:
    for sel in BODY_SELECTORS:
        node = soup.select_one(sel)
        if node:
            t = node.get_text("\n", strip=True)
            if len(t) > 80:
                return t
    ps = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    ps = [p for p in ps if len(p) > 20]
    return "\n".join(ps) if ps else None


def fetch_detail(session: requests.Session, url: str) -> dict:
    soup = get_soup(session, url)
    text = soup.get_text("\n", strip=True)
    return {
        "pub_date": meta(soup, "PubDate") or meta(soup, "MakeTime"),
        "content_source": meta(soup, "ContentSource"),
        "keywords": meta(soup, "Keywords"),
        "recall_numbers": sorted(set(RECALL_NO_RE.findall(text))),
        "affected_units_total": parse_units(text),
        "body": extract_body(soup) or meta(soup, "Description") or "",
    }


def main():
    session = make_session()
    raw = scrape_list(session, PAGES)

    results = []
    for it in raw:
        brands, origin, is_moto, is_comm = classify(it["title"])
        if is_moto:
            continue
        if is_comm and not KEEP_COMMERCIAL:
            continue
        if not brands:                     # только целевые китайские бренды
            continue
        rec = {**it, "brands": brands, "origin": origin}
        if FETCH_DETAILS:
            try:
                rec.update(fetch_detail(session, it["url"]))
            except Exception as e:
                rec["detail_error"] = str(e)
            time.sleep(REQUEST_DELAY)
        results.append(rec)

    results.sort(key=lambda r: (r.get("pub_date") or r.get("list_date") or ""),
                 reverse=True)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    cols = ["pub_date", "brands", "origin", "title",
            "recall_numbers", "affected_units_total", "url"]
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in results:
            w.writerow([
                r.get("pub_date") or r.get("list_date") or "",
                "; ".join(r.get("brands", [])),
                r.get("origin", ""),
                r.get("title", ""),
                "; ".join(r.get("recall_numbers", [])),
                r.get("affected_units_total") or "",
                r.get("url", ""),
            ])

    print(f"\nГотово: {len(results)} отзывов -> {OUT_JSON}, {OUT_CSV}")


if __name__ == "__main__":
    main()
