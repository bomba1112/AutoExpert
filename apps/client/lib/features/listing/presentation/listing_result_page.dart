import 'package:autoexpert_client/core/theme/app_theme.dart';
import 'package:autoexpert_client/features/buyer/presentation/technical_display.dart';
import 'package:autoexpert_client/features/listing/data/listing_intake_api.dart';
import 'package:autoexpert_client/features/vin/data/vin_validation.dart';
import 'package:autoexpert_client/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:url_launcher/url_launcher.dart';

class ListingResultPage extends StatelessWidget {
  const ListingResultPage(
      {required this.result,
      required this.onCheckVin,
      required this.onAddComparison,
      super.key});

  final Map<String, dynamic> result;
  final ValueChanged<String?> onCheckVin;
  final ValueChanged<String> onAddComparison;

  static Map<String, dynamic> _map(Object? value) =>
      value is Map<String, dynamic> ? value : {};
  static List<dynamic> _list(Object? value) => value is List ? value : const [];
  static String _text(Object? value) => value == null ? '' : '$value';

  Map<String, dynamic>? _claim(String field) {
    for (final item in _list(result['claims'])) {
      if (item is Map<String, dynamic> && item['field_name'] == field) {
        return item;
      }
    }
    return null;
  }

  String _raw(String field) => _text(_claim(field)?['raw_value']);

