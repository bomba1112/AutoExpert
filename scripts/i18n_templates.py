"""Russian and Azerbaijani wording of the templated buyer-facing texts (owner decision
2026-10-03). The variable parts (NHTSA component, topic, CarComplaints problem) come from the
single glossary data_work/_shared/i18n/glossary.json; numbers, campaign and bulletin numbers,
codes and URLs are carried over unchanged.

Used by scripts/i18n_build.py. A text no template matches goes to the reviewed free-text
translations (data_work/_shared/i18n/llm/*.json) or to MANUAL below.
"""

from __future__ import annotations

import re

# full sentences that occur once or twice: translated by hand, terms as in the glossary
MANUAL = {
    "Ask for service records and test for the reported symptom during inspection.": (
        "Запросите сервисную историю и проверьте заявленный симптом при осмотре.",
        "Servis tarixçəsini istəyin və baxış zamanı bildirilən əlaməti yoxlayın."),
    "Ask for service records and test for the reported problem during inspection.": (
        "Запросите сервисную историю и проверьте заявленную неисправность при осмотре.",
        "Servis tarixçəsini istəyin və baxış zamanı bildirilən nasazlığı yoxlayın."),
    "Brake booster vacuum pump failure: sudden loss of brake assist": (
        "Отказ вакуумного насоса усилителя тормозов: внезапная потеря усиления тормозов",
        "Əyləc gücləndiricisinin vakuum nasosunun nasazlığı: əyləc gücləndirilməsinin qəfil itməsi"),
    "Chirping noise from the high-pressure fuel pump (2GR-FKS)": (
        "Стрекочущий шум топливного насоса высокого давления (2GR-FKS)",
        "Yüksək təzyiqli yanacaq nasosundan cırıltılı səs (2GR-FKS)"),
    "Electric power steering ECU damage: possible loss of power steering (2015)": (
        "Повреждение блока управления электроусилителя руля: возможна потеря усиления руля (2015)",
        "Elektrik sükan gücləndiricisinin idarəetmə blokunun zədələnməsi: sükan gücləndirilməsi itə bilər (2015)"),
    "Electric water pump coolant leak or malfunction indicator with water pump codes": (
        "Течь охлаждающей жидкости из электрической помпы или индикатор неисправности с кодами помпы",
        "Elektrik su nasosundan soyuducu maye sızması və ya nasos kodları ilə nasazlıq indikatoru"),
    "Engine block casting porosity can crack and leak coolant (2.5 L)": (
        "Пористость отливки блока цилиндров: возможна трещина и течь охлаждающей жидкости (2.5 л)",
        "Silindrlər blokunun tökməsində məsaməlilik: çat və soyuducu maye sızması mümkündür (2.5 l)"),
    "Fuel delivery pipe may leak in the engine compartment (2014)": (
        "Возможна течь топливной рампы в моторном отсеке (2014)",
        "Mühərrik bölməsində yanacaq paylayıcı borusundan sızma mümkündür (2014)"),
    "Hesitation on acceleration from a slow roll (A25A engine)": (
        "Провал при разгоне с медленного хода (двигатель A25A)",
        "Yavaş hərəkətdən sürətlənmədə ləngimə (A25A mühərriki)"),
    "Left front lower arm may separate from the ball joint (2014, 16/17-inch rims)": (
        "Левый передний нижний рычаг может отсоединиться от шаровой опоры (2014, диски 16/17 дюймов)",
        "Sol ön aşağı ling kürəvi oynaqdan ayrıla bilər (2014, 16/17 düymlük disklər)"),
    "Low-pressure fuel pump failure can stall the engine": (
        "Отказ топливного насоса низкого давления может заглушить двигатель",
        "Aşağı təzyiqli yanacaq nasosunun nasazlığı mühərriki söndürə bilər"),
    "Occupant Classification System sensor short: front passenger air bag may not deploy": (
        "Замыкание датчика системы классификации пассажира: передняя подушка безопасности пассажира может не сработать",
        "Sərnişin təsnifatı sisteminin sensorunda qısaqapanma: ön sərnişin təhlükəsizlik yastığı açılmaya bilər"),
    "Oversized pistons may stall the 2.5 L engine (2018)": (
        "Поршни увеличенного размера могут заглушить двигатель 2.5 л (2018)",
        "Böyük ölçülü porşenlər 2.5 l mühərriki söndürə bilər (2018)"),
    "Torque converter shudder (U760E 6-speed automatic)": (
        "Вибрация гидротрансформатора (6-ступенчатый автомат U760E)",
        "Hidrotransformatorun titrəməsi (6 pilləli avtomat U760E)"),
    "V6 fuel delivery pipes may not be properly connected (2018)": (
        "Топливные рампы V6 могут быть неправильно подсоединены (2018)",
        "V6 yanacaq paylayıcı boruları düzgün birləşdirilməyə bilər (2018)"),
    "Whine or grind noise from the 8-speed transmission (2021)": (
        "Вой или скрежет 8-ступенчатой коробки передач (2021)",
        "8 pilləli sürətlər qutusundan uğultu və ya sürtünmə səsi (2021)"),
    "Check for coolant traces at the electric water pump and connector, scan for P26CB71/P26CA14/P26CA31, check coolant level when cold.": (
        "Проверьте следы охлаждающей жидкости у электрической помпы и разъёма, считайте коды P26CB71/P26CA14/P26CA31, проверьте уровень охлаждающей жидкости на холодном двигателе.",
        "Elektrik su nasosu və birləşdiricidə soyuducu maye izlərini yoxlayın, P26CB71/P26CA14/P26CA31 kodlarını oxuyun, soyuq mühərrikdə soyuducu maye səviyyəsini yoxlayın."),
    "Listen at idle with the hood open for a chirp from the high-pressure fuel pump area.": (
        "На холостом ходу с открытым капотом прислушайтесь, нет ли стрекота в зоне топливного насоса высокого давления.",
        "Kapot açıq halda boş gedişdə yüksək təzyiqli yanacaq nasosu nahiyəsində cırıltı olub-olmadığına qulaq asın."),
    "Test drive at 25-50 mph with light throttle and feel for a shudder; ask for torque converter repair records.": (
        "На тест-драйве на скорости 25–50 миль/ч (40–80 км/ч) с лёгким нажатием педали газа проверьте, нет ли вибрации; запросите записи о ремонте гидротрансформатора.",
        "Sınaq sürüşündə 25–50 mil/saat (40–80 km/saat) sürətlə qaz pedalını yüngül basaraq titrəmə olub-olmadığını yoxlayın; hidrotransformatorun təmiri haqqında qeydləri istəyin."),
    "Check by VIN whether recall 14V576000 applies and the suspect fuel delivery pipes were replaced.": (
        "Проверьте по VIN, распространяется ли на автомобиль отзывная кампания 14V576000 и заменены ли подозрительные топливные рампы.",
        "VIN üzrə 14V576000 geri çağırma kampaniyasının avtomobilə aid olub-olmadığını və şübhəli yanacaq paylayıcı borularının dəyişdirildiyini yoxlayın."),
    "Check by VIN whether recall 14V715000 applies and the left lower arm was replaced.": (
        "Проверьте по VIN, распространяется ли на автомобиль отзывная кампания 14V715000 и заменён ли левый нижний рычаг.",
        "VIN üzrə 14V715000 geri çağırma kampaniyasının avtomobilə aid olub-olmadığını və sol aşağı lingin dəyişdirildiyini yoxlayın."),
    "Check by VIN whether recall 15V144000 applies and the EPS ECU serial-number inspection was done.": (
        "Проверьте по VIN, распространяется ли на автомобиль отзывная кампания 15V144000 и выполнена ли проверка серийного номера блока управления электроусилителя руля (EPS).",
        "VIN üzrə 15V144000 geri çağırma kampaniyasının avtomobilə aid olub-olmadığını və elektrik sükan gücləndiricisinin (EPS) idarəetmə blokunun seriya nömrəsinin yoxlanıldığını yoxlayın."),
    "Check by VIN whether recall 18V108000 applies and the fuel pipe inspection was completed.": (
        "Проверьте по VIN, распространяется ли на автомобиль отзывная кампания 18V108000 и выполнена ли проверка топливной трубки.",
        "VIN üzrə 18V108000 geri çağırma kampaniyasının avtomobilə aid olub-olmadığını və yanacaq borusunun yoxlanıldığını yoxlayın."),
    "Check by VIN whether recall 18V200000 applies; the remedy replaces the engine assembly when affected pistons are found.": (
        "Проверьте по VIN, распространяется ли на автомобиль отзывная кампания 18V200000; при обнаружении дефектных поршней двигатель заменяется в сборе.",
        "VIN üzrə 18V200000 geri çağırma kampaniyasının avtomobilə aid olub-olmadığını yoxlayın; qüsurlu porşenlər aşkar edildikdə mühərrik komplekt şəkildə dəyişdirilir."),
    "Check by VIN whether recall 20V064000 applies and the engine inspection/replacement was done.": (
        "Проверьте по VIN, распространяется ли на автомобиль отзывная кампания 20V064000 и выполнены ли проверка или замена двигателя.",
        "VIN üzrə 20V064000 geri çağırma kampaniyasının avtomobilə aid olub-olmadığını və mühərrikin yoxlanıldığını və ya dəyişdirildiyini yoxlayın."),
    "Check by VIN whether recall 23V865000 applies and the sensor inspection/replacement was done.": (
        "Проверьте по VIN, распространяется ли на автомобиль отзывная кампания 23V865000 и выполнены ли проверка или замена датчика.",
        "VIN üzrə 23V865000 geri çağırma kampaniyasının avtomobilə aid olub-olmadığını və sensorun yoxlanıldığını və ya dəyişdirildiyini yoxlayın."),
    "Check by VIN whether recalls 18V211000 and 21V890000 apply and were completed (vacuum pump repaired or replaced).": (
        "Проверьте по VIN, распространяются ли на автомобиль отзывные кампании 18V211000 и 21V890000 и выполнены ли они (вакуумный насос отремонтирован или заменён).",
        "VIN üzrə 18V211000 və 21V890000 geri çağırma kampaniyalarının avtomobilə aid olub-olmadığını və icra edildiyini yoxlayın (vakuum nasosu təmir və ya dəyişdirilib)."),
    "Check by VIN with a Toyota dealer or NHTSA whether recall remedies 20V012000, 20V682000 or 25V028000 apply and were completed; ask for the fuel pump replacement record.": (
        "Проверьте по VIN у дилера Toyota или в NHTSA, распространяются ли на автомобиль отзывные кампании 20V012000, 20V682000 или 25V028000 и выполнены ли они; запросите запись о замене топливного насоса.",
        "VIN üzrə Toyota dilerində və ya NHTSA-da 20V012000, 20V682000 və ya 25V028000 geri çağırma kampaniyalarının avtomobilə aid olub-olmadığını və icra edildiyini yoxlayın; yanacaq nasosunun dəyişdirilməsi haqqında qeydi istəyin."),
    "On a test drive listen for whine or grind under acceleration and coasting; ask whether TSB 10188917 work was done.": (
        "На тест-драйве прислушайтесь, нет ли воя или скрежета при разгоне и движении накатом; уточните, выполнены ли работы по бюллетеню TSB 10188917.",
        "Sınaq sürüşündə sürətlənmə və ətalətlə hərəkət zamanı uğultu və ya sürtünmə səsinə qulaq asın; TSB 10188917 bülleteni üzrə işlərin görülüb-görülmədiyini soruşun."),
    "On a test drive, slow to a roll and accelerate gently; ask whether the ECM calibration update from TSB 10173797 was applied.": (
        "На тест-драйве сбросьте скорость почти до остановки и плавно разгонитесь; уточните, установлено ли обновление калибровки блока управления двигателем (ECM) по бюллетеню TSB 10173797.",
        "Sınaq sürüşündə sürəti demək olar ki, dayanana qədər azaldın və rəvan sürətlənin; TSB 10173797 bülleteni üzrə mühərrik idarəetmə blokunun (ECM) kalibrləmə yeniləməsinin quraşdırılıb-quraşdırılmadığını soruşun."),
}

