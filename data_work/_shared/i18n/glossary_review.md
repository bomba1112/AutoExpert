# Glossary review — glossary.json 2026-10-03.1 → 2026-10-03.2

Independent review of `data_work/_shared/i18n/glossary.json` (EN → RU / AZ Latin) against the app seed (`terms.json` → `app_seed`) and against the real NHTSA component paths in `sources.json` (each segment checked in the hierarchy it actually occurs in).

Entries checked: **685** — nhtsa_component_segment 253, issue_topic 41, issue_topic_part 76, carcomplaints_problem 8, maintenance_service 5, maintenance_condition 6, maintenance_qualifier 12, general 284.

Entries changed: **16** (RU changed in 9, AZ changed in 15). Every key is kept; the file layout (one entry per line, CRLF) is unchanged apart from the edited lines and `version`.

## What was checked

- Meaning of each technical term in context (brake booster vs master cylinder, inflator vs air bag, steering shaft vs drive shaft, POWER TRAIN vs POWERTRAIN, segment meaning under its parent).
- Standard RU workshop terminology and AZ automotive terminology; AZ spelling (ə ı ö ü ç ş ğ), Turkish forms, leftover English.
- Consistency of the same concept across `nhtsa_component_segment`, `issue_topic`, `issue_topic_part`, `carcomplaints_problem` and `general` (automatic cross-kind comparison: only singular/plural and case differences remain).
- Agreement with every `app_seed` term (maintenance jobs, actions, severity, probability, fact labels): no conflicts found.
- Case rules: NHTSA segments sentence case (no ALL CAPS beyond the listed abbreviations and ШРУС); topics keep source case; topics composed of parts match the whole-topic translation in meaning.
- Values that would break composition: no `/` inside topic parts; one segment contained `: ` (fixed, see below).

## Changes

