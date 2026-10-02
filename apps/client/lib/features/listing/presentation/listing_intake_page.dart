import 'dart:convert';

import 'package:autoexpert_client/features/listing/data/listing_intake_api.dart';
import 'package:autoexpert_client/features/listing/presentation/listing_result_page.dart';
import 'package:autoexpert_client/l10n/app_localizations.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

class ListingIntakePage extends StatefulWidget {
  const ListingIntakePage(
      {required this.api,
      required this.language,
      required this.onCheckVin,
      required this.onAddComparison,
      this.manual = false,
      super.key});

  final ListingIntakeApi api;
  final String language;
  final bool manual;
  final ValueChanged<String?> onCheckVin;
  final ValueChanged<String> onAddComparison;

  @override
  State<ListingIntakePage> createState() => _ListingIntakePageState();
}

class _ListingIntakePageState extends State<ListingIntakePage> {
  final _url = TextEditingController();
  final _content = TextEditingController();
  final _manual = <String, TextEditingController>{
    for (final key in [
      'make',
      'model',
      'year',
      'engine',
      'fuel',
      'transmission',
      'drivetrain',
      'body',
      'market',
      'price',
      'currency',
      'mileage',
      'mileage_unit',
      'vin',
      'city',
      'color',
      'seller_type',
      'owners',
      'condition',
      'description',
    ])
      key: TextEditingController(),
  };
  bool _busy = false;
  bool _urlReferenced = false;
  bool _htmlMode = false;
  String? _localFileName;
  String? _error;