  @override
  Widget build(BuildContext context) {
    final copy = AppLocalizations.of(context);
    final snapshot = _map(result['snapshot']);
    final match = _map(result['match']);
    final candidates = _list(match['candidates']);
    final conflicts = _list(match['conflicts']);
    final status = _text(match['status']);
    final sourceUrl = _text(snapshot['source_url']);
    final make = _raw('make');
    final model = _raw('model');
    final year = _raw('year');
    final vin = _text(_claim('vin')?['normalized_value']);
    final hasVin = isValidUsVin(vin);
    final lead =
        candidates.isNotEmpty && candidates.first is Map<String, dynamic>
            ? candidates.first as Map<String, dynamic>
            : <String, dynamic>{};
    final candidateFacts = TechnicalDisplay.factsFromCandidate(lead);
    final candidateDescription = TechnicalDisplay.configuration(
        candidateFacts, Localizations.localeOf(context).languageCode);
    List<String> conflictCatalogValues(Map<String, dynamic> item) =>
        _list(item['catalog_values'])
            .map((value) => TechnicalDisplay.conflictCatalogValue(
                _text(item['field_name']),
                value,
                Localizations.localeOf(context).languageCode))
            .whereType<String>()
            .toList();
    final claimLabels = <String, String>{
      'engine': copy.listingEngine,
      'fuel': copy.listingFuel,
      'transmission': copy.listingTransmission,
      'drivetrain': copy.listingDrivetrain,
      'body': copy.listingBody,
      'market': copy.listingMarket,
      'color': copy.listingColor,
      'vin': 'VIN',
      'seller_type': copy.listingSellerType,
      'owners': copy.listingOwners,
      'condition': copy.listingCondition,
      'description': copy.listingDescription,
    };

    return Scaffold(
      appBar: AppBar(title: Text(copy.listingResultTitle)),
      body: SafeArea(
        child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 26),
            child: Center(
                child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 650),
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Card(
                        clipBehavior: Clip.antiAlias,
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              SizedBox(
                                  height: 168,
                                  child: SvgPicture.asset(
                                      'assets/buyer-road.svg',
                                      fit: BoxFit.cover)),
                              Padding(
                                  padding: const EdgeInsets.all(18),
                                  child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Wrap(spacing: 8, children: [
                                          _Badge(
                                              text: sourceUrl.isNotEmpty
                                                  ? 'Turbo.az'
                                                  : copy.listingOwnInput),
                                          if (year.isNotEmpty)
                                            _Badge(text: year),
                                        ]),
                                        const SizedBox(height: 8),
                                        Text(
                                            [make, model]
                                                .where((v) => v.isNotEmpty)
                                                .join(' '),
                                            style: Theme.of(context)
                                                .textTheme
                                                .headlineSmall),
                                        const SizedBox(height: 8),
                                        Wrap(
                                            spacing: 12,
                                            runSpacing: 6,
                                            children: [
                                              if (_raw('price').isNotEmpty)
                                                Text(
                                                    '${_raw('price')} ${_raw('currency')}',
                                                    style: const TextStyle(
                                                        fontWeight:
                                                            FontWeight.w800,
                                                        color: AppTheme.blue)),
                                              if (_raw('mileage').isNotEmpty)
                                                Text(
                                                    '${_raw('mileage')} ${_raw('mileage_unit')}'),
                                              if (_raw('city').isNotEmpty)
                                                Text(_raw('city')),
                                            ]),
                                        if (isTurboAzUrl(sourceUrl))
                                          TextButton.icon(
                                              onPressed: () => launchUrl(
                                                  Uri.parse(sourceUrl),
                                                  mode: LaunchMode
                                                      .externalApplication),
                                              icon: const Icon(
                                                  Icons.open_in_new_rounded,
                                                  size: 18),
                                              label: Text(
                                                  copy.listingOpenOriginal)),
                                      ])),
                            ])),
                    const SizedBox(height: 12),
                    Card(
                        child: Padding(
                            padding: const EdgeInsets.all(18),
                            child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(copy.listingSellerClaims,
                                      style: Theme.of(context)
                                          .textTheme
                                          .titleMedium),
                                  const SizedBox(height: 12),
                                  for (final entry in claimLabels.entries)
                                    if (_raw(entry.key).isNotEmpty)
                                      _FactRow(
                                          label: entry.value,
                                          value: _raw(entry.key)),
                                ]))),
                    const SizedBox(height: 12),
                    Card(
                        child: Padding(
                            padding: const EdgeInsets.all(18),
                            child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(copy.listingMatchTitle,
                                      style: Theme.of(context)
                                          .textTheme
                                          .titleMedium),
                                  const SizedBox(height: 10),
                                  if (status != 'OUT_OF_PRODUCT_SCOPE')
                                    Text(switch (status) {
                                      'EXACT_MATCH' => copy.listingExact,
                                      'MULTIPLE_CANDIDATES' =>
                                        copy.listingMultiple,
                                      'CLAIM_CONFLICT' => copy.listingConflict,
                                      _ => copy.listingNoMatch,
                                    }),
                                  if (status == 'EXACT_MATCH' &&
                                      candidateDescription.isNotEmpty) ...[
                                    const SizedBox(height: 10),
                                    Text(candidateDescription,
                                        style: const TextStyle(
                                            fontWeight: FontWeight.w700)),
                                  ],
                                  if (status == 'MULTIPLE_CANDIDATES' &&
                                      _text(match['question']).isNotEmpty) ...[
                                    const SizedBox(height: 10),
                                    Text(_text(match['question']),
                                        style: const TextStyle(
                                            fontWeight: FontWeight.w700)),
                                  ],
                                  if (status == 'CLAIM_CONFLICT')
                                    for (final item in conflicts)
                                      if (item is Map<String, dynamic>) ...[
                                        const SizedBox(height: 10),
                                        Text(
                                            '${copy.listingClaimed}: ${_text(item['claimed'])}'),
                                        if (conflictCatalogValues(item)
                                            .isNotEmpty)
                                          Text(
                                              '${copy.listingCatalogValue}: ${conflictCatalogValues(item).join(', ')}'),
                                      ],
                                ]))),
                    const SizedBox(height: 18),
                    FilledButton.icon(
                        onPressed: () => onCheckVin(hasVin ? vin : null),
                        icon: const Icon(Icons.pin_rounded),
                        label: Text(status == 'OUT_OF_PRODUCT_SCOPE'
                            ? copy.listingOutOfScope
                            : hasVin
                                ? copy.listingCheckVin
                                : copy.listingAddVin)),
                    if (lead['variant_id'] is String) ...[
                      const SizedBox(height: 8),
                      OutlinedButton.icon(
                          onPressed: () =>
                              onAddComparison(lead['variant_id'] as String),
                          icon: const Icon(Icons.balance_rounded),
                          label: Text(copy.listingAddCompare)),
                    ],
                  ]),
            ))),
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge({required this.text});
  final String text;
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
            color: AppTheme.paleBlue, borderRadius: BorderRadius.circular(12)),
        child: Text(text,
            style: const TextStyle(
                color: AppTheme.blue, fontWeight: FontWeight.w700)),
      );
}

class _FactRow extends StatelessWidget {
  const _FactRow({required this.label, required this.value});
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 9),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          SizedBox(
              width: 125,
              child: Text(label,
                  style: const TextStyle(color: Color(0xFF597087)))),
          Expanded(
              child: Text(value,
                  style: const TextStyle(fontWeight: FontWeight.w600))),
        ]),
      );
}
