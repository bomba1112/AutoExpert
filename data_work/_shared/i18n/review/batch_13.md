# Review of llm/batch_13.json (NHTSA recall summaries, RU/AZ)

Items checked: 70, all `recall_summary`. By filer: 58 Chrysler (48 "Chrysler (FCA US LLC)", 9 "Chrysler (FCA US, LLC)", 1 "Chrysler Group LLC (Chrysler)"), 9 Mitsubishi, 2 GM and 1 Accessible Technologies (ProCharger superchargers). Items changed: 16. Field edits: 25 (RU 16, AZ 9) in 24 fields. Eight items were changed in both languages: `37223ffb136d`, `3c3f99a34166`, `3db848e284ed`, `46fc7af44c98`, `588038942d83`, `67ed670b0ddf`, `75234475a1fc` and `f52f280e3a37`. `46fc7af44c98` RU has two edits.

**How the file was written**
- Before the review, the three files of this round (batches 13-15) were backed up to the scratchpad as `bk/batch_NN.json`.
- One script (`b13_15_apply.py`, edit list `b13_15_edits.py`) applied the edits. Each edit replaces one exact substring and must match exactly once.
- Before writing, the script confirmed that the real file still had the backup's sha256.
- Before the edits, a JSON round trip of the original file was confirmed byte-identical. The file keeps its formatting: indent 1, CRLF, no trailing newline, UTF-8, ensure_ascii false.
- The kind/hash pairs and their order did not change.
- The backup sha256 is 97cbc6cd...; the final sha256 is b65c46f6...

**Check results:** before the review, `scripts/i18n_batches.py check 13` gave 70 pass, 0 fail, with 14 GLOSSARY lines. After it gives 70 pass, 0 fail, with 15 GLOSSARY lines. The extra line is `37223ffb136d` ru 'transmission' -> 'коробка передач'. The RU now uses the glossary term for a CVT, 'вариатор (CVT)'. All 15 lines are false positives of the stem check:
- 'fire' in "Fire Extinguishers" = огнетушители (`f482c84a2abb`).
- 'steering' in "steering knuckle" (`f5ca927c7b87`), "electro-hydraulic power steering" = электрогидравлический усилитель руля (`eb134ef9ceda`) and "power steering hose" = шланг усилителя руля (`bac990f92b9c`).
- 'wheel' in "tone wheel" = задающий диск / impuls diski (`1a0e158e3fa2`) and in "all-wheel-drive" = полноприводные / tam ötürücülü (`7844fd76b076`).
- 'tire' as the genitive plural 'шин' (`7214e214d688`).
- 'side air bag' in "passenger side air bag" (`6a0bb05efff1`). This is the bag on the passenger side, not a side air bag.
- 'seat' and 'seat belt' in "seat belt pretensioners" = преднатяжители ремней безопасности (`e5a2e4397ba6`).

**Numbers, dates and names**
- A script compared every digit group in all 70 items, RU and AZ, with the source. Nothing is missing, changed or added. The script's only alarms came from a model number followed by a year (it read "Ram 1500 2014" as one number).
- All 29 dates in 11 items (production ranges and one amendment date) were compared by script (day, month, year) in RU and AZ. Every AZ year suffix (-ci / -cı / -cu / -cü) was checked against its year.
- Model years and model-year ranges match the source in every item.
- Model names, codes and part numbers are present as printed: 300x, 500x, 4XE, Promaster and ProMaster, DCSD, CVPAM, FCM-ECU, AB037A-100(P), A037A-100B, 6ML07TRMAA, 6GA92TRMAA, OCR, EHPS, BCM, the two NHTSA PDF URLs, and 'Pindicator' in single quotes.
- The FMVSS 110, 111 ("Rear Visibility", and "Rearview Mirrors" as printed in `e82e46ab1a71`), 138 and 214 titles match batches 01-12 word for word in RU and AZ.
- A scripted scan of the AZ text found no Turkish forms, no Cyrillic letters and no English function words.

## Changes

