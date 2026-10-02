import 'package:autoexpert_client/app/app_controller.dart';
import 'package:autoexpert_client/features/buyer/data/buyer_catalog_api.dart';
import 'package:autoexpert_client/features/buyer/presentation/technical_display.dart';
import 'package:autoexpert_client/l10n/app_localizations.dart';
import 'package:flutter/material.dart';

class ComparisonPage extends StatefulWidget {
  const ComparisonPage(
      {required this.controller,
      required this.api,
      required this.language,
      required this.onAdd,
      required this.onOpenProfile,
      super.key});
  final AppController controller;
  final BuyerCatalogApi api;
  final String language;
  final VoidCallback onAdd;
  final ValueChanged<String> onOpenProfile;
  @override
  State<ComparisonPage> createState() => _ComparisonPageState();
}

class _ComparisonPageState extends State<ComparisonPage> {
  bool _busy = false;
  bool _failed = false;
  Map<String, dynamic>? _result;
  final Map<String, Future<Map<String, dynamic>>> _profiles = {};

  Future<void> _compare() async {
    if (_busy || widget.controller.comparisonIds.length < 2) return;
    setState(() {
      _busy = true;
      _failed = false;
    });
    try {
      final result = await widget.api
          .compare(widget.controller.comparisonIds, widget.language);
      if (mounted) setState(() => _result = result);
    } catch (_) {
      if (mounted) setState(() => _failed = true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final copy = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(copy.compareTitle)),
      body: SafeArea(
          child: AnimatedBuilder(
        animation: widget.controller,
        builder: (context, _) {
          final ids = widget.controller.comparisonIds;
          final members = _result?['members'] is List
              ? _result!['members'] as List
              : const [];
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Center(
                child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 650),
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(copy.compareChoose,
                        style: Theme.of(context).textTheme.bodyLarge),
                    const SizedBox(height: 14),
                    for (final id in ids)
                      FutureBuilder<Map<String, dynamic>>(
                        future: _profiles.putIfAbsent(
                            id, () => widget.api.vehicle(id, widget.language)),
                        builder: (context, snapshot) {
                          final vehicle = snapshot.data;
                          return Card(
                              child: ListTile(
                            title: Text(vehicle == null
                                ? copy.profileTitle
                                : '${vehicle['make']} ${vehicle['model']}'),
                            subtitle: vehicle == null
                                ? null
                                : Text([
                                    '${vehicle['year']}',
                                    TechnicalDisplay.configuration(
                                        vehicle['facts'] is Map<String, dynamic>
                                            ? vehicle['facts']
                                                as Map<String, dynamic>
                                            : const {},
                                        widget.language),
                                  ]
                                    .where((part) => part.isNotEmpty)
                                    .join(' · ')),
                            trailing: IconButton(
                                icon: const Icon(Icons.close_rounded),
                                onPressed: () {
                                  widget.controller.removeComparison(id);
                                  setState(() => _result = null);
                                }),
                            onTap: vehicle == null
                                ? null
                                : () => widget.onOpenProfile(id),
                          ));
                        },
                      ),
                    if (ids.length < 3)
                      OutlinedButton.icon(
                          onPressed: widget.onAdd,
                          icon: const Icon(Icons.add_rounded),
                          label: Text(copy.compareAdd)),
                    const SizedBox(height: 10),
                    FilledButton(
                        onPressed: ids.length < 2 || _busy ? null : _compare,
                        child: Text(copy.compareRun)),
                    if (_busy)
                      const Padding(
                          padding: EdgeInsets.all(14),
                          child: Center(child: CircularProgressIndicator())),
                    if (_failed)
                      Padding(
                          padding: const EdgeInsets.only(top: 10),
                          child: Text(copy.compareFailed)),
                    if (members.isNotEmpty) ...[
                      const SizedBox(height: 18),
                      for (final member in members)
                        if (member is Map<String, dynamic>)
                          Card(
                              child: Padding(
                                  padding: const EdgeInsets.all(16),
                                  child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                            '${member['make']} ${member['model']}',
                                            style: Theme.of(context)
                                                .textTheme
                                                .titleMedium),
                                        const SizedBox(height: 5),
                                        Text([
                                          '${member['year']}',
                                          TechnicalDisplay.configuration(
                                              member['facts']
                                                      is Map<String, dynamic>
                                                  ? member['facts']
                                                      as Map<String, dynamic>
                                                  : const {},
                                              widget.language),
                                        ]
                                            .where((part) => part.isNotEmpty)
                                            .join(' · ')),
                                      ]))),
                    ],
                  ]),
            )),
          );
        },
      )),
    );
  }
}
