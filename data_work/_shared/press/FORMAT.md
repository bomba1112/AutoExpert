# Press materials (manufacturer newsrooms, US) — shared collection and extraction format

Fields 5, 10, 11, 12 of the prompt (power/torque, tires, dimensions incl. ground clearance and
cargo, suspension/brakes/steering) come mainly from the manufacturers' US press "specifications"
pages per model year. One collector + one parser per newsroom host. Everything is done by
scripts; values are never typed by hand or taken from memory.

## Rules
- One request at a time per host, 2-5 s pause, respect robots.txt, no logins, no captcha or
  bot-check bypass, no paywalls. A host that blocks scripted access: stop it, write the reason
  into the manifest (`status=blocked`) and the summary.
- US newsroom only (US model years, US units). Canada/Europe/global press sites are not used.
- Only the model lines and model years of `scripts/us_tech_lines.py` (LINES; years = Line.years).
- Use the project helpers: `scripts/us_tech_common.py` (`RAW_ROOT`, `WORK`, `Fetcher`, `Manifest`,
  `write_gz`, `read_maybe_gz`, `sha256`, `now`) and `scripts/us_tech_lines.py` (`LINES`, `BY_KEY`).
- Do not touch the database, the loaders, or files of other hosts.

## Files per host (`<host>` e.g. `pressroom.toyota.com`)
- Collector script: `scripts/collect_press_<short>.py` (resumable: skip URLs already `ok` in the manifest).
- Raw pages: `RAW_ROOT/press/<host>/<file>.html.gz` (or `.pdf` for spec PDFs).
- Manifest: `data_work/_shared/manifest_press/<host>.csv` with columns
  `make,line,year,doc_type,title,url,http_status,bytes,sha256,retrieved_at,path,status,note`
  (`line` = registry key such as `toyota/rav4`; `doc_type` = `press_specifications`;
  `sha256` of the stored body before compression; `path` relative to RAW_ROOT).
- Page text for quote checks: `RAW_ROOT/pagetext/<sha256>.json.gz` =
  `{"sha256": ..., "file": "press/<host>/<file>", "pages": ["<plain text of the spec page>"]}`
  (one "page" per HTML document; PDFs: one entry per PDF page).
- Parser script: `scripts/extract_press_<short>.py` writing one JSON per document to
  `data_work/<make>/extracted/press-<host-short>-<line-slug>-<year>-<sha8>.json`:

```json
{
  "doc": {
    "key": "press-<host-short>-<line-slug>-<year>-<sha8>",
    "make": "<registry make, e.g. toyota>",
    "lines": ["toyota/rav4"],
    "years": [2019],
    "doc_type": "press_specifications",
    "title": "<page title as published>",
    "path": "<absolute path of the raw file>",
    "url": "<page url>",
    "page_url": "",
    "sha256": "<sha256 of the stored body>",
    "retrieved_at": "<ISO time>",
    "tier": "A",
    "source_type": "PRESS_RELEASE",
    "publisher": "<manufacturer US newsroom, e.g. Toyota USA Newsroom (pressroom.toyota.com)>",
    "authenticity": "OFFICIAL_PUBLISHER"
  },
  "extractor": "press-<short>-1",
  "pages": 1,
  "edition_market": "US",
  "status": "ok",
  "engine_codes": [],
  "review": [],
  "facts": [
    {"key": "power_hp", "value": 203, "page": 1,
     "quote": "<verbatim text from the page that contains the value>",
     "original": "<the row/cell as published, e.g. 'Horsepower (SAE net) 203 @ 6,600 rpm'>",
     "engine_text": "<engine/trim label the value is given for, as published, e.g. '2.5L 4-cyl. (A25A-FKS)'; null when the page has one engine>",
     "row": "<label of the table row>"}
  ]
}
```
`quote` must be found verbatim (after whitespace normalisation) in `pages[page-1]` of the page text.

## Fact keys (value types and units exactly as listed; convert nothing except number parsing)
| key | value | notes |
|---|---|---|
| power_hp | number | SAE net horsepower of the engine (combustion engine) |
| power_rpm | string | e.g. "6,600" or "5,500-6,000" |
| system_power_hp | number | hybrid/PHEV total system output |
| torque_lb_ft | number | engine torque |
| torque_rpm | string | |
| electric_motor | string | motor description/output as published |
| engine_description | string | e.g. "2.5-liter, 4-cylinder, DOHC 16-valve" |
| engine_displacement_cc | number | |
| bore_stroke_mm / bore_stroke_in | string | "87.5 x 103.4" |
| compression_ratio | string | "13.0:1" |
| valvetrain | string | |
| injection | string | fuel system as published |
| transmission_description | string | e.g. "8-speed Direct Shift automatic" |
| front_suspension / rear_suspension | string | |
| front_brakes / rear_brakes | string | incl. size if published, e.g. "12.0-in ventilated disc" |
| steering | string | type as published |
| turning_circle_ft | number | curb-to-curb if stated |
| tires | string | one size per fact, e.g. "225/65R17 102H" (several sizes = several facts) |
| wheel_size_in | number | |
| length_in, width_in, height_in, wheelbase_in, track_front_in, track_rear_in | number | inches |
| ground_clearance_in | number | |
| curb_weight_lb | number | one per fact; engine_text/trim label when the page lists several |
| cargo_cu_ft | number | behind 2nd row / seats up as published; put the condition into `row` |
| cargo_max_cu_ft | number | seats folded |
| passenger_volume_cu_ft | number | |
| fuel_tank_gal | number | |
| seats | number | seating capacity |
| towing_lb | number | max towing |

Rows the parser cannot read unambiguously (merged cells, one label with two values without
engine/trim labels) go to `review` (`{"page":1,"row":"...","reason":"..."}`), not to `facts`.

## Summary (final message of the agent)
Per host: pages downloaded / not found / blocked, documents parsed, facts per key, lines and
years without a spec page, robots or blocking notes, the exact commands to re-run.
