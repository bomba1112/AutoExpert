# Review of llm/batch_07.json (NHTSA recall summaries, RU/AZ)

Items checked: 78 (all `recall_summary`: Hyundai/Genesis, Jaguar Land Rover, Kia). Items changed: 12. Field edits: 15 in 14 fields (RU 6 edits in 6 fields, AZ 9 edits in 8 fields; `0747a6c33bca` az has two edits). Two items were changed in both languages: `0b0eedf0c2f7` and `e914a58aadb8`. Four were changed in RU only (`74b8db9efa20`, `32f67c798564`, `bf6f30165329`, `b11022d01fae`) and six in AZ only (`8fe8127da838`, `0747a6c33bca`, `464e5da559f7`, `4f66bdefb236`, `e7fe509c3f85`, `1cacabf2c72f`).

Before the review the file was backed up to the scratchpad as `batch_07.backup.json` (sha256 ab1b44e7...). One script applied the edits to a copy first, and the copy passed the same checks. The real file was confirmed unchanged since the backup (same sha256) and then written by the same script. It is byte-identical to the copy (sha256 73e5e69a...). The 78 kind/hash pairs and their order did not change, and the file keeps its formatting (indent 1, CRLF, no trailing newline).

The check after the edits, `scripts/i18n_batches.py check 07`, gives 78 pass, 0 fail. The run shows 38 GLOSSARY lines, the same 38 as before the review. All are false positives of the stem check or intended forms:
- **Model names:** "plug-in hybrid" in Santa Fe / Tucson / Sorento / Sportage / Niro "Plug-In Hybrid (Electric)". These are model names and stay as printed, as in batch 06 (`442ed5a0e208`).
- **A term inside a longer term:** "seat" and "seat belt" written as "ремней/ремня безопасности" (stem 'реме' vs 'ремн'); "seat belt buckle" = "замок ремня безопасности" in an oblique form; "engine" in "engine compartment" = моторный отсек; "steering" in "power steering" = усилитель руля; "wheel" in "steering wheel" = sükan çarxı; "frame" in "seat frame" = каркас / karkas; "leak" in "water may leak into" = просачиваться (water entering a camera, not a fluid leak).

A script compared all numbers in all 78 items, RU and AZ (none missing, changed or added; "4.2" is now "4,2" with the same digits). It also checked:
- all 32 dates in the 15 dated items (production dates plus the two recall dates in `8b2bbf066d05`), with day, month, year and order in RU and AZ;
- every Azerbaijani ordinal suffix after a year (2009-cu, 2011/2015/2020-ci, 2013/2014-cü, 2016-cı), all correct;
- the model-year sets of the multi-model items, read against the source by hand.

The script found no mixed Latin/Cyrillic words and no Cyrillic in AZ. It found no Turkish forms (ve, ile, için, değil, olarak, veya, araç, fren, kemer, lastik ...). The hits for "ğı" are Azerbaijani forms (yastığı), and "sürüşə" in `3cfe41cebc09` is AZ "sürüşmək" (to slip out of place). The FMVSS titles were compared with batches 01-06: 108, 110, 111, 118 (long title, as batch 05 `929d9f021fd1`), 135, 138, 141, 208 and 209 match. 101 "Controls and Displays" is new. It was checked against the English, and its five occurrences are identical.

## Most serious errors

1. **`0b0eedf0c2f7` ru + az (Land Rover clockspring connector):** "Разъём спирального кабеля рулевого колеса подушки безопасности водителя" was a chain of four genitives, so the steering wheel's spiral cable belonged to the air bag. The AZ "Sürücünün təhlükəsizlik yastığının sükanın spiral kabelinin birləşdiricisi" stacked four genitives with no head relation and does not parse. Both now say what the source says: the clockspring connector that serves the driver air bag ("Разъём спирального кабеля рулевого колеса для подушки безопасности водителя" / "Sükanın spiral kabelində sürücünün təhlükəsizlik yastığına aid birləşdirici").
2. **Wrong part named as the assembly (RU "в сборе" misplaced):**
   - `bf6f30165329` ru (Kia shift lever): "компонентами рычага переключения передач автоматической коробки передач в сборе" made the automatic transmission the assembly. The source names the shift lever assembly. It is now "компонентами узла рычага переключения передач автоматической коробки передач".
   - `32f67c798564` ru (Idle Stop & Go): "масляного насоса системы Idle Stop & Go в сборе" made the system the assembly. It is now "масляного насоса в сборе системы Idle Stop & Go", the same word order batch 01 (`7236c2744ce1`) used for the same part.
3. **Added or changed meaning in RU:**
   - `74b8db9efa20`: "insufficiently welded" became "недостаточно проварен", which adds a weld-penetration diagnosis. Batch 06 made the same fix (`6885cd768499`). It is now "недостаточно качественно сварен".
   - `b11022d01fae`: "and the vehicle is driven" became "автомобиль продолжает движение", which assumes the car was already moving when the latch was released. It is now "автомобиль движется".
