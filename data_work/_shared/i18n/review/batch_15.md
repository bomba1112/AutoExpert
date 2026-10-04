# Review of llm/batch_15.json (NHTSA recall summaries, RU/AZ)

Items checked: 47, all `recall_summary`. By filer: 28 GM (15 "General Motors, LLC (GM)", 9 "General Motors LLC (GM)", 1 "General Motors", 1 "General Motors, LLC", 1 "General Motors, LLC (M)", and the 2014 ignition-switch notice `61fe764e3826`) and 19 Mitsubishi (17 "(MMNA)", 2 "(Mitsubishi)"). Items changed: 7. Field edits: 9 (RU 5, AZ 4). Two items were changed in both languages: `43a5924b4c22` and `5b94ad470782`.

**How the file was written**
- Before the review, the three files of this round (batches 13-15) were backed up to the scratchpad as `bk/batch_NN.json`.
- One script (`b13_15_apply.py`, edit list `b13_15_edits.py`) applied the edits. Each edit replaces one exact substring and must match exactly once.
- Before writing, the script confirmed that the real file still had the backup's sha256.
- Before the edits, a JSON round trip of the original file was confirmed byte-identical. The file keeps its formatting: indent 1, CRLF, no trailing newline, UTF-8, ensure_ascii false.
- The kind/hash pairs and their order did not change.
- The backup sha256 is 4e583c64...; the final sha256 is ef489bb2...

**Check results:** `scripts/i18n_batches.py check 15` gives 47 pass, 0 fail before and after. The same 14 GLOSSARY lines appear before and after, and all are false positives of the stem check:
- 'crash' in "rollover crash" = авария с опрокидыванием / aşma ilə nəticələnən qəza (`449a8bf1c922`). The conventions allow авария / qəza.
- 'steering' and 'power steering' in "loss of power steering assist" = потеря усиления руля, the glossary term (`b96ba78b36f8`).
- 'wheel' as колёс / колёсами (`11f9cb6c85ff`, `5cf162235b31`) and 'tire' in the FMVSS 110 title 'шин' (`524c113827d3`).
- 'seat belt' in the genitive or plural (`43a5924b4c22`, `316250d62422`, `1a930bc246bc`, `a448a9c8d9a1`). 'seat' appears in "seat belt assemblies" and in the FMVSS 210 title (`1a930bc246bc`, `a448a9c8d9a1`).

**Numbers, dates and names**
- A script compared every digit group in all 47 items, RU and AZ, with the source. Nothing is missing, changed or added, including 554 328, 24-inch, 18-inch, 6-cylinder and 10-speed.
- All 29 production and notice dates in 10 items were compared by script in RU and AZ, and all AZ year suffixes are correct.
- In `c7e57f452209`, all 56 state and territory codes of zones A, B and C were compared with the source in RU and AZ. Each zone keeps its own list and its own model years (2014 / 2011-2014 + 2011-2013 / 2010-2014 + 2010-2013).
- The state lists of `18c6137bae89` and `a16601e46316` have 22 states plus the District of Columbia in RU and AZ, as in the source.
- Names and codes are kept as printed: 9-4X, CTS-V, A-IVI, CVT-ECU, ALR, ETRS, DRLs, SDM, PSAN, the "(M)" typo of `43a5924b4c22`, "Suburban 1500", and Saab.
- The FMVSS 108, 110, 111, 135, 208, 210 and 214 titles match batches 01-12. FMVSS 216 appears for the first time (see below).
- A scripted scan of the AZ text found no Turkish forms, no Cyrillic letters and no English function words.

## Changes

