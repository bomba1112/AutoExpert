# Review of llm/batch_14.json (NHTSA recall summaries, RU/AZ)

Items checked: 70, all `recall_summary`. By filer: 59 Chrysler (39 "Chrysler (FCA US, LLC)", 6 "(FCA US LLC)", 1 "Chrysler(FCA US LLC)", 1 "(FCA US, LLC) (Stellantis)", 9 "Chrysler Group LLC", 1 "Chrysler Group, LLC", 2 plain "Chrysler") and 11 GM. Items changed: 6. Field edits: 10 (RU 6, AZ 4). Four items were changed in both languages: `1f49e13b0bee`, `1f6c97920ed8`, `835914bf9fd7` and `fe5d87919234`. One more planned edit was blocked by the check; see "Found but not fixed".

**How the file was written**
- Before the review, the three files of this round (batches 13-15) were backed up to the scratchpad as `bk/batch_NN.json`.
- One script (`b13_15_apply.py`, edit list `b13_15_edits.py`) applied the edits. Each edit replaces one exact substring and must match exactly once.
- Before writing, the script confirmed that the real file still had the backup's sha256.
- Before the edits, a JSON round trip of the original file was confirmed byte-identical. The file keeps its formatting: indent 1, CRLF, no trailing newline, UTF-8, ensure_ascii false.
- The kind/hash pairs and their order did not change.
- The backup sha256 is a99d42a6...; the final sha256 is 7e86a20e...
- One extra edit (`40d9f3c318b2` RU) made `check 14` fail. The three files were restored from the backup, that edit was dropped, and the rest were applied again.

**Check results:** `scripts/i18n_batches.py check 14` gives 70 pass, 0 fail before and after. The same 21 GLOSSARY lines appear before and after, and all are false positives of the stem check:
- 'wheel' in "tone wheel" (`005986f5e08d` AZ impuls diski).
- 'battery' in "high voltage battery" = высоковольтная батарея / yüksək gərginlikli batareya, the glossary term (`2a8bff7958de`, `f14eab8f4d27`).
- 'air bag' in "curtain air bag" = шторка безопасности, the glossary term (`84554629db81`).
- 'frame' in "seat back frame" = каркас / karkas (`c072657f8168`, `d54654603c80`).
- 'seat belt' in the genitive or plural, 'ремня / ремней безопасности' (`becb46647e80`, `1f49e13b0bee`). 'seat' appears in "seat belt pretensioners" (`1f49e13b0bee`).
- 'headlight' as the genitive plural 'фар' (`e6e0999a5b65`) and 'tire' as the accusative 'шину' (`fa3c453fd666`).
- 'steering' in "steering knuckle" (`835914bf9fd7`) and in "electric power steering" = электроусилитель руля (`9bf685473fa2`, `05cf27a5651d`, `d27c2c52f046`).

**Numbers, dates and names**
- A script compared every digit group in all 70 items, RU and AZ, with the source. Nothing is missing, changed or added. The only alarms were the same "model number + year" artefact as in batch 13.
- All 32 production dates in 15 items were compared by script in RU and AZ. All AZ year suffixes are correct, including 2010-cu.
- Model years and ranges match. Names and codes are kept as printed: 4XE and 4Xe, WK, CTS-V, Twin Turbo V6, SLM, HCP, HPFP, IPC, ORC, OCR, SCCM, MIL, GVWR, "Chrysler(FCA US LLC)" without a space, and "(Stellantis)".
- The FMVSS 101 ("Controls and Displays" / "Control and Displays" / "Displays and Controls"), 102, 103, 108, 111, 126, 202, 208, 210, 214, 225, 226 and 301 titles match batches 01-12 word for word in RU and AZ.
- A scripted scan of the AZ text found no Turkish forms, no Cyrillic letters and no English function words.

## Changes