4. **AZ words and forms that are not standard Azerbaijani or do not parse:**
   - `0747a6c33bca` and `464e5da559f7`: "daim yanılı qalır / qalacaq". 'yanılı' is not standard, the same defect fixed in batches 03 and 04. It is now "yanar vəziyyətdə".
   - `0747a6c33bca`: "aksessuar yedəkləmə qurğusu naqil dəstəsi" lacked the izafet ending. It is now "yedəkləmə qurğusunun naqil dəstəsi", as in `6bb03c75f22b`.
   - `1cacabf2c72f`: "sürətölçən və odometrin ölçü vahidlərini" lacked the genitive on 'sürətölçən', and "sürücünün displey blokuna əmri olmadan" was a calque. The sentence now follows the RU structure.
   - `4f66bdefb236`: the shift cable was "keçid trosu" (transition cable). It is now "sürətlərin dəyişdirilməsi trosu", the term fixed in batches 04 and 05.
   - `e7fe509c3f85`: "sürüş şəraitində" is now "hərəkət şəraitində", as in batches 04 and 05.
5. **Wrong sense or typography:**
   - `8fe8127da838` az: "deploy unintentionally" was "gözlənilmədən açılma" (unexpectedly / without warning). It is now "qeyri-ixtiyari açılma", as in batch 01 (`2dc1129ab1df`) and in the RU "непреднамеренному раскрытию".
   - `e914a58aadb8` ru + az: the screen size was written 4.2" with an English decimal point and inch mark. It is now "диагональю 4,2 дюйма" / "4,2 düymlük", with a decimal comma as in batch 03 ("2,5 л").

## Noted, not changed

- `ea785019698d`: the source has the typo "Occupation Crash Protection" for FMVSS 208. RU/AZ use the standard title «Защита людей в салоне при столкновении» / «Toqquşma zamanı salondakıların qorunması», as in every other item. This is the real title of the standard, not added content.
- `d6ec9bbb6c83` az: "müəyyən edə bilməyə bilər" is kept. The source says "may not be able to determine", and 'edə bilməyə bilər' is the standard AZ form for "may be unable to". It is not the case batch 06 fixed in `47edc4d54c9f`, where the source said "may fail to prevent" and there was no 'able'.
- `fbd12bb8334a`: "seat belt anchors may detach" = "Элементы крепления ремней безопасности / təhlükəsizlik kəmərlərinin bərkidilmə elementləri". The glossary "seat belt anchorage = точка крепления" names a location, and a location cannot detach. The physical anchor part is meant, so this was kept.
- `fbd12bb8334a` and `1fa1d18cdac3` keep the source's model-year structure. "Hyundai Santa Fe Hybrid" in `fbd12bb8334a` has no year of its own in the source, and the RU/AZ lists do not invent one.
- `f8b9668d5fb6`: "equipped with the panoramic sunroof option" follows the second group (Sonata) in RU and AZ, as in the source. The source is ambiguous and the translation keeps that ambiguity.
- `8d315d72a02f` ru "встроенный центральный блок управления (ICU)" for "Integrated Central Control Unit". "Встроенный" for "integrated" is the wording batch 01 used for BMW "Integrated Brake" (`68487ad959a9` etc.).
- `1d2ffe7728cf`, `b3115e58761d`, `1fa1d18cdac3`, `2adb01e04d68`: "Plug-In Hybrid Electric (PHEV)" and "HPCU" are kept as model name and glossary abbreviation.
- `4e199b6f5cd6` has the same English sentence as batch 06 `ef56d834ddc8` (K5 vs Sonata check valve). The RU differs only in "оплавлению бака" vs "его оплавлению". The AZ uses "bu da ... səbəb olur" where batch 06 has "; bu zaman ...". Both are correct, so they were not aligned.
- `1fa1d18cdac3` / `2adb01e04d68` ru "может отказать дисплей приборной панели" vs batch 03 `ecbbe6f659bc` "может выйти из строя". Both render "may fail" correctly. Kept.
- `d534f7dc8014` ru "центральных стойках кузова" (B-pillar). Batch 03 `dff4c1318a30` has "средней стойке". Both are standard Russian for the B-pillar. Kept.
- `464e5da559f7` ru "Демпфер упора педали тормоза может разрушиться" for "stopper pad can deteriorate". The pad crumbles, which is the failure in this recall. The AZ "xarab ola bilər" is neutral. Kept.

## All changes

Format: hash prefix, field: old -> new. Reason.