- `e7c4cc2103a4` **ru**: "на печатной плате, которая может отказать, что приведёт" -> "на печатной плате. Эта микросхема может отказать, что приведёт". 'которая' after 'на печатной плате' attaches to the nearest noun, so the RU said the circuit board fails. The part that fails is the voltage regulator chip (the AZ already says 'bu mikrosxem sıradan çıxa bilər').
- `67ed670b0ddf` **ru**: "из-за чего образуются газовые карманы" -> "из-за чего образуются газовые полости". 'газовые карманы' is a calque of 'gas pockets'. Batch 01 (4edd2eeea9d4) has the identical GM sentence as 'газовые полости'.
- `67ed670b0ddf` **az**: "porşenlərinin örtüyü kifayət qədər olmaya bilər ki," -> "porşenlərinin örtüyü qeyri-kafi ola bilər ki,". Same sentence as batch 01 4edd2eeea9d4, where the review replaced 'örtüyü kifayət qədər olmaya bilər' with 'örtüyü qeyri-kafi ola bilər' (insufficient coating).
- `9f83073d8da0` **ru**: "могут не запираться надёжно" -> "могут ненадёжно защёлкиваться". 'запираться' means 'to lock' (glossary lock = замок). The source 'may not latch securely' is about the latch (glossary latch = защёлка), so the verb is 'защёлкиваться'.
- `5cb1fca90900` **ru**: "функция автоматического удержания тормозами (BAH)" -> "функция автоматического удержания тормоза (BAH)". 'удержания тормозами' (holding by brakes, with no object) is not Russian. Brake Auto Hold is 'автоматическое удержание тормоза'.
- `37223ffb136d` **ru**: "оснащены бесступенчатой коробкой передач (вариатором CVT), которая" -> "оснащены вариатором (CVT), который". Glossary: continuously variable transmission = 'вариатор (CVT)'. The RU put a second noun inside the brackets ('(вариатором CVT)'). The source's 'constant velocity transmission' is a misnomer for a CVT; the abbreviation confirms the meaning, and 'constant velocity' (ШРУС) must not be translated.
- `37223ffb136d` **az**: "pilləsiz sürətlər qutusu (CVT variatoru) ilə təchiz olunub ki, o da müəyyən sürmə şəraitində" -> "variator (CVT) ilə təchiz olunub ki, o da müəyyən hərəkət şəraitində". Glossary CVT = 'variator (CVT)'. 'in certain driving conditions' is 'müəyyən hərəkət şəraitində' in batches 04, 05 and 07 (b04 4fac07b97a75, b07 e7fe509c3f85); 'sürmə şəraiti' was not used before.
- `588038942d83` **ru**: "может касаться магистрали ABS и повредить её" -> "может касаться тормозной трубки ABS и повредить её". Glossary brake line = 'тормозная трубка'. Batches 11-12 use it for every brake line (b11 4dff047dcaa4, b12 de3196816199).
- `588038942d83` **az**: "ABS xəttinə toxunaraq" -> "ABS borusuna toxunaraq". Glossary brake line = 'əyləc borusu'. 'xətt' means a line or route and is not used for a hydraulic line in batches 01-12 (b11 4dff047dcaa4, b12 2c76cb20d28b 'əyləc boruları').
- `46fc7af44c98` **ru**: "зубьев входных шлицов" -> "зубьев входных шлицев". Grammar: the genitive plural of 'шлиц' is 'шлицев'.
- `46fc7af44c98` **ru**: "к потере функции Park на неподвижном автомобиле" -> "к потере функции стояночной блокировки на неподвижном автомобиле". English 'Park' was left in the RU. Batch 14 f0a73fddd399 and f862226ae43e describe the same PTU defect as 'потере функции стояночной блокировки'.
- `46fc7af44c98` **az**: "dayanarkən isə Park funksiyasının itməsinə" -> "dayanarkən isə park funksiyasının itməsinə". The English capitalised 'Park' was kept. Batch 14 f0a73fddd399 / f862226ae43e write the same thing as 'park funksiyasının itməsinə'.
- `f52f280e3a37` **ru**: "перепутана полярность клемм аккумулятора." -> "перепутана их полярность.". 'клемм аккумулятора' was said twice in one clause ('on the graphic of the battery terminals the polarity of the battery terminals is reversed').
- `f52f280e3a37` **az**: "təsvirində akkumulyator klemmlərinin qütbləri" -> "təsvirində onların qütbləri". 'akkumulyator klemmlərinin' was said twice in one clause, the same problem as in the RU.
- `3db848e284ed` **ru**: "неподходящий шток блокировки парковки коробки передач." -> "неподходящий шток механизма парковочной блокировки.". 'коробку передач ... коробки передач' says 'transmission' twice in one short sentence, and 'блокировка парковки' is a calque. The part is the rod of the park lock mechanism ('парковочная блокировка').
- `3db848e284ed` **az**: "Sürətlər qutusuna sürətlər qutusunun park kilidinin səhv çubuğu" -> "Sürətlər qutusuna park kilidinin səhv çubuğu". 'Sürətlər qutusuna sürətlər qutusunun' said 'transmission' twice in a row.
- `6a0bb05efff1` **ru**: "В подушке безопасности со стороны пассажира в сборе гайки крепления газогенератора внутри модуля в сборе могут быть ослаблены." -> "Внутри модуля подушки безопасности со стороны пассажира гайки крепления газогенератора могут быть ослаблены.". 'со стороны пассажира в сборе' reads as 'of the passenger in assembly', and 'в сборе' was used twice. The nuts are loose inside the passenger air bag module.
- `0066238351ea` **ru**: "может быть установлена в перевёрнутом положении" -> "может быть установлена в обратном направлении". 'в перевёрнутом положении' means upside down. A 'reversed' camshaft cap is turned the wrong way round, front to back. The AZ already says 'tərsinə quraşdırılmış'.
- `3c3f99a34166` **ru**: "и к потере функции PARK на стоянке." -> "и к потере функции стояночной блокировки на неподвижном автомобиле.". English 'PARK' was left in the RU, and 'на стоянке' means 'in a car park' rather than 'when stationary'. This now matches 46fc7af44c98 and b14 f0a73fddd399.
- `3c3f99a34166` **az**: "dayanarkən isə PARK funksiyasının itməsinə" -> "dayanarkən isə park funksiyasının itməsinə". The English 'PARK' was kept. This now matches b14 f0a73fddd399 ('park funksiyasının itməsinə').
- `d3450176e929` **ru**: "Рычаг или рычаги стеклоочистителя ветрового стекла могут ослабнуть" -> "Крепление рычага или рычагов стеклоочистителя ветрового стекла может ослабнуть". 'рычаг может ослабнуть' says the arm itself becomes weak. The source 'arm may loosen' means its fastening works loose.
- `75234475a1fc` **ru**: "а автомобиль не находится в положении PARK," -> "а автомобиль не находится в положении парковки,". English 'PARK' was left in the RU. Batches 01-09 write the park position as 'положение парковки' (b07 0b29319363e4 'находится в положении парковки').
- `75234475a1fc` **az**: "avtomobil PARK vəziyyətində olmadıqda" -> "avtomobil park mövqeyində olmadıqda". The English 'PARK' was kept. Glossary park position = 'park mövqeyi (P)', and b07 0b29319363e4 has 'avtomobil park mövqeyində olarkən'.
- `bac990f92b9c` **ru**: "что приводит к отсоединению возвратного шланга низкого давления." -> "из-за чего возвратный шланг низкого давления может отсоединиться.". 'мог быть установлен ..., что приводит к отсоединению' states the detachment as a fact. It follows from a possible assembly error, so it is a possible consequence (the AZ already says 'səbəb olar').
- `97b57128c0cb` **az**: "arxa alt asqı qolları ilə təchiz oluna bilər." -> "arxa alt asqı qolları ilə təchiz olunmuş ola bilər.". 'təchiz oluna bilər' reads as 'can be fitted', a future option. The source 'may be equipped' is a possibility about how the cars were built, which the batches write as '... olunmuş ola bilər'.

