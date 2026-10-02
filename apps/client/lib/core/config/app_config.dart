class AppConfig {
  const AppConfig._();

  static const apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000/api/v1',
  );

  // The currently connected history adapter is an isolated fixture.
  static const vinHistoryFixtureOnly = bool.fromEnvironment(
    'VIN_HISTORY_FIXTURE_ONLY',
    defaultValue: true,
  );
  static const vinHistoryFixtureVin = '3FA6P0HD0KR114795';
}
