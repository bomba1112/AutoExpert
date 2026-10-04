# Review of llm/batch_11.json (NHTSA recall summaries, RU/AZ)

Items checked: 78, all `recall_summary`. They are Toyota (6: four filed as Toyota Motor Engineering & Manufacturing, two as "Toyota") and Volkswagen Group of America (72: 44 filed as "(Volkswagen)", one of them misspelled "(Volkswaen)"; 27 as "(Audi)"; 1 as "(VW)"). Items changed: 18. Field edits: 22 (RU 6, AZ 16) in 21 fields. `a0899f2aedee`, `a1241bca70fd` and `c0591ad4e7ab` were changed in both languages; `d377edb140ca` AZ has two edits.

**How the file was written**
- Before the review, the file was backed up to the scratchpad as `b11/batch_11.backup.json` (sha256 a7a3d9d9...).
- One script (`b11/apply.py`, edit list `b11/edits.py`) applied the edits to a copy first. The copy passed `check 11` against a copy of the batch, the glossary and the check scripts.
- The script confirmed that the real file still had the backup's sha256, then wrote it. The result is byte-identical to the copy (sha256 4b8f84a6...).
- The 78 kind/hash pairs and their order did not change. The file keeps its formatting: indent 1, CRLF, no trailing newline.

**Check results:** `scripts/i18n_batches.py check 11` gives 78 pass, 0 fail, before and after. The same 18 GLOSSARY lines appear before and after, and all are false positives of the stem check:
- 'ignition' in "ignition booster tablets" (`2f9725f504f5`) = "усилитель воспламенения". This is a pyrotechnic term; "зажигание" would mean the engine ignition. The AZ uses glossary "alışdırma".
- 'axle' in GAWR = "нагрузка на ось" / "oxa düşən", the wording used for GAWR in batches 06 and 09.
- 'tire' in the FMVSS 110 title "шин" (genitive plural), and 'frame' in "seatback frame" / "seat frame" = каркас / karkas.
- 'seat belt' as plural or genitive "ремней безопасности". In `d7a59fbd6df6`, 'side air bag' is "driver's side air bag", which means the driver-side bag, not a side air bag.
- 'body' in "body-sensing mat", 'air bag' in "curtain air bag" = шторка безопасности (glossary), and 'wheel' in "long wheel base" = удлинённая база.

**Numbers, dates and names**
- A script compared every digit group in all 78 items, RU and AZ, with the source. Nothing is missing, changed or added.
- Every production date (day, month, year) was compared with the source in RU and AZ by script. Every AZ year suffix (-ci / -cı / -cu / -cü) was checked against the year.
- Each multi-model list was compared with the source by script. The only differences are "а также" / "həmçinin" for a repeated "and" and the Cyrillic "е-трон" (see below).
- These titles match batches 01-10 word for word in RU and AZ: FMVSS 108, 110, 111, 135, 208, 209, 210, 214, 226 and 301, plus 49 CFR Part 567. GAWR and GVWR match batches 05, 06 and 09.

## Changes

