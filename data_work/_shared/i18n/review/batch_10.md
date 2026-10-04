# Review of llm/batch_10.json (NHTSA recall summaries, RU/AZ)

Items checked: 78, all `recall_summary`. They are Tesla (26) and Toyota Motor Engineering & Manufacturing (52, one of them filed as "(Lexus)"). Items changed: 19. Field edits: 21 (RU 4, AZ 17). Two items were changed in both languages: `0c2dcdc80999` and `7554769deb53`.

**How the file was written**
- Before the review, the file was backed up to the scratchpad as `b10/batch_10.backup.json` (sha256 a02d6e03...).
- One script (`b10/apply.py`) applied the edits to a copy first. The copy passed `check 10` against a copy of the batch, the glossary and the check scripts.
- The real file was confirmed unchanged since the backup (same sha256). The same script then wrote it.
- The result is byte-identical to the copy (sha256 bb818bd5...).
- The 78 kind/hash pairs and their order did not change. The file keeps its formatting: indent 1, CRLF, no trailing newline.

**Check results:** `scripts/i18n_batches.py check 10` gives 78 pass, 0 fail, both before and after the edits.

The number of GLOSSARY lines went from 26 to 25. The "seat belt" line for `10c35227271f` RU is gone, because the new text says "ремень". All 25 remaining lines are false positives of the stem check:
- "seat" / "seat belt" in plural or genitive forms ("ремней", "ремня", "сидений", "oturacaqlarının").
- "frame" in "sub-frame" = подрамник / köməkçi rama, and in "seat cushion frame" = каркас / karkas.
- "steering" in "steering knuckle" = поворотный кулак / dönmə yumruğu.
- "wheel" in "steering wheel" = sükan çarxı.
- "air bag" in "curtain air bag" = шторка безопасности.
- "plug-in hybrid" inside the model name "Prius Plug-in Hybrid".
- "tire" in the FMVSS 110 title, genitive plural "шин".

**Numbers, dates and names**
- A script compared every digit group in all 78 items, RU and AZ, with the source. Nothing is missing, changed or added. 2,5 л / 3,5 л / 2,5 litrlik use a decimal comma. "Autopilot Computer 2.5" and the software version 2023.38.4 stay as printed.
- All production dates in `860492a91a71`, `6604c8a67c80`, `99b1d32f19e4`, `b666abb52f72`, `0a4203d8642b`, `f9496789794e`, `b971890ee6a3`, `aadf76d6e66e` and `5dd3db65220c` were checked for day, month, year, order and the AZ suffix (-ci / -cı / -cü).
- The model-year groups of the multi-model lists were read against the source by hand: `ab1eec45ef25`, `1fd1b64436f0`, `8b721ca9cc2e`, `0c46db681392`, `8772fdcb5021`, `fea94ba40339`, `d5d7d5dfba42`, `620350a1355c`, `a9ac4344add2`, `44e9ef6b52d3`, `c3b1f8485b16`, `67373628a41b`, `10c35227271f`, `0c2dcdc80999`, `66b4d3ecd975`, `20b534a26c06`, `5eb63f4ceb0a`, `1ad4de312b66`, `87061b9491fc`, `acb665c35b36`, `846359f3624b` and `5ba9ba580b59`.
- `c3b1f8485b16` (zones A, B, C) was checked state by state: 14 / 21 / 21 places in RU and in AZ, with the right vehicle list for each zone.
- These titles match batches 01-09 word for word in RU and AZ: FMVSS 101, 108, 110, 111 ("Rear Visibility" and the older "Rearview Mirrors"), 113, 135, 201, 202, 207, 208, 212, 214, 226 and 301, plus 49 CFR Part 567 and Part 581.

## Changes

