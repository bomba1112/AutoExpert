import 'package:autoexpert_client/features/buyer/presentation/technical_display.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  final facts = <String, dynamic>{
    'engine_displacement': {'value': '2.5'},
    'cylinders': {'value': '4'},
    'fuel': {'value': 'GASOLINE'},
    'engine_description': {'value': 'inline-4 gasoline'},
    'transmission_family': {'value': 'AT'},
    'gears': {'value': '8'},
    'transmission_description': {'value': '8-speed torque-converter automatic'},
    'drivetrain': {'value': 'Front'},
  };

  test('RU and AZ descriptions use structured facts, not raw source prose', () {
    final ru = TechnicalDisplay.configuration(facts, 'ru');
    final az = TechnicalDisplay.configuration(facts, 'az');
    expect(ru, contains('Бензин'));
    expect(ru, contains('Передний привод'));
    expect(az, contains('Benzin'));
    expect(az, contains('Ön ötürücü'));
    for (final description in [ru, az]) {
      expect(description, isNot(contains('gasoline')));
      expect(description, isNot(contains('inline-4')));
      expect(description, isNot(contains('torque-converter')));
      expect(description, isNot(contains('Front')));
    }
  });

  test('unspecified automatic is never presented as exact AT', () {
    final value = TechnicalDisplay.transmission({
      'transmission_family': {'value': 'AUTOMATIC_UNSPECIFIED'},
      'transmission_description': {'value': 'Automatic (S8)'},
    }, 'ru');
    expect(value, contains('точный тип неизвестен'));
    expect(value, isNot(contains('AT')));
  });

  test('source code survives, raw prose does not', () {
    expect(
        TechnicalDisplay.rowValue(
            'engine_description',
            {
              'engine_code': {'value': 'B48B20'},
              'engine_description': {'value': 'inline-4 gasoline'},
            },
            'ru',
            'inline-4 gasoline'),
        'B48B20');
    expect(
        TechnicalDisplay.conflictCatalogValue(
            'transmission', '8-speed torque-converter automatic', 'ru'),
        isNull);
  });

  test('embedded source-backed engine codes survive localized composition', () {
    final sourceFacts = <String, dynamic>{
      'engine_displacement': {'value': '2.5'},
      'fuel': {'value': 'GASOLINE'},
      'engine_description': {
        'value': 'inline-4 gasoline; D-4S / GDI; Gamma-II'
      },
    };
    for (final language in ['ru', 'az']) {
      final label = TechnicalDisplay.engine(sourceFacts, language);
      expect(label, contains('D-4S'));
      expect(label, contains('GDI'));
      expect(label, contains('Gamma-II'));
      expect(label, isNot(contains('inline-4')));
      expect(label, isNot(contains('gasoline')));
    }
  });
}