- `d05b7e5ed444` **ru**: "неверна, что может привести к перегрузке автомобиля." -> "неверна, из-за чего автомобиль может оказаться перегруженным.". The source says 'which can allow the vehicle to be overloaded'. The wrong label lets the owner overload the car; it does not cause the overload itself. The AZ already says 'imkan verə bilər'.
- `a5d177921536` **ru**: "несовместимости программного обеспечения управления фронтальной камерой и нагревательного элемента" -> "несовместимости программного обеспечения управления фронтальной камерой с нагревательным элементом". 'несовместимость X и Y' reads as two separate things that are each incompatible. The source means an incompatibility between the software and the heating element, which Russian expresses as 'несовместимость чего с чем'.
- `a0899f2aedee` **ru**: "могли быть изготовлены неправильно и при столкновении ненадлежащим образом удерживать людей на передних сиденьях." -> "могли быть изготовлены неправильно, из-за чего при столкновении они могут ненадлежащим образом удерживать людей на передних сиденьях.". 'могли ... удерживать' put the restraint failure in the past ('could have restrained'). The source gives it as what happens in a future crash ('and fail to properly restrain occupants during a crash').
- `a0899f2aedee` **az**: "toqquşma zamanı oturanları lazımi qaydada saxlamaya bilər." -> "toqquşma zamanı ön oturacaqlardakı insanları lazımi qaydada saxlamaya bilər.". 'oturanlar' ('those sitting') is not the term for 'occupants'. The new text matches the RU 'людей на передних сиденьях' and batch 09 (444b7d683edd) 'salondakı insanları'.
- `13e9faa697aa` **ru**: "Эти автомобили были собраны со шторками безопасности в сборе, которые" -> "На эти автомобили были установлены шторки безопасности в сборе, которые". 'собраны ... в сборе' repeats the same root ('assembled with ... assemblies'). 'установлены' keeps the meaning and the glossary form 'в сборе'.
- `a1241bca70fd` **ru**: "в неправильном положении, что допускает утечку топлива." -> "в неправильном положении, из-за чего возможна утечка топлива.". 'что допускает утечку' reads as 'which permits a leak', as if by design. The source 'allowing fuel to leak' is a possible consequence.
- `a1241bca70fd` **az**: "Yanacaq çənindəki şırnaq nasosu səhv vəziyyətdə qaynaq edilmiş ola bilər ki, bu da yanacaq sızmasına imkan verir." -> "Yanacaq çənindəki şırnaqlı nasos səhv vəziyyətdə qaynaq edilmiş ola bilər ki, bu da yanacaq sızmasına imkan verər.". Batch 04 (7d0d961390a9) uses 'şırnaqlı nasos' for 'suction jet pump'. The verb after 'ola bilər ki, bu da' is aorist, following the rule set in batches 09-10.
- `0b6c4c6034de` **az**: "bu da gövdənin korroziyasına səbəb olur." -> "bu da gövdənin korroziyasına səbəb olar.". 'imkan verə bilər ki, bu da ...' describes a possible consequence, so the verb is aorist, as in batches 09-10.
- `4dff047dcaa4` **az**: "aşağı düşməsinə səbəb olur." -> "aşağı düşməsinə səbəb olar.". This is the 'baş verə bilər ki, bu da ...' pattern, so the verb is aorist, as in batches 09-10.
- `d2c3cf151bf8` **az**: "idarəetmə blokuna axmasına səbəb olur." -> "idarəetmə blokuna axmasına səbəb olar.". This is the 'burulmuş ola bilər ki, bu da ...' pattern, so the verb is aorist, as in batches 09-10.
- `03bc7213eed0` **az**: "istəmədən qismən dolmasına" -> "təsadüfən qismən dolmasına". 'istəmədən' means 'without wanting to' and needs a person as the agent. For a device acting by itself, batches 05-10 use 'təsadüfən' (b08 4186b86ff22b 'təsadüfən işə düşə bilər').
- `cc3b13ddf890` **az**: "və ya istəmədən açılmasına" -> "və ya təsadüfən açılmasına". 'inadvertent deployment' of an air bag is 'təsadüfən', for the same reason as 03bc7213eed0.
- `4c8bb6aa1efa` **az**: "və bu, yağlamanın çatışmaması səbəbindən diyircəkli yastıqların yeyilməsinə səbəb olar." -> "və bu, yağlama çatışmadığından turbokompressorun yastıqlarının yeyilməsinə səbəb olar.". 'diyircəkli' (rolling-element) adds a bearing type that the source does not state. Batches 02-09 render plain 'bearings' as 'yastıqlar'. The rewrite also removes 'səbəbindən ... səbəb olar', which used the same root twice.
- `d377edb140ca` **az**: "əsas oturacaqlarla" -> "baza oturacaqlarla". 'əsas oturacaqlar' means 'main seats'. The source 'basic seats' is the base version of the seat (RU 'базовыми сиденьями').
- `d377edb140ca` **az**: "sensor döşəkcəsinin gərginliyə məruz qalması" -> "sensor döşəkcəsinin mexaniki yükə məruz qalması". Next to an electrical sensor, 'gərginlik' reads as 'voltage'. The source 'stress' means mechanical load (RU 'нагрузок').
- `c0591ad4e7ab` **az**: "silikat çöküntüləri yığıldıqda sürətlər qutusunun sürət qolu park mövqeyində olmadıqda" -> "silikat çöküntülərinin yığılması səbəbindən sürətlər qutusunun sürət qolu park mövqeyində olmadıqda". Two stacked '-dıqda' clauses ('when ... when ...') made the sentence hard to parse and lost the cause. In the source, the build-up is the cause.
- `c0591ad4e7ab` **ru**: "ключ можно извлечь из замка зажигания, когда" -> "ключ может извлекаться из замка зажигания, когда". The source says 'may enable the key to be removed'. 'можно извлечь' stated it as certain; the new wording restores 'may'.
- `344304a600a8` **az**: "Avtomobilin qapısının açılıb-bağlanması zamanı yaranan kimi vibrasiyalar arxa qapıların uşaq kilidlərinin açılmasına səbəb ola bilər" -> "Vibrasiyalar (məsələn, avtomobilin qapısı açılıb-bağlanarkən yaranan vibrasiyalar) arxa qapıların uşaq kilidlərinin deaktiv olmasına səbəb ola bilər". After a participle, 'yaranan kimi' means 'as soon as they arise', not 'such as'. 'uşaq kilidlərinin açılması' could also be read as the doors opening. The source says the child locks disengage (RU 'выключению блокировки').
- `bdf8a5a9d84c` **az**: "işə salma qüvvəsinin artmasına" -> "əyləcin işə salınması üçün tələb olunan qüvvənin artmasına". 'işə salma qüvvəsi' ('start-up force') is not a term. The source 'actuating force' is the force needed to apply the brakes.
- `b71ddbb17f30` **az**: "birbaşa ötürmə dəyişdirməli sürətlər qutuları (DSG)" -> "birbaşa keçidli sürətlər qutuları (DSG)". 'birbaşa ötürmə dəyişdirməli' is an ungrammatical calque. 'Direct-Shift Transmission' is 'birbaşa keçidli sürətlər qutusu' (RU 'прямого переключения').
- `9547862b2571` **az**: "Bu avtomobillərin bort şəbəkəsində ekran funksiyalarına təsir edən aşağı gərginlik hadisəsi baş verə bilər." -> "Bu avtomobillərin bort şəbəkəsində gərginlik aşağı düşə bilər və bu, ekran funksiyalarına təsir edər.". 'aşağı gərginlik hadisəsi' is a word-for-word calque of 'low-voltage electrical event'. The rewrite says what happens, as the RU does ('может возникнуть пониженное напряжение').
- `fab34f6e119d` **az**: "park mövqeyi seçilməsinə baxmayaraq" -> "park mövqeyinin seçilməsinə baxmayaraq". The subject of a verbal noun takes the genitive: 'park mövqeyinin seçilməsi'.

