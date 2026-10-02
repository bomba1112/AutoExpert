import 'package:autoexpert_client/core/theme/app_theme.dart';
import 'package:autoexpert_client/features/buyer/data/buyer_catalog_api.dart';
import 'package:autoexpert_client/features/buyer/presentation/technical_display.dart';
import 'package:autoexpert_client/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class BuyerSearchPage extends StatefulWidget {
  const BuyerSearchPage(
      {required this.api,
      required this.language,
      required this.onOpenProfile,
      required this.onAddComparison,
      super.key});
  final BuyerCatalogApi api;
  final String language;
  final ValueChanged<String> onOpenProfile;
  final ValueChanged<String> onAddComparison;
  @override
  State<BuyerSearchPage> createState() => _BuyerSearchPageState();
}

class _BuyerSearchPageState extends State<BuyerSearchPage> {
  final _query = TextEditingController();
  final _budget = TextEditingController();
  final _yearMin = TextEditingController(text: '2012');
  final _yearMax = TextEditingController();
  String _body = '';
  String _engine = 'ANY';
  String _transmission = 'ANY';
  bool _busy = false;
  bool _failed = false;
  Map<String, dynamic>? _result;

  @override
  void dispose() {
    _query.dispose();
    _budget.dispose();
    _yearMin.dispose();
    _yearMax.dispose();
    super.dispose();
  }

