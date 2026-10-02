import 'package:autoexpert_client/core/theme/app_theme.dart';
import 'package:autoexpert_client/features/home/presentation/home_page.dart';
import 'package:autoexpert_client/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  for (final language in ['ru', 'az']) {
    for (final width in [360.0, 390.0, 430.0]) {
      testWidgets('approved home entrances fit $language at ${width.toInt()}px',
          (tester) async {
        tester.view.physicalSize = Size(width, 852);
        tester.view.devicePixelRatio = 1;
        addTearDown(() {
          tester.view.resetPhysicalSize();
          tester.view.resetDevicePixelRatio();
        });
        final opened = <String>[];
        await tester.pumpWidget(MaterialApp(
          theme: AppTheme.light,
          locale: Locale(language),
          supportedLocales: AppLocalizations.supportedLocales,
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          home: HomePage(
            onChangeLanguage: () {},
            onCheckVehicle: (_) => opened.add('check'),
            onFindCar: (_) => opened.add('buyer'),
            onCompare: (_) => opened.add('compare'),
            onReports: (_) => opened.add('reports'),
          ),
        ));
        await tester.pumpAndSettle();
        expect(tester.takeException(), isNull);
        final context = tester.element(find.byType(HomePage));
        final copy = AppLocalizations.of(context);
        expect(find.text(copy.buyCarTitle), findsOneWidget);
        expect(find.text(copy.checkCarTitle), findsOneWidget);
        expect(find.text(copy.battleTitle), findsOneWidget);
        await tester.tap(find.text(copy.buyCarCta));
        expect(opened, ['buyer']);
        await tester.ensureVisible(find.text(copy.checkCarCta));
        await tester.pumpAndSettle();
        await tester.tap(find.text(copy.checkCarCta));
        expect(opened, ['buyer', 'check']);
        await tester.ensureVisible(find.text(copy.battleAll));
        await tester.pumpAndSettle();
        await tester.tap(find.text(copy.battleAll));
        expect(opened, ['buyer', 'check', 'compare']);
      });
    }
  }

  testWidgets('AZ home remains readable at 360px with 140% text',
      (tester) async {
    tester.view.physicalSize = const Size(360, 852);
    tester.view.devicePixelRatio = 1;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });
    await tester.pumpWidget(MaterialApp(
      theme: AppTheme.light,
      locale: const Locale('az'),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      builder: (context, child) => MediaQuery(
        data: MediaQuery.of(context)
            .copyWith(textScaler: const TextScaler.linear(1.4)),
        child: child!,
      ),
      home: HomePage(
        onChangeLanguage: () {},
        onCheckVehicle: (_) {},
        onFindCar: (_) {},
        onCompare: (_) {},
        onReports: (_) {},
      ),
    ));
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
  });
}
