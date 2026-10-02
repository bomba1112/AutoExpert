# US tech database — batch progress (all makes, MY2014–2026)

Updated: 2026-10-02. Prompt: `CLAUDE_CODE_US_TECH_DATABASE_PROMPT.md` (section 8 revised by the owner on 2026-10-02). The pipeline runs by source, not by vehicle. The only stop is at the end; there is one report for all makes.

## Owner decisions in force (2026-10-02)
- **Write order:** Hyundai, Kia, Toyota (remaining lines), Mercedes-Benz, BMW, Chevrolet, Ford, Lexus, Honda, Nissan, Land Rover, then the rest (Infiniti, Cadillac, Jeep, Audi, Volkswagen, Mitsubishi, Tesla).
- **Scripts:**
  - loaders and parsers are batch scripts over every line of Appendix A and run in the background;
  - AI is used only where a script fails;
  - parallel agents split work by source, with one request stream per site.
- **New configurations** stay in the research layer and are not published.
- **Backups** are kept outside OneDrive in `C:\AutoExpertBackups\`. Bulky raw files live in `C:\AutoExpertData\raw` (`AUTOEXPERT_RAW_ROOT`); manifests are tracked in `data_work/_shared/`.
- **Demo cleanup** (groups A and B) is done (`249b05f`); demo seeding is opt-in.

## Pipeline
| Stage | Script | Status |
|---|---|---|
| Line registry (90 lines; EPA, NHTSA, vPIC, mcum and carmans names) | `scripts/us_tech_lines.py` | done |
| EPA vehicles.csv | `data_work/_shared/raw/epa/` | cached |
| vPIC models + Canadian specs (468 requests) | `scripts/collect_us_apis.py vpic` | done |
| NHTSA products, recalls, complaints | `scripts/collect_us_apis.py nhtsa` | running in background (`C:\AutoExpertData\logs\nhtsa.log`) |
| NHTSA Manufacturer Communications | `data_work/_shared/raw/nhtsa_mfrcomms/` | cached (760k rows ≥ MY2014) |
| carmans.net manuals (308 matched sitemap posts) | `scripts/collect_carmans.py` | running |
| mycarusermanual.com crawl (priority sections first, then full) | `scripts/crawl_mycarusermanual.py --all` | running |
| Official manual portals | 4 research agents per source family → `data_work/_shared/official_manuals/<make>.json` | running |
| PDF page text cache | `scripts/pdf_text_store.py` | running; rerun as downloads finish |
| Base-layer staging per make | `scripts/build_us_batch_staging.py <make>` | — |
| 10% recheck | `scripts/recheck_us_batch.py <make>` | — |
| Load | `scripts/load_us_tech_facts.py <make> <line> --db autoexpert.db` | — |
| Manual facts (oil, fluids, capacities, maintenance) | extractor + AI review queue | next |

## Makes
| Make | Base layer (EPA, vPIC, NHTSA, issues) | Manual facts | Commit |
|---|---|---|---|
| Hyundai | loaded 2026-10-02 (7 lines, 5594 scoped TE, 379 issues), recheck 124/124 | pending | (this commit) |
| Kia … Tesla | pending | pending | — |
| Toyota Camry | done earlier (`4a6e5d5`) | done | — |

## How to resume
1. Check the background logs in `C:\AutoExpertData\logs\*.log`. Each collector resumes from its manifest; to continue, re-run the same command.
2. Build the staging: `.venv/Scripts/python.exe scripts/build_us_batch_staging.py <make>`. The output must show `errors: 0`.
3. Run the recheck: `.venv/Scripts/python.exe scripts/recheck_us_batch.py <make>`. It must find 0 mismatches.
4. Rehearse on a copy at `C:\AutoExpertData\work\rehearsal_batch.db`. Then make a backup in `C:\AutoExpertBackups\` and load each line into `autoexpert.db`.
5. Run the tests (backend, Flutter, web), commit `data(us): <make> — …`, and update this file.
