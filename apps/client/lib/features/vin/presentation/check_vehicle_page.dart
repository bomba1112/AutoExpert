import 'package:autoexpert_client/features/listing/data/listing_intake_api.dart';
import 'package:autoexpert_client/features/listing/presentation/listing_intake_page.dart';
import 'package:autoexpert_client/features/vin/data/vin_history_api.dart';
import 'package:autoexpert_client/features/vin/presentation/vin_history_page.dart';
import 'package:autoexpert_client/l10n/app_localizations.dart';
import 'package:flutter/material.dart';

class CheckVehiclePage extends StatelessWidget {
  const CheckVehiclePage(
      {required this.vinApi,
      required this.listingApi,
      required this.language,
      required this.onAddComparison,
      this.qaMode = false,
      this.initialTab = 0,
      this.initialVin,
      super.key});

  final VinHistoryApi vinApi;
  final ListingIntakeApi listingApi;
  final String language;
  final ValueChanged<String> onAddComparison;
  final bool qaMode;
  final int initialTab;
  final String? initialVin;

  @override
  Widget build(BuildContext context) {
    final copy = AppLocalizations.of(context);
    void openVin(String? vin) =>
        Navigator.of(context).push(MaterialPageRoute<void>(
          builder: (_) => CheckVehiclePage(
              vinApi: vinApi,
              listingApi: listingApi,
              language: language,
              qaMode: qaMode,
              onAddComparison: onAddComparison,
              initialVin: vin),
        ));
    return DefaultTabController(
      length: 3,
      initialIndex: initialTab,
      child: Scaffold(
        appBar: AppBar(
            title: Text(copy.checkCarTitle),
            bottom: TabBar(
              isScrollable: true,
              tabAlignment: TabAlignment.center,
              tabs: [
                Tab(text: 'VIN'),
                Tab(text: copy.checkTabTurbo),
                Tab(text: copy.checkTabManual)
              ],
            )),
        body: TabBarView(children: [
          VinHistoryPage(
              api: vinApi,
              language: language,
              qaMode: qaMode,
              embedded: true,
              initialVin: initialVin),
          ListingIntakePage(
              api: listingApi,
              language: language,
              onCheckVin: openVin,
              onAddComparison: onAddComparison),
          ListingIntakePage(
              api: listingApi,
              language: language,
              manual: true,
              onCheckVin: openVin,
              onAddComparison: onAddComparison),
        ]),
      ),
    );
  }
}
