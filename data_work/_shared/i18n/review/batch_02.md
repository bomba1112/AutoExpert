# Review of llm/batch_02.json (NHTSA recall summaries, RU/AZ)

Items checked: 78 (all `recall_summary`). Items changed: 17. Field edits: 25 in 24 fields (RU 16, AZ 9 edits in 8 fields).

Check after the edits: `scripts/i18n_batches.py check 02` -> 78 pass, 0 fail. The 25 GLOSSARY lines that remain are false positives of the stem check. They come from inflected forms ("ремня безопасности", "шин", "раме"), from a term inside a longer glossary term ("seat" in "seat belt", "engine" in "engine compartment" = моторный отсек, "steering" in "electric power steering" = электроусилитель руля, "wheel" in "steering wheel" = sükan çarxı), from "frame" in "seat cushion frame" = каркас, from "hybrid battery" (a traction battery, not the 12 V аккумулятор), or from a model name ("RAV 4 Plug-in Hybrid").

A script compared the model years, dates, campaign numbers (15V-568, 17V-152, 17V-226), FMVSS numbers, software versions and model names in all 78 items. No number is missing, changed or added, and no model name was dropped. In `9b9137eb52e1`, "model year 2016", given three times in the source, is said once ("2016 модельного года" / "2016 model ilinə aid") and covers all three models. The FMVSS titles match the wording reviewed in batch 01 (108, 110, 111, 114, 118, 208). Titles new in this batch (102, 103, 126, 141, 207, 401) were checked against the English.

## Most serious errors

1. `2a89b46e2419` az + ru (BMW PHEV battery short circuit): "Boş qalmış qaynaq damcıları" means weld beads "left empty / idle", not loose (detached) beads, so the cause of the short circuit was lost. The RU had "сварочные наплывы", which is a different weld defect (overlap). It was replaced with "Незакреплённые капли сварочного металла".
2. `f2a8828c1285` ru + az (GM shift cable): "transmission shift lever" was rendered as the cabin gear lever ("рычаг переключения передач" / "sürət qolu"). The cable adjuster detaches from the lever on the gearbox. The RU also used the calque "затронутых".
3. `c56d320c104e` ru (BMW Pirelli tyres): "отдельными шинами Pirelli" ("separate tyres") is a calque of "certain". The model list in parentheses directly after "Pirelli" read as a list of tyre types.
4. `099b27209c67` ru (Hyundai curtain air bags): the subject switched from "шторки" to "подушки безопасности" in the consequence. "not to deploy as intended" became "могут не раскрыться должным образом". `06b7fb139ebd` ru: "может работать неисправно ... что приводит" turned the possible consequence into a statement of fact.
5. `41cc2833ad1b` az: piston oil rings were called "yağtutan halqaları" (oil-catching rings). The term is "yağsıyırıcı halqalar". The same item and `ecab56d83309`, `d2c756df4979` and `8de52394feb9` left the Latin litre unit in the Russian ("2.0l", "2.0L", "2.5L" -> "2,0 л", "2,5 л").

## Noted, not changed

- `ecab56d83309` ru: "A4 allroad" is written "A4 Олроуд". The check rejects a lower-case Latin word in RU ("untranslated") and a capitalised "Allroad" that is not in this source text, so the model name cannot stay in Latin here. Other items whose source writes "Allroad" keep it in Latin. Fixing this needs `allroad` to be accepted as a name in `scripts/i18n_build.py`.
- "указанных модельных годов" / "aşağıdakı model illərinə aid" (`be24445e81bb`) and "Aidiyyəti olan avtomobillər" (AZ for "affected vehicles") were left as they are. Batch 01 uses the same house style, and the AZ phrase is normal official wording.

## All changes

Format: hash prefix, field: old -> new. Reason.