- `5b94ad470782` **ru**: "может не выводить сигнальную лампу" -> "может не включать сигнальную лампу". A warning lamp is switched on, not 'output' ('выводить лампу' is not Russian). b13 6260f03a4b27 has 'не включать сигнальную лампу'.
- `5b94ad470782` **az**: "xəbərdarlıq lampasını göstərməyə bilər" -> "xəbərdarlıq lampasını yandırmaya bilər". The lamp lights up ('yandırmaq') rather than being 'shown'. b13 6260f03a4b27 has 'xəbərdarlıq lampasını ... yandırmaya bilər'.
- `9f77f459cc07` **az**: "dörd təkərə ötürücülü (4WD)" -> "dörd təkər ötürücülü (4WD)". Grammar: the dative 'təkərə' cannot sit inside the compound adjective. Compare 'tam ötürücülü' and 'ön ötürücülü'.
- `43a5924b4c22` **ru**: "могла быть сформирована неправильно." -> "могла быть неправильно расклёпана.". 'сформирована' is not used for a rivet. An improperly formed rivet is one whose head was set badly, 'неправильно расклёпана'.
- `43a5924b4c22` **az**: "pərçim düzgün formalaşdırılmamış ola bilər." -> "pərçim düzgün pərçimlənməmiş ola bilər.". 'formalaşdırılmamış' (not shaped/formed) is a calque. A rivet is set by riveting, 'pərçimləmək'.
- `1a930bc246bc` **ru**: "в ремнях безопасности правого переднего сиденья, а также правого и левого сидений второго ряда в сборе может" -> "в ремнях безопасности в сборе правого переднего сиденья, а также правого и левого сидений второго ряда может". 'в сборе' at the end attached to 'сидений второго ряда' ('second-row seats in assembly'). The source assemblies are the seat belt assemblies.
- `743a11e7f935` **ru**: "Из-за неправильного программирования программного обеспечения бортовая" -> "Из-за неправильного программирования бортовая". 'программирования программного обеспечения' repeats the root ('programming of the programs'). The meaning, 'improper software programming', is kept.
- `61fe764e3826` **ru**: "Брелок-ключ (при наличии)" -> "Брелок дистанционного управления (при наличии)". The source keeps the ignition key on the ring and removes the key fob. 'Брелок-ключ' suggests the fob is itself the key; on these cars it is the separate remote transmitter. The AZ 'Açar breloku' is fine.
- `cdce6e4438fd` **az**: "magistral sürətlərində" -> "magistral yollara xas sürətlərdə". 'magistral sürətləri' ('the highway's speeds') is a calque of 'highway speeds'. The meaning is the speeds typical of highways (RU 'на скоростях движения по автомагистрали').

## Flagged by the translator: verdicts

- `c7e57f452209` US state postal codes kept as printed: **accepted**. There are 56 codes in three zones. Writing them out would roughly triple the length and add 56 names to transliterate; the codes are unambiguous, and the zone letters A/B/C are the campaign's own designations. RU correctly says "в штатах и территориях" for zone A, which contains PR, AS, GU, MP and VI. Zone B contains DC and is called "штаты" as in the source.
- `a448a9c8d9a1` FMVSS 216 «Сопротивление крыши раздавливанию» / «Damın əzilməyə qarşı müqaviməti»: **accepted**. Both follow the official title "Roof Crush Resistance" (сопротивление чего чему; 'əzilməyə qarşı müqavimət'). Both are grammatical and parallel the other titles of the series. This is the first occurrence in batches 01-15, so it should be reused verbatim from now on.

## Seen and left as is

- `7e1f7b9fe43c` "Chevrolet Silverado and GMC Sierra Trucks" -> "грузовики" / "yük avtomobilləri": kept literal, although these are pickups.
- `5b94ad470782`: the source omits "Motor" ("Federal Vehicle Safety Standard number 135"). RU/AZ use the standard full title of the series, so the standard identified is the same.
- `cdce6e4438fd` RU "может быть затянута с моментом, не соответствующим требованиям" and `72a267085ac9` the same: correct for "not torqued to specification".
- `9f77f459cc07`: as in b14 `c4ae14b5a911`, the AZ repeats "geri çağırır" for the second vehicle group. Kept.
- `61fe764e3826`: the item opens with the safety advice ("This defect can affect ...") and then the notice. RU/AZ keep that order and the number 554 328.
- `18c6137bae89`, `a16601e46316`: RU/AZ lists and state names checked (Коннектикут ... Висконсин / Konnektikut ... Viskonsin), with DC moved to the end ("а также в округе Колумбия" / "həmçinin Kolumbiya dairəsində"). No state is missing.
