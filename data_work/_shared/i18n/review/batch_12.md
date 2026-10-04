# Review of llm/batch_12.json (NHTSA recall summaries, RU/AZ)

Items checked: 68, all `recall_summary`. 67 are filed as "Volkswagen Group of America, Inc. (Volkswagen)" and one as "Volkswagen Group of North America (Volkswagen)". They cover Audi and VW models from 2009 to 2026. Items changed: 20. Field edits: 23 (RU 8, AZ 15) in 22 fields. `44c3f27c0feb` and `1b39b560a795` were changed in both languages. `fcd77971b6e3` AZ has two edits.

**How the file was written**
- Before the review, the file was backed up to the scratchpad as `b12/batch_12.backup.json` (sha256 f8385714...).
- One script (`b12/apply.py`, edit list `b12/edits.py`) first applied the edits to a copy, `b12/batch_12.copy.json`. The number, name and date scripts were then run on the copy.
- The script confirmed that the real file still had the backup's sha256, then wrote it. Final sha256: c412cdf7...
- The 68 kind/hash pairs and their order did not change. The file keeps its formatting: indent 1, CRLF, no trailing newline.
- One planned edit (`32a7fcb9a9dc` RU) made `check 12` fail. It was dropped, the backup was restored, and the remaining 23 edits were applied again. See "Found but not fixed".

**Check results:** before the review, `scripts/i18n_batches.py check 12` gave 68 pass, 0 fail, with 20 GLOSSARY lines. After it gives 68 pass, 0 fail, with 21 GLOSSARY lines. The extra line comes from `ac4b0dc0d0f9`, where 'crash' is not rendered as 'столкновение': "side impact crash" is now "при боковом ударе", the batch 03 wording (7afd8526dbd5). All 21 lines are false positives of the stem check:
- 'steering' in "steering knuckle" (поворотный кулак / dönmə yumruğu, `5039df18f78b`, `843ed74a6f5c`) and in "power steering" (усилитель руля, `3318f96d2075`).
- 'battery' in "high-voltage battery" and "hybrid battery" = высоковольтная батарея / yüksək gərginlikli batareya (glossary), in `72bb12c8fdfe`, `72a054185719` and `03cf695696de`.
- 'trailer' in "trailer hitch" = тягово-сцепное устройство / yedəkləmə qurğusu (glossary), `4d3431788e59`.
- 'wheel' in "long wheel base" = удлинённая колёсная база (`dc60f741442e`, `ea3201424242`). 'seat belt' appears in the plural or genitive, "ремней безопасности" (`8ce32c29ec1d`, `fa9aabb5f35b`, `e23ed7d0097d`).
- 'tie rod' in `e2819f93ff85`: the part is on the rear axle assembly of a Tiguan, which is not steered. Here a tie rod is the rear toe/track link. RU "поперечная тяга" / AZ "eninə çubuq" fits that part, while the glossary's 'рулевая тяга / sükan çubuğu' would suggest rear steering.

**Numbers, dates and names**
- A script compared every digit group in all 68 items, RU and AZ, with the source. Nothing is missing, changed or added. The only difference is `c75f738515d5` RU, where "2024 Atlas and 2024 Atlas Cross Sport" became "Atlas и Atlas Cross Sport 2024 модельного года". This is the same year, merged.
- All 11 items with full production dates were compared by script (day, month, year) in RU and AZ. Every AZ year suffix (-ci / -cı / -cu / -cü) was checked against its year.
- Every model name and code in the source (Q8, SQ5, RS Q8, ID.4, Atlas PA2, Atlas Cross Sport PA, E-Golf, 2.0TFSI, 4.0L, 255/50 R 20 105 T, 25V082, LWB, PHEV, PODS, BCM, TDI) is present in RU and AZ. Source spellings "Toureg" and "Atlas Cross Sports" are kept as printed.
- These titles match batches 01-11 word for word in RU and AZ: FMVSS 101, 102, 108, 110, 111, 114, 118, 138, 207, 208 and 301, plus 49 CFR Part 567.
- No Turkish forms, Cyrillic letters in the AZ text, or English words were found.

## Changes

