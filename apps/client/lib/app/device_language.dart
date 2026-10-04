import 'dart:ui' show PlatformDispatcher;

/// The language the app starts in before the user chooses one (product phase, stage 1):
/// en -> EN, ru -> RU, az -> AZ, any other device language -> EN.
String deviceLanguage([List<String>? codes]) {
  final languages = codes ??
      PlatformDispatcher.instance.locales.map((l) => l.languageCode).toList();
  for (final code in languages) {
    final base = code.toLowerCase().split(RegExp('[-_]')).first;
    if (const ['en', 'ru', 'az'].contains(base)) return base;
  }
  return 'en';
}
