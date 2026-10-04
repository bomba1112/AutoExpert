# Review of llm/batch_09.json (NHTSA recall summaries, RU/AZ)

Items checked: 78, all `recall_summary`. They are Nissan / INFINITI (68), Southeast Toyota Distributors (4), Tesla (5) and Tenneco (1). Items changed: 19. Field edits: 24 (RU 9, AZ 15). Five items were changed in both languages: `7b9510ff9d98`, `856108543e41`, `80ae04b88c1e`, `c4d182aebe82` and `29b427af2428`.

**How the file was written**
- Before the review, the file was backed up to the scratchpad as `b09/batch_09.backup.json` (sha256 680b52f0...).
- One script (`b09/apply.py`) applied the edits to a copy first. The copy passed `check 09` against a copy of the batch and the glossary.
- The real file was confirmed unchanged since the backup (same sha256). The same script then wrote it.
- The result is byte-identical to the copy (sha256 d4ab53e8...).
- The 78 kind/hash pairs and their order did not change. The file keeps its formatting: indent 1, CRLF, no trailing newline.

**Check results:** `scripts/i18n_batches.py check 09` gives 78 pass, 0 fail, both before and after the edits.

The number of GLOSSARY lines went from 17 to 18. The new line is "seat belt" in `444b7d683edd`, because the plural "ремни" fails the 'реме' stem check. All 18 lines are false positives of the stem check or intended forms:
- "frame" in "seat frame" / "seatback frame" = каркас / karkas.
- "seat belt" in plural or genitive forms "ремней" / "ремни".
- "leak" in "leak into" = проникать (water getting in, not a fluid leak).
- "wheel" in "front wheel drive" = передний привод.
- "body" in "throttle body" = дроссельный узел / drossel qovşağı.
- "engine" in "engine compartment" = моторный отсек.
- "axle" in "Gross Axle Weight Rating" = нагрузка на ось / oxa düşən yük. A rated axle load is "ось", not a drive "мост".
- "tire" in the FMVSS 110 title, genitive plural "шин".

**Numbers, dates and names**
- A script compared every digit group in all 78 items, RU and AZ, with the source. Nothing is missing, changed or added: 41,388 / 4,536 / 10,000 are written with a space, and 2.0L / 2.5 / 1.5L with a decimal comma. "Altima 3.5" stays as a model name.
- All 65 production dates were checked for day, month name, year and order. They are correct in RU and in AZ.
- The model-year groups of the multi-model lists were read against the source by hand: `cb9de2557d37`, `68c6ca44076a`, `c6474b30d1b2`, `4b8d4a1115db`, `393b5bc045af`, `f550ceb591d7`, `b9450baaa018`, `cbb084e83318`, `d6397ce4af43`, `f1e1723d2f2a`, `02bac0489d7a`, `fd859184b2db`, `5e44eeea94c9`, `7bc05bd0560e`, `b973418b9599`, `e41f0d0abad6` and `172e8a82feb5`.
- These titles match batches 01-08 word for word in RU and AZ:
  - FMVSS 108, 110 (short, "for Passenger Cars" and the long GVWR title)
  - FMVSS 111, 114, 202a, 205, 207, 208, 209, 210, 225 and 301

  FMVSS 113 «Система защёлки капота» / «Kapot cəftəsi sistemi» appears for the first time here and follows the glossary 'hood latch'.

## Changes

