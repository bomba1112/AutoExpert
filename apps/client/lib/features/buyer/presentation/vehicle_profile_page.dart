import 'package:autoexpert_client/core/theme/app_theme.dart';
import 'package:autoexpert_client/features/buyer/data/buyer_catalog_api.dart';
import 'package:autoexpert_client/features/buyer/presentation/technical_display.dart';
import 'package:autoexpert_client/features/buyer/presentation/us_tech_panel.dart';
import 'package:autoexpert_client/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class VehicleProfilePage extends StatefulWidget {
  const VehicleProfilePage(
      {required this.api,
      required this.language,
      required this.variantId,
      required this.onCheckVin,
      this.qaMode = false,
      this.usTechFacts = false,
      super.key});
  final BuyerCatalogApi api;
  final String language;
  final String variantId;
  final VoidCallback onCheckVin;
  final bool qaMode;

  /// The show_us_tech_facts flag from the client configuration.
  final bool usTechFacts;
  @override
  State<VehicleProfilePage> createState() => _VehicleProfilePageState();
}

class _VehicleProfilePageState extends State<VehicleProfilePage> {
  Map<String, dynamic>? _vehicle;
  bool _failed = false;
  String _selected = 'technical';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final value = await widget.api.vehicle(widget.variantId, widget.language);
      if (mounted) setState(() => _vehicle = value);
    } catch (_) {
      if (mounted) setState(() => _failed = true);
    }
  }

  static Map<String, dynamic> _map(Object? value) =>
      value is Map<String, dynamic> ? value : {};
  static List<dynamic> _list(Object? value) => value is List ? value : const [];
  static String _text(Object? value) => value == null ? '' : '$value';

  List<dynamic> _visibleRows(List<dynamic> rows, {bool fluids = false}) => [
        for (final item in rows)
          if (item is Map<String, dynamic> &&
              _text(item['value']).isNotEmpty &&
              (!fluids ||
                  item['reuse_status'] == 'COMMERCIAL_OK' ||
                  (widget.qaMode && item['qa_fixture'] == true)))
            item,
      ];

  Widget _rows(List<dynamic> rows, Map<String, dynamic> facts) =>
      Column(children: [
        for (final item in rows)
          if (item is Map<String, dynamic> &&
              TechnicalDisplay.rowValue(_text(item['key']), facts,
                      widget.language, _text(item['value'])) !=
                  null)
            Padding(
                padding: const EdgeInsets.only(bottom: 11),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                        flex: 2,
                        child: Text(_text(item['label']),
                            style: const TextStyle(color: Color(0xFF5F7289)))),
                    const SizedBox(width: 9),
                    Expanded(
                        flex: 3,
                        child: Text(
                            TechnicalDisplay.rowValue(_text(item['key']), facts,
                                widget.language, _text(item['value']))!,
                            style:
                                const TextStyle(fontWeight: FontWeight.w600))),
                  ],
                )),
      ]);

  Widget _technical(Map<String, dynamic> profile, Map<String, dynamic> facts,
      AppLocalizations copy) {
    final groups = _list(profile['technical']);
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      for (final group in groups)
        if (group is Map<String, dynamic> &&
            _visibleRows(_list(group['rows']), fluids: group['key'] == 'fluids')
                .isNotEmpty)
          Card(
              child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_text(group['title']),
                          style: Theme.of(context).textTheme.titleMedium),
                      if (group['key'] == 'fluids' &&
                          widget.qaMode &&
                          _visibleRows(_list(group['rows']), fluids: true)
                              .whereType<Map<String, dynamic>>()
                              .any((row) => row['qa_fixture'] == true))
                        const Padding(
                          padding: EdgeInsets.only(top: 6),
                          child: Text('QA fixture · test only',
                              style: TextStyle(
                                  color: Color(0xFFAD6800),
                                  fontWeight: FontWeight.w700)),
                        ),
                      const SizedBox(height: 10),
                      if (group['key'] == 'fluids')
                        _fluids(
                            _visibleRows(_list(group['rows']), fluids: true),
                            facts,
                            copy)
                      else
                        _rows(_visibleRows(_list(group['rows'])), facts),
                    ],
                  ))),
    ]);
  }

  Widget _fluids(
      List<dynamic> rows, Map<String, dynamic> facts, AppLocalizations copy) {
    const oilKeys = {
      'engine_oil_viscosity',
      'engine_oil_specification',
      'engine_oil_capacity_l',
      'engine_oil_alternatives'
    };
    final engineOil = <Map<String, dynamic>>[];
    final others = <Map<String, dynamic>>[];
    final seen = <String>{};
    for (final item in rows) {
      if (item is! Map<String, dynamic>) continue;
      final key = _text(item['key']);
      if (!seen.add(key)) continue;
      if (oilKeys.contains(key)) {
        engineOil.add(item);
      } else {
        others.add(item);
      }
    }
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      if (engineOil.isNotEmpty) ...[
        Text(copy.profileEngineOil,
            style: const TextStyle(
                color: AppTheme.blue, fontWeight: FontWeight.w800)),
        const SizedBox(height: 8),
        _rows(engineOil, facts),
      ],
      if (others.isNotEmpty) _rows(others, facts),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    final copy = AppLocalizations.of(context);
    final vehicle = _vehicle;
    final profile = _map(vehicle?['profile']);
    final facts = _map(vehicle?['facts']);
    final categories = _list(profile['categories']);
    final selected = categories
        .whereType<Map<String, dynamic>>()
        .where((item) => item['key'] == _selected)
        .firstOrNull;
    return Scaffold(
      appBar: AppBar(title: Text(copy.profileTitle)),
      body: vehicle == null
          ? Center(
              child: _failed
                  ? Text(copy.profileLoadFailed)
                  : const CircularProgressIndicator())
          : SafeArea(
              child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
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
                                    padding: const EdgeInsets.all(16),
                                    child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                              '${_text(vehicle['make'])} ${_text(vehicle['model'])}',
                                              style: Theme.of(context)
                                                  .textTheme
                                                  .headlineSmall),
                                          const SizedBox(height: 5),
                                          Text([
                                            _text(vehicle['year']),
                                            TechnicalDisplay.configuration(
                                                facts, widget.language)
                                          ]
                                              .where((part) => part.isNotEmpty)
                                              .join(' · ')),
                                          const SizedBox(height: 10),
                                          _rows(
                                              _visibleRows(
                                                  _list(profile['summary'])),
                                              facts),
                                        ])),
                              ])),
                      const SizedBox(height: 16),
                      Wrap(spacing: 8, runSpacing: 8, children: [
                        for (final item in categories)
                          if (item is Map<String, dynamic>)
                            _CategoryButton(
                              title: _text(item['title']),
                              selected: _selected == item['key'],
                              keyName: _text(item['key']),
                              onTap: () => setState(
                                  () => _selected = _text(item['key'])),
                            ),
                      ]),
                      const SizedBox(height: 14),
                      if (_selected == 'technical')
                        _technical(profile, facts, copy)
                      else if (selected != null) ...[
                        for (final entry in _list(selected['entries']))
                          if (entry is Map<String, dynamic> &&
                              _text(entry['text']).isNotEmpty)
                            Card(
                                child: Padding(
                                    padding: const EdgeInsets.all(16),
                                    child: Text(_text(entry['text'])))),
                        if (_list(selected['entries']).isEmpty &&
                            _text(selected['empty_text']).isNotEmpty)
                          Card(
                              child: Padding(
                                  padding: const EdgeInsets.all(16),
                                  child: Text(_text(selected['empty_text'])))),
                      ],
                      if (widget.usTechFacts)
                        UsTechSection(
                            api: widget.api,
                            variantId: widget.variantId,
                            language: widget.language,
                            enabled: widget.usTechFacts),
                      const SizedBox(height: 14),
                      FilledButton.icon(
                          onPressed: widget.onCheckVin,
                          icon: const Icon(Icons.pin_rounded),
                          label: Text(copy.listingAddVin)),
                    ]),
              )),
            )),
    );
  }
}