- `66b4d3ecd975` **az**: "qırılan sancaqlar" -> "qırılan ştiftlər". "sancaq" is a safety pin, brooch or flag. It is not a machine part. The RU has "срезные штифты", and "ştift" is the Azerbaijani technical word for these steering-column breakaway pins.
- `1ad4de312b66` **az**: "Arxa qapının açarına su daxil olaraq" -> "Arxa qapının elektrik açarına su daxil olaraq". On its own, "qapının açarı" reads as "the door key". The source part is an electrical switch, which is "выключатель" in the RU. "elektrik açarı" removes the ambiguity.
- `1ad4de312b66` **az**: "açılmasına gətirib çıxarır." -> "açılmasına gətirib çıxarar.". The clause depends on "ola bilər ki, bu da ...", which describes a possible consequence. Batch 09 set the aorist for this pattern (`135d7cd9c46a`).
- `ca92917b7428` **az**: same two changes as `1ad4de312b66`, for the same reasons. The source text is the same.
- `0c2dcdc80999` **ru**: "и привести к потере усиления электроусилителя руля." -> "и привести к потере усиления руля.". "усиления электроусилителя" says "boost" twice. Glossary 'loss of power steering assist' = "потеря усиления руля". The EPS is already named earlier in the same text.
- `0c2dcdc80999` **az**: "elektrik sükan gücləndiricisinin köməyinin itməsinə" -> "elektrik sükan gücləndirməsinin itməsinə". "gücləndiricinin köməyi" ("the help of the booster") does not follow glossary 'loss of power steering assist' = "sükan gücləndirməsinin itməsi".
- `99b1d32f19e4` **az**: "əyləcləri tətbiq edə bilər." -> "avtomobili əyləcləyə bilər.". "əyləcləri tətbiq etmək" is a calque of "apply the brakes". "işə sala bilər" would repeat the "işə düşərək" just before it, so the verb "əyləcləmək" is used instead.
- `e5df6c1d9b62` **az**: "avtomobildə geri hərəkət ötürməsi qoşulu olduqda" -> "avtomobil arxa gediş ötürməsində olarkən". Batches 01-09 never use "geri hərəkət ötürməsi" for reverse gear. "is in reverse" = "arxa gediş ötürməsində olarkən" (`34a218621fe9`, `cbb084e83318`).
- `20b534a26c06` **az**: "Geri hərəkət ötürməsi qoşulduqda" -> "Avtomobil arxa gediş ötürməsinə keçirildikdə". The term is the same as above. "is placed in reverse" follows batch 02 `4fc2d6d428ae`.
- `7554769deb53` **ru**: "может ошибочно зафиксировать ошибку" -> "может ложно обнаружить ошибку". "ошибочно ... ошибку" repeats the same root. The source says "falsely detect an error".
- `7554769deb53` **az**: "dartı qüvvəsinin itməsinə səbəb olur." -> "dartı qüvvəsinin itməsinə səbəb olar.". This is the "ola bilər ki, bu da" (here "söndürə bilər ki, bu da") pattern.
- `ae353b55507c` **ru**: "могут быть недостаточно приварены" -> "могут быть недостаточно качественно приварены". "недостаточно приварены" ("not welded on enough") does not say what is insufficient. Batches 02 (`4a6b76f18d0b`) and 07 (`74b8db9efa20`) translate "insufficiently welded" as "недостаточно качественно сварен(о)".
- `10c35227271f` **ru**: "может не блокироваться должным образом" -> "может не блокировать ремень так, как предусмотрено". "Блокирующий механизм ... может не блокироваться" made the locking mechanism itself the thing that locks. The source says "may not lock as intended", meaning the mechanism may not lock the belt.
- `5dd3db65220c` **az**: "...lazım olan qaz, qaz generatorundan sıza bilər." -> "...səbəbindən qaz generatorundan sürücünün diz təhlükəsizlik yastığının doldurulması üçün lazım olan qaz sıza bilər.". The comma between subject and predicate is a punctuation error. Moving "qaz generatorundan" forward avoids both the comma and the "qaz qaz" sequence.
- `fce3e11034e4` **az**: "təxminən 110 funt çəkisi olan şəxslər" -> "çəkisi təxminən 110 funt olan şəxslər". The old word order reads as "persons who have a weight of about 110 pounds". The normal order is "whose weight is about 110 pounds".
- `c46be5da60e4` **az**: "kapotun köməkçi cəftəsinin bağlanmasına mane olur." -> "kapotun köməkçi cəftəsinin ilişməsinə mane olar.". "engaging" of a latch is "ilişmə", as in batch 03 (`35ec583b2e35`) and the RU "не входит в зацепление". The verb is also aorist after "ola bilər ki, bu da".
- `ae30a7aa75b3` **az**: "ayrılmasına səbəb olur." -> "ayrılmasına səbəb olar.". "ola bilər ki, bu da" pattern, as above.
- `0c46db681392` **az**: "işləməməsinə səbəb olur." -> "işləməməsinə səbəb olar.". Same pattern.
- `9a8134a7f971` **az**: "itməsinə səbəb olur." -> "itməsinə səbəb olar.". Same pattern.
- `7078681e2b3a` **az**: "qısa qapanmasına səbəb olur." -> "qısa qapanmasına səbəb olar.". Same pattern.
- `6ef66accc4a7` **az**: "saxlamasına mane olur." -> "saxlamasına mane olar.". Same pattern.
- `aadf76d6e66e` **az**: "müəyyən etməsinə mane olur." -> "müəyyən etməsinə mane olar.". Same pattern.

## Seen and left as is

- `ab1eec45ef25` ru "достигает предельного износа за срок службы" for "reaches lifetime wear" is a bit literal. "исчерпывает свой ресурс" was tried, but it drops the glossary term 'wear' = "износ" (the check then flags it). The meaning is correct, so it was kept.
- `d5d7d5dfba42` / `44e9ef6b52d3` az "hibrid sistem işini dayandıra bilər və bu, ... səbəb olur": this is a coordinated clause, not the "ki, bu da" pattern, and it was left. `b619342f0aff` az "Proqram təminatı xətası ... mane olur" translates the definite "prevents" and is correct.
- `8b721ca9cc2e` ru "разъём жгута кабелей". Batch 09 has "кабельный жгут" for "cable harness". Both are correct and the meaning is the same.
- `6ef66accc4a7` ru "Верхняя точка крепления ... на крыше": "верхняя" is implied by "roof anchor" and adds nothing wrong.
- `fea94ba40339` ru "мог не быть снят" and `e7313b32982a` ru "больше указанного размера" are correct Russian. They were kept.
- `fce3e11034e4` "110 фунтов / 110 funt" is left without a kg value. The glossary convention adds a converted value only for mph, and batch 08 (`b367c40ae9d1`) left psi unconverted.
- `8772fdcb5021` lists Part 581 inside "требованиям федеральных стандартов (FMVSS) ... и части 581" / "... və hissə 581". The source groups it the same way. This is the wording of batch 06 for Part 567.
- `9dca251a89e1` ru "шторка безопасности ..., что может привести к перекручиванию подушки безопасности": the generic "подушка безопасности" for the curtain is acceptable. The AZ uses the same generic word.
- Model names are kept as printed in the source: "Rav4" (`706bc2cc912c`), "RAV 4" (`3f32d5b0984e`), "Highlander hybrid" (`e07caf8219dc`, translated "в гибридном исполнении" / "hibrid", because the source has it in lower case).
