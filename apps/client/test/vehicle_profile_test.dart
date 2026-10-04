import 'package:autoexpert_client/features/buyer/data/buyer_catalog_api.dart';
import 'package:autoexpert_client/features/buyer/presentation/vehicle_profile_page.dart';
import 'package:autoexpert_client/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeCatalogApi extends BuyerCatalogApi {
  @override
  Future<Map<String, dynamic>> vehicle(
      String variantId, String language) async {
    return {
      'id': variantId,
      'make': 'Toyota',
      'model': 'Camry',
      'year': 2018,
      'configuration': '2.5 automatic FWD',
      'facts': {
        'engine_displacement': {'value': '2.5'},
        'cylinders': {'value': '4'},
        'fuel': {'value': 'GASOLINE'},
        'engine_description': {'value': 'inline-4 gasoline'},
        'transmission_family': {'value': 'AT'},
        'gears': {'value': '8'},
        'transmission_description': {
          'value': '8-speed torque-converter automatic'
        },
        'drivetrain': {'value': 'FWD'},
      },
      'profile': {
        'summary': [
          {'key': 'market', 'label': 'Исходный рынок', 'value': 'USA'},
        ],
        'technical': [
          {
            'key': 'engine',
            'title': 'Двигатель',
            'rows': [
              {
                'key': 'engine_displacement',
                'label': 'Объём',
                'value': '2.5 L'
              },
            ],
          },
          {
            'key': 'fluids',
            'title': 'Масла и жидкости',
            'rows': [
              {
                'key': 'engine_oil_viscosity',
                'label': 'Вязкость масла',
                'value': '5W-30',
                'qa_fixture': true,
              },
              {
                'key': 'engine_oil_viscosity',
                'label': 'Вязкость масла',
                'value': '5W-30',
                'qa_fixture': true,
              },
              {
                'key': 'engine_oil_capacity_l',
                'label': 'Объём масла',
                'value': '4.4 L',
                'qa_fixture': true,
              },
            ],
          },
          {
            'key': 'wheels',
            'title': 'Шины и диски',
            'rows': [],
            'empty_text': 'Подтверждённых данных нет.',
          },
        ],
        'categories': [
          {'key': 'technical', 'title': 'Техническая часть'},
          {
            'key': 'weak_points',
            'title': 'Слабые места',
            'entries': [],
            'empty_text': 'Применимые слабые места пока не подтверждены.'
          },
          {'key': 'campaigns', 'title': 'Сервисные кампании', 'entries': []},
          {
            'key': 'inspection',
            'title': 'Что проверить при покупке',
            'entries': [],
            'empty_text': 'Проверьте VIN и документы.'
          },
        ],
      },
    };
  }
}

class FuelCatalogApi extends FakeCatalogApi {
  @override
  Future<Map<String, dynamic>> vehicle(
      String variantId, String language) async {
    final data = await super.vehicle(variantId, language);
    final profile = data['profile'] as Map<String, dynamic>;
    profile['technical'] = [
      {
        'key': 'fuel',
        'title': 'Топливо',
        'rows': [
          {
            'key': 'fuel_octane_maker',
            'kind': 'manufacturer',
            'label': 'Бензин по требованию производителя',
            'value': 'АИ-95 (AKI 91 по шкале США)',
            'basis': 'по требованию производителя',
          },
          {
            'key': 'fuel_recommendation',
            'kind': 'recommendation',
            'label': 'Рекомендация Auto Expert',
            'value': 'не ниже АИ-98, рекомендация для АЗ/СНГ',
            'basis': 'рекомендация для АЗ/СНГ',
            'reason': 'турбонаддув; требование производителя выше',
          },
        ],
      },
    ];
    return data;
  }
}