## Found but not fixed: blocked by the check

These are real defects. The check script rejects a lowercase Latin word in RU as "untranslated" (`i18n_build.check`, the `w.islower()` rule). The same rule runs in `i18n_build.py`, so a corrected text would also be dropped into failed.json at build time. The rehearsal showed this: the corrected texts gave 4 FAILs and were reverted. Fixing them needs the check to accept a lowercase source word inside a name (owner decision), then the following edits:
- `52bb9508392d` **ru**: the company is transliterated as «Тойота Мотор Инжиниринг энд Мэньюфэкчуринг» (Toyota), because the source prints "Engineering & manufacturing" in lowercase. It should be "Toyota Motor Engineering & Manufacturing (Toyota)", as in the other three Toyota Motor Engineering items of this batch. Batch 03 `adf15e706e10` has the same transliteration.
- `7dee92d5cf6e` **ru** "A3 е-трон" and `3bef18c1afee` **ru** "RS е-трон GT, е-трон GT, Q4 е-трон Sportback, Q4 е-трон, е-трон Quattro, е-трон Sportback Quattro": these model names were changed to Cyrillic and should be "e-tron" as printed. The AZ keeps "e-tron". Batch 04 `236a985da7a7` RU has "A3 е-трон" too.
- `d34a958a6e8c` **ru**: "отзывает некоторые оснащённые шинами Continental автомобили Atlas ..." is grammatical but bookish. The natural order, which puts "..., оснащённые шинами Continental." at the end, fails because of the trailing period. The check reads "Continental." as a Latin word that is not in the source. The current text was kept.

## Seen and left as is

- `e665497776eb` ru "стойки С кузова" uses a Cyrillic "С" for the C-pillar. Batch 08 does the same ("стойки А кузова", "стойку С кузова"), so it was kept for consistency.
- `faa20e00e958`: the source misspells the brand as "(Volkswaen)", and RU/AZ write "(Volkswagen)". This corrects an obvious typo in a name and was kept.
- `03bc7213eed0`: the source has "Engineering and Manufacturing", and RU/AZ use "&" as in the other Toyota items. This was kept.
- `0b6c4c6034de` ru "в газогенераторе может произойти излом" follows glossary 'fracture' = "излом". `1402cc0640ef` / `0d8335c0e3c6` az "düzgün açılmaya bilər" / "düzgün açmaya bilər" for "deploy improperly" follows batch 01 (`972c5c20c252`).
- `f6c248d98ce1` az "1,4 l mühərriklə": batches 02-09 use both "1,4 l" and "litrlik". "mühərrik tutula bilər" for "seize" follows batch 09 (`9023fb4dc531`).
- `55922d663feb` az "divar qalınlığı kifayət qədər olmadan istehsal edilmiş" is a little heavy but grammatical and correct.
- `0dcb825a9a9f` az "sürücü tərəfdə ... ön təhlükəsizlik yastığı" for "driver frontal airbag" is correct. The glossary form is "sürücünün", but the meaning is the same.
- `357e0a288241` az "əlavə aksesuar yan pillələri" repeats a little ("additional accessory"), but the meaning is correct.
