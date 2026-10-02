import 'package:autoexpert_client/app/app_controller.dart';
import 'package:autoexpert_client/core/theme/app_theme.dart';
import 'package:autoexpert_client/core/network/api_client.dart';
import 'package:autoexpert_client/features/buyer/data/buyer_catalog_api.dart';
import 'package:autoexpert_client/features/buyer/presentation/buyer_search_page.dart';
import 'package:autoexpert_client/features/buyer/presentation/comparison_page.dart';
import 'package:autoexpert_client/features/buyer/presentation/vehicle_profile_page.dart';
import 'package:autoexpert_client/features/home/presentation/home_page.dart';
import 'package:autoexpert_client/features/language/presentation/language_page.dart';
import 'package:autoexpert_client/features/listing/data/listing_intake_api.dart';
import 'package:autoexpert_client/features/vin/data/vin_history_api.dart';
import 'package:autoexpert_client/features/vin/presentation/check_vehicle_page.dart';
import 'package:autoexpert_client/l10n/app_localizations.dart';
import 'package:flutter/material.dart';

class AutoExpertApp extends StatefulWidget {
  const AutoExpertApp({super.key});

  @override
  State<AutoExpertApp> createState() => _AutoExpertAppState();
}

class _AutoExpertAppState extends State<AutoExpertApp> {
  late final AppController _controller;
  late final VinHistoryApi _vinApi;
  late final ListingIntakeApi _listingApi;
  late final BuyerCatalogApi _buyerApi;
  late final ApiClient _configApi;
  bool _qaMode = false;

  @override
  void initState() {
    super.initState();
    _controller = AppController()..addListener(_refresh);
    _vinApi = VinHistoryApi();
    _listingApi = ListingIntakeApi(_vinApi);
    _buyerApi = BuyerCatalogApi();
    _configApi = ApiClient();
    _loadClientConfig();
  }

  Future<void> _loadClientConfig() async {
    try {
      final config = await _configApi.getJson('/meta/client-config');
      if (mounted) setState(() => _qaMode = config['qa_mode'] == true);
    } catch (_) {
      // A failed config request must not expose QA-only controls.
    }
  }

  void _refresh() => setState(() {});

  @override
  void dispose() {
    _controller
      ..removeListener(_refresh)
      ..dispose();
    _vinApi.close();
    _buyerApi.close();
    _configApi.close();
    super.dispose();
  }

  String get _reportLanguage =>
      _controller.locale?.languageCode == 'az' ? 'az' : 'ru';

  void _openCheck(BuildContext context, {String? initialVin}) =>
      Navigator.of(context).push(MaterialPageRoute<void>(
          builder: (_) => CheckVehiclePage(
              vinApi: _vinApi,
              listingApi: _listingApi,
              language: _reportLanguage,
              qaMode: _qaMode,
              initialVin: initialVin,
              onAddComparison: _controller.addComparison)));

  void _openProfile(BuildContext context, String id) =>
      Navigator.of(context).push(MaterialPageRoute<void>(
          builder: (_) => VehicleProfilePage(
              api: _buyerApi,
              language: _reportLanguage,
              variantId: id,
              qaMode: _qaMode,
              onCheckVin: () => _openCheck(context))));

  void _openBuyer(BuildContext context) =>
      Navigator.of(context).push(MaterialPageRoute<void>(
          builder: (_) => BuyerSearchPage(
              api: _buyerApi,
              language: _reportLanguage,
              onOpenProfile: (id) => _openProfile(context, id),
              onAddComparison: _controller.addComparison)));

  void _openCompare(BuildContext context) =>
      Navigator.of(context).push(MaterialPageRoute<void>(
          builder: (_) => ComparisonPage(
              controller: _controller,
              api: _buyerApi,
              language: _reportLanguage,
              onAdd: () => _openBuyer(context),
              onOpenProfile: (id) => _openProfile(context, id))));

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Auto Expert',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      locale: _controller.locale ?? const Locale('ru'),
      home: _controller.locale == null
          ? LanguagePage(onSelected: _controller.selectLanguage)
          : HomePage(
              onChangeLanguage: _controller.resetLanguage,
              onCheckVehicle: _openCheck,
              onFindCar: _openBuyer,
              onCompare: _openCompare,
              onReports: _openCheck,
            ),
    );
  }
}