## Flagged by the translator: verdicts

- `e7c4cc2103a4` "Town and Country" -> "Town & Country": **accepted**. Town & Country is the official model name. Writing "and" would leave an English function word, which the check rejects in RU ('untranslated') and AZ.
- `c2bd44543869`, `88e7d783f7ba` "Street and Racing Technology" -> "Street & Racing Technology (SRT)": **accepted** for the same reason; the '&' is the official spelling of the SRT name.
- `46fc7af44c98`, `a2a0d65f2c10` PTU = раздаточная коробка / paylayıcı qutu: **accepted**. On the Cherokee the PTU is the unit that divides torque between the front axle and the propeller shaft to the rear axle, and in `46fc7af44c98` it is two-speed. That is what раздаточная коробка means. The kept "(PTU)" identifies the part, and the glossary's new TRANSFER CASE also = раздаточная коробка / paylayıcı qutu. Batch 14 (`f0a73fddd399`, `f862226ae43e`) uses the same terms.
- `3c3f99a34166` pinion gears = сателлиты / satellitlər: **correct**. "Both pinion gears" inside the front differential are the differential pinions, which are сателлиты. They are not the final-drive pinion (ведущая шестерня главной передачи).
- `0066238351ea` AZ "klapan çubuqlarının fiksatorları" for "valve stem keepers": **accepted**. The keepers are the split collets (RU сухари клапанов). 'klapan çubuğu' = valve stem and 'fiksator' = keeper/retainer, so the phrase is exact and avoids workshop slang ('suxari'). The RU 'сухари клапанов' is the standard term.
- `37223ffb136d` CVT: **meaning right, form changed** (see Changes). The source's "constant velocity transmission" is a misnomer for a continuously variable transmission. The abbreviation CVT and the symptom (delayed acceleration) confirm this, so the translation must not render "constant velocity" (ШРУС). The RU '(вариатором CVT)' and AZ '(CVT variatoru)' put a second noun inside the brackets. Both now use the glossary form 'вариатор (CVT)' / 'variator (CVT)'.

