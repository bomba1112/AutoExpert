import 'package:autoexpert_client/features/buyer/data/buyer_catalog_api.dart';
import 'package:autoexpert_client/features/buyer/presentation/buyer_search_page.dart';
import 'package:autoexpert_client/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class _ScopeApi extends BuyerCatalogApi {
  Map<String, dynamic>? filters;

  @override
  Future<Map<String, dynamic>> search(
      Map<String, dynamic> filters, String language) async {
    this.filters = filters;
    return {'recommendation': {}};
  }
}

void main() {
  testWidgets('buyer UI clamps old year input to USA MY2012+ product scope',
      (tester) async {
    final api = _ScopeApi();
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('ru'),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      home: BuyerSearchPage(
        api: api,
        language: 'ru',
        onOpenProfile: (_) {},
        onAddComparison: (_) {},
      ),
    ));
    expect(find.text('USA · MY2012+'), findsOneWidget);
    await tester.enterText(find.widgetWithText(TextField, 'Год от'), '2000');
    final show = find.text('Показать подходящие машины');
    await tester.ensureVisible(show);
    await tester.tap(show);
    await tester.pumpAndSettle();
    expect(api.filters?['markets'], ['USA']);
    expect(api.filters?['year_min'], 2012);
    expect(find.widgetWithText(TextField, 'Год от'), findsOneWidget);
    expect(find.text('2000'), findsNothing);
  });
}
