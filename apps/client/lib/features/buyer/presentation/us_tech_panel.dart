// US technical facts of a configuration (next-stage prompt, stage C). Shown only while the API
// advertises the show_us_tech_facts flag; with the flag off nothing is requested or drawn.
import 'package:autoexpert_client/core/theme/app_theme.dart';
import 'package:autoexpert_client/features/buyer/data/buyer_catalog_api.dart';
import 'package:flutter/material.dart';

const _copy = {
  'ru': {
    'title': 'Технические данные · США',
    'technical': 'Техника',
    'weak_points': 'Слабые места',
    'campaigns': 'Сервисные кампании',
    'maintenance': 'ТО',
    'sources': 'Источники',
    'component': 'Узел',
    'severity': 'Серьёзность',
    'probability': 'Вероятность',
    'symptoms': 'Симптомы',
    'check': 'Как проверить',
    'years': 'Годы',
    'normal': 'Обычные условия',
    'severe': 'Тяжёлые условия',
    'limit': 'не позже',
  },
  'az': {
    'title': 'Texniki məlumatlar · ABŞ',
    'technical': 'Texnika',
    'weak_points': 'Zəif yerlər',
    'campaigns': 'Servis kampaniyaları',
    'maintenance': 'TXQ',
    'sources': 'Mənbələr',
    'component': 'Qovşaq',
    'severity': 'Ciddilik',
    'probability': 'Ehtimal',
    'symptoms': 'Əlamətlər',
    'check': 'Necə yoxlamalı',
    'years': 'İllər',
    'normal': 'Adi şərait',
    'severe': 'Ağır şərait',
    'limit': 'gec olmayaraq',
  },
};

Map<String, dynamic> _map(Object? value) =>
    value is Map<String, dynamic> ? value : const {};
List<dynamic> _list(Object? value) => value is List ? value : const [];
String _text(Object? value) => value == null ? '' : '$value';

/// Loads the facts of the configuration behind a catalogue variant and shows the panel; any
/// failure (no configuration behind the variant, flag off on the server) shows nothing.
class UsTechSection extends StatefulWidget {
  const UsTechSection(
      {required this.api,
      required this.variantId,
      required this.language,
      required this.enabled,
      super.key});
  final BuyerCatalogApi api;
  final String variantId;
  final String language;
  final bool enabled;
  @override
  State<UsTechSection> createState() => _UsTechSectionState();
}

class _UsTechSectionState extends State<UsTechSection> {
  Map<String, dynamic>? _data;

  @override
  void initState() {
    super.initState();
    if (widget.enabled) _load();
  }

  @override
  void didUpdateWidget(covariant UsTechSection oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.variantId != oldWidget.variantId ||
        widget.language != oldWidget.language ||
        widget.enabled != oldWidget.enabled) {
      _data = null;
      if (widget.enabled) _load();
    }
  }

  Future<void> _load() async {
    try {
      final value =
          await widget.api.usTechForVariant(widget.variantId, widget.language);
      if (mounted) setState(() => _data = value);
    } catch (_) {
      // nothing to show
    }
  }

  @override
  Widget build(BuildContext context) =>
      !widget.enabled || _data == null
          ? const SizedBox.shrink()
          : UsTechPanel(data: _data!, language: widget.language);
}

class UsTechPanel extends StatefulWidget {
  const UsTechPanel({required this.data, required this.language, super.key});
  final Map<String, dynamic> data;
  final String language;

  /// Tabs that have records, in the approved order; an empty tab is not shown.
  static List<String> tabsOf(Map<String, dynamic> data) => [
        if (_list(data['categories']).isNotEmpty) 'technical',
        if (_list(data['weak_points']).isNotEmpty) 'weak_points',
        if (_list(data['campaigns']).isNotEmpty) 'campaigns',
        if (_list(data['maintenance']).isNotEmpty) 'maintenance',
      ];

  @override
  State<UsTechPanel> createState() => _UsTechPanelState();
}

class _UsTechPanelState extends State<UsTechPanel> {
  String? _selected;

  Map<String, String> get t => _copy[widget.language == 'az' ? 'az' : 'ru']!;
  Map<String, dynamic> get labels => _map(widget.data['labels']);