| # | Kind | EN | Old RU | Old AZ | New RU | New AZ | Reason |
|---|---|---|---|---|---|---|---|
| 1 | nhtsa_component_segment | STRUCTURE | Несущая конструкция | Daşıyıcı konstruksiya | Конструкция | Konstruksiya | Top-level NHTSA category that also holds bumpers, exterior trim, dashboard, hinges and the emergency exit; 'несущая / daşıyıcı' (load-bearing) narrowed it to the body shell and was wrong for most children. |
| 2 | nhtsa_component_segment | VEHICLE SPEED CONTROL | Регулирование скорости (круиз-контроль) | Sürətin tənzimlənməsi (kruiz-kontrol) | Управление скоростью | Sürətin idarə edilməsi | NHTSA category for accelerator pedal, throttle control and cruise control; the '(круиз-контроль / kruiz-kontrol)' gloss made 'VEHICLE SPEED CONTROL: ACCELERATOR PEDAL' read as a cruise-control part. |
| 3 | nhtsa_component_segment | CONTROL/DRIVE MODULE | Модуль управления и привода | İdarəetmə və ötürmə modulu | Блок управления насосом | Nasosun idarəetmə bloku | Sits only under FUEL PUMP: it is the fuel pump control/driver module (electronic power stage). 'модуль ... привода / ötürmə modulu' read as a mechanical drive / transmission; convention: control module = блок управления / idarəetmə bloku. |
| 4 | nhtsa_component_segment | THROTTLEBODY/MANIFOLD | Дроссельный узел / коллектор | Drossel qovşağı / kollektor | Дроссельный узел / впускной коллектор | Drossel qovşağı / sorma kollektoru | Under FUEL INJECTION SYSTEM the manifold is the intake manifold; a bare 'коллектор / kollektor' is ambiguous with the exhaust manifold. |
| 5 | nhtsa_component_segment | COOLING UNIT AND LINES | Блок охлаждения и магистрали | Soyutma bloku və xətləri | Радиатор охлаждения и магистрали | Soyutma radiatoru və xətləri | Under AUTOMATIC TRANSMISSION this is the transmission (fluid) cooler and its lines; 'блок охлаждения / soyutma bloku' is the engine radiator-and-fan module in RU usage. |
| 6 | nhtsa_component_segment | POWER CONTROL UNIT/MODULE (HPCU) | Блок управления силовой установкой (HPCU) | Güc qurğusunun idarəetmə bloku (HPCU) | Блок управления гибридной силовой установкой (HPCU) | Hibrid güc qurğusunun idarəetmə bloku (HPCU) | HPCU = Hybrid Power Control Unit; without 'гибридной / hibrid' it was word-for-word the PCM translation (блок управления силовой установкой / güc qurğusunun idarəetmə bloku). |
| 7 | nhtsa_component_segment | SENSOR/CONTROL MODULE-INACTIVE | Датчик / блок управления: неактивное состояние | Sensor / idarəetmə bloku: qeyri-aktiv vəziyyət | Датчик / блок управления (неактивный) | Sensor / idarəetmə bloku (qeyri-aktiv) | The value contained ': ', the separator used to join component segments, so the full component showed a fake extra level starting in lowercase; the qualifier is now in parentheses. |
| 8 | nhtsa_component_segment | INTERIOR | Салонное | Daxili | Внутренние | Daxili (unchanged) | Only used as REARVIEW MIRRORS/DEVICES: INTERIOR; RU 'Салонное' (singular neuter) did not agree with the plural parent 'Зеркала заднего вида' or with its sibling EXTERIOR 'Наружные'. AZ unchanged. |
| 9 | nhtsa_component_segment | ONBOARD | Бортовой | Bort | Бортовой (unchanged) | Avtomobildəki | AZ 'Bort' alone reads as the noun 'side/board' and collides with 'Arxa bort' (tailgate) and 'Şinin bortu' (tire bead) in this glossary; under CHARGING: CABLE/CORD it means the cord carried in the vehicle. RU unchanged. |
| 10 | nhtsa_component_segment | EMERGENCY | Аварийные средства | Qəza vasitələri | Аварийные средства (unchanged) | Təcili hallar üçün vasitələr | AZ 'Qəza vasitələri' means 'accident vehicles/means'; the child ESCAPE/EGRESS/EXIT is 'Təcili çıxış', so the parent uses 'təcili' (emergency) too. RU unchanged. |
| 11 | nhtsa_component_segment | KEY/SENDER | Ключ / передатчик | Açar / ötürücü | Ключ / передатчик (unchanged) | Açar / verici | AZ 'ötürücü' is the glossary/app-seed word for drivetrain/drive (привод); a key fob transmitter is 'verici'. RU unchanged. |
| 12 | nhtsa_component_segment | RELAYS/SOLENOIDS | Реле и соленоиды | Rele və solenoidlər | Реле и соленоиды (unchanged) | Relelər və solenoidlər | AZ plural agreement: 'Rele' was singular next to plural 'solenoidlər'. RU unchanged (реле is indeclinable). |
| 13 | issue_topic_part | latch | защёлка | cəftə | защёлка двери | qapı cəftəsi | Convention: each part reads on its own. The part only comes from 'door lock / latch'; a bare 'защёлка / cəftə' lost the door, while its sibling part 'door lock' says 'замок двери / qapı kilidi'. Now matches general 'door latch'. |
| 14 | general | electrical overload | электрическая перегрузка | elektrik yüklənməsi | электрическая перегрузка (unchanged) | elektrik ifrat yüklənməsi | AZ 'elektrik yüklənməsi' means electrical load(ing), not overload; overload = 'ifrat yüklənmə'. RU unchanged. |
| 15 | general | subframe | подрамник | altrama | подрамник (unchanged) | köməkçi rama | AZ 'altrama' is a non-standard calque of 'подрамник'; the usual AZ term is 'köməkçi rama'. RU unchanged. |
| 16 | general | park position | положение парковки (P) | parklama mövqeyi (P) | положение парковки (P) (unchanged) | park mövqeyi (P) | AZ 'parklama' is not a standard Azerbaijani form; the glossary itself uses 'park' attributively ('park sensoru'). RU unchanged. |

## Reviewed and left as is (borderline)

- `DRIVESHAFT` / `driveshaft` = приводной вал / ötürücü val: NHTSA uses it for both propeller shafts and half-shafts; the generic term is the safe one (`propeller shaft` = карданный вал / kardan valı and `axle shaft` = полуось / yarımox stay separate, as in the seed).
- `general: stall` = остановка двигателя / mühərrikin sönməsi: noun form; the verb form двигатель глохнет / mühərrik sönür is used in topics, as the convention says.
- `SWITCH` = Выключатель / Açar: 'açar' is the standard AZ word for an electrical switch even though it also means key.
- `CUSHION` = Оболочка подушки / Yastığın örtüyü: the inflatable bag fabric; acceptable in both languages.
- `VISIBILITY` = Обзорность / Görünüş: kept consistent with `rear visibility` = arxa görünüş and the standard 'arxa görünüş güzgüsü'.
- `PROPULSION SYSTEM` = Тяговая система / Dartı sistemi vs `HYBRID PROPULSION SYSTEM` = Гибридная силовая установка: different NHTSA branches, both correct.
