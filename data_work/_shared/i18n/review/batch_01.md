# Review of llm/batch_01.json (NHTSA recall summaries, RU/AZ)

Items checked: 78 (all `recall_summary`). Items changed: 29. Field edits: 42 (RU 22, AZ 20).

Check after the edits: `scripts/i18n_batches.py check 01` -> 78 pass, 0 fail.

Model years, campaign numbers (17V-224, 21V-295, 42L1), FMVSS numbers and dates were compared by script for all 78 items: no number is missing, changed or added.

## Most serious errors

1. `91730405de19` az (Tesla Autosteer): "idarəetmə vasitələri" (operating controls) used for the driver-monitoring safeguards. The sentence then says the operating controls were not prominent enough, which is a different defect.
2. `19a5e0c2b7c3` ru (Hyundai fail-safe mode): "режим движения автомобиля с ограниченной подвижностью" reads as "the drive mode of a vehicle with limited mobility". It should name a limited-mobility drive mode; the AZ also used "fövqəladə" instead of "qəza rejimi".
3. `22ec6193c5c9` ru/az (Kia KSDS): Knock Sensor Detection System rendered as a system that monitors the knock sensor ("система контроля датчика детонации" / "detonasiya sensorunun nəzarət sistemi"). KSDS actually uses the knock sensor to detect engine knock.
4. `c6fe97606922`, `5fb6a00a0571` ru/az (Hyundai ABS fire): the leak or malfunction that *causes* the electrical short became two parallel events ("утечка ... и короткое замыкание"), which lost the failure mechanism.
5. `3650f43a636e` ru/az: leftover English "(Part 573)", which also doubled the number. In the same item, "конструкция программного обеспечения" / "proqram təminatının konstruksiyası" is a calque. Also `f6bef7c4493a` ru added an adjustment ("регулировка") where the source says only "inspected".

## All changes

Format: hash prefix, field: old -> new. Reason.

