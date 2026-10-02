import 'dart:convert';
import 'dart:typed_data';

import 'package:autoexpert_client/core/config/app_config.dart';
import 'package:autoexpert_client/core/network/api_client.dart';
import 'package:autoexpert_client/features/vin/data/vin_history_api.dart';
import 'package:autoexpert_client/features/vin/data/vin_validation.dart';
import 'package:autoexpert_client/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class VinHistoryPage extends StatefulWidget {
  const VinHistoryPage({
    required this.api,
    required this.language,
    this.qaMode = false,
    this.embedded = false,
    this.initialVin,
    super.key,
  });

  final VinHistoryApi api;
  final String language;
  final bool qaMode;
  final bool embedded;
  final String? initialVin;

  @override
  State<VinHistoryPage> createState() => _VinHistoryPageState();
}

class _VinHistoryPageState extends State<VinHistoryPage> {
  final _vinController = TextEditingController();
  Map<String, dynamic>? _check;
  Map<String, dynamic>? _report;
  final Map<String, Future<Uint8List>> _assetLoads = {};
  bool _busy = true;
  bool _invalidVin = false;
  bool _demoOnlyVin = false;
  bool _requestFailed = false;

  @override
  void initState() {
    super.initState();
    if (widget.initialVin != null) {
      _vinController.text = widget.initialVin!;
      _busy = false;
    } else {
      _restore();
    }
  }

  @override
  void dispose() {
    _vinController.dispose();
    super.dispose();
  }