- `ac4b0dc0d0f9` **ru**: "при столкновении с боковым ударом." -> "при боковом ударе.". 'столкновение с боковым ударом' reads as 'a collision with a side impact', which is not Russian. The source 'side impact crash' is 'боковой удар', as in batch 03 (7afd8526dbd5 'при боковом ударе') and the FMVSS 214 title 'Защита при боковом ударе'.
- `06652bf40fff` **ru**: "через линию разрыва панели приборов." -> "через линию разрыва приборной панели.". Glossary: INSTRUMENT PANEL = 'Приборная панель'. Batch 08 (37d646f1d258) has 'Линия разрыва приборной панели' for the same tear seam, and 10 of 11 earlier RU renderings of 'instrument panel' use 'приборная панель'.
- `7fb3099b8744` **ru**: "через линию разрыва панели приборов." -> "через линию разрыва приборной панели.". Same as 06652bf40fff: glossary INSTRUMENT PANEL = 'Приборная панель'; batch 08 37d646f1d258.
- `fbe118b2b0d0` **ru**: "каркас панели приборов" -> "каркас приборной панели". Glossary INSTRUMENT PANEL = 'Приборная панель' (same term as 06652bf40fff).
- `0639d1cbdb7e` **ru**: "Панель приборов может не отображать" -> "Приборная панель может не отображать". Glossary INSTRUMENT PANEL = 'Приборная панель'; the AZ already uses the glossary 'Cihazlar paneli'.
- `44c3f27c0feb` **ru**: "на ступице колеса с подшипником ступицы." -> "на ступице колеса с подшипником.". 'ступице колеса с подшипником ступицы' says 'hub' twice ('the wheel hub with the hub bearing'). The source 'wheel bearing hub' is one part, the hub with its bearing.
- `1b39b560a795` **ru**: "из-за чего ось может сместиться, а педаль тормоза — сместиться со своего места." -> "из-за чего ось может перемещаться, а педаль тормоза — сместиться со своего места.". The same verb 'сместиться' was used twice in one clause. The source has two different actions: the pin can 'move', and the pedal can 'dislodge'.
- `c80770571533` **ru**: "Шатунные подшипники двигателя могут быть повреждены," -> "Шатунные подшипники двигателя могут повредиться,". 'могут быть повреждены' reads as 'may already be damaged'. The source 'may become damaged' is a future failure; batch 04 (3f04c6244b94) has the identical sentence as 'могут повредиться'.
- `622942763ff2` **az**: "bu da qaranlıqda sürücünün görmə imkanını azaldır." -> "bu da qaranlıqda sürücünün görmə imkanını azaldar.". This is the 'ola bilər ki, bu da ...' pattern for a possible consequence, so the verb is aorist (batches 09-11).
- `1787e094d340` **az**: "bu da onun açılma qüvvəsinə təsir edir." -> "bu da onun açılma qüvvəsinə təsir edər.". This is the 'qatlanmamış ola bilər ki, bu da ...' pattern, so the verb is aorist (batches 09-11).
- `44c3f27c0feb` **az**: "kifayət qədər bərkidilməsinə mane olur." -> "kifayət qədər bərkidilməsinə mane olar.". This is the 'emal edilməmiş ola bilər ki, bu da ...' pattern, so the verb is aorist (batches 09-11).
- `fcd77971b6e3` **az**: "sürətlər qutusunun torpaqlama naqili" -> "sürətlər qutusunun kütlə naqili". In a car, 'ground' is the body/chassis return ('масса'), not an earth connection. Batch 04 (e55a5952da22) uses 'kütlə' for the ground connection; 'torpaqlama' means earthing.
- `fcd77971b6e3` **az**: "bu da elektrik dövrəsinin qırılmasına səbəb olur." -> "bu da elektrik dövrəsinin qırılmasına səbəb olar.". This is the 'birləşdirilməmiş ola bilər ki, bu da ...' pattern, so the verb is aorist (batches 09-11).
- `1b39b560a795` **az**: "əyləc pedalının yerindən çıxmasına imkan verir." -> "əyləc pedalının yerindən çıxmasına imkan verər.". 'olmaya bilər, bu da ...' describes a possible consequence, so the verb is aorist (batches 09-11).
- `b4b006dc1eab` **az**: "ön sərnişinin təhlükəsizlik yastığını söndürə bilər." -> "ön sərnişinin təhlükəsizlik yastığını deaktiv edə bilər.". 'söndürmək' means 'switch off / extinguish' (used for lights, engines). For an air bag that is deactivated by the system, batches 01-03 use 'deaktiv etmək' (b01 70cedcbbbfda 'təhlükəsizlik yastığını deaktiv edə bilər').
- `372991521cff` **az**: "ön sərnişinin təhlükəsizlik yastığını söndürə bilər." -> "ön sərnişinin təhlükəsizlik yastığını deaktiv edə bilər.". Same as b4b006dc1eab: 'deactivate the air bag' = 'deaktiv etmək' (b01 70cedcbbbfda).
- `6eba1362a62c` **az**: "qoruyucular blokuna zədələnmiş rele quraşdırılmış ola bilər" -> "qoruyucular blokuna zədələnmiş relelər quraşdırılmış ola bilər". The source has 'relays' (plural, specific parts), and the RU has 'реле' in the plural. The AZ singular 'rele' reads as one relay.
- `77867d591635` **az**: "nəticədə arxa görünüş kamerasının təsviri nəzərdə tutulduğu kimi göstərilməyəcək." -> "nəticədə arxa görünüş kamerasının təsviri nəzərdə tutulduğu kimi göstərilməz.". The categorical future 'göstərilməyəcək' ('will not be shown') follows 'xəta baş verə bilər' ('an error may occur'). The consequence is conditional, so the verb is aorist, as in batches 09-11.
- `da7152f2152c` **az**: "avtomobil arxa gediş vəziyyətində olduqda" -> "avtomobil arxa gediş ötürməsində olduqda". 'arxa gediş vəziyyəti' ('reverse state') is vague. 'in reverse' is the reverse gear; batch 01 (34a218621fe9) 'avtomobil arxa gediş ötürməsində olarkən' and b05 4d01e0200317 'Arxa gediş ötürməsi qoşulduqda'.
- `163fc4b5fea3` **az**: "sisteminin yenidən başlamasına səbəb ola bilər." -> "sisteminin yenidən yüklənməsinə səbəb ola bilər.". 'yenidən başlamaq' means 'to start over' (of an action), not a module 'reset'. Batch 01 (0322eb6fc187) uses 'yenidən yüklənə bilər' for a control unit reset; the RU has 'перезагрузка'.
- `87e06eda1856` **az**: "İstehsal buraxılışları ilə bağlı problemlər səbəbindən" -> "İstehsalda yol verilən ölçü kənarlaşmaları ilə bağlı problemlər səbəbindən". 'istehsal buraxılışları' reads as 'production releases / output batches' ('buraxılış' = release, issue, output). The source 'manufacturing tolerance issues' means the permitted dimensional deviations (RU 'производственными допусками').
- `e3cbbad26333` **az**: "iyul 2007-ci ildən iyun 2014-cü ilədək" -> "2007-ci ilin iyulundan 2014-cü ilin iyununadək". 'iyul 2007-ci ildən' puts the ablative on 'il' ('from the year 2007, July'). A month without a day is written 'YYYY-cı ilin <ay>ından'.
- `86c444787650` **az**: "Yüksək təzyiqli yanacaq nasosunu bərkidən bərkidici elementlər lazımi qaydada" -> "Yüksək təzyiqli yanacaq nasosunun bərkidici elementləri lazımi qaydada". 'bərkidən bərkidici elementlər ... bərkidilməmiş' repeats the same root three times in one clause. 'nasosun bərkidici elementləri' says the same, as the RU 'Крепёжные элементы топливного насоса' does.