- `fe5d87919234` **ru**: "вывести селектор из положения Park без нажатия" -> "вывести селектор из положения парковки без нажатия". English 'Park' was left in the RU. Batches 07-09 write 'shift out of Park' as 'вывести ... из положения парковки' (b08 977e14777b53, b09 72c2b9d0570e).
- `fe5d87919234` **az**: "sürət seçicisini Park vəziyyətindən çıxarmağa" -> "sürət seçicisini park mövqeyindən çıxarmağa". The English 'Park' was kept. Glossary park position = 'park mövqeyi (P)'; b08 977e14777b53 has 'park mövqeyindən çıxarmağa'.
- `1f6c97920ed8` **ru**: "вывести селектор из положения Park без нажатия" -> "вывести селектор из положения парковки без нажатия". Same as fe5d87919234 RU.
- `1f6c97920ed8` **az**: "sürət seçicisini Park vəziyyətindən çıxara bilər" -> "sürət seçicisini park mövqeyindən çıxara bilər". Same as fe5d87919234 AZ.
- `84554629db81` **ru**: "может препятствовать её раскрытию надлежащим образом." -> "может препятствовать её надлежащему раскрытию.". 'препятствовать её раскрытию надлежащим образом' can be read as 'properly prevent its deployment'. The source means the air bag may not deploy as intended.
- `835914bf9fd7` **ru**: "Неправильно обработанный поворотный кулак может разделиться между шаровой опорой и кулаком, из-за чего" -> "На неправильно обработанном поворотном кулаке шаровая опора может отделиться от кулака, из-за чего". 'кулак может разделиться между шаровой опорой и кулаком' is a word-for-word calque in which the knuckle separates from itself. The ball joint separates from the knuckle, the same failure as b13 f5ca927c7b87.
- `835914bf9fd7` **az**: "Düzgün emal edilməmiş dönmə yumruğu kürəvi oynaq ilə yumruq arasında ayrıla bilər ki," -> "Düzgün emal edilməmiş dönmə yumruğunda kürəvi oynaq yumruqdan ayrıla bilər ki,". Same calque as in the RU: the knuckle 'separated between the ball joint and the knuckle'. The ball joint separates from the knuckle.
- `1f49e13b0bee` **ru**: "Контрольная лампа неисправности MIL должна загореться, чтобы заранее предупредить водителя об отказе." -> "Контрольная лампа неисправности (MIL) должна загореться, чтобы сразу предупредить водителя об отказе.". 'заранее' means 'in advance', before the failure. The lamp can only light once the OCR fault is present; the source 'initially warn' means it gives the first warning. The abbreviation now goes in brackets, as everywhere else.
- `1f49e13b0bee` **az**: "Sürücünü sıradan çıxma barədə əvvəlcədən xəbərdar etmək üçün" -> "Sürücünü sıradan çıxma barədə dərhal xəbərdar etmək üçün". 'əvvəlcədən' means 'beforehand', the same meaning error as in the RU.
- `9bf685473fa2` **ru**: "Усиление электроусилителя руля (EPS) может кратковременно пропадать, после чего усиление EPS внезапно восстанавливается." -> "Усиление руля, создаваемое электроусилителем (EPS), может кратковременно пропадать, после чего оно внезапно восстанавливается.". 'Усиление электроусилителя' repeats the root ('the assist of the assist unit'). Glossary: loss of power steering assist = 'потеря усиления руля'; electric power steering = 'электроусилитель руля'.

## Found but not fixed: blocked by the check

- `40d9f3c318b2` **ru** (flagged by the translator): "Grand Cherokee 2014 модельного года в комплектациях non-SRT". The English prefix 'non-' stays in the Russian text. The fix "Grand Cherokee 2014 модельного года (кроме комплектаций SRT)" was applied in the rehearsal and gave 1 FAIL: "ru: Latin word 'SRT' not in the source". `i18n_build.check` tokenises the source "non-SRT" as one word, so a standalone "SRT" counts as foreign, and every Russian wording without the literal "non-SRT" fails. The current text was kept. Verdict: **wrong in principle, kept only because of the tokenizer**. The AZ "SRT-dən fərqli komplektasiyalarda" is correct. Fixing this needs either a tokenizer that splits on '-' or a hand translation in `scripts/i18n_templates.py`.

## Seen and left as is

- `e6e0999a5b65` "the AUTO position" -> "в положение AUTO" / "AUTO vəziyyətinə": AUTO is the marking on the switch and is kept as such. `d8858117722e` has 'auto position' in lower case, which was translated as 'автоматического режима' / 'avtomatik rejim'. Both are correct.
- `02d899739a37`: the source writes "Ram 3500 cab chassis" in lower case. RU/AZ capitalise "Cab Chassis" as the model designation used elsewhere in the same list. Lower-case English words would be flagged as untranslated.
- `9f0748d4fda7`: "Saltillo" is "Сальтильо" in RU and "Saltillo" in AZ. Both are acceptable.
- `c4ae14b5a911` AZ repeats "geri çağırır" (once for the vehicles, once for the Continental tires). Grammatical, kept.
- `c8fdb0bb33f7` RU "внутренние частицы" for "internal debris" (particles from inside the pump): kept.
- `742b06212f82` RU "были приварены ненадлежащим образом" for "were not welded properly": kept.
- `2a8bff7958de`, `f14eab8f4d27`, `2ec00d71f1fb`, `81be519ed0ca`: 4XE / 4Xe and "Plug-In Hybrid Electric (PHEV)" are kept as printed in each item.