  @override
  void dispose() {
    _url.dispose();
    _content.dispose();
    for (final controller in _manual.values) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _submit(String inputType,
      {String? text, String? html, Map<String, dynamic>? fields}) async {
    if (_busy) return;
    final copy = AppLocalizations.of(context);
    final source = _url.text.trim();
    if (source.isNotEmpty && !isTurboAzUrl(source)) {
      setState(() => _error = copy.listingInvalidUrl);
      return;
    }
    if (inputType == 'URL_REFERENCE' && source.isEmpty) {
      setState(() => _error = copy.listingEnterUrl);
      return;
    }
    final content = text ?? html;
    if (content != null && content.trim().isEmpty) {
      setState(() => _error = copy.listingEnterContent);
      return;
    }
    final maxBytes = inputType == 'TEXT' ? 60000 : 256000;
    if (content != null && utf8.encode(content).length > maxBytes) {
      setState(() => _error = copy.listingTooLarge);
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final response = await widget.api.submit(
        inputType: inputType,
        language: widget.language,
        sourceUrl: source.isEmpty ? null : source,
        text: text,
        html: html,
        fields: fields,
      );
      if (!mounted) return;
      if (response['next_step'] == 'PROVIDE_CONTENT') {
        setState(() => _urlReferenced = true);
      } else {
        Navigator.of(context).push(MaterialPageRoute<void>(
          builder: (_) => ListingResultPage(
              result: response,
              onCheckVin: widget.onCheckVin,
              onAddComparison: widget.onAddComparison),
        ));
      }
    } catch (_) {
      if (mounted) setState(() => _error = copy.listingRequestFailed);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _chooseFile() async {
    final copy = AppLocalizations.of(context);
    try {
      final file = await FilePicker.pickFile(
        type: FileType.custom,
        allowedExtensions: const ['html', 'htm', 'txt'],
      );
      if (!mounted || file == null) return;
      final maxBytes = file.extension?.toLowerCase() == 'txt' ? 60000 : 256000;
      final fileLength = file.lengthSync() ?? await file.length();
      if (fileLength == null || fileLength > maxBytes) {
        setState(() => _error = copy.listingTooLarge);
        return;
      }
      final fileBytes = await file.readAsBytes();
      if (fileBytes.length > maxBytes) {
        setState(() => _error = copy.listingTooLarge);
        return;
      }
      final decoded = utf8.decode(fileBytes, allowMalformed: false);
      setState(() {
        _content.text = decoded;
        _localFileName = file.name;
        _htmlMode = file.extension?.toLowerCase() != 'txt';
        _error = null;
      });
    } catch (_) {
      if (mounted) setState(() => _error = copy.listingFileFailed);
    }
  }

  void _submitManual() {
    final copy = AppLocalizations.of(context);
    final fields = <String, dynamic>{};
    for (final entry in _manual.entries) {
      final value = entry.value.text.trim();
      if (value.isNotEmpty) fields[entry.key] = value;
    }
    if ((fields['make'] ?? '').toString().isEmpty ||
        (fields['model'] ?? '').toString().isEmpty) {
      setState(() => _error = copy.listingNeedMakeModel);
      return;
    }
    _submit('MANUAL', fields: fields);
  }

  Widget _field(String key, String label, {TextInputType? keyboard}) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: TextField(
            controller: _manual[key],
            keyboardType: keyboard,
            decoration: InputDecoration(labelText: label)),
      );

  @override
  Widget build(BuildContext context) {
    final copy = AppLocalizations.of(context);
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Center(
          child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 650),
        child:
            Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Text(widget.manual ? copy.listingManualTitle : copy.listingUrlTitle,
              style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 7),
          Text(widget.manual
              ? copy.listingManualSubtitle
              : copy.listingUrlSubtitle),
          const SizedBox(height: 18),
          if (!widget.manual) ...[
            TextField(
                controller: _url,
                keyboardType: TextInputType.url,
                decoration: InputDecoration(
                    labelText: copy.listingUrlLabel,
                    hintText: 'https://turbo.az/autos/...')),
            const SizedBox(height: 10),
            if (!_urlReferenced)
              FilledButton(
                  onPressed: _busy ? null : () => _submit('URL_REFERENCE'),
                  child: Text(copy.listingAddLink)),
            if (_urlReferenced) ...[
              const SizedBox(height: 12),
              Card(
                  child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Text(copy.listingReferenceOnly))),
            ],
            const SizedBox(height: 16),
            SegmentedButton<bool>(
              segments: [
                ButtonSegment(value: false, label: Text(copy.listingText)),
                ButtonSegment(value: true, label: Text(copy.listingHtml))
              ],
              selected: {_htmlMode},
              onSelectionChanged: (value) =>
                  setState(() => _htmlMode = value.first),
            ),
            const SizedBox(height: 10),
            TextField(
                controller: _content,
                minLines: 5,
                maxLines: 10,
                decoration: InputDecoration(
                    labelText: _htmlMode
                        ? copy.listingHtmlLabel
                        : copy.listingTextLabel,
                    alignLabelWithHint: true)),
            if (_localFileName != null)
              Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(_localFileName!)),
            const SizedBox(height: 10),
            OutlinedButton.icon(
                onPressed: _busy ? null : _chooseFile,
                icon: const Icon(Icons.upload_file_rounded),
                label: Text(copy.listingChooseFile)),
            const SizedBox(height: 8),
            FilledButton(
                onPressed: _busy
                    ? null
                    : () => _submit(_htmlMode ? 'HTML_SNAPSHOT' : 'TEXT',
                        html: _htmlMode ? _content.text : null,
                        text: _htmlMode ? null : _content.text),
                child: Text(copy.listingAnalyze)),
          ] else ...[
            _field('make', copy.listingMake),
            _field('model', copy.listingModel),
            _field('year', copy.listingYear, keyboard: TextInputType.number),
            _field('engine', copy.listingEngine),
            _field('fuel', copy.listingFuel),
            _field('transmission', copy.listingTransmission),
            _field('drivetrain', copy.listingDrivetrain),
            _field('body', copy.listingBody),
            _field('market', copy.listingMarket),
            _field('price', copy.listingPrice, keyboard: TextInputType.number),
            _field('currency', copy.listingCurrency),
            _field('mileage', copy.listingMileage,
                keyboard: TextInputType.number),
            _field('mileage_unit', copy.listingMileageUnit),
            _field('vin', 'VIN'),
            ExpansionTile(title: Text(copy.listingMoreFields), children: [
              _field('city', copy.listingCity),
              _field('color', copy.listingColor),
              _field('seller_type', copy.listingSellerType),
              _field('owners', copy.listingOwners),
              _field('condition', copy.listingCondition),
              _field('description', copy.listingDescription),
            ]),
            const SizedBox(height: 10),
            FilledButton(
                onPressed: _busy ? null : _submitManual,
                child: Text(copy.listingAnalyze)),
          ],
          if (_busy)
            const Padding(
                padding: EdgeInsets.all(16),
                child: Center(child: CircularProgressIndicator())),
          if (_error != null)
            Padding(
                padding: const EdgeInsets.only(top: 10),
                child: Text(_error!,
                    style:
                        TextStyle(color: Theme.of(context).colorScheme.error))),
        ]),
      )),
    );
  }
}
