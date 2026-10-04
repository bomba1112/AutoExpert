# Review of llm/batch_08.json (NHTSA recall summaries, RU/AZ)

Items checked: 78, all `recall_summary`: Kia (39), Mercedes-Benz USA (28) and Nissan / INFINITI (11). Items changed: 10. Field edits: 10 (RU 9, AZ 1). No item was changed in both languages.

Before the review the file was backed up to the scratchpad as `batch_08.backup.json` (sha256 2c382f12...). One script applied the edits to a copy first, and the copy passed the same checks. The real file was confirmed unchanged since the backup (same sha256) and then written by the same script. It is byte-identical to the copy (sha256 fc00d4c6...). The 78 kind/hash pairs and their order did not change, and the file keeps its formatting (indent 1, CRLF, no trailing newline).

`scripts/i18n_batches.py check 08` gives 78 pass, 0 fail, both before and after the edits. The number of GLOSSARY lines went from 38 to 41. The three new lines are "seat belt" in `c0cefc603301`, `9f29420e330b` and `fe2bd999b8a0`: the plural forms "ремней" and "ремни" fail the 'реме' stem check. All 41 lines are false positives of the stem check or intended forms:
- **Model names:** "plug-in hybrid" in Sportage / Sorento / Optima "Plug-In Hybrid (Electric)" / "PHEV". These stay as printed, as in batches 06 and 07.
- **A term inside a longer term or in another sense:**
  - "engine" in "engine compartment" = моторный отсек;
  - "battery" in "high voltage battery" = высоковольтная батарея (glossary 'high-voltage battery');
  - "air bag" in "curtain air bag" = шторка безопасности;
  - "tire" in "spare tire" = запасное колесо, and in the FMVSS title "шин";
  - "frame" in "seatback frame" = каркас / karkas;
  - "wheel" in "front wheel drive" = передний привод;
  - "seat" / "side air bag" in "child seat" = детское кресло and "passenger side air bag" = подушка со стороны пассажира, which is not a side air bag;
  - "strut" in "camber strut" = тяга развала, a link and not a damper strut.

A script compared all numbers in all 78 items, RU and AZ, with the source. None is missing, changed or added; decimals use a comma (4,2 / 2,4 / 1,6). It also checked:
- every model or code token that has a digit or is all capitals, all present in RU and AZ;
- all 18 production dates in the 9 dated items, with day, month, year and order in RU and AZ;
- the AZ ordinal suffixes after years (2012/2015-ci, 2013/2014-cü, 2016-cı), all correct;
- the model-year groups of the multi-model lists (Kia `98161882204f`, `87fad0f23d40`, `92a4293acf51`; MBUSA `2a9b9b26543c`, `ca09ce4d9184`, `eca10045ca07`), read against the source by hand.

The script found no Cyrillic in AZ and no mixed Latin/Cyrillic words in RU. It found no Turkish forms; the hit " için" is the AZ "içindən" in `67b9d81f6c20`. The FMVSS titles were compared with batches 01-07: 101, 108, 110 (short and "for Passenger Cars"), 114, 201, 208 and 209 match. 138 is singular because this source says "System". 141 and 226 are covered below.

## Changes

