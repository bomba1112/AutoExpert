import 'package:autoexpert_client/core/network/api_client.dart';

class BuyerCatalogApi {
  BuyerCatalogApi({ApiClient? client}) : _client = client ?? ApiClient();
  final ApiClient _client;

  Future<Map<String, dynamic>> search(
          Map<String, dynamic> filters, String language) =>
      _client.postJson(
          '/knowledge/search?language=${Uri.encodeQueryComponent(language)}',
          filters);

  Future<Map<String, dynamic>> vehicle(String variantId, String language) =>
      _client.getJson('/knowledge/vehicles/${Uri.encodeComponent(variantId)}'
          '?language=${Uri.encodeQueryComponent(language)}');

  Future<Map<String, dynamic>> compare(List<String> ids, String language) =>
      _client.postJson('/knowledge/compare', {
        'variant_ids': ids,
        'language': language,
      });

  void close() => _client.close();
}