- `b18d0e87f042` **az**: "mobil şəbəkə ilə bağlantının sıradan çıxmasına" -> "mobil şəbəkə ilə bağlantının pozulmasına". "sıradan çıxmaq" is said of devices, not of a network connection; calque
- `b18d0e87f042` **ru**: "Ошибка в программном обеспечении карты SIM коммуникационного модуля может привести к отказу подключения к мобильной сети" -> "Ошибка в программном обеспечении сим-карты коммуникационного модуля может привести к сбою подключения к мобильной сети". unnatural "карты SIM" (сим-карта is the dictionary spelling); "отказ подключения" reads as "connection refused" - glossary "отказ" is for a part failing, not a network connection
- `265e76242c8c` **ru**: "RX 350L, а также 2019 Toyota Avalon и Corolla и некоторые Lexus NX 300 и ES 350." -> "RX 350L и 2019 Toyota Avalon и Corolla, а также некоторые Lexus NX 300 и ES 350.". two "а также" in one list, and the "certain Lexus NX 300, ES 350" group was not set off
- `22ec6193c5c9` **az**: "detonasiya sensorunun nəzarət sistemi (KSDS)" -> "detonasiya sensoru vasitəsilə mühərrikdə döyüntünün aşkarlanması sistemi (KSDS)". wrong meaning: "sensor monitoring system" instead of knock detection via the knock sensor; glossary engine knock = mühərrikdə döyüntü
- `22ec6193c5c9` **ru**: "связанной с системой контроля датчика детонации (KSDS)" -> "связанной с системой обнаружения стука двигателя по датчику детонации (KSDS)". wrong meaning: KSDS detects engine knock with the knock sensor, it does not monitor the sensor
- `3650f43a636e` **az**: "573-cü hissə (Part 573) üzrə hesabata baxın. Proqram təminatının konstruksiyasına görə rabitə modulu" -> "573-cü hissə üzrə geri çağırma hesabatına baxın. Proqram təminatının dizayn xüsusiyyətlərinə görə rabitə modulu". leftover English "Part 573"; "proqram təminatının konstruksiyası" is a calque
- `3650f43a636e` **ru**: "см. в отчёте по части 573 (Part 573). Из-за особенностей конструкции программного обеспечения" -> "см. в отчёте об отзывной кампании по части 573. Из-за особенностей архитектуры программного обеспечения". leftover English "Part 573" (duplicated number); "конструкция программного обеспечения" is unnatural
- `53ebcf9f7d1c` **ru**: "экран может не засветиться" -> "экран может не включиться". unnatural verb for a display
- `b85a6dc9e52c` **az**: "mətn oxunmaz hala düşə bilər" -> "mətn oxunmaz ola bilər". "... hala düşmək" follows Turkish "hale düşmek"
- `c6fe97606922` **az**: "blokunda əyləc mayesinin daxili sızması və qısa qapanma baş verə bilər ki," -> "blokunda əyləc mayesinin daxili sızması qısa qapanma yarada bilər ki,". cause-effect lost: in the source the internal brake-fluid leak causes the electrical short
- `c6fe97606922` **ru**: "может возникнуть внутренняя утечка тормозной жидкости и короткое замыкание, что может привести" -> "может возникнуть внутренняя утечка тормозной жидкости, вызывающая короткое замыкание, что может привести". cause-effect lost: in the source the internal brake-fluid leak causes the electrical short
- `cffd2973cf8d` **az**: "12 V sisteminin doldurulmasının itməsinə" -> "12 V sisteminin doldurulmasının dayanmasına". "doldurulmanın itməsi" is unnatural; charging stops
- `f1735cbaf4d5` **az**: "12 V sisteminin doldurulmasının itməsinə" -> "12 V sisteminin doldurulmasının dayanmasına". "doldurulmanın itməsi" is unnatural; charging stops
- `ab553edf978a` **ru**: "Это может привести к некорректному отображению изображения камеры заднего вида." -> "Из-за этого изображение камеры заднего вида может отображаться некорректно.". tautology "отображению изображения"
- `f6a28c698093` **az**: "Problemli avtomobillərdə" -> "Həmin avtomobillərdə". "problemli" adds a judgement; "affected" = the vehicles concerned
- `f6a28c698093` **ru**: "На затронутых автомобилях" -> "На этих автомобилях". calque of "affected vehicles"
- `f6bef7c4493a` **ru**: "могла не быть проверена регулировка углов установки колёс заднего моста." -> "углы установки колёс заднего моста могли остаться непроверенными.". added meaning ("регулировка" = adjustment; source says only inspected) and awkward "могла не быть проверена"
- `fa2357a04b66` **az**: "düzgün qaynaq edilməmiş ola bilər və sərt əyləcləmə zamanı" -> "bir-birinə düzgün qaynaqlanmamış ola bilər və kəskin əyləcləmə zamanı". "sərt əyləcləmə" is not the Azerbaijani term for hard braking (kəskin əyləcləmə); rotor and shaft are welded to each other
- `fa2357a04b66` **ru**: "могли быть приварены неправильно и могут разъединиться при резком торможении, что может привести к отказу антиблокировочной системы тормозов (ABS) и потере усиления торможения." -> "могли быть некачественно сварены между собой и при резком торможении могут разъединиться, что может привести к отказу антиблокировочной системы тормозов (ABS) и потере усиления тормозов.". "приварены" means welded to something else (rotor and shaft are welded to each other); glossary loss of power brake assist = потеря усиления тормозов
- `5fb6a00a0571` **az**: "blokunda nasazlıq və qısa qapanma yarana bilər ki," -> "blokunda nasazlıq yarana və qısa qapanma törədə bilər ki,". cause-effect lost: in the source the malfunction causes the electrical short
- `5fb6a00a0571` **ru**: "может возникнуть неисправность и короткое замыкание, что может привести" -> "может возникнуть неисправность, вызывающая короткое замыкание, что может привести". cause-effect lost: in the source the malfunction causes the electrical short
- `7236c2744ce1` **az**: "Idle Stop & Go sisteminin yağ nasosu qovşağının elektron kontrolleri zədələnmiş elektrik komponentlərinə malik ola bilər ki," -> "Idle Stop & Go (mühərrikin avtomatik dayandırılması və işə salınması) sisteminin yağ nasosu qovşağının elektron kontrollerində zədələnmiş elektrik komponentləri ola bilər ki,". "komponentlərə malik ola bilər" is unnatural; the feature name explained
- `7236c2744ce1` **ru**: "Электронный контроллер масляного насоса в сборе системы Idle Stop & Go может содержать повреждённые электронные компоненты" -> "Электронный контроллер масляного насоса в сборе системы автоматической остановки и запуска двигателя Idle Stop & Go может иметь повреждённые электрические компоненты". source says electrical (not electronic) components; the feature name alone tells a Russian reader nothing
- `19a5e0c2b7c3` **az**: "işə düşən «fövqəladə» məhdud hərəkət rejiminin işi pozula bilər" -> "işə düşən «qəza» rejiminin (məhdud hərəkət rejimi) işi pozula bilər". "fövqəladə" means extraordinary/emergency situation; the limp-home mode is "qəza rejimi"
- `19a5e0c2b7c3` **ru**: "Работа «аварийного» режима движения автомобиля с ограниченной подвижностью может быть нарушена при его включении вследствие неисправности масляного насоса коробки передач, что может привести к полной потере тяги." -> "«Аварийный» режим с ограниченными возможностями движения, включающийся при неисправности масляного насоса коробки передач, может работать со сбоями, что может привести к полной потере тяги.". wrong meaning: "автомобиля с ограниченной подвижностью" reads as a vehicle with limited mobility, not a limited-mobility drive mode
- `7b61f2f1c6f6` **az**: "Problemli avtomobillərdə təmir zamanı" -> "Həmin avtomobillərdə təmir zamanı". "problemli" adds a judgement; "affected" = the vehicles concerned
- `23e73eeb1ae4` **az**: "problemli avtomobillərin bütün" -> "həmin avtomobillərin bütün". "problemli" adds a judgement; "affected" = the vehicles concerned
- `23e73eeb1ae4` **ru**: "что затронутые автомобили не будут соответствовать" -> "что эти автомобили не будут соответствовать". calque of "affected vehicles"
- `2e89f7980bba` **ru**: "эти частицы могут тлеть и вызвать оплавление" -> "эти частицы могут начать тлеть и вызвать оплавление". aspect mismatch "могут тлеть и вызвать"
- `130f64f15fe2` **az**: "Diz təhlükəsizlik yastığı (sürücü və/və ya sərnişin)" -> "Diz təhlükəsizlik yastığı (sürücünün və/və ya sərnişinin)". missing genitive ending (whose knee air bag)
- `130f64f15fe2` **ru**: "могла быть изготовлена неправильно, что может привести к тому, что коленная подушка безопасности не раскроется так, как предусмотрено." -> "могла быть изготовлена неправильно, из-за чего она может раскрыться не так, как предусмотрено.". clumsy double "что ... что" and repeated subject
- `17aeca9c2d53` **ru**: "может ошибочно определять, что пассажиры пристегнули ремень безопасности," -> "может ошибочно определять пассажиров как пристёгнутых,". number disagreement (пассажиры ... ремень) and unnatural phrasing
- `64dca76ae6be` **ru**: "Плохо загерметизированный электрический разъём водяного насоса может подвергнуться воздействию воды, что приведёт к короткому замыканию." -> "Ненадлежащим образом загерметизированный электрический разъём водяного насоса может подвергнуться воздействию воды, что может привести к короткому замыканию.". colloquial "плохо"; consequence stated as certain while the source says "may"
- `41ba188560c3` **az**: "hidroakkumulyatorunun son qapağında" -> "hidroakkumulyatorunun uc qapağında". "son qapaq" means "last cover"; endcap = uc qapağı
- `4edd2eeea9d4` **az**: "porşenlərinin örtüyü kifayət qədər olmaya bilər ki," -> "porşenlərinin örtüyü qeyri-kafi ola bilər ki,". "örtüyü kifayət qədər olmaya bilər" is ungrammatical (insufficient coating = qeyri-kafi örtük)
- `1bff942aba76` **ru**: "может быть заблокирован" -> "может быть перекрыт". "заблокирован" is not used for an oil passage (blocked = перекрыт/засорён)
- `488bf574f35e` **az**: "Yaxın sahə aşkarlama modulu (NFSM)" -> "Yaxın zonada obyektlərin aşkarlanması modulu (NFSM)". "yaxın sahə aşkarlama modulu" is a word-for-word calque
- `488bf574f35e` **ru**: "Модуль ближнего обнаружения (NFSM)" -> "Модуль обнаружения объектов в ближней зоне (NFSM)". "модуль ближнего обнаружения" is not a Russian term
- `901a4e3ca945` **ru**: "В гидравлическом электронном блоке управления (HECU)" -> "В гидроэлектронном блоке управления (HECU)". established Russian term for HECU
- `9e4db07e5112` **az**: "Problemli avtomobillərin sağ" -> "Həmin avtomobillərin sağ". "problemli" adds a judgement; "affected" = the vehicles concerned
- `91730405de19` **az**: "bu funksiyanın idarəetmə vasitələrinin nəzərəçarpanlığı" -> "bu funksiyanın nəzarət vasitələrinin nəzərəçarpanlığı". wrong meaning: "controls" here are the driver-monitoring safeguards (nəzarət), not operating controls (idarəetmə)
- `91730405de19` **ru**: "оснащённые всеми версиями функции Autosteer, предшествующими версии (версиям), в которой содержится устранение неисправности по отзывной кампании." -> "оснащённые всеми версиями функции Autosteer, выпущенными до версии (версий) с устранением неисправности по отзывной кампании.". awkward "содержится устранение"; case error "предшествующими версии (версиям)"