- `a29578ed188c` **az**: "Əyləc pedalının dayaq amortizatoru korlana bilər" -> "Əyləc pedalının dayaq yastıqcığı korlana bilər". The source says "stopper pad", a rubber pad. "amortizator" is the glossary word for shock absorber and names a different part. The new wording matches batch 07 `464e5da559f7` (same Hyundai/Kia text).
- `7109814128ea` **ru**: "отзывает некоторые оснащённые двигателями 2,4 л с непосредственным впрыском бензина (GDI) или 2,0 л GDI Turbo автомобили Optima 2013–2014 модельных годов." -> "отзывает некоторые автомобили Optima 2013–2014 модельных годов, оснащённые двигателями объёмом 2,4 л с непосредственным впрыском бензина (GDI) или двигателями GDI Turbo объёмом 2,0 л.". The long participle phrase sat between 'некоторые' and 'автомобили', which reads unnaturally. This is the same fix as batch 05 `8a08ce892287` and batch 06 `1931fe5cd544`. The volume is placed so that the sentence does not end with a Latin word, which the check would read as 'Turbo.'.
- `8705c859b69a` **ru**: "отзывает некоторые оснащённые двигателем 2,0 л Nu MPI автомобили Forte 2017–2018 модельных годов." -> "отзывает некоторые автомобили Forte 2017–2018 модельных годов, оснащённые двигателем Nu MPI объёмом 2,0 л.". Same participle fix as above.
- `0e26811b211d` **ru**: "отзывает некоторые оснащённые двигателями Gamma 1,6 л Turbo-GDI или Theta II 2,0 л Turbo-GDI автомобили Optima 2019 модельного года." -> "отзывает некоторые автомобили Optima 2019 модельного года, оснащённые двигателями Gamma Turbo-GDI объёмом 1,6 л или Theta II Turbo-GDI объёмом 2,0 л.". Same participle fix as above.
- `f3fa6e5d2064` **ru**: "отзывает некоторые оснащённые двигателями 2,5 л T-GDI автомобили K5 2021–2022 модельных годов." -> "отзывает некоторые автомобили K5 2021–2022 модельных годов, оснащённые двигателями T-GDI объёмом 2,5 л.". Same participle fix as above.
- `c0cefc603301` **ru**: "При столкновении преднатяжитель, которым оснащён ремень безопасности переднего сиденья со стороны водителя и (или) пассажира, может взорваться при срабатывании." -> "При столкновении преднатяжители ремней безопасности передних сидений со стороны водителя и/или пассажира могут взорваться при срабатывании.". The singular put one belt on one front seat "on the driver's and/or passenger's side", which makes no sense. The source names the driver-side and/or passenger-side pretensioner(s). The new wording is the batch 06 sentence for the same text (`4df6f2fb99e5`, `fb0f7aef13f0`).
- `9f29420e330b` **ru**: same old -> new as `c0cefc603301`, for the same reason.
- `fe2bd999b8a0` **ru**: "Ремень безопасности заднего центрального сиденья мог быть установлен без функции защиты детского кресла и может не обеспечивать" -> "Ремни безопасности заднего центрального сиденья могли быть установлены без функции защиты детского кресла и могут не обеспечивать". The source has "seat belts", plural. The RU had the singular, while the AZ ("kəmərləri") already had the plural.
- `f64810f5af59` **ru**: "«Снижение риска выпадения людей из автомобиля»" -> "«Снижение риска выбрасывания людей из автомобиля»". FMVSS 226 "Ejection Mitigation" is about occupants being thrown out in a crash or rollover. 'выпадение' means falling out and understates this. The AZ "kənara atılma" was already correct.
- `e47db721c51e` **ru**: "«Минимальные требования к звуку для гибридных электромобилей»" -> "«Минимальные требования к звуку для гибридных электрических транспортных средств»". In Russian 'электромобиль' means a battery-electric car, so "гибридный электромобиль" is contradictory. It also does not render "vehicles". The new wording follows the source "Hybrid Electric Vehicles" and the AZ "Hibrid elektrik nəqliyyat vasitələri", and keeps the "транспортных средств" wording of batches 02 and 07.

## Seen and left as is

- `37d646f1d258` ru "отзывает некоторые Pathfinders 2014 модельного года": the source's English plural "Pathfinders" stays. The check accepts a Latin word in RU only if it appears in the source, and the source has only "Pathfinders", so "автомобили Pathfinder" would fail the check. The AZ already reads "Pathfinder avtomobillərini". This needs a checker exception if it is to be fixed.
- `b4abe89e9a2f` ru "(AMG E 53 4MATIC+ WAGON)" stays in parentheses. A sentence-final "WAGON." would be read by the check as a new Latin token.
- `d90245a14b02` "шатунных подшипников": batch 02 uses the same wording (`a77554af2c11`). Batch 04 uses "вкладыши шатунов". Both are in use, so this was not changed.
- `4186b86ff22b` ru "непреднамеренно" / az "təsadüfən" for "inadvertently" are kept for consistency with batches 01-07, which use them throughout.
- `e256ac167f24` "поперечина щитка передка" / "ön panelin eninə tiri" for "cowl crossbar" are acceptable and were not changed. No earlier batch has this term.
