import 'package:autoexpert_client/features/vin/data/vin_history_api.dart';

bool isTurboAzUrl(String value) {
  final trimmed = value.trim();
  if (trimmed.length > 2000 || RegExp(r'[\s\x00-\x1F]').hasMatch(trimmed)) {
    return false;
  }
  const allowedHosts = {
    'turbo.az',
    'www.turbo.az',
    'ru.turbo.az',
    'en.turbo.az'
  };
  final authority = RegExp(r'^https://([^/?#]+)', caseSensitive: false)
      .firstMatch(trimmed)
      ?.group(1)
      ?.toLowerCase();
  if (!allowedHosts.contains(authority)) {
    return false;
  }
  final rawPath = RegExp(r'^https://[^/?#]+([^?#]*)', caseSensitive: false)
          .firstMatch(trimmed)
          ?.group(1) ??
      '';
  if (rawPath.contains('%') || rawPath.contains('\\')) {
    return false;
  }
  final uri = Uri.tryParse(trimmed);
  if (uri == null ||
      uri.scheme != 'https' ||
      uri.userInfo.isNotEmpty ||
      uri.hasPort) {
    return false;
  }
  if (!allowedHosts.contains(uri.host)) {
    return false;
  }
  final path = uri.path.toLowerCase();
  return !path.contains('%') &&
      !path.contains('\\') &&
      RegExp(r'^/autos/[0-9]{4,12}(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?/?$')
          .hasMatch(path);
}

class ListingIntakeApi {
  ListingIntakeApi(this._session);

  final VinHistoryApi _session;

  Future<Map<String, dynamic>> submit({
    required String inputType,
    required String language,
    String? sourceUrl,
    String? text,
    String? html,
    Map<String, dynamic>? fields,
  }) {
    return _session.postDemoJson(
        '/listings/intake',
        {
          'input_type': inputType,
          'language': language,
          if (sourceUrl != null && sourceUrl.trim().isNotEmpty)
            'source_url': sourceUrl.trim(),
          if (text != null && text.trim().isNotEmpty) 'text': text.trim(),
          if (html != null && html.trim().isNotEmpty) 'html': html.trim(),
          if (fields != null) 'fields': fields,
        },
        language);
  }

  Future<Map<String, dynamic>> get(String id, String language) => _session
      .getDemoJson('/listings/intake/${Uri.encodeComponent(id)}', language);
}