## Checked and deliberately not changed

- `fa2357a04b66`, `6ae8b2fb04c8`, `64dca76ae6be`: the source spells the BMW names "xdrive50i", "xdrive45e" and "xdrive 40e". The translations write "xDrive...", the official spelling. Restoring the lowercase source spelling makes the check fail ("untranslated 'xdrive'"), so the corrected spelling is kept. `f665b5886d5a` keeps the source typo "A5 Cabrioleet" as printed.
- `10839f047f67` ru: "(P)" after "положение парковки" (glossary form) is rejected by the check (Latin "P" is not in the source, which says PARK), so it is left without "(P)".
- `f745f75ee78f` az: "akkumulyator batareyası" is kept. It is the usual Azerbaijani term and it carries the glossary stem for "battery".
- `b18d0e87f042`: the glossary's "failure = отказ / sıradan çıxma" is for a part that fails. A mobile network *connection* failure is "сбой подключения" / "bağlantının pozulması", so the two GLOSSARY warnings for this item are expected.
- The remaining GLOSSARY warnings are false positives of the stem check:
  - "шин" (plural of шина), "ремней" / "ремня" (forms of ремень), "seat" inside "seat belt";
  - "engine compartment" = моторный отсек; "seat frame" = каркас сиденья / oturacağın karkası (glossary entries);
  - "Bolt" is the Chevrolet Bolt EV model name.
- Feature and trade names are kept in Latin, as in the source: Idle Stop & Go, Autosteer, Auto-Park, Panoramic View Monitor, MBUX, eCall. Where it was useful, a translated description was added (7236c2744ce1).