## Seen and left as is

- `f482c84a2abb`: the source says "A list of the affected **trailer** models" in a vehicle recall (an NHTSA template slip). RU/AZ keep 'прицепов' / 'qoşqu' as printed.
- `e82e46ab1a71`: FMVSS 111 is printed with its former title "Rearview Mirrors". RU/AZ keep that title (b01-12 have both titles).
- `1a0e158e3fa2` RU "может расслоиться, из-за чего двигатель теряет способность ...": the present tense describes what happens once the disc delaminates, and the sentence ends with 'что может привести'. Kept (same as b14 `005986f5e08d`).
- `f5ca927c7b87` AZ "təkərin xaricə doğru aşmasına" ('the wheel tipping outward') for "the wheel to fall outward": kept (same in b14 `835914bf9fd7`).
- `830988c87065` RU "одна из муфт сцепления" for a clutch inside the 9-speed automatic: understandable, kept. 'фрикцион' would be more precise.
- `2e3b8411989b` AZ "bu avtomobillər ... satılmış və (və ya) hazırda qeydiyyatdadır": the state names are correct (Men, Merilend, Massaçusets, Delaver, Nyu-Cersi, Qərbi Virciniya ...), and all 27 states plus DC are present in RU and AZ.
- `d6b9d805772d`, `830988c87065`, `1a0e158e3fa2`, `a6f7d2f781fa`, `57711167ee9c` and others: "некоторые оснащённые двигателями 2.4L автомобили ..." puts a long participle phrase before the noun, as in batches 11-12. It is bookish but grammatical; batch 11/12 explain the tokenizer reason for keeping it.
- `e7c4cc2103a4`, `9546a9c1289d`, `b9be89d93ecb`, `e82e46ab1a71`, `349c0d8b7dc2`, `6260f03a4b27`: multi-model lists keep the source order inside parentheses, including the repeated "и" ("Charger и Durango и Chrysler 300x"), as in batches 02-12.