  Future<void> _search() async {
    if (_busy) return;
    final min = int.tryParse(_yearMin.text.trim());
    final effectiveMin = min == null || min < 2012 ? 2012 : min;
    if (_yearMin.text != '$effectiveMin') _yearMin.text = '$effectiveMin';
    final max = int.tryParse(_yearMax.text.trim());
    final budget = int.tryParse(_budget.text.trim());
    setState(() {
      _busy = true;
      _failed = false;
    });
    try {
      final result = await widget.api.search({
        'catalog_scope': 'US_BASE_2000',
        'country': 'AZ',
        'market_preference': 'SELECTED',
        'markets': ['USA'],
        if (_query.text.trim().isNotEmpty) 'query': _query.text.trim(),
        'year_min': effectiveMin,
        if (max != null) 'year_max': max,
        if (budget != null && budget > 0) 'budget_max_minor': budget * 100,
        if (_body.isNotEmpty) 'body': [_body],
        'engine': _engine,
        'transmission': _transmission,
        'limit': 30,
      }, widget.language);
      if (mounted) setState(() => _result = result);
    } catch (_) {
      if (mounted) setState(() => _failed = true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Widget _choice(String label, bool selected, VoidCallback onTap) => ChoiceChip(
        label: Text(label),
        selected: selected,
        onSelected: (_) => onTap(),
        selectedColor: AppTheme.paleBlue,
        side: BorderSide(
            color: selected ? AppTheme.blue : const Color(0xFFCEDDED)),
        labelStyle: TextStyle(color: selected ? AppTheme.blue : AppTheme.ink),
      );

  @override
  Widget build(BuildContext context) {
    final copy = AppLocalizations.of(context);
    final recommendation = _result?['recommendation'] is Map<String, dynamic>
        ? _result!['recommendation'] as Map<String, dynamic>
        : <String, dynamic>{};
    final top = recommendation['top'];
    final competitors = recommendation['competitors'] is List
        ? recommendation['competitors'] as List
        : const [];
    final needsConfirmation = _result?['needs_confirmation'] is List
        ? _result!['needs_confirmation'] as List
        : const [];
    return Scaffold(
      appBar: AppBar(title: Text(copy.buyerTitle)),
      body: SafeArea(
        child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
            child: Center(
                child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 650),
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                      _Step(
                          number: '1',
                          label: copy.buyerStepParameters,
                          selected: _result == null),
                      const Expanded(child: Divider()),
                      _Step(
                          number: '2',
                          label: copy.buyerStepResults,
                          selected: _result != null),
                    ]),
                    const SizedBox(height: 18),
                    Text(copy.buyerHeading,
                        style: Theme.of(context).textTheme.headlineSmall),
                    const SizedBox(height: 5),
                    Text(copy.buyerSubtitle),
                    const SizedBox(height: 16),
                    TextField(
                        controller: _query,
                        decoration:
                            InputDecoration(labelText: copy.buyerQuery)),
                    const SizedBox(height: 10),
                    Row(children: [
                      Expanded(
                          child: TextField(
                              controller: _budget,
                              keyboardType: TextInputType.number,
                              decoration: InputDecoration(
                                  labelText: copy.buyerBudget))),
                      const SizedBox(width: 8),
                      Expanded(
                          child: TextField(
                              controller: _yearMin,
                              keyboardType: TextInputType.number,
                              decoration: InputDecoration(
                                  labelText: copy.buyerYearFrom))),
                      const SizedBox(width: 8),
                      Expanded(
                          child: TextField(
                              controller: _yearMax,
                              keyboardType: TextInputType.number,
                              decoration: InputDecoration(
                                  labelText: copy.buyerYearTo))),
                    ]),
                    const SizedBox(height: 14),
                    Text(copy.buyerMarket,
                        style: const TextStyle(fontWeight: FontWeight.w700)),
                    const SizedBox(height: 5),
                    const Chip(label: Text('USA · MY2012+')),
                    const SizedBox(height: 8),
                    Text(copy.buyerBody,
                        style: const TextStyle(fontWeight: FontWeight.w700)),
                    Wrap(spacing: 6, children: [
                      for (final pair in [
                        ('SEDAN', copy.buyerSedan),
                        ('CROSSOVER', copy.buyerCrossover),
                        ('HATCHBACK', copy.buyerHatchback)
                      ])
                        _choice(
                            pair.$2,
                            _body == pair.$1,
                            () => setState(
                                () => _body = _body == pair.$1 ? '' : pair.$1)),
                    ]),
                    const SizedBox(height: 10),
                    Text(copy.buyerEngine,
                        style: const TextStyle(fontWeight: FontWeight.w700)),
                    Wrap(spacing: 6, children: [
                      for (final pair in [
                        ('ANY', copy.buyerAny),
                        ('GASOLINE_NA', copy.buyerGasolineNa),
                        ('GASOLINE_TURBO', copy.buyerGasolineTurbo),
                        ('DIESEL', copy.buyerDiesel),
                        ('HEV', copy.buyerHybrid),
                        ('BEV', copy.buyerElectric)
                      ])
                        _choice(pair.$2, _engine == pair.$1,
                            () => setState(() => _engine = pair.$1)),
                    ]),
                    const SizedBox(height: 10),
                    Text(copy.buyerGearbox,
                        style: const TextStyle(fontWeight: FontWeight.w700)),
                    Wrap(spacing: 6, children: [
                      for (final pair in [
                        ('ANY', copy.buyerAny),
                        ('AT', copy.buyerAt),
                        ('CVT', copy.buyerCvt),
                        ('DCT', copy.buyerDct),
                        ('MANUAL', copy.buyerManual)
                      ])
                        _choice(pair.$2, _transmission == pair.$1,
                            () => setState(() => _transmission = pair.$1)),
                    ]),
                    const SizedBox(height: 16),
                    FilledButton.icon(
                        onPressed: _busy ? null : _search,
                        icon: const Icon(Icons.arrow_forward_rounded),
                        label: Text(copy.buyerShowMatches)),
                    if (_busy)
                      const Padding(
                          padding: EdgeInsets.all(14),
                          child: Center(child: CircularProgressIndicator())),
                    if (_failed)
                      Padding(
                          padding: const EdgeInsets.only(top: 10),
                          child: Text(copy.buyerSearchFailed)),
                    if (_result != null) ...[
                      const SizedBox(height: 24),
                      Text(copy.buyerResultsTitle,
                          style: Theme.of(context).textTheme.headlineSmall),
                      const SizedBox(height: 10),
                      if (top is Map<String, dynamic>) ...[
                        Text(copy.buyerTopLabel,
                            style: const TextStyle(
                                color: AppTheme.blue,
                                fontWeight: FontWeight.w800)),
                        _VehicleCard(
                            vehicle: top,
                            onOpen: widget.onOpenProfile,
                            onAdd: widget.onAddComparison),
                      ],
                      if (competitors.isNotEmpty) ...[
                        const SizedBox(height: 12),
                        Text(copy.buyerCompetitors,
                            style: Theme.of(context).textTheme.titleMedium),
                        for (final value in competitors)
                          if (value is Map<String, dynamic>)
                            _VehicleCard(
                                vehicle: value,
                                onOpen: widget.onOpenProfile,
                                onAdd: widget.onAddComparison),
                      ],
                      if (needsConfirmation.isNotEmpty) ...[
                        const SizedBox(height: 12),
                        Text(copy.buyerNeedsConfirmation,
                            style: Theme.of(context).textTheme.titleMedium),
                        for (final value in needsConfirmation)
                          if (value is Map<String, dynamic>)
                            _VehicleCard(
                                vehicle: value,
                                onOpen: widget.onOpenProfile,
                                onAdd: widget.onAddComparison),
                      ],
                      if (top == null && needsConfirmation.isEmpty)
                        Text(copy.buyerNoResults),
                    ],
                  ]),
            ))),
      ),
    );
  }
}

