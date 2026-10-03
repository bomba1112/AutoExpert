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

  /// US technical facts of the configuration behind a variant (served only while the
  /// show_us_tech_facts flag is on; 404 otherwise).
  Future<Map<String, dynamic>> usTechForVariant(
          String variantId, String language) =>
      _client.getJson('/catalog/variants/${Uri.encodeComponent(variantId)}/us-tech'
          '?language=${Uri.encodeQueryComponent(language)}');

  void close() => _client.close();
}
