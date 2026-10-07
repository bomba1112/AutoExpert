import 'dart:convert';

import 'package:autoexpert_client/core/network/api_client.dart';
import 'package:autoexpert_client/features/listing/data/listing_intake_api.dart';
import 'package:autoexpert_client/features/listing/presentation/listing_intake_page.dart';
import 'package:autoexpert_client/features/listing/presentation/listing_result_page.dart';
import 'package:autoexpert_client/features/vin/data/vin_history_api.dart';
import 'package:autoexpert_client/features/vin/presentation/check_vehicle_page.dart';
import 'package:autoexpert_client/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

class FakeListingApi extends ListingIntakeApi {
  FakeListingApi() : super(VinHistoryApi());

  final calls = <Map<String, dynamic>>[];
  Map<String, dynamic> result = const {};

  @override
  Future<Map<String, dynamic>> submit({
    required String inputType,
    required String language,
    String? sourceUrl,
    String? text,
    String? html,
    Map<String, dynamic>? fields,
  }) async {
    calls.add({
      'input_type': inputType,
      'language': language,
      'source_url': sourceUrl,
      'text': text,
      'html': html,
      'fields': fields,
    });
    if (inputType == 'URL_REFERENCE') {
      return {'next_step': 'PROVIDE_CONTENT'};
    }
    return result;
  }
}

class EmptyVinApi extends VinHistoryApi {
  @override
  Future<Map<String, dynamic>?> loadSavedCheck(String language) async => null;
}

class MemoryVinStore implements VinSessionStore {
  String? token;
  @override
  Future<String?> readToken() async => token;
  @override
  Future<String?> readCheckId() async => null;
  @override
  Future<void> writeToken(String? value) async => token = value;
  @override
  Future<void> writeCheckId(String? value) async {}
}

Map<String, dynamic> listingResult(String status) => {
      'next_step': 'VIEW_RESULT',
      'snapshot': {
        'source_type': 'TURBO_AZ',
        'source_url': 'https://turbo.az/autos/12345678-chevrolet-cruze'
      },
      'claims': [
        {'field_name': 'make', 'raw_value': 'Chevrolet'},
        {'field_name': 'model', 'raw_value': 'Cruze'},
        {'field_name': 'year', 'raw_value': '2017'},
        {'field_name': 'engine', 'raw_value': '1.4 L'},
      ],
      'match': {
        'status': status,
        'candidates': [
          {
            'variant_id': 'cruze-2017',
            'make': 'Chevrolet',
            'model': 'Cruze',
            'year': 2017,
            'configuration': '1.4 automatic FWD',
          }
        ],
        'conflicts': status == 'CLAIM_CONFLICT'
            ? [
                {
                  'field_name': 'engine',
                  'claimed': '3.5 L',
                  'catalog_values': ['1.4']
                }
              ]
            : [],
        'question': status == 'MULTIPLE_CANDIDATES'
            ? 'Which engine is shown in the listing?'
            : null,
      }
    };

Widget shell(Widget child, {String language = 'ru'}) => MaterialApp(
      locale: Locale(language),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      home: Scaffold(body: child),
    );

