/// Consumer wording is composed from corroborated structured facts. Source
/// descriptions and codes remain in the API for provenance, but free-form
/// English descriptions are not presented as RU/AZ product copy.
class TechnicalDisplay {
  const TechnicalDisplay._();

  static Map<String, dynamic> _map(Object? value) =>
      value is Map<String, dynamic> ? value : const {};

  static String _raw(Map<String, dynamic> facts, String key) {
    final fact = _map(facts[key]);
    final value = fact['value'];
    return value == null ? '' : '$value'.trim();
  }

  static String _language(String language) => language == 'az' ? 'az' : 'ru';

  static String? _term(String value, String language) {
    final terms = <String, (String, String)>{
      'ICE': ('ДВС', 'Daxiliyanma mühərriki'),
      'BEV': ('Электромобиль', 'Elektromobil'),
      'HEV': ('Гибрид', 'Hibrid'),
      'PHEV': ('Подключаемый гибрид', 'Şarj olunan hibrid'),
      'MHEV': ('Мягкий гибрид', 'Yumşaq hibrid'),
      'GASOLINE': ('Бензин', 'Benzin'),
      'DIESEL': ('Дизель', 'Dizel'),
      'ELECTRICITY': ('Электричество', 'Elektrik'),
      'HYDROGEN': ('Водород', 'Hidrogen'),
      'TURBO': ('Турбо', 'Turbo'),
      'NATURALLY_ASPIRATED': ('Без наддува', 'Turbosuz'),
      'AT': (
        'Гидротрансформаторный автомат AT',
        'Hidrotransformatorlu avtomat AT'
      ),
      'CVT': ('Вариатор CVT', 'Variator CVT'),
      'ECVT': ('Электромеханическая e-CVT', 'Elektromexaniki e-CVT'),
      'DCT': ('Робот DCT', 'Robot DCT'),
      'MANUAL': ('Механическая коробка', 'Mexaniki sürətlər qutusu'),
      'SINGLE_SPEED': ('Одноступенчатый редуктор', 'Birpilləli reduktor'),
      'AUTOMATIC_UNSPECIFIED': (
        'Автоматическая, точный тип неизвестен',
        'Avtomatik, dəqiq növ məlum deyil'
      ),
      'VARIABLE_UNSPECIFIED': (
        'Бесступенчатая, точный тип неизвестен',
        'Pilləsiz, dəqiq növ məlum deyil'
      ),
      'AMT_UNSPECIFIED': (
        'Автоматизированная, точный тип неизвестен',
        'Avtomatlaşdırılmış, dəqiq növ məlum deyil'
      ),
      'FWD': ('Передний привод', 'Ön ötürücü'),
      'FRONT': ('Передний привод', 'Ön ötürücü'),
      'RWD': ('Задний привод', 'Arxa ötürücü'),
      'REAR': ('Задний привод', 'Arxa ötürücü'),
      'AWD': ('Полный привод AWD', 'Tam ötürücü AWD'),
      '4WD': ('Полный привод 4WD', 'Tam ötürücü 4WD'),
      'PART_TIME_4WD': ('Подключаемый полный привод', 'Qoşulan tam ötürücü'),
      'SEDAN': ('Седан', 'Sedan'),
      'CROSSOVER': ('Кроссовер', 'Krossover'),
      'SUV': ('SUV', 'SUV'),
      'HATCHBACK': ('Хетчбэк', 'Hetçbek'),
      'WAGON': ('Универсал', 'Universal'),
      'COUPE': ('Купе', 'Kupe'),
    };
    final pair = terms[value.toUpperCase()];
    return pair == null
        ? null
        : _language(language) == 'az'
            ? pair.$2
            : pair.$1;
  }

  static String? _sourceCode(String raw) =>
      RegExp(r'^[A-Z0-9][A-Z0-9._/+\-]{1,19}$').hasMatch(raw) ? raw : null;

  static List<String> _engineCodes(Map<String, dynamic> facts) {
    final codes = <String>[];
    final seen = <String>{};
    void add(String? code) {
      if (code != null && seen.add(code.toUpperCase())) codes.add(code);
    }

    add(_sourceCode(_raw(facts, 'engine_code')));
    final description = _raw(facts, 'engine_description');
    add(_sourceCode(description));
    // Only recognizable standalone technical identifiers are retained from
    // a source-backed description. Surrounding English prose is discarded.
    final embedded = RegExp(
      r'(^|[^A-Za-z0-9])(D-4S|GDI|Gamma-II|SIDI|TFSI|TSI|MPI|CRDi)(?=$|[^A-Za-z0-9])',
      caseSensitive: false,
    );
    for (final match in embedded.allMatches(description)) {
      add(match.group(2));
    }
    return codes;
  }

