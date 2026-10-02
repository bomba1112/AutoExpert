# US tech database — batch progress (all makes, MY2014–2026)

Updated: 2026-10-03. Prompt: `CLAUDE_CODE_US_TECH_DATABASE_PROMPT.md`; the owner revised section 8 on 2026-10-02. The pipeline runs by source, not by vehicle. The batch is complete. The final report is `data_work/REPORT.md`, with per-make reports in `data_work/<make>/REPORT.md`.

## Owner decisions in force
- **Scripts:** loaders and parsers are batch scripts over every line of Appendix A. AI is used only where a script fails. Parallel agents split work by source, at most 2 at a time, with one request stream per site.
- **New configurations** stay in the research layer and are not published.
- **Storage:** backups go outside OneDrive in `C:\AutoExpertBackups\`. Raw files are in `C:\AutoExpertData\raw` (`AUTOEXPERT_RAW_ROOT`). Manifests are in `data_work/_shared/`.
- **Makes loaded:** of the last 7 makes, only Audi, Volkswagen and Tesla were loaded. Cadillac, Jeep and Mitsubishi were not loaded; their staging is prepared. Infiniti had already been loaded (`f47df93`) before this decision and stays as it is.
- **Replacing own rows:** rows written earlier by this pipeline are replaced only by owner decision (`--replace-own`), and every change is logged in `corrections.json`. This was done for Hyundai/Kia, Land Rover, and Mercedes GLC (2026-10-03).
- **No VDB.** Not used as a source: turbo.az, LEMON, charm.li. No logins and no captcha bypass.

## Makes
| Make | Status | Last commit |
|---|---|---|
| Hyundai, Kia | base layer + manual facts (per-engine capacities, schedules), press, CarComplaints | `0ec3c41` |
| Toyota | base layer + manual fluids and capacities, press (Camry: earlier report `REPORT_CAMRY.md`) | `2550256` |
| Mercedes-Benz | base layer, then manual fluids; this round adds per-model tables, alternative mbusa editions, auto-data.net (secondary) and Service A/B maintenance | (this commit) |
| BMW, Chevrolet, Ford, Lexus, Honda, Nissan, Land Rover | second pass: manual facts, press, CarComplaints | `40e3af4` … `bec9c2d` |
| Infiniti | first load (before the stop decision) | `f47df93` |
| Audi, Volkswagen, Tesla | first load | `73fdc49`, `e96b2ee`, `0ac8e0d` |
| Cadillac, Jeep, Mitsubishi | not loaded (owner decision); staging prepared | — |

## Mercedes-Benz gap-closing round (2026-10-02/03)
- **www.mbusa.com:** the original pass got 44 documents (35 operator's manuals and 9 warranty/maintenance booklets); 91 manuals failed with gateway 502. The retry with a 180 s timeout got 0 of 7 and was stopped by the owner.
- **Alternative US editions** for the same line-years (`scripts/collect_mbusa_alternatives.py`, one request at a time, 180 s): 96 line-years, 25 editions downloaded.
- **Per-model tables** of the operator's manuals ("Model | Capacity / Filling quantity", "MB-Freigabe or MB-Approval"), parsed by `scripts/extract_manual_facts.py`, pass `mb-model-table-4`. Each value is tied to the model row printed in the table. The pass also reads two sentence statements: brake fluid "MB-Approval 331.0" and coolant "MB 310.1/320.1".
- **auto-data.net (secondary)** fills oil and coolant volume only for line-years without a US manual value (`scripts/collect_autodata.py`, registry `auto-data`). The oil approval there is behind a login and was not collected.
- **Maintenance:** Service A/B from the official mbusa.com page (`scripts/build_maintenance_mb.py`). Stored as SECONDARY_NOTE: the page says "approximately" and names no model or year. EV lines (EQS, EQB) get a gap with the reason.
- **Corrections:** 23 own rows logged in `data_work/mercedes-benz/staging/*/corrections.json`:
  - volumes moved from "drain & refill" to "with filter", because the manual says the volume includes the filter;
  - "MB-Approval 331.0" removed from coolant, because it is the brake-fluid approval;
  - GLC replaced by owner decision.

## How to resume / repeat for a make
1. Collectors resume from their manifests. Logs are in `C:\AutoExpertData\logs\*.log`.
2. Page text: `uv run --no-project --with pypdfium2 python scripts/pdf_text_store.py official/<make>`.
3. Extract facts: `uv run --no-project --with pdfplumber --with pypdfium2 python scripts/extract_manual_facts.py <make>`.
4. Build the staging: `.venv/Scripts/python.exe scripts/run_make_pass.py <make> build`. It must report 0 errors.
5. Run the 10% recheck: `uv run ... python scripts/recheck_us_batch.py <make>`. It must find 0 mismatches.
6. Rehearse: refresh the copy (`run_conveyor.refresh_copy`), then run `run_make_pass.py <make> rehearse`. Check that conflicts and stale rows are 0 or explained.
7. Log corrections: `run_make_pass.py <make> corrections`.
8. Live load: `run_make_pass.py <make> live [--replace-own <line>]`. It takes a backup first.
9. Run the tests (backend, Flutter, web) and commit `data(us): <make> — …`. Regenerate the report with `scripts/build_us_report.py`.