void main() {
  test('Turbo.az URL validator rejects off-site and active-content schemes',
      () {
    expect(isTurboAzUrl('https://turbo.az/autos/12345678-a'), isTrue);
    expect(isTurboAzUrl('https://www.turbo.az/autos/12345678-a'), isTrue);
    expect(isTurboAzUrl('https://ru.turbo.az/autos/12345678-a'), isTrue);
    expect(isTurboAzUrl('https://turbo.az.evil.test/autos/1'), isFalse);
    expect(isTurboAzUrl('http://turbo.az/autos/1'), isFalse);
    expect(isTurboAzUrl('https://user@turbo.az/autos/1'), isFalse);
    expect(isTurboAzUrl('https://turbo.az:443/autos/12345678-a'), isFalse);
    expect(isTurboAzUrl('https://turbo.az/autos/%31%32%33%34-a'), isFalse);
    expect(isTurboAzUrl('https://turbo.az/autos'), isFalse);
    expect(isTurboAzUrl('file:///autos/1'), isFalse);
  });

  test('URL-reference request only reaches auth and listing intake', () async {
    final paths = <String>[];
    final client = MockClient((request) async {
      paths.add(request.url.path);
      if (request.url.path.endsWith('/auth/demo')) {
        return http.Response(
            jsonEncode({'access_token': 'local-demo-token'}), 200);
      }
      expect(request.url.path, endsWith('/listings/intake'));
      expect(request.method, 'POST');
      expect(request.headers['X-AutoExpert-Token'], 'local-demo-token');
      expect(request.headers.containsKey('Authorization'), isFalse);
      final body = jsonDecode(request.body) as Map<String, dynamic>;
      expect(body['input_type'], 'URL_REFERENCE');
      expect(body['source_url'], 'https://turbo.az/autos/12345678-a');
      expect(body.containsKey('text'), isFalse);
      return http.Response(jsonEncode({'next_step': 'PROVIDE_CONTENT'}), 200);
    });
    final vinApi = VinHistoryApi(
        client: ApiClient(client: client), store: MemoryVinStore());
    final result = await ListingIntakeApi(vinApi).submit(
      inputType: 'URL_REFERENCE',
      language: 'ru',
      sourceUrl: 'https://turbo.az/autos/12345678-a',
    );
    expect(result['next_step'], 'PROVIDE_CONTENT');
    expect(paths, ['/api/v1/auth/demo', '/api/v1/listings/intake']);
    vinApi.close();
  });

  testWidgets('VIN, Turbo.az and manual remain separate check tabs',
      (tester) async {
    final vin = EmptyVinApi();
    final listings = FakeListingApi();
    await tester.pumpWidget(shell(CheckVehiclePage(
      vinApi: vin,
      listingApi: listings,
      language: 'ru',
      onAddComparison: (_) {},
    )));
    await tester.pumpAndSettle();
    expect(find.text('VIN'), findsWidgets);
    expect(find.text('Turbo.az'), findsWidgets);
    expect(find.text('Вручную'), findsOneWidget);
    await tester.tap(find.text('Turbo.az').first);
    await tester.pumpAndSettle();
    expect(find.text('Ссылка Turbo.az'), findsOneWidget);
    await tester.tap(find.text('Вручную'));
    await tester.pumpAndSettle();
    expect(find.text('Введите данные автомобиля'), findsOneWidget);
    vin.close();
  });

  testWidgets('URL is stored as reference then content is submitted by user',
      (tester) async {
    final api = FakeListingApi()..result = listingResult('EXACT_MATCH');
    await tester.pumpWidget(shell(ListingIntakePage(
      api: api,
      language: 'ru',
      onCheckVin: (_) {},
      onAddComparison: (_) {},
    )));
    await tester.enterText(find.byType(TextField).first,
        'https://turbo.az/autos/12345678-chevrolet-cruze');
    await tester.tap(find.text('Сохранить ссылку'));
    await tester.pumpAndSettle();
    expect(api.calls, hasLength(1));
    expect(api.calls.single['input_type'], 'URL_REFERENCE');
    expect(api.calls.single['text'], isNull);
    expect(find.textContaining('Ссылка сохранена'), findsOneWidget);
    await tester.enterText(find.byType(TextField).last,
        'Chevrolet Cruze 2017, 1.4 L, automatic, FWD');
    await tester.ensureVisible(find.text('Сопоставить объявление'));
    await tester.tap(find.text('Сопоставить объявление'));
    await tester.pumpAndSettle();
    expect(api.calls, hasLength(2));
    expect(api.calls.last['input_type'], 'TEXT');
    expect(api.calls.last['source_url'],
        'https://turbo.az/autos/12345678-chevrolet-cruze');
    expect(find.byType(ListingResultPage), findsOneWidget);
    expect(find.text('Chevrolet Cruze'), findsOneWidget);
  });

  testWidgets('manual entry submits seller claims without URL fetch',
      (tester) async {
    final api = FakeListingApi()..result = listingResult('EXACT_MATCH');
    await tester.pumpWidget(shell(
        ListingIntakePage(
          api: api,
          language: 'az',
          manual: true,
          onCheckVin: (_) {},
          onAddComparison: (_) {},
        ),
        language: 'az'));
    await tester.enterText(find.byType(TextField).at(0), 'Chevrolet');
    await tester.enterText(find.byType(TextField).at(1), 'Cruze');
    await tester.enterText(find.byType(TextField).at(2), '2017');
    await tester.ensureVisible(find.byType(FilledButton).last);
    await tester.tap(find.byType(FilledButton).last);
    await tester.pumpAndSettle();
    expect(api.calls.single['input_type'], 'MANUAL');
    expect(api.calls.single['source_url'], isNull);
    expect((api.calls.single['fields'] as Map)['year'], '2017');
    expect(find.byType(ListingResultPage), findsOneWidget);
  });

  testWidgets('conflicting claim is never shown as confirmed catalog data',
      (tester) async {
    await tester.pumpWidget(shell(ListingResultPage(
      result: listingResult('CLAIM_CONFLICT'),
      onCheckVin: (_) {},
      onAddComparison: (_) {},
    )));
    expect(find.textContaining('3.5 L'), findsOneWidget);
    expect(find.textContaining('1.4'), findsWidgets);
    expect(find.textContaining('CLAIM_CONFLICT'), findsNothing);
  });

  testWidgets('multiple candidates ask a clarifying question', (tester) async {
    await tester.pumpWidget(shell(ListingResultPage(
      result: listingResult('MULTIPLE_CANDIDATES'),
      onCheckVin: (_) {},
      onAddComparison: (_) {},
    )));
    expect(find.text('Which engine is shown in the listing?'), findsOneWidget);
    expect(find.textContaining('MULTIPLE_CANDIDATES'), findsNothing);
  });

  testWidgets('out-of-scope result has only neutral VIN CTA', (tester) async {
    await tester.pumpWidget(shell(ListingResultPage(
      result: listingResult('OUT_OF_PRODUCT_SCOPE'),
      onCheckVin: (_) {},
      onAddComparison: (_) {},
    )));
    expect(find.text('Проверить автомобиль по VIN'), findsOneWidget);
    expect(find.textContaining('вне технического каталога'), findsNothing);
    expect(find.textContaining('OUT_OF_PRODUCT_SCOPE'), findsNothing);
  });
}
