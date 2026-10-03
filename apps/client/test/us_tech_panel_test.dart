import 'package:autoexpert_client/features/buyer/data/buyer_catalog_api.dart';
import 'package:autoexpert_client/features/buyer/presentation/us_tech_panel.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const labels = {
  'secondary': 'по данным справочников',
  'approximate': 'ориентировочно',
  'owner_reports': 'владельцы сообщают',
  'sources': 'Источники',
};

Map<String, dynamic> value(String v,
        {String? qualifier, bool secondary = false}) =>
    {
      'value': v,
      'qualifier': qualifier,
      'secondary': secondary,
      'approximate': false,
      'level': 'GENERATION',
      'source': {'title': 'Owner manual', 'locator': 'page 541', 'quote': 'q'},
    };

Map<String, dynamic> data({
  List<Map<String, dynamic>> categories = const [],
  List<Map<String, dynamic>> weakPoints = const [],
  List<Map<String, dynamic>> campaigns = const [],
  List<Map<String, dynamic>> maintenance = const [],
}) =>
    {
      'summary': '2.5 л · ДВС · Передний',
      'categories': categories,
      'weak_points': weakPoints,
      'campaigns': campaigns,
      'maintenance': maintenance,
      'labels': labels,
    };

Map<String, dynamic> category(String key, String title, int rows) => {
      'key': key,
      'title': title,
      'rows': [
        for (var i = 0; i < rows; i++)
          {
            'key': '$key$i',
            'label': 'Поле $i',
            'values': [value('$i мм')]
          }
      ],
    };

Widget host(Widget child) =>
    MaterialApp(home: Scaffold(body: SingleChildScrollView(child: child)));

class CountingApi extends BuyerCatalogApi {
  int calls = 0;
  @override
  Future<Map<String, dynamic>> usTechForVariant(
      String variantId, String language) async {
    calls++;
    return data(categories: [category('engine', 'Двигатель', 3)]);
  }
}

void main() {
  testWidgets('empty tabs are hidden; maintenance appears only with records',
      (tester) async {
    await tester.pumpWidget(host(UsTechPanel(
        data: data(categories: [category('engine', 'Двигатель', 5)]),
        language: 'ru')));
    expect(find.byKey(const ValueKey('us-tech-tab-technical')), findsOneWidget);
    expect(find.byKey(const ValueKey('us-tech-tab-maintenance')), findsNothing);
    expect(find.byKey(const ValueKey('us-tech-tab-weak_points')), findsNothing);
    expect(find.byKey(const ValueKey('us-tech-tab-campaigns')), findsNothing);

    await tester.pumpWidget(host(UsTechPanel(
        data: data(maintenance: [
          {
            'job': 'Масло и масляный фильтр',
            'action': 'замена',
            'interval': '16 000 км или 1 год, что наступит раньше',
            'severe': false,
            'approximate': true,
            'secondary': false,
          }
        ]),
        language: 'ru')));
    expect(find.byKey(const ValueKey('us-tech-tab-maintenance')), findsOneWidget);
    expect(find.text('ориентировочно'), findsOneWidget);
    expect(find.text('16 000 км или 1 год, что наступит раньше'), findsOneWidget);
  });

  testWidgets('nothing at all renders nothing', (tester) async {
    await tester.pumpWidget(host(UsTechPanel(data: data(), language: 'ru')));
    expect(find.byKey(const ValueKey('us-tech-panel')), findsNothing);
  });

  testWidgets('secondary values carry the reference-book mark and qualifiers',
      (tester) async {
    await tester.pumpWidget(host(UsTechPanel(
        data: data(categories: [
          {
            'key': 'fluids',
            'title': 'Масла и жидкости',
            'rows': [
              {
                'key': 'engine_oil_viscosity',
                'label': 'Вязкость масла',
                'values': [value('SAE 0W-16', secondary: true)]
              },
              {
                'key': 'curb_weight_kg',
                'label': 'Масса',
                'values': [
                  value('1470 кг', qualifier: 'L'),
                  value('1495 кг', qualifier: 'LE')
                ]
              },
            ],
          }
        ]),
        language: 'ru')));
    expect(find.text('SAE 0W-16'), findsOneWidget);
    expect(find.text('по данным справочников'), findsOneWidget);
    expect(find.text('LE'), findsOneWidget);
    expect(find.text('Источники · 3'), findsOneWidget);
  });

  testWidgets('five and forty rows lay out without overflow', (tester) async {
    tester.view.physicalSize = const Size(390 * 3, 844 * 3);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.reset);
    for (final rows in [5, 40]) {
      await tester.pumpWidget(host(UsTechPanel(
          data: data(categories: [
            category('body', 'Кузов и размеры', rows),
            category('engine', 'Двигатель', 2),
          ]),
          language: 'az')));
      await tester.pumpAndSettle();
      expect(tester.takeException(), isNull);
      expect(find.text('Texniki məlumatlar · ABŞ'), findsOneWidget);
      expect(find.text('Поле ${rows - 1}'), findsOneWidget); // first group is open
    }
  });

  testWidgets('flag off: no request and nothing drawn', (tester) async {
    final api = CountingApi();
    await tester.pumpWidget(host(UsTechSection(
        api: api, variantId: 'v1', language: 'ru', enabled: false)));
    await tester.pumpAndSettle();
    expect(api.calls, 0);
    expect(find.byKey(const ValueKey('us-tech-panel')), findsNothing);

    await tester.pumpWidget(host(UsTechSection(
        api: api, variantId: 'v2', language: 'ru', enabled: true)));
    await tester.pumpAndSettle();
    expect(api.calls, 1);
    expect(find.byKey(const ValueKey('us-tech-panel')), findsOneWidget);
  });
}