void main() {
  previewBadgeTests();
  testWidgets('fuel: the recommendation is its own marked line, apart from '
      "the manufacturer's octane", (tester) async {
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('ru'),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      home: VehicleProfilePage(
        api: FuelCatalogApi(),
        language: 'ru',
        variantId: 'turbo-2020',
        onCheckVin: () {},
      ),
    ));
    await tester.pumpAndSettle();
    final maker = find.byKey(const ValueKey('fuel-manufacturer'));
    final recommendation = find.byKey(const ValueKey('fuel-recommendation'));
    expect(maker, findsOneWidget);
    expect(recommendation, findsOneWidget);
    expect(
        find.descendant(
            of: maker, matching: find.text('Бензин по требованию производителя')),
        findsOneWidget);
    expect(
        find.descendant(
            of: recommendation,
            matching: find.text('не ниже АИ-98, рекомендация для АЗ/СНГ')),
        findsOneWidget);
    expect(
        find.descendant(
            of: recommendation,
            matching: find.textContaining('по требованию производителя')),
        findsNothing);
  });
  testWidgets(
      'technical profile shows confirmed oil once and hides empty groups',
      (tester) async {
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('ru'),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      home: VehicleProfilePage(
        api: FakeCatalogApi(),
        language: 'ru',
        variantId: 'camry-2018',
        qaMode: true,
        onCheckVin: () {},
      ),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Toyota Camry'), findsOneWidget);
    expect(find.textContaining('inline-4'), findsNothing);
    expect(find.textContaining('torque-converter'), findsNothing);
    expect(find.textContaining('Передний привод'), findsOneWidget);
    expect(find.text('5W-30'), findsOneWidget);
    expect(find.text('QA fixture · test only'), findsOneWidget);
    expect(find.text('4.4 L'), findsOneWidget);
    expect(find.text('Шины и диски'), findsNothing);
    expect(find.text('Подтверждённых данных нет.'), findsNothing);
    await tester.tap(find.text('Что проверить при покупке'));
    await tester.pumpAndSettle();
    expect(find.text('Проверьте VIN и документы.'), findsOneWidget);
    expect(find.text('5W-30'), findsNothing);
    expect(find.text('QA fixture · test only'), findsNothing);
  });

  testWidgets('production profile hides local QA oil fixture entirely',
      (tester) async {
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('ru'),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      home: VehicleProfilePage(
        api: FakeCatalogApi(),
        language: 'ru',
        variantId: 'camry-2018',
        onCheckVin: () {},
      ),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Масла и жидкости'), findsNothing);
    expect(find.text('5W-30'), findsNothing);
    expect(find.text('4.4 L'), findsNothing);
    expect(find.textContaining('2.5 л'), findsWidgets);
  });

  testWidgets('AZ card uses structured facts instead of raw English',
      (tester) async {
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('az'),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      home: VehicleProfilePage(
        api: FakeCatalogApi(),
        language: 'az',
        variantId: 'camry-2018',
        onCheckVin: () {},
      ),
    ));
    await tester.pumpAndSettle();
    expect(find.textContaining('Benzin'), findsOneWidget);
    expect(find.textContaining('Ön ötürücü'), findsOneWidget);
    expect(find.textContaining('gasoline'), findsNothing);
    expect(find.textContaining('automatic'), findsNothing);
  });
}

class PreviewCatalogApi extends FakeCatalogApi {
  @override
  Future<Map<String, dynamic>> vehicle(
          String variantId, String language) async =>
      {...await super.vehicle(variantId, language), 'preview': true};
}

void previewBadgeTests() {
  testWidgets('a preview configuration carries the preview badge',
      (tester) async {
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('az'),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      home: VehicleProfilePage(
        api: PreviewCatalogApi(),
        language: 'az',
        variantId: 'preview-2022',
        onCheckVin: () {},
      ),
    ));
    await tester.pumpAndSettle();
    expect(find.text('Ön baxış · 2021–2026'), findsOneWidget);
  });
  testWidgets('a production configuration has no preview badge',
      (tester) async {
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('ru'),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      home: VehicleProfilePage(
        api: FakeCatalogApi(),
        language: 'ru',
        variantId: 'camry-2018',
        onCheckVin: () {},
      ),
    ));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('preview-badge')), findsNothing);
  });
}
