import 'dart:typed_data';

import 'package:autoexpert_client/core/network/api_client.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

abstract class VinSessionStore {
  Future<String?> readToken();
  Future<String?> readCheckId();
  Future<void> writeToken(String? token);
  Future<void> writeCheckId(String? checkId);
}

class SecureVinSessionStore implements VinSessionStore {
  const SecureVinSessionStore();

  static const _storage = FlutterSecureStorage();
  static const _tokenKey = 'vin_demo_access_token';
  static const _checkKey = 'vin_demo_last_check_id';

  @override
  Future<String?> readToken() => _storage.read(key: _tokenKey);

  @override
  Future<String?> readCheckId() => _storage.read(key: _checkKey);

  @override
  Future<void> writeToken(String? token) => token == null
      ? _storage.delete(key: _tokenKey)
      : _storage.write(key: _tokenKey, value: token);

  @override
  Future<void> writeCheckId(String? checkId) => checkId == null
      ? _storage.delete(key: _checkKey)
      : _storage.write(key: _checkKey, value: checkId);
}

class VinHistoryApi {
  VinHistoryApi({ApiClient? client, VinSessionStore? store})
      : _client = client ?? ApiClient(),
        _store = store ?? const SecureVinSessionStore();

  final ApiClient _client;
  final VinSessionStore _store;
  String? _token;

  Future<void> _restoreToken() async {
    _token ??= await _store.readToken();
    _client.setAccessToken(_token);
  }

  Future<void> _demoSession(String language) async {
    final response = await _client.postJson('/auth/demo', {
      'preferred_language': language,
    });
    final token = response['access_token'] as String?;
    if (token == null || token.isEmpty) {
      throw const ApiException(500, 'No session');
    }
    _token = token;
    _client.setAccessToken(token);
    await _store.writeToken(token);
  }

  Future<bool> _renew() async {
    if (_token == null) return false;
    try {
      final response = await _client.postJson('/auth/local-session/renew', {});
      final token = response['access_token'] as String?;
      if (token == null || token.isEmpty) return false;
      _token = token;
      _client.setAccessToken(token);
      await _store.writeToken(token);
      return true;
    } on ApiException {
      return false;
    }
  }

  Future<T> _authorized<T>(Future<T> Function() request,
      {required String language, bool allowNewDemoSession = false}) async {
    await _restoreToken();
    if (_token == null) {
      if (!allowNewDemoSession) throw const ApiException(401, 'No session');
      await _demoSession(language);
    }
    try {
      return await request();
    } on ApiException catch (error) {
      if (error.statusCode != 401) rethrow;
      if (await _renew()) return request();
      if (!allowNewDemoSession) rethrow;
      _token = null;
      _client.setAccessToken(null);
      await _store.writeToken(null);
      await _demoSession(language);
      return request();
    }
  }

  Future<Map<String, dynamic>> createCheck(String vin, String language) async {
    final check = await _authorized(
      () => _client
          .postJson('/vin/history/checks', {'vin': vin, 'language': language}),
      language: language,
      allowNewDemoSession: true,
    );
    final checkId = check['check_id'] as String?;
    if (checkId != null) await _store.writeCheckId(checkId);
    return check;
  }

  /// Reuses the same isolated demo identity for other user-assisted flows.
  Future<Map<String, dynamic>> postDemoJson(
    String path,
    Map<String, dynamic> body,
    String language,
  ) =>
      _authorized(
        () => _client.postJson(path, body),
        language: language,
        allowNewDemoSession: true,
      );

  Future<Map<String, dynamic>> getDemoJson(String path, String language) =>
      _authorized(
        () => _client.getJson(path),
        language: language,
      );

  /// A saved check is never fetched using a newly created demo identity.
  /// If the prior session cannot be restored, ownership is not bypassed.
  Future<Map<String, dynamic>?> loadSavedCheck(String language) async {
    final checkId = await _store.readCheckId();
    if (checkId == null) return null;
    await _restoreToken();
    if (_token == null) return null;
    try {
      return await _client
          .getJson('/vin/history/checks/${Uri.encodeComponent(checkId)}');
    } on ApiException catch (error) {
      if (error.statusCode == 401 && await _renew()) {
        return _client
            .getJson('/vin/history/checks/${Uri.encodeComponent(checkId)}');
      }
      if (error.statusCode == 401 || error.statusCode == 404) return null;
      rethrow;
    }
  }

  Future<Map<String, dynamic>> mockPayment(String checkId, String language) =>
      _authorized(
        () => _client.postJson(
          '/vin/history/checks/${Uri.encodeComponent(checkId)}/payments/mock',
          {'simulate_failure': false},
        ),
        language: language,
      );

  Future<Map<String, dynamic>> getCheck(String checkId, String language) =>
      _authorized(
        () => _client.getJson(
          '/vin/history/checks/${Uri.encodeComponent(checkId)}',
        ),
        language: language,
      );

  Future<Map<String, dynamic>> retryReport(String checkId, String language) =>
      _authorized(
        () => _client.postJson(
          '/vin/history/checks/${Uri.encodeComponent(checkId)}/retry',
          {},
        ),
        language: language,
      );

  Future<Map<String, dynamic>> getReport(String checkId, String language) =>
      _authorized(
        () => _client.getJson(
          '/vin/history/checks/${Uri.encodeComponent(checkId)}/report'
          '?language=${Uri.encodeQueryComponent(language)}',
        ),
        language: language,
      );

  Future<Uint8List> getAssetBytes(
    String checkId,
    String assetId,
    String language,
  ) =>
      _authorized(
        () => _client.getBytes(
          '/vin/history/checks/${Uri.encodeComponent(checkId)}'
          '/assets/${Uri.encodeComponent(assetId)}',
        ),
        language: language,
      );

  void close() => _client.close();
}
