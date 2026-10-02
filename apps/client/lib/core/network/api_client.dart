import 'dart:convert';
import 'dart:typed_data';

import 'package:autoexpert_client/core/config/app_config.dart';
import 'package:http/http.dart' as http;

class ApiException implements Exception {
  const ApiException(this.statusCode, this.message);

  final int statusCode;
  final String message;

  @override
  String toString() => 'ApiException($statusCode, $message)';
}

class ApiClient {
  ApiClient({http.Client? client}) : _client = client ?? http.Client();

  static const _requestTimeout = Duration(seconds: 20);
  final http.Client _client;
  String? _accessToken;

  void setAccessToken(String? value) => _accessToken = value;

  Future<Map<String, dynamic>> getJson(String path) async {
    final response = await _client
        .get(
          Uri.parse('${AppConfig.apiBaseUrl}$path'),
          headers: _headers,
        )
        .timeout(_requestTimeout);
    return _decode(response);
  }

  Future<Uint8List> getBytes(String path) async {
    final response = await _client
        .get(
          Uri.parse('${AppConfig.apiBaseUrl}$path'),
          headers: _headers,
        )
        .timeout(_requestTimeout);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException(response.statusCode, 'Request failed');
    }
    return response.bodyBytes;
  }

  Future<Map<String, dynamic>> postJson(
    String path,
    Map<String, dynamic> body,
  ) async {
    final response = await _client
        .post(
          Uri.parse('${AppConfig.apiBaseUrl}$path'),
          headers: _headers,
          body: jsonEncode(body),
        )
        .timeout(_requestTimeout);
    return _decode(response);
  }

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
      };

  Map<String, dynamic> _decode(http.Response response) {
    final decoded = response.body.isEmpty
        ? <String, dynamic>{}
        : jsonDecode(response.body) as Map<String, dynamic>;
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException(
        response.statusCode,
        decoded['detail']?.toString() ?? 'Request failed',
      );
    }
    return decoded;
  }

  void close() => _client.close();
}