  @override
  Widget build(BuildContext context) {
    final tabs = UsTechPanel.tabsOf(widget.data);
    if (tabs.isEmpty) return const SizedBox.shrink();
    final selected = tabs.contains(_selected) ? _selected! : tabs.first;
    return Column(
      key: const ValueKey('us-tech-panel'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const SizedBox(height: 18),
        Text(t['title']!, style: Theme.of(context).textTheme.titleLarge),
        if (_text(widget.data['summary']).isNotEmpty)
          Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(_text(widget.data['summary']),
                  style: const TextStyle(color: Color(0xFF5F7289)))),
        const SizedBox(height: 12),
        Wrap(spacing: 8, runSpacing: 8, children: [
          for (final key in tabs)
            ChoiceChip(
              key: ValueKey('us-tech-tab-$key'),
              label: Text(t[key]!),
              selected: key == selected,
              onSelected: (_) => setState(() => _selected = key),
            ),
        ]),
        const SizedBox(height: 12),
        switch (selected) {
          'technical' => _technical(),
          'weak_points' => _weakPoints(),
          'campaigns' => _campaigns(),
          _ => _maintenance(),
        },
      ],
    );
  }

  Widget _badge(String text, Color background, Color color) => Container(
        margin: const EdgeInsets.only(left: 6, top: 2),
        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 1),
        decoration: BoxDecoration(
            color: background, borderRadius: BorderRadius.circular(8)),
        child: Text(text, style: TextStyle(fontSize: 11, color: color)),
      );

  List<Widget> _marks(Map<String, dynamic> value) => [
        if (value['secondary'] == true)
          _badge(_text(labels['secondary']), const Color(0xFFFFF4E0),
              const Color(0xFF8A5200)),
        if (value['approximate'] == true)
          _badge(_text(labels['approximate']), const Color(0xFFEAF2FF),
              const Color(0xFF1554B3)),
      ];

  Widget _value(Map<String, dynamic> value) => Wrap(
        alignment: WrapAlignment.end,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          if (_text(value['qualifier']).isNotEmpty)
            Padding(
                padding: const EdgeInsets.only(right: 6),
                child: Text(_text(value['qualifier']),
                    style: const TextStyle(
                        fontSize: 12, color: Color(0xFF5C6B7A)))),
          Text(_text(value['value']),
              style: const TextStyle(fontWeight: FontWeight.w600)),
          ..._marks(value),
        ],
      );

  Widget _technical() {
    final categories = _list(widget.data['categories']);
    return Column(children: [
      for (final (index, category) in categories.indexed)
        if (category is Map<String, dynamic>)
          Card(
            child: ExpansionTile(
              key: ValueKey('us-tech-category-${category['key']}'),
              initiallyExpanded: index == 0,
              title: Text(_text(category['title'])),
              trailing: Text('${_list(category['rows']).length}'),
              childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
              children: [
                for (final row in _list(category['rows']))
                  if (row is Map<String, dynamic>)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(
                                flex: 2,
                                child: Text(_text(row['label']),
                                    style: const TextStyle(
                                        color: Color(0xFF5F7289)))),
                            const SizedBox(width: 9),
                            Expanded(
                                flex: 3,
                                child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.end,
                                    children: [
                                      for (final value in _list(row['values']))
                                        if (value is Map<String, dynamic>)
                                          _value(value),
                                    ])),
                          ]),
                    ),
                _sources(category),
              ],
            ),
          ),
    ]);
  }

  Widget _sources(Map<String, dynamic> category) {
    final items = <String>[];
    for (final row in _list(category['rows'])) {
      for (final value in _list(_map(row)['values'])) {
        final source = _map(_map(value)['source']);
        final where = [source['title'], source['publisher'], source['locator']]
            .where((part) => _text(part).isNotEmpty)
            .join(' · ');
        final quote = _text(source['quote']);
        items.add('${_text(_map(row)['label'])}: $where'
            '${quote.isEmpty ? '' : ' — «$quote»'}');
      }
    }
    return ExpansionTile(
      tilePadding: EdgeInsets.zero,
      title: Text('${t['sources']} · ${items.length}',
          style: const TextStyle(fontSize: 13, color: Color(0xFF5C6B7A))),
      children: [
        for (final item in items)
          Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Text(item, style: const TextStyle(fontSize: 12))),
      ],
    );
  }

  Widget _pair(String label, String value) => value.isEmpty
      ? const SizedBox.shrink()
      : Padding(
          padding: const EdgeInsets.only(top: 4),
          child: Row(children: [
            Expanded(
                child: Text(label,
                    style: const TextStyle(color: Color(0xFF5F7289)))),
            Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
          ]));

  Widget _weakPoints() => Column(children: [
        for (final issue in _list(widget.data['weak_points']))
          if (issue is Map<String, dynamic>)
            Card(
              shape: issue['owner_reports'] == true
                  ? RoundedRectangleBorder(
                      side: const BorderSide(color: Color(0xFFD8A24A)),
                      borderRadius: BorderRadius.circular(16))
                  : null,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_text(issue['title']),
                          style: Theme.of(context).textTheme.titleMedium),
                      if (_text(issue['note']).isNotEmpty)
                        Text(_text(issue['note']),
                            style: const TextStyle(
                                fontSize: 12, color: Color(0xFF8A5200))),
                      _pair(t['component']!, _text(issue['component'])),
                      _pair(t['severity']!, _text(issue['severity'])),
                      _pair(t['probability']!, _text(issue['probability'])),
                      if (_list(issue['symptoms']).isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Text(t['symptoms']!,
                            style: const TextStyle(fontWeight: FontWeight.w700)),
                        for (final symptom in _list(issue['symptoms']))
                          Text('• ${_text(symptom)}'),
                      ],
                      if (_text(issue['how_to_check']).isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Text(t['check']!,
                            style: const TextStyle(fontWeight: FontWeight.w700)),
                        Text(_text(issue['how_to_check'])),
                      ],
                    ]),
              ),
            ),
      ]);

  String _years(Object? value) {
    final years = _list(value);
    if (years.isEmpty) return '';
    return years.first == years.last
        ? _text(years.first)
        : '${years.first}–${years.last}';
  }

  Widget _campaigns() => Column(children: [
        for (final campaign in _list(widget.data['campaigns']))
          if (campaign is Map<String, dynamic>)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_text(campaign['number']),
                          style: Theme.of(context).textTheme.titleMedium),
                      if (_text(campaign['component']).isNotEmpty)
                        Text(_text(campaign['component']),
                            style: const TextStyle(
                                fontWeight: FontWeight.w700,
                                color: Color(0xFF5F7289))),
                      if (_text(campaign['summary']).isNotEmpty)
                        Padding(
                            padding: const EdgeInsets.only(top: 6),
                            child: Text(_text(campaign['summary']))),
                      const SizedBox(height: 6),
                      Text(
                          '${t['years']}: ${_years(campaign['years'])} · ${_text(campaign['note'])}',
                          style: const TextStyle(
                              fontSize: 12, color: Color(0xFF67788B))),
                    ]),
              ),
            ),
      ]);

  Widget _maintenance() {
    final items =
        _list(widget.data['maintenance']).whereType<Map<String, dynamic>>();
    return Column(children: [
      for (final (severe, title) in [(false, t['normal']!), (true, t['severe']!)])
        if (items.any((item) => (item['severe'] == true) == severe))
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: Theme.of(context).textTheme.titleMedium),
                    for (final item in items
                        .where((item) => (item['severe'] == true) == severe))
                      Padding(
                        padding: const EdgeInsets.only(top: 10),
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Wrap(children: [
                                Text(
                                    [item['job'], item['action']]
                                        .where((p) => _text(p).isNotEmpty)
                                        .join(' · '),
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w700,
                                        color: AppTheme.navy)),
                                ..._marks(item),
                              ]),
                              Text([
                                _text(item['interval']),
                                _text(item['occurrence']),
                                if (_text(item['max_interval']).isNotEmpty)
                                  '${t['limit']} ${item['max_interval']}',
                                _text(item['system']),
                              ].where((p) => p.isNotEmpty).join(' · ')),
                              if ([
                                item['service'],
                                item['qualifier'],
                                item['condition_detail']
                              ].any((p) => _text(p).isNotEmpty))
                                Text(
                                    [
                                      item['service'],
                                      item['qualifier'],
                                      item['condition_detail']
                                    ]
                                        .where((p) => _text(p).isNotEmpty)
                                        .join(' · '),
                                    style: const TextStyle(
                                        fontSize: 12,
                                        color: Color(0xFF67788B))),
                            ]),
                      ),
                  ]),
            ),
          ),
    ]);
  }
}