  static String engine(Map<String, dynamic> facts, String language) {
    final powertrain = _raw(facts, 'powertrain');
    if (powertrain == 'BEV' || powertrain == 'FCEV') {
      return _term(powertrain, language) ?? '';
    }
    final displacement = _raw(facts, 'engine_displacement');
    final cylinders = _raw(facts, 'cylinders');
    final fuel = _term(_raw(facts, 'fuel'), language);
    final aspiration = _term(_raw(facts, 'aspiration'), language);
    final codes = _engineCodes(facts);
    final parts = <String>[
      if (displacement.isNotEmpty)
        '$displacement ${language == 'az' ? 'l' : 'л'}',
      if (cylinders.isNotEmpty && RegExp(r'^\d+$').hasMatch(cylinders))
        language == 'az' ? '$cylinders silindr' : '$cylinders цилиндра',
      if (fuel != null) fuel,
      if (aspiration != null) aspiration,
      ...codes,
    ];
    if (parts.isEmpty) {
      return _term(powertrain, language) ?? '';
    }
    return parts.join(' · ');
  }

  static String transmission(Map<String, dynamic> facts, String language) {
    final family = _term(_raw(facts, 'transmission_family'), language);
    if (family == null) {
      return _sourceCode(_raw(facts, 'transmission_code')) ??
          _sourceCode(_raw(facts, 'transmission_description')) ??
          '';
    }
    final gears = _raw(facts, 'gears');
    if (gears.isEmpty || !RegExp(r'^\d+$').hasMatch(gears)) return family;
    return language == 'az'
        ? '$gears pilləli $family'
        : '$gears-ступенчатая · $family';
  }

  static String configuration(Map<String, dynamic> facts, String language) {
    return [
      engine(facts, language),
      transmission(facts, language),
      _term(_raw(facts, 'drivetrain'), language) ?? '',
    ].where((part) => part.isNotEmpty).join(' · ');
  }

  static Map<String, dynamic> factsFromCandidate(
      Map<String, dynamic> candidate) {
    final result = <String, dynamic>{};
    for (final key in [
      'engine_displacement',
      'cylinders',
      'powertrain',
      'fuel',
      'aspiration',
      'transmission_family',
      'gears',
      'drivetrain',
    ]) {
      if (candidate[key] != null && '${candidate[key]}'.isNotEmpty) {
        result[key] = {'value': candidate[key]};
      }
    }
    return result;
  }

  static String? conflictCatalogValue(
      String field, Object? value, String language) {
    if (value == null) return null;
    final raw = '$value'.trim();
    if (raw.isEmpty) return null;
    if (field == 'drivetrain' ||
        field == 'fuel' ||
        field == 'body' ||
        field == 'powertrain') {
      return _term(raw, language);
    }
    if (field == 'transmission') return _sourceCode(raw);
    return raw;
  }

  static String? rowValue(String key, Map<String, dynamic> facts,
      String language, String apiValue) {
    if (key == 'engine_description') {
      final value = engine(facts, language);
      return value.isEmpty ? null : value;
    }
    if (key == 'transmission_description') {
      final value = transmission(facts, language);
      return value.isEmpty ? null : value;
    }
    if (key == 'motor_description') {
      return _sourceCode(_raw(facts, key));
    }
    if (key == 'engine_displacement') {
      final value = _raw(facts, key);
      return value.isEmpty ? null : '$value ${language == 'az' ? 'l' : 'л'}';
    }
    if (key == 'cylinders') {
      final value = _raw(facts, key);
      return value.isEmpty ? null : value;
    }
    if (key == 'transmission_family' ||
        key == 'powertrain' ||
        key == 'fuel' ||
        key == 'drivetrain' ||
        key == 'aspiration' ||
        key == 'body') {
      return _term(_raw(facts, key), language);
    }
    // This is a final UI guard for the common raw source descriptions. Other
    // fields (numeric facts, manufacturer codes and localized copy) are kept.
    if (RegExp(r'\b(gasoline|inline-\d+|torque-converter|front)\b',
            caseSensitive: false)
        .hasMatch(apiValue)) {
      return null;
    }
    return apiValue.isEmpty ? null : apiValue;
  }
}