class _Step extends StatelessWidget {
  const _Step(
      {required this.number, required this.label, required this.selected});
  final String number, label;
  final bool selected;
  @override
  Widget build(BuildContext context) => Column(children: [
        CircleAvatar(
            radius: 15,
            backgroundColor: selected ? AppTheme.blue : const Color(0xFFB9C7D9),
            child: Text(number, style: const TextStyle(color: Colors.white))),
        const SizedBox(height: 4),
        Text(label,
            style: TextStyle(
                color: selected ? AppTheme.blue : AppTheme.ink, fontSize: 12)),
      ]);
}

class _VehicleCard extends StatelessWidget {
  const _VehicleCard(
      {required this.vehicle, required this.onOpen, required this.onAdd});
  final Map<String, dynamic> vehicle;
  final ValueChanged<String> onOpen, onAdd;
  @override
  Widget build(BuildContext context) {
    final copy = AppLocalizations.of(context);
    final id = vehicle['id'] is String ? vehicle['id'] as String : '';
    final label =
        [vehicle['make'], vehicle['model']].whereType<String>().join(' ');
    return Card(
      margin: const EdgeInsets.only(top: 10),
      clipBehavior: Clip.antiAlias,
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        SizedBox(
            height: 120,
            child:
                SvgPicture.asset('assets/buyer-road.svg', fit: BoxFit.cover)),
        Padding(
            padding: const EdgeInsets.all(14),
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(label, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 3),
              Text(
                  [
                    vehicle['year'],
                    TechnicalDisplay.configuration(
                        vehicle['facts'] is Map<String, dynamic>
                            ? vehicle['facts'] as Map<String, dynamic>
                            : const {},
                        Localizations.localeOf(context).languageCode)
                  ].where((v) => v != null && '$v'.isNotEmpty).join(' · '),
                  maxLines: 2),
              const SizedBox(height: 10),
              Row(children: [
                Expanded(
                    child: FilledButton(
                        onPressed: id.isEmpty ? null : () => onOpen(id),
                        child: Text(copy.buyerOpenProfile))),
                const SizedBox(width: 8),
                IconButton(
                    onPressed: id.isEmpty ? null : () => onAdd(id),
                    tooltip: copy.listingAddCompare,
                    icon: const Icon(Icons.balance_rounded)),
              ]),
            ])),
      ]),
    );
  }
}