class _CategoryButton extends StatelessWidget {
  const _CategoryButton(
      {required this.title,
      required this.keyName,
      required this.selected,
      required this.onTap});
  final String title, keyName;
  final bool selected;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) {
    final color = switch (keyName) {
      'technical' => const Color(0xFFDCEBFF),
      'weak_points' => const Color(0xFFFFE9CF),
      'campaigns' => const Color(0xFFE6F5E9),
      _ => const Color(0xFFEDE9FA),
    };
    final icon = switch (keyName) {
      'technical' => Icons.settings_rounded,
      'weak_points' => Icons.warning_amber_rounded,
      'campaigns' => Icons.campaign_outlined,
      _ => Icons.fact_check_outlined,
    };
    return SizedBox(
        width: 154,
        child: Material(
          color: color,
          borderRadius: BorderRadius.circular(14),
          child: InkWell(
            onTap: onTap,
            borderRadius: BorderRadius.circular(14),
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                  border: selected
                      ? Border.all(color: AppTheme.blue, width: 2)
                      : null,
                  borderRadius: BorderRadius.circular(14)),
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(icon, color: AppTheme.navy),
                    const SizedBox(height: 7),
                    Text(title,
                        maxLines: 2,
                        style: const TextStyle(fontWeight: FontWeight.w700)),
                  ]),
            ),
          ),
        ));
  }
}