- `4a6b76f18d0b` **ru**: "из-за чего соединение может разъединиться, а подушка" -> "из-за чего соединение может нарушиться, а подушка". tautology 'соединение ... разъединиться' (the connection disconnects); 'separate' = the connection breaks
- `ecab56d83309` **ru**: "двигателями 2.0l Turbo FSI" -> "двигателями 2,0 л Turbo FSI". Latin unit 'l' left in Russian text; Russian writes the litre as 'л' with a decimal comma
- `ecab56d83309` **az**: "2.0l Turbo FSI mühərrikləri" -> "2,0 l Turbo FSI mühərrikləri". decimal comma and spaced unit as written in Azerbaijani
- `d2c756df4979` **ru**: "двигателями 2.0l Turbo FSI" -> "двигателями 2,0 л Turbo FSI". Latin unit 'l' left in Russian text
- `d2c756df4979` **az**: "2.0l Turbo FSI mühərrikləri" -> "2,0 l Turbo FSI mühərrikləri". decimal comma and spaced unit as written in Azerbaijani
- `06b7fb139ebd` **ru**: "Камера заднего вида может работать неисправно в течение цикла зажигания, что приводит к появлению чёрного экрана или зависанию мультимедийной системы." -> "В течение цикла зажигания в работе камеры заднего вида может возникнуть неисправность, что приведёт к появлению чёрного экрана или зависанию мультимедийной системы.". 'может работать неисправно' is unnatural; 'что приводит' states the consequence as a general fact instead of the result of the possible malfunction
- `be24445e81bb` **ru**: "На затронутых автомобилях посторонние частицы" -> "На этих автомобилях посторонние частицы". calque of 'affected vehicles' (same fix as in batch 01)
- `be24445e81bb` **az**: "sisteminin sükan spiral kabelini" -> "sisteminin sükanın spiral kabelini". glossary: clockspring = 'sükanın spiral kabeli'
- `e7ac726e87f2` **ru**: "При сборке затронутых автомобилей" -> "При сборке этих автомобилей". calque of 'affected vehicles'
- `2a89b46e2419` **ru**: "Отделившиеся сварочные наплывы могут образовать токопроводящую цепь" -> "Незакреплённые капли сварочного металла могут образовать токопроводящий путь". 'сварочный наплыв' is a weld defect (metal flowed onto the base without fusion), not loose weld beads; 'path' = путь
- `2a89b46e2419` **az**: "Boş qalmış qaynaq damcıları hibrid batareyasının elementləri" -> "Qopub ayrılmış qaynaq damcıları hibrid batareyanın elementləri". 'boş qalmış' means 'left empty / idle', not 'loose (detached)'; 'hibrid' is an attribute, so 'hibrid batareyanın' (no possessive -sı)
- `4052028d30a7` **ru**: "Подголовники крайних сидений второго ряда могут быть неподходящего для данного автомобиля типа." -> "На крайних сиденьях второго ряда могут быть установлены подголовники неподходящего для данного автомобиля типа.". unnatural word order 'могут быть неподходящего ... типа'
- `c56d320c104e` **ru**: "отзывает некоторые автомобили, оснащённые отдельными шинами Pirelli (2021 X6 (sDrive40i, xDrive40i и M50i) и X5 (sDrive40i, xDrive40i и M50i))." -> "отзывает некоторые автомобили, оснащённые определёнными шинами Pirelli: 2021 X6 (sDrive40i, xDrive40i и M50i) и X5 (sDrive40i, xDrive40i и M50i).". 'отдельными шинами' is a calque of 'certain' (reads as 'separate tyres'); the model list placed after 'Pirelli' read as a list of tyre types
- `77c847571da7` **az**: "kifayət qədər işığı əks etdirməyə bilər" -> "kifayət qədər işıq əks etdirməyə bilər". indefinite object after 'kifayət qədər' takes no accusative -ı
- `f2a8828c1285` **ru**: "На затронутых автомобилях регулятор троса переключения передач может отсоединиться от рычага переключения передач." -> "На этих автомобилях регулятор троса переключения передач может отсоединиться от рычага переключения на коробке передач.". calque 'затронутых'; 'transmission shift lever' is the lever on the gearbox, not the cabin gear lever
- `f2a8828c1285` **az**: "tənzimləyicisi sürət qolundan ayrıla bilər" -> "tənzimləyicisi sürətlər qutusunun üzərindəki sürət qolundan ayrıla bilər". 'transmission shift lever' is the lever on the gearbox; 'sürət qolu' alone is the cabin gear lever
- `6dd6129f4efd` **ru**: "Затронутые автомобили оснащены" -> "Эти автомобили оснащены". calque of 'affected vehicles'
- `90aa0ae01078` **ru**: "На затронутых автомобилях тяги" -> "На этих автомобилях тяги". calque of 'affected vehicles'
- `a3a382d21eff` **ru**: "На затронутых автомобилях трос" -> "На этих автомобилях трос". calque of 'affected vehicles'
- `41cc2833ad1b` **ru**: "с двигателями 2.0L Nu MPI" -> "с двигателями 2,0 л Nu MPI". Latin unit 'L' left in Russian text
- `41cc2833ad1b` **az**: "2.0L Nu MPI mühərrikləri" -> "2,0 l Nu MPI mühərrikləri". decimal comma and Azerbaijani unit
- `41cc2833ad1b` **az**: "Porşenlərin yağtutan halqaları" -> "Porşenlərin yağsıyırıcı halqaları". piston oil (control) rings are 'yağsıyırıcı halqalar'; 'yağtutan' (oil-catching) is not the term
- `8de52394feb9` **ru**: "двигателями 2.5L с турбонаддувом" -> "двигателями 2,5 л с турбонаддувом". Latin unit 'L' left in Russian text
- `8de52394feb9` **az**: "turbokompressorlu 2.5L mühərrikləri" -> "turbokompressorlu 2,5 l mühərrikləri". decimal comma and Azerbaijani unit
- `099b27209c67` **ru**: "из-за чего подушки безопасности могут не раскрыться должным образом." -> "из-за чего шторки могут раскрыться не так, как предусмотрено.". the subject switched from 'шторки' to 'подушки безопасности'; 'not deploy as intended' = deploy other than designed, not 'may fail to deploy properly'