- `8fe8127da838` **az**: "təhlükəsizlik yastıqlarının gözlənilmədən açılmasına" -> "təhlükəsizlik yastıqlarının qeyri-ixtiyari açılmasına". 'deploy unintentionally' is 'qeyri-ixtiyari açılma' (batch 01 2dc1129ab1df); 'gözlənilmədən' means 'unexpectedly', the wording batch 06 used for 'deploy without warning'
- `0747a6c33bca` **az**: "ehtiyat hissə kimi satılan aksessuar yedəkləmə qurğusu naqil dəstəsi ilə" -> "ehtiyat hissə kimi satılan aksessuar yedəkləmə qurğusunun naqil dəstəsi ilə". missing izafet (genitive) ending: 'trailer hitch harness' is 'yedəkləmə qurğusunun naqil dəstəsi', as in 6bb03c75f22b
- `0747a6c33bca` **az**: "ya da daim yanılı qalır (yanıb-sönmür)" -> "ya da daim yanar vəziyyətdə qalır (yanıb-sönmür)". 'yanılı' is not a standard Azerbaijani word; same fix as batch 03 (88ac87656adf) and batch 04 (c4cf7c5f794b)
- `464e5da559f7` **az**: "Nəticədə stop-siqnallar daim yanılı qalacaq." -> "Nəticədə stop-siqnallar daim yanar vəziyyətdə qalacaq.". 'yanılı' is not a standard Azerbaijani word; same fix as batches 03 and 04
- `4f66bdefb236` **az**: "sürətlər qutusunun keçid trosu sürət qolunun barmağından" -> "sürətlərin dəyişdirilməsi trosu sürət qolunun barmağından". 'keçid trosu' (passage / transition cable) is not the AZ name of the shift cable; batch 04 (c998b01be17a) and batch 05 (0860a884cce9, 4397c54f966e) use 'sürətlərin dəyişdirilməsi trosu'
- `e7fe509c3f85` **az**: "Müəyyən sürüş şəraitində" -> "Müəyyən hərəkət şəraitində". 'certain driving conditions' is 'müəyyən hərəkət şəraiti' in batches 04 and 05 (4fac07b97a75, fd4d884aa03f, aff95537cd79); 'sürüş' reads as a Turkish form
- `1cacabf2c72f` **az**: "Proqram təminatı xətası cihazlar blokunun sürətölçən və odometrin ölçü vahidlərini sürücünün displey blokuna əmri olmadan saatda mil (MPH) və saatda kilometr (KM/H) arasında təsadüfi olaraq dəyişdirməsinə səbəb ola bilər." -> "Proqram təminatı xətası səbəbindən cihazlar bloku sürətölçənin və odometrin ölçü vahidlərini sürücü displey blokuna əmr vermədən saatda mil (MPH) və saatda kilometr (KM/H) arasında təsadüfi olaraq dəyişdirə bilər.". 'sürətölçən' lacked the genitive ending that 'odometrin' has (both govern 'ölçü vahidləri'), so the phrase did not parse; 'sürücünün ... əmri olmadan' was a stiff calque of 'without driver input'. The sentence now follows the RU structure (due to a software error the cluster may switch the units)
- `0b0eedf0c2f7` **ru**: "Разъём спирального кабеля рулевого колеса подушки безопасности водителя может" -> "Разъём спирального кабеля рулевого колеса для подушки безопасности водителя может". a chain of four genitives made the clockspring belong to the air bag ('steering wheel of the driver's air bag'); the connector is on the clockspring and serves the driver air bag
- `0b0eedf0c2f7` **az**: "Sürücünün təhlükəsizlik yastığının sükanın spiral kabelinin birləşdiricisi korroziyaya uğraya bilər" -> "Sükanın spiral kabelində sürücünün təhlükəsizlik yastığına aid birləşdirici korroziyaya uğraya bilər". four stacked genitives with no head relation ('of the driver's air bag of the steering wheel's spiral cable connector') are ungrammatical; the connector is in the clockspring and belongs to the driver air bag
- `74b8db9efa20` **ru**: "мог быть недостаточно проварен" -> "мог быть недостаточно качественно сварен". 'insufficiently welded' names no specific defect; 'проварен' implies weld penetration. Same fix as batch 06 (6885cd768499) and the wording of batches 02/03 ('недостаточно качественно сварено')
- `32f67c798564` **ru**: "Электронный контроллер масляного насоса системы Idle Stop & Go в сборе" -> "Электронный контроллер масляного насоса в сборе системы Idle Stop & Go". 'в сборе' at the end attached to the Idle Stop & Go system; the source assembly is the oil pump assembly. Word order as batch 01 (7236c2744ce1), the same part
- `bf6f30165329` **ru**: "с неисправными компонентами рычага переключения передач автоматической коробки передач в сборе" -> "с неисправными компонентами узла рычага переключения передач автоматической коробки передач". 'в сборе' at the end made the automatic transmission the assembly; the source names the shift lever assembly ('узел', as batch 05 c60177e4f887)
- `e914a58aadb8` **ru**: "с жидкокристаллическим экраном (LCD) 4.2"" -> "с жидкокристаллическим экраном (LCD) диагональю 4,2 дюйма". Russian uses a decimal comma and writes the inch unit out (batch 03 '2,5 л', batch 02 '21-дюймовыми'); the English inch mark is not Russian typography
- `e914a58aadb8` **az**: "4.2" LCD ekranlı" -> "4,2 düymlük LCD ekranlı". Azerbaijani uses a decimal comma (batch 03 '2,5 l'); the inch is 'düymlük' (batches 02 and 05), not the English inch mark
- `b11022d01fae` **ru**: "основная защёлка капота была открыта и автомобиль продолжает движение" -> "основная защёлка капота была открыта и автомобиль движется". 'and the vehicle is driven' does not say the car was already moving when the latch was released; 'продолжает движение' adds that