- `8a83ad6cb959` **az**: "söykənəcək meyl mexanizminin oynaqlarında" -> "söykənəcəyin meyl mexanizminin oynaqlarında". Glossary 'seat recliner' = "söykənəcəyin meyl mexanizmi". The genitive was missing.
- `4b8d4a1115db` **az**: "bir və ya bir neçə şin şinlərin istehsalı zamanı" -> "bir və ya bir neçə şin istehsal zamanı". "şin şinlərin" repeated the noun and reads as an error.
- `7b9510ff9d98` **ru**: "Левая и (или) правая" -> "Левая и/или правая"; **az**: "Sol və (və ya) sağ" -> "Sol və/və ya sağ". "и (или)" / "və (və ya)" is used only in batch 05 and in this batch. Batches 01-04 and 06-08 use "и/или" / "və/və ya".
- `856108543e41` **ru** / **az**: same old -> new as `7b9510ff9d98`, for the same reason.
- `80ae04b88c1e` **ru**: "В левом и (или) правом" -> "В левом и/или правом"; **az**: "Sol və (və ya) sağ" -> "Sol və/və ya sağ". Same reason.
- `c4d182aebe82` **ru**: "левом и (или) правом" -> "левом и/или правом"; **az**: "sol və (və ya) sağ" -> "sol və/və ya sağ". Same reason.
- `135d7cd9c46a` **az**: "bərkidilməsinə mane olur." -> "bərkidilməsinə mane olar.". The clause depends on "ola bilər ki, bu da ...", which describes a possible consequence. The batches use the aorist "olar" in this pattern. The present "olur" states it as a fact.
- `a4a332a5b997` **az**: "Qaynaq tikişlərinin yetərsizliyi" -> "Qaynaq tikişlərinin kifayət qədər möhkəm olmaması". "yetərsiz" is the Turkish "yetersiz". Batches 01-08 never use it and translate "insufficient" with "kifayət qədər" or "qeyri-kafi". The new wording matches the RU "недостаточно прочных сварных швов".
- `ead43c1a6163` **az**: "ayrıla bilən yetərsiz qaynaq tikişləri" -> "kifayət qədər möhkəm olmayan və ayrıla bilən qaynaq tikişləri". Same Turkish form as above.
- `4641c9b1cd0b` **ru**: "Крепёжный элемент, которым ремень безопасности заднего сиденья крепится в точках крепления анкера, мог быть" -> "Крепёжный элемент в точках крепления ремня безопасности заднего сиденья мог быть". The old text said "крепится в точках крепления", which repeats itself, and it added "анкера". The source simply says "the fastener in the rear seat belt anchor attachment points".
- `444b7d683edd` **ru**: "из-за чего ремень безопасности может ненадлежащим образом удерживать пристёгнутого человека." -> "из-за чего ремни безопасности могут не удерживать людей на этих сиденьях должным образом.". The source says "the seat belts ... occupants", in the plural, and is about both front seats. The RU had a single belt and a single person, while the AZ already had "kəmərlərinin ... insanları". This is the same singular/plural error that was fixed in batch 08 (`fe2bd999b8a0`).
- `9023fb4dc531` **az**: "mühərrik podşipniklərinin tutularaq" -> "mühərrikin yastıqlarının tutularaq". "podşipnik" is the Russian loan "подшипник". Batch 06 (`1931fe5cd544`) has "mühərrikin yastıqları" for "engine bearing", and no batch uses "podşipnik".
- `7e51ef882558` **ru**: "в сборе либо может иметь ослабленный или отсутствующий стопорный зажим, что" -> "в сборе, либо его стопорный зажим может быть ослаблен или отсутствовать, что". "иметь отсутствующий зажим" ("to have a missing clip") is an English calque and does not make sense in Russian. The AZ already said "boşalmış ola və ya olmaya bilər".
- `cbb084e83318` **az**: "avtomobil arxa gedişdə olduqda" -> "avtomobil arxa gediş ötürməsində olarkən". The source says "is in reverse", meaning the gear. Batches 01-08 use "arxa gediş ötürməsində olarkən" / "ötürməsinə keçirildikdə", and the RU says "при включённой передаче заднего хода".
- `b28f95c05921` **az**: "kronşteyni uşaq saxlama sistemini (CRS)" -> "kronşteyni kəmər uşaq saxlama sistemini (CRS)". Without a subject, "istifadə edildikdə" read as "when the bracket is used to secure the CRS". It is the belt that is used, as the RU says ("если ремень безопасности используется").
- `9ddd119967ea` **az**: "naqil dəstəsindəki kontakt pini" -> "naqil dəstəsindəki kontakt ucluğu". "pin" is an English word left in the text.
- `e41f0d0abad6` **ru**: "могут быть неправильно установлены аксессуары, установленные компанией SET" -> "могут быть неправильно смонтированы аксессуары, установленные компанией SET". The old text said "установлены ... установленные" in the same clause.
- `29b427af2428` **ru**: "Обжим уплотнения жидкости на главном тормозном цилиндре может быть недостаточным, что может привести к утечке тормозной жидкости или разъединению цилиндра." -> "Обжим уплотнителя главного тормозного цилиндра может быть недостаточным, что может привести к утечке тормозной жидкости или к разъединению частей цилиндра.". There were two problems:
  - "уплотнение жидкости" literally means "compaction of the liquid".
  - "разъединение цилиндра" reads as the cylinder being disconnected from something. The source says "the cylinder to come apart", that is, its parts separate.
- `29b427af2428` **az**: "və ya silindrin ayrılmasına" -> "və ya silindrin hissələrinin bir-birindən ayrılmasına". Same "come apart" error: the old text read as the cylinder detaching.
- `5ab891ac2206` **az**: "Sürücü tərəfdəki günlükdə" -> "Sürücü tərəfdəki günəşlikdə". In Azerbaijani "günlük" means "parasol" or "daily", which is the Turkish sense. Batches 04, 07 and 08 use "günəşlik" for "sun visor".

## Seen and left as is

- `4b8d4a1115db` ru "отзывает некоторые оснащённые шинами Continental автомобили (...)" and `6b90d056331d` ru "отзывает некоторые оснащённые рулевыми рейками Bosch автомобили Tesla Model S ...". Batch 08 moved this kind of participle phrase after the noun. Here, any word order with the phrase after the noun ends the sentence on "Continental." / "Bosch.". The check would then read that as a new Latin token, because the source has "Continental tires" / "Bosch steering racks". The short phrase placed before the noun is correct Russian, so it was kept. Batch 05 has the same construction (Hankook).
- `cb9de2557d37` "может раскрыться неправильно" and `fe5da3008d81` "могут раскрыться не так, как предусмотрено", for "may not properly deploy" / "not to deploy as intended", are kept. These are the wordings of batch 01 (`544e3f85e04a`) and batch 08 (`37d646f1d258`).
- `a3310b3f2b23` RU "зона щитка передка" against AZ "ön şüşənin altındakı panel zonası" for "cowl area". Both are acceptable, and batch 08 (`e256ac167f24`) uses "щиток передка" for the cowl.
- `72c2b9d0570e` az "stop-siqnallar yanılı qalar" is the same wording as batch 08 `977e14777b53`, which had the same source text. It was kept.
- `135d7cd9c46a` az "məftil skobaları" for "tether wires": "skoba" is in common Azerbaijani technical use. No earlier batch has this term.
- `d6397ce4af43` ru has nested parentheses "(... Infiniti Q70 (только автомобили с двигателем V8), а также QX80)". These come from the source "(V8 engine vehicles only)" inside the house list format, so they were kept.
- Typos in the source are kept as printed: "Infinity" in `f550ceb591d7` and "Inc.'s (Nissan)" in `40c13b80fe4f` / `b973418b9599`. "Direct Adaptive Steering" stays as a system name.
