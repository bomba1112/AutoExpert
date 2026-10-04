import 'dart:convert';
import 'dart:io';

import 'package:autoexpert_client/app/device_language.dart';
import 'package:autoexpert_client/features/buyer/presentation/technical_display.dart';
import 'package:autoexpert_client/features/language/presentation/language_page.dart';
import 'package:autoexpert_client/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

final _cyrillic = RegExp('[А-Яа-яЁё]');

void main() {
  test('the device language: en, ru, az, else English', () {
    expect(deviceLanguage(['ru-RU', 'en-US']), 'ru');
    expect(deviceLanguage(['az_AZ']), 'az');
    expect(deviceLanguage(['en-CA']), 'en');
    expect(deviceLanguage(['de-DE']), 'en');
    expect(deviceLanguage([]), 'en');
  });

  test('every UI string exists in EN, RU and AZ and English has no Russian', () {
    Map<String, dynamic> load(String code) =>
        jsonDecode(File('lib/l10n/app_$code.arb').readAsStringSync()) as Map<String, dynamic>;
    final en = load('en'), ru = load('ru'), az = load('az');
    Set<String> keys(Map<String, dynamic> m) => m.keys.where((k) => !k.startsWith('@')).toSet();
    expect(keys(ru), keys(en));
    expect(keys(az), keys(en));
    final russian = en.entries.where((e) => e.value is String && _cyrillic.hasMatch(e.value as String));
    expect(russian, isEmpty);
  });

  test('technical terms are English in English', () {
    final facts = <String, dynamic>{
      'engine_displacement': {'value': '2.5'},
      'cylinders': {'value': '4'},
      'fuel': {'value': 'GASOLINE'},
      'aspiration': {'value': 'TURBO'},
      'transmission_family': {'value': 'AT'},
      'gears': {'value': '8'},
      'drivetrain': {'value': 'AWD'},
    };
    final text = TechnicalDisplay.configuration(facts, 'en');
    expect(text, contains('2.5 L'));
    expect(text, contains('4 cylinders'));
    expect(text, contains('8-speed'));
    expect(text, contains('All-wheel drive (AWD)'));
    expect(_cyrillic.hasMatch(text), isFalse);
    expect(TechnicalDisplay.configuration(facts, 'ru'), contains('Бензин'));
  });

  testWidgets('language switch: the device language is preselected and any language can be chosen',
      (tester) async {
    String? chosen;
    await tester.pumpWidget(MaterialApp(
      locale: const Locale('en'),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      home: LanguagePage(onSelected: (code) => chosen = code, initial: 'en'),
    ));
    await tester.pumpAndSettle();
    expect(find.text('English'), findsOneWidget);
    await tester.tap(find.byType(FilledButton));
    expect(chosen, 'en');
    await tester.tap(find.text('Русский'));
    await tester.pumpAndSettle();
    await tester.tap(find.byType(FilledButton));
    expect(chosen, 'ru');
  });
}
