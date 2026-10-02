import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:autoexpert_client/features/vin/data/vin_history_api.dart';
import 'package:autoexpert_client/features/vin/data/vin_validation.dart';
import 'package:autoexpert_client/features/vin/presentation/vin_history_page.dart';
import 'package:autoexpert_client/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeVinHistoryApi extends VinHistoryApi {
  Map<String, dynamic>? saved;
  Map<String, dynamic>? check;
  Map<String, dynamic>? report;
  Completer<Map<String, dynamic>>? paymentGate;
  Map<String, dynamic>? retryResult;
  int createCalls = 0;
  int paymentCalls = 0;
  int reportCalls = 0;
  int retryCalls = 0;
  int assetCalls = 0;

  @override
  Future<Map<String, dynamic>?> loadSavedCheck(String language) async => saved;

  @override
  Future<Map<String, dynamic>> createCheck(String vin, String language) async {
    createCalls++;
    return check!;
  }

  @override
  Future<Map<String, dynamic>> mockPayment(String checkId, String language) {
    paymentCalls++;
    return paymentGate?.future ??
        Future.value(
            {...check!, 'is_unlocked': true, 'status': 'REPORT_READY'});
  }

  @override
  Future<Map<String, dynamic>> getReport(
      String checkId, String language) async {
    reportCalls++;
    return report!;
  }

  @override
  Future<Map<String, dynamic>> retryReport(
      String checkId, String language) async {
    retryCalls++;
    return retryResult!;
  }

  @override
  Future<Uint8List> getAssetBytes(
      String checkId, String assetId, String language) async {
    assetCalls++;
    return Uint8List.fromList(utf8.encode(
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"></svg>'));
  }
}

Map<String, dynamic> checkFixture({int? photoCount, bool unlocked = false}) => {
      'check_id': 'fixture-check',
      'is_mock': true,
      'vin': '3FA6P0HD0KR114795',
      'status': unlocked ? 'REPORT_READY' : 'AWAITING_PAYMENT',
      'vehicle_identity': {
        'make': 'Ford',
        'model': 'Fusion',
        'model_year': 2019
      },
      'preview': {
        'available_record_types': <String>[],
        if (photoCount != null) 'photo_count': photoCount,
        'content_determined_after_purchase': photoCount == null,
      },
      'quote': {
        'retail_price_azn': '15.00',
        'currency': 'AZN',
        'sellable': true
      },
      'is_unlocked': unlocked,
    };

Map<String, dynamic> reportFixture() => {
      'check_id': 'fixture-check',
      'is_mock': true,
      'vin': '3FA6P0HD0KR114795',
      'language': 'ru',
      'status': 'REPORT_READY',
      'vehicle_identity': {
        'make': 'Ford',
        'model': 'Fusion',
        'model_year': 2019
      },
      'sections': [
        {
          'key': 'timeline',
          'title': 'Хронология',
          'items': [
            {'date': '2020-01-02', 'text': 'Подтверждённая запись события'}
          ],
        },
      ],
      'mileage_anomaly': false,
      'asset_ids': <String>[],
    };

Future<void> pumpVinPage(WidgetTester tester, FakeVinHistoryApi api) async {
  await tester.pumpWidget(MaterialApp(
    locale: const Locale('ru'),
    supportedLocales: AppLocalizations.supportedLocales,
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    home: VinHistoryPage(api: api, language: 'ru', qaMode: true),
  ));
  await tester.pumpAndSettle();
}

void main() {
  test('US VIN input verifies check digit before any request', () {
    expect(isValidUsVin('3FA6P0HD0KR114795'), isTrue);
    expect(isValidUsVin('3FA6P0HD1KR114795'), isFalse);
    expect(isValidUsVin('3FA6P0HD0KR11479I'), isFalse);
  });

  testWidgets('invalid VIN never calls API', (tester) async {
    final api = FakeVinHistoryApi();
    await pumpVinPage(tester, api);
    await tester.enterText(find.byType(TextField), '3FA6P0HD1KR114795');
    await tester.tap(find.text('Проверить VIN'));
    await tester.pump();
    expect(find.text('Проверьте VIN и его контрольную цифру'), findsOneWidget);
    expect(api.createCalls, 0);
    api.close();
  });

  testWidgets('fixture-only flow does not imply coverage for another VIN',
      (tester) async {
    final api = FakeVinHistoryApi();
    await pumpVinPage(tester, api);
    await tester.enterText(find.byType(TextField), '1HGCM82633A004352');
    await tester.tap(find.text('Проверить VIN'));
    await tester.pump();
    expect(find.textContaining('только VIN 3FA6P0HD0KR114795'), findsOneWidget);
    expect(api.createCalls, 0);
    api.close();
  });

  testWidgets('unknown photo coverage stays neutral and report stays locked',
      (tester) async {
    final api = FakeVinHistoryApi()..check = checkFixture();
    await pumpVinPage(tester, api);
    await tester.enterText(find.byType(TextField), '3FA6P0HD0KR114795');
    await tester.tap(find.text('Проверить VIN'));
    await tester.pumpAndSettle();
    expect(find.text('Предварительная проверка'), findsOneWidget);
    expect(find.textContaining('Состав конкретных записей определяется'),
        findsOneWidget);
    expect(find.textContaining('Подтверждено фотографий'), findsNothing);
    expect(find.textContaining('Подтверждённая запись события'), findsNothing);
    expect(api.reportCalls, 0);
    api.close();
  });

  testWidgets('confirmed photo count and one mock payment open report',
      (tester) async {
    final api = FakeVinHistoryApi()
      ..check = checkFixture(photoCount: 3)
      ..report = reportFixture()
      ..paymentGate = Completer<Map<String, dynamic>>();
    await pumpVinPage(tester, api);
    await tester.enterText(find.byType(TextField), '3FA6P0HD0KR114795');
    await tester.tap(find.text('Проверить VIN'));
    await tester.pumpAndSettle();
    expect(find.text('Подтверждено фотографий: 3'), findsOneWidget);
    expect(find.textContaining('Подтверждённая запись события'), findsNothing);
    await tester.ensureVisible(find.text('Тестовая оплата и отчёт'));
    await tester.tap(find.text('Тестовая оплата и отчёт'));
    await tester.tap(find.text('Тестовая оплата и отчёт'));
    expect(api.paymentCalls, 1);
    api.paymentGate!.complete({
      ...api.check!,
      'is_unlocked': true,
      'status': 'REPORT_READY',
    });
    await tester.pumpAndSettle();
    expect(
        find.textContaining('Подтверждённая запись события',
            skipOffstage: false),
        findsOneWidget);
    expect(api.reportCalls, 1);
    api.close();
  });

  testWidgets('saved entitled report is reopened without a new payment',
      (tester) async {
    final api = FakeVinHistoryApi()
      ..saved = checkFixture(unlocked: true)
      ..report = reportFixture();
    await pumpVinPage(tester, api);
    expect(
        find.textContaining('Подтверждённая запись события',
            skipOffstage: false),
        findsOneWidget);
    expect(api.createCalls, 0);
    expect(api.paymentCalls, 0);
    api.close();
  });

  testWidgets('post-payment provider failure offers retry, not another payment',
      (tester) async {
    final api = FakeVinHistoryApi()
      ..saved = {
        ...checkFixture(),
        'is_unlocked': true,
        'status': 'FAILED_RETRYABLE',
      }
      ..retryResult = checkFixture(unlocked: true)
      ..report = reportFixture();
    await pumpVinPage(tester, api);
    expect(find.text('Тестовая оплата и отчёт'), findsNothing);
    expect(find.text('Повторить получение отчёта'), findsOneWidget);
    expect(api.reportCalls, 0);
    await tester.ensureVisible(find.text('Повторить получение отчёта'));
    await tester.tap(find.text('Повторить получение отчёта'));
    await tester.pumpAndSettle();
    expect(api.retryCalls, 1);
    expect(api.reportCalls, 1);
    expect(
        find.textContaining('Подтверждённая запись события',
            skipOffstage: false),
        findsOneWidget);
    api.close();
  });

  testWidgets('asset bytes are requested only after report entitlement',
      (tester) async {
    final api = FakeVinHistoryApi()
      ..check = checkFixture(photoCount: 1)
      ..report = {
        ...reportFixture(),
        'asset_ids': ['asset-1'],
        'assets': [
          {
            'id': 'asset-1',
            'caption': 'Учебный макет фотографии',
            'event_date': '2021-02-01',
            'source': 'local_history_fixture',
            'photo_type': 'WHOLESALE_PHOTO',
          }
        ],
      };
    await pumpVinPage(tester, api);
    await tester.enterText(find.byType(TextField), '3FA6P0HD0KR114795');
    await tester.tap(find.text('Проверить VIN'));
    await tester.pumpAndSettle();
    expect(api.assetCalls, 0);
    await tester.ensureVisible(find.text('Тестовая оплата и отчёт'));
    await tester.tap(find.text('Тестовая оплата и отчёт'));
    await tester.pumpAndSettle();
    expect(api.assetCalls, 1);
    expect(find.text('Аукционная фотография', skipOffstage: false),
        findsOneWidget);
    expect(find.text('Учебный макет фотографии', skipOffstage: false),
        findsOneWidget);
    expect(find.text('Источник: Тестовый источник', skipOffstage: false),
        findsOneWidget);
    api.close();
  });

  testWidgets('production mode hides mock controls and sample VIN',
      (tester) async {
    final api = FakeVinHistoryApi()..saved = checkFixture();
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('ru'),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      home: VinHistoryPage(api: api, language: 'ru'),
    ));
    await tester.pumpAndSettle();
    expect(
        find.text(
            'Введите VIN из 17 символов. Предварительная проверка покажет только подтверждённые сведения.'),
        findsOneWidget);
    expect(find.textContaining('Перед тестовой оплатой'), findsNothing);
    expect(find.text('Тестовая оплата и отчёт'), findsNothing);
    expect(find.textContaining('только VIN 3FA6P0HD0KR114795'), findsNothing);
    expect(find.text('3FA6P0HD0KR114795'), findsNothing);
    expect(find.text('Предварительная проверка'), findsNothing);
    api.close();
  });

  testWidgets('AZ production VIN copy has no test-payment wording',
      (tester) async {
    final api = FakeVinHistoryApi();
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('az'),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      home: VinHistoryPage(api: api, language: 'az'),
    ));
    await tester.pumpAndSettle();
    expect(find.textContaining('Sınaq ödənişindən əvvəl'), findsNothing);
    expect(find.textContaining('İlkin yoxlama yalnız təsdiqlənmiş'),
        findsOneWidget);
    expect(find.textContaining('Sınaq rejimi'), findsNothing);
    api.close();
  });
}