## Found but not fixed: blocked by the check

- `32a7fcb9a9dc` **ru**: the RU joins the source's two sentences into one with 'поскольку': "отзывает некоторые автомобили Volkswagen Atlas, поскольку из-за ошибки при производстве ... возможна утечка топлива". That adds a causal 'because' and breaks the fixed opening sentence. The AZ keeps two sentences. The fix is "... Volkswagen Atlas. Из-за ошибки при производстве ...". The rehearsal gave 1 FAIL: `i18n_build.check` tokenises "Atlas." with its full stop, so it reads it as a Latin word that is not in the source. This is the same tokenizer limit noted in batch 11 (d34a958a6e8c). The meaning is still correct, so the current text was kept.
- `7e88c9c22392`, `be2407d57a1f`, `87e06eda1856` **ru**: "некоторые оснащённые двигателями TDI автомобили Passat ..." and similar put a long participle phrase before the noun. This is grammatical but bookish. The natural order, which ends the sentence with "..., оснащённые ...", runs into the same tokenizer problem whenever a Latin name comes last. It was kept, as in batch 11.

## Seen and left as is

- `6eba1362a62c` ru "могут непреднамеренно включить" (relays): batches 08-09 use 'непреднамеренно' for devices too (b08 4186b86ff22b 'может срабатывать непреднамеренно'). It was kept for consistency.
- `10187dffc3de`, `e23ed7d0097d`: the multi-model lists keep the source order inside parentheses ("(2019 Golf, ..., 2019–2020 Golf GTI и Jetta)"), as in batches 02-11. This keeps the source's ambiguity about which year applies to the last model.
- `72bb12c8fdfe`: "A7 E Hybrid Electric PHEV" is kept as one model name, in the source order. The source does not say whether "Q5" is the PHEV too, and RU/AZ do not resolve it.
- `24ca9de74237`: "давление накачки" for "inflation pressure" matches batches 04 and 07.
- `dc60f741442e`, `ea3201424242` ru "с удлинённой колёсной базой (LWB)" while batch 11 has "с удлинённой базой (LWB)". Both are correct; the fuller form was kept.
- `0639d1cbdb7e`: the source prints the FMVSS 101 title as "Control and Displays". RU/AZ use the standard title «Органы управления и индикаторы» / «İdarəetmə orqanları və göstəricilər», as in batch 07.
- `86c444787650`: the source says "one Audi SQ7 vehicles". RU/AZ use the singular "один автомобиль" / "bir ... avtomobilini", matching "one".