  Future<void> _restore() async {
    try {
      final check = await widget.api.loadSavedCheck(widget.language);
      if (!mounted) return;
      if (check != null && (widget.qaMode || !_mockRecord(check))) {
        setState(() {
          _check = check;
          _vinController.text = _text(check['vin']);
        });
        if (check['is_unlocked'] == true && _reportReady(check)) {
          await _loadReport();
        }
      }
    } catch (_) {
      if (mounted) setState(() => _requestFailed = true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _refreshCheck() async {
    if (_busy) return;
    final checkId = _text(_check?['check_id']);
    if (checkId.isEmpty) return;
    setState(() {
      _busy = true;
      _requestFailed = false;
    });
    try {
      final check = await widget.api.getCheck(checkId, widget.language);
      if (!mounted) return;
      if (!widget.qaMode && _mockRecord(check)) return;
      setState(() => _check = check);
      if (check['is_unlocked'] == true && _reportReady(check)) {
        await _loadReport();
      }
    } catch (_) {
      if (mounted) setState(() => _requestFailed = true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _submit() async {
    if (_busy) return;
    final vin = _vinController.text.trim().toUpperCase();
    if (!isValidUsVin(vin)) {
      setState(() {
        _invalidVin = true;
        _demoOnlyVin = false;
      });
      return;
    }
    if (widget.qaMode &&
        AppConfig.vinHistoryFixtureOnly &&
        vin != AppConfig.vinHistoryFixtureVin) {
      setState(() {
        _demoOnlyVin = true;
        _invalidVin = false;
      });
      return;
    }
    setState(() {
      _busy = true;
      _invalidVin = false;
      _demoOnlyVin = false;
      _requestFailed = false;
      _check = null;
      _report = null;
      _assetLoads.clear();
    });
    try {
      final check = await widget.api.createCheck(vin, widget.language);
      if (!widget.qaMode && _mockRecord(check)) {
        if (mounted) setState(() => _requestFailed = true);
        return;
      }
      if (mounted) setState(() => _check = check);
    } on ApiException {
      if (mounted) setState(() => _requestFailed = true);
    } catch (_) {
      if (mounted) setState(() => _requestFailed = true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _payMock() async {
    if (_busy) return;
    final checkId = _text(_check?['check_id']);
    if (checkId.isEmpty) return;
    setState(() {
      _busy = true;
      _requestFailed = false;
    });
    try {
      final check = await widget.api.mockPayment(checkId, widget.language);
      if (!mounted) return;
      setState(() => _check = check);
      if (check['is_unlocked'] == true && _reportReady(check)) {
        await _loadReport();
      }
    } catch (_) {
      if (mounted) setState(() => _requestFailed = true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _loadReport() async {
    final checkId = _text(_check?['check_id']);
    if (checkId.isEmpty) return;
    try {
      final report = await widget.api.getReport(checkId, widget.language);
      if (mounted) setState(() => _report = report);
    } catch (_) {
      if (mounted) setState(() => _requestFailed = true);
    }
  }

  Future<void> _retryReport() async {
    if (_busy) return;
    final checkId = _text(_check?['check_id']);
    if (checkId.isEmpty) return;
    setState(() {
      _busy = true;
      _requestFailed = false;
    });
    try {
      final check = await widget.api.retryReport(checkId, widget.language);
      if (!mounted) return;
      setState(() => _check = check);
      if (check['is_unlocked'] == true && _reportReady(check)) {
        await _loadReport();
      }
    } catch (_) {
      if (mounted) setState(() => _requestFailed = true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  static bool _reportReady(Map<String, dynamic> check) =>
      check['status'] == 'REPORT_READY' || check['status'] == 'PARTIAL';

  static String _text(Object? value) => value is String ? value : '';

  static Map<String, dynamic> _map(Object? value) =>
      value is Map<String, dynamic> ? value : <String, dynamic>{};

  static List<dynamic> _list(Object? value) => value is List ? value : const [];

  bool _mockRecord(Map<String, dynamic> value) =>
      value['is_mock'] == true ||
      value['provider_id'] == 'local_history_fixture' ||
      value['provider_mode'] == 'MOCK' ||
      value['provider_mode'] == 'SANDBOX';

  Widget _assetImage(Uint8List bytes, {double height = 220}) {
    final prefix = utf8.decode(bytes.take(256).toList(), allowMalformed: true);
    if (prefix.contains('<svg')) {
      return SvgPicture.memory(bytes, height: height, fit: BoxFit.contain);
    }
    return Image.memory(bytes, height: height, fit: BoxFit.contain);
  }

  void _openAsset(Uint8List bytes) {
    showDialog<void>(
      context: context,
      builder: (context) => Dialog(
        child: InteractiveViewer(
          minScale: 1,
          maxScale: 5,
          child: _assetImage(bytes, height: 460),
        ),
      ),
    );
  }

  String? _recordLabel(String key, AppLocalizations copy) {
    final normalized = key.toLowerCase();
    if (normalized.contains('auction')) return copy.vinAuctions;
    if (normalized.contains('damage') || normalized.contains('accident')) {
      return copy.vinDamage;
    }
    if (normalized.contains('odometer') || normalized.contains('mileage')) {
      return copy.vinOdometer;
    }
    if (normalized.contains('title') || normalized.contains('salvage')) {
      return copy.vinTitleRecords;
    }
    if (normalized.contains('theft')) return copy.vinTheft;
    if (normalized.contains('registration')) return copy.vinRegistration;
    if (normalized.contains('sale')) return copy.vinSales;
    return null;
  }

  String? _photoTypeLabel(String key, AppLocalizations copy) => switch (key) {
        'RETAIL_PHOTO' => copy.vinRetailPhoto,
        'WHOLESALE_PHOTO' => copy.vinWholesalePhoto,
        'HISTORICAL_PHOTO' => copy.vinHistoricalPhoto,
        _ => null,
      };

  Widget _preview(AppLocalizations copy) {
    final check = _check;
    if (check == null) return const SizedBox.shrink();
    if (!widget.qaMode && _mockRecord(check)) return const SizedBox.shrink();
    final identity = _map(check['vehicle_identity']);
    final preview = _map(check['preview']);
    final quote = _map(check['quote']);
    final identityParts = <String>[
      _text(identity['make']),
      _text(identity['model']),
      if (identity['model_year'] != null) '${identity['model_year']}',
    ].where((value) => value.isNotEmpty).toList();
    final confirmed = <String>{};
    for (final item in _list(preview['available_record_types'])) {
      final label = _recordLabel('$item', copy);
      if (label != null) confirmed.add(label);
    }
    if (preview['damage_records_available'] == true) {
      confirmed.add(copy.vinDamage);
    }
    if (preview['title_records_available'] == true) {
      confirmed.add(copy.vinTitleRecords);
    }
    final photos = preview['photo_count'];
    final odometerEvents = preview['odometer_event_count'];
    final retail = _text(quote['retail_price_azn']);
    final sellable = quote['sellable'] == true;
    final unlocked = check['is_unlocked'] == true;
    final status = _text(check['status']);
    final awaitingPayment = status == 'PREFLIGHT_COMPLETE' ||
        status == 'AWAITING_PAYMENT' ||
        status == 'CREATED';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const SizedBox(height: 18),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(copy.vinPreviewTitle,
                    style: Theme.of(context).textTheme.titleMedium),
                if (identityParts.isNotEmpty) ...[
                  const SizedBox(height: 10),
                  Text(identityParts.join(' · ')),
                ],
                if (confirmed.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  for (final item in confirmed)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Row(children: [
                        const Icon(Icons.check_circle_outline, size: 18),
                        const SizedBox(width: 8),
                        Expanded(child: Text(item)),
                      ]),
                    ),
                ],
                if (photos is int && photos > 0)
                  Text('${copy.vinPhotoCount}: $photos'),
                if (odometerEvents is int && odometerEvents > 0)
                  Text('${copy.vinOdometerEventCount}: $odometerEvents'),
                if (preview['content_determined_after_purchase'] == true ||
                    (confirmed.isEmpty &&
                        !(photos is int && photos > 0) &&
                        !(odometerEvents is int && odometerEvents > 0))) ...[
                  const SizedBox(height: 10),
                  Text(copy.vinCoverageAfterRequest),
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        if (unlocked && _reportReady(check))
          FilledButton(
            onPressed: _busy ? null : _loadReport,
            child: Text(copy.vinOpenReport),
          )
        else if (unlocked && status == 'FAILED_RETRYABLE') ...[
          Text(copy.vinProcessing),
          const SizedBox(height: 10),
          OutlinedButton(
            onPressed: _busy ? null : _retryReport,
            child: Text(copy.vinRetryReport),
          ),
        ] else if (!awaitingPayment) ...[
          Text(status == 'REFUND_REQUIRED'
              ? copy.vinPaymentRecovery
              : status == 'FAILED_FINAL'
                  ? copy.vinPurchaseUnavailable
                  : copy.vinProcessing),
          const SizedBox(height: 10),
          OutlinedButton(
            onPressed: _busy ? null : _refreshCheck,
            child: Text(copy.vinRefreshStatus),
          ),
        ] else if (sellable && widget.qaMode) ...[
          if (retail.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text('${copy.vinPrice}: $retail AZN'),
            ),
          FilledButton(
            onPressed: _busy ? null : _payMock,
            child: Text(copy.vinMockPayment),
          ),
          const SizedBox(height: 8),
          Text(copy.vinNoRealCharge,
              style: Theme.of(context).textTheme.bodySmall),
        ] else
          Text(copy.vinPurchaseUnavailable),
      ],
    );
  }

  Widget _reportContent(AppLocalizations copy) {
    final report = _report;
    if (report == null) return const SizedBox.shrink();
    if (!widget.qaMode &&
        (_mockRecord(_check ?? const {}) || _mockRecord(report))) {
      return const SizedBox.shrink();
    }
    final sections = _list(report['sections']);
    final assets = _list(report['asset_ids']);
    final assetMetadata = {
      for (final value in _list(report['assets']))
        if (value is Map<String, dynamic> && _text(value['id']).isNotEmpty)
          _text(value['id']): value,
    };
    final checkId = _text(report['check_id']);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const SizedBox(height: 24),
        Text(copy.vinReportTitle,
            style: Theme.of(context).textTheme.headlineSmall),
        if (report['mileage_anomaly'] == true) ...[
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(copy.vinMileageAnomaly),
            ),
          ),
        ],
        for (final rawSection in sections)
          if (rawSection is Map<String, dynamic> &&
              _list(rawSection['items']).isNotEmpty)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(_text(rawSection['title']),
                        style: Theme.of(context).textTheme.titleMedium),
                    for (final rawItem in _list(rawSection['items']))
                      if (rawItem is Map<String, dynamic> &&
                          _text(rawItem['text']).isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.only(top: 10),
                          child: Text([
                            if (_text(rawItem['date']).isNotEmpty)
                              _text(rawItem['date']),
                            _text(rawItem['text']),
                          ].join(' · ')),
                        ),
                  ],
                ),
              ),
            ),
        if (assets.isNotEmpty) ...[
          const SizedBox(height: 12),
          Text(copy.vinPhotos, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          for (final rawId in assets)
            if (rawId is String && rawId.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: FutureBuilder<Uint8List>(
                            future: _assetLoads.putIfAbsent(
                              rawId,
                              () => widget.api.getAssetBytes(
                                checkId,
                                rawId,
                                widget.language,
                              ),
                            ),
                            builder: (context, snapshot) => snapshot.hasData
                                ? InkWell(
                                    onTap: () => _openAsset(snapshot.data!),
                                    child: _assetImage(snapshot.data!),
                                  )
                                : snapshot.hasError
                                    ? const SizedBox.shrink()
                                    : const SizedBox(
                                        height: 220,
                                        child: Center(
                                            child: CircularProgressIndicator()),
                                      ),
                          ),
                        ),
                        if (assetMetadata[rawId] != null) ...[
                          const SizedBox(height: 8),
                          if (_photoTypeLabel(
                                  _text(assetMetadata[rawId]!['photo_type']),
                                  copy) !=
                              null)
                            Text(_photoTypeLabel(
                                _text(assetMetadata[rawId]!['photo_type']),
                                copy)!),
                          if (_text(assetMetadata[rawId]!['event_date'])
                              .isNotEmpty)
                            Text(_text(assetMetadata[rawId]!['event_date'])),
                          if (_text(assetMetadata[rawId]!['caption'])
                              .isNotEmpty)
                            Text(_text(assetMetadata[rawId]!['caption'])),
                          if (_text(assetMetadata[rawId]!['source']).isNotEmpty)
                            Text('${copy.vinSource}: '
                                '${_text(assetMetadata[rawId]!['source']) == 'local_history_fixture' ? copy.vinDemoSource : _text(assetMetadata[rawId]!['source'])}'),
                        ],
                      ],
                    ),
                  ),
                ),
              ),
        ],
        const SizedBox(height: 10),
        Text(copy.vinEvidenceNotice,
            style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final copy = AppLocalizations.of(context);
    final content = SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 680),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(copy.vinInputTitle,
                    style: Theme.of(context).textTheme.headlineSmall),
                const SizedBox(height: 8),
                Text(copy.vinInputDescription),
                if (widget.qaMode && AppConfig.vinHistoryFixtureOnly) ...[
                  const SizedBox(height: 8),
                  Text(copy.vinDemoNotice,
                      style: Theme.of(context).textTheme.bodySmall),
                ],
                const SizedBox(height: 20),
                TextField(
                  controller: _vinController,
                  maxLength: 17,
                  textCapitalization: TextCapitalization.characters,
                  autocorrect: false,
                  decoration: InputDecoration(
                    labelText: 'VIN',
                    hintText:
                        widget.qaMode ? AppConfig.vinHistoryFixtureVin : null,
                    errorText: _invalidVin
                        ? copy.vinInvalid
                        : _demoOnlyVin
                            ? copy.vinDemoOnly
                            : null,
                    border: const OutlineInputBorder(),
                  ),
                  onChanged: (_) {
                    if (_invalidVin || _demoOnlyVin) {
                      setState(() {
                        _invalidVin = false;
                        _demoOnlyVin = false;
                      });
                    }
                  },
                  onSubmitted: (_) => _submit(),
                ),
                const SizedBox(height: 12),
                FilledButton(
                  onPressed: _busy ? null : _submit,
                  child: Text(copy.vinStartCheck),
                ),
                if (_busy) ...[
                  const SizedBox(height: 16),
                  const Center(child: CircularProgressIndicator()),
                ],
                if (_requestFailed) ...[
                  const SizedBox(height: 12),
                  Text(copy.vinRequestFailed,
                      style: TextStyle(
                          color: Theme.of(context).colorScheme.error)),
                ],
                _preview(copy),
                _reportContent(copy),
              ],
            ),
          ),
        ),
      ),
    );
    return widget.embedded
        ? content
        : Scaffold(
            appBar: AppBar(title: Text(copy.checkVehicle)), body: content);
  }
}