# (pattern, ru template, az template); {n} and {list} are copied, {part} is the glossary term
TEMPLATES = [
    (re.compile(r"^Ask a dealer whether manufacturer communications (?P<list>[\w, ]+?) apply to this VIN and were performed\.$"),
     "Уточните у дилера, относятся ли к этому VIN сервисные сообщения производителя {list} и выполнены ли они.",
     "Dilerdən soruşun: istehsalçının {list} saylı servis bildirişləri bu VIN-ə aiddirmi və icra olunubmu."),
    (re.compile(r"^Check that NHTSA recall (?P<n>\w+) was completed for this VIN \(nhtsa\.gov/recalls or a dealer\)\.$"),
     "Проверьте, выполнена ли для этого VIN отзывная кампания NHTSA {n} (nhtsa.gov/recalls или у дилера).",
     "Bu VIN üçün NHTSA {n} geri çağırma kampaniyasının icra olunduğunu yoxlayın (nhtsa.gov/recalls və ya diler)."),
]
TITLE_TEMPLATES = [
    # (pattern, glossary kind of the part, ru, az)
    (re.compile(r"^NHTSA recall (?P<n>\w+): (?P<part>.+)$"), "nhtsa_component",
     "Отзывная кампания NHTSA {n}: {part}", "NHTSA geri çağırma kampaniyası {n}: {part}"),
    (re.compile(r"^Manufacturer communication: (?P<part>.+)$"), "issue_topic",
     "Сервисное сообщение производителя: {part}", "İstehsalçının servis bildirişi: {part}"),
    (re.compile(r"^Owners report \(CarComplaints\.com\): (?P<part>.+)$"), "carcomplaints_problem",
     "Владельцы сообщают (CarComplaints.com): {part}", "Sahiblər bildirir (CarComplaints.com): {part}"),
    (re.compile(r"^Owners report: (?P<part>.+)$"), "issue_topic",
     "Владельцы сообщают: {part}", "Sahiblər bildirir: {part}"),
]
# English of the same titles (product phase, stage 1): the part in the glossary's English
TITLE_TEMPLATES_EN = [
    "NHTSA recall {n}: {part}",
    "Manufacturer communication: {part}",
    "Owners report (CarComplaints.com): {part}",
    "Owners report: {part}",
]
