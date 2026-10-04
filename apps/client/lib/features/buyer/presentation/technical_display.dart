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

  static String _litre(String language) =>
      switch (language) { 'az' => 'l', 'en' => 'L', _ => 'л' };

  static String _language(String language) =>
      language == 'az' || language == 'en' ? language : 'ru';

  static String? _term(String value, String language) {
    final terms = <String, (String, String, String)>{
      'ICE': ('ДВС', 'Daxiliyanma mühərriki', 'Gas engine'),
      'BEV': ('Электромобиль', 'Elektromobil', 'Electric vehicle'),
      'HEV': ('Гибрид', 'Hibrid', 'Hybrid'),
      'PHEV': ('Подключаемый гибрид', 'Şarj olunan hibrid', 'Plug-in hybrid'),
      'MHEV': ('Мягкий гибрид', 'Yumşaq hibrid', 'Mild hybrid'),
      'GASOLINE': ('Бензин', 'Benzin', 'Gasoline'),
      'DIESEL': ('Дизель', 'Dizel', 'Diesel'),
      'ELECTRICITY': ('Электричество', 'Elektrik', 'Electricity'),
      'HYDROGEN': ('Водород', 'Hidrogen', 'Hydrogen'),
      'TURBO': ('Турбо', 'Turbo', 'Turbo'),
      'NATURALLY_ASPIRATED': ('Без наддува', 'Turbosuz', 'Naturally aspirated'),
      'AT': (
        'Гидротрансформаторный автомат AT',
        'Hidrotransformatorlu avtomat AT', 'Torque-converter automatic (AT)'),
      'CVT': ('Вариатор CVT', 'Variator CVT', 'CVT'),
      'ECVT': ('Электромеханическая e-CVT', 'Elektromexaniki e-CVT', 'Electric e-CVT'),
      'DCT': ('Робот DCT', 'Robot DCT', 'Dual-clutch DCT'),
      'MANUAL': ('Механическая коробка', 'Mexaniki sürətlər qutusu', 'Manual transmission'),
      'SINGLE_SPEED': ('Одноступенчатый редуктор', 'Birpilləli reduktor', 'Single-speed reduction gear'),
      'AUTOMATIC_UNSPECIFIED': (
        'Автоматическая, точный тип неизвестен',
        'Avtomatik, dəqiq növ məlum deyil', 'Automatic, exact type unknown'),
      'VARIABLE_UNSPECIFIED': (
        'Бесступенчатая, точный тип неизвестен',
        'Pilləsiz, dəqiq növ məlum deyil', 'Continuously variable, exact type unknown'),
      'AMT_UNSPECIFIED': (
        'Автоматизированная, точный тип неизвестен',
        'Avtomatlaşdırılmış, dəqiq növ məlum deyil', 'Automated, exact type unknown'),
      'FWD': ('Передний привод', 'Ön ötürücü', 'Front-wheel drive'),
      'FRONT': ('Передний привод', 'Ön ötürücü', 'Front-wheel drive'),
      'RWD': ('Задний привод', 'Arxa ötürücü', 'Rear-wheel drive'),
      'REAR': ('Задний привод', 'Arxa ötürücü', 'Rear-wheel drive'),
      'AWD': ('Полный привод AWD', 'Tam ötürücü AWD', 'All-wheel drive (AWD)'),
      '4WD': ('Полный привод 4WD', 'Tam ötürücü 4WD', 'Four-wheel drive (4WD)'),
      'PART_TIME_4WD': ('Подключаемый полный привод', 'Qoşulan tam ötürücü', 'Part-time four-wheel drive'),
      'SEDAN': ('Седан', 'Sedan', 'Sedan'),
      'CROSSOVER': ('Кроссовер', 'Krossover', 'Crossover'),
      'SUV': ('SUV', 'SUV', 'SUV'),
      'HATCHBACK': ('Хетчбэк', 'Hetçbek', 'Hatchback'),
      'WAGON': ('Универсал', 'Universal', 'Wagon'),
      'COUPE': ('Купе', 'Kupe', 'Coupe'),
    };
    final pair = terms[value.toUpperCase()];
    return pair == null
        ? null
        : switch (_language(language)) {
            'az' => pair.$2,
            'en' => pair.$3,
            _ => pair.$1,
          };
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
        '$displacement ${_litre(language)}',
      if (cylinders.isNotEmpty && RegExp(r'^\d+$').hasMatch(cylinders))
        switch (language) {
          'az' => '$cylinders silindr',
          'en' => '$cylinders cylinders',
          _ => '$cylinders цилиндра',
        },
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
    return switch (language) {
      'az' => '$gears pilləli $family',
      'en' => '$gears-speed $family',
      _ => '$gears-ступенчатая · $family',
    };
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
      return value.isEmpty ? null : '$value ${_litre(language)}';
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
