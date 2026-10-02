import 'package:autoexpert_client/core/theme/app_theme.dart';
import 'package:autoexpert_client/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';

class HomePage extends StatelessWidget {
  const HomePage(
      {required this.onChangeLanguage,
      required this.onCheckVehicle,
      required this.onFindCar,
      required this.onCompare,
      required this.onReports,
      super.key});

  final VoidCallback onChangeLanguage;
  final ValueChanged<BuildContext> onCheckVehicle;
  final ValueChanged<BuildContext> onFindCar;
  final ValueChanged<BuildContext> onCompare;
  final ValueChanged<BuildContext> onReports;

  @override
  Widget build(BuildContext context) {
    final copy = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(
        centerTitle: false,
        titleSpacing: 18,
        title: Row(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.directions_car_filled_rounded,
              color: AppTheme.navy, size: 30),
          const SizedBox(width: 8),
          Flexible(
              child: FittedBox(
            fit: BoxFit.scaleDown,
            alignment: Alignment.centerLeft,
            child: Text.rich(
                TextSpan(children: [
                  const TextSpan(
                      text: 'AUTO ', style: TextStyle(color: AppTheme.blue)),
                  const TextSpan(
                      text: 'EXPERT', style: TextStyle(color: AppTheme.ink)),
                ]),
                style:
                    const TextStyle(fontSize: 17, fontWeight: FontWeight.w900)),
          )),
        ]),
        actions: [
          IconButton(
              tooltip: copy.changeLanguage,
              onPressed: onChangeLanguage,
              icon: const Icon(Icons.language_rounded))
        ],
      ),
      bottomNavigationBar: NavigationBar(
        height: 72,
        selectedIndex: 0,
        onDestinationSelected: (index) {
          if (index == 1) onCompare(context);
          if (index == 2) onCheckVehicle(context);
          if (index == 3) onReports(context);
        },
        destinations: [
          NavigationDestination(
              icon: const Icon(Icons.home_outlined),
              selectedIcon: const Icon(Icons.home_rounded),
              label: copy.navHome),
          NavigationDestination(
              icon: const Icon(Icons.balance_outlined), label: copy.navCompare),
          NavigationDestination(
              icon: const Icon(Icons.search_rounded), label: copy.navCheck),
          NavigationDestination(
              icon: const Icon(Icons.description_outlined),
              label: copy.navReports),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 28),
            child: Center(
                child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 620),
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(copy.homeTitle,
                        style: Theme.of(context).textTheme.displaySmall),
                    const SizedBox(height: 6),
                    Text(copy.homeSubtitle,
                        style: Theme.of(context).textTheme.bodyMedium),
                    const SizedBox(height: 18),
                    _BuyerCard(copy: copy, onTap: () => onFindCar(context)),
                    const SizedBox(height: 10),
                    _CheckCard(
                        copy: copy, onTap: () => onCheckVehicle(context)),
                    const SizedBox(height: 22),
                    Wrap(
                        alignment: WrapAlignment.spaceBetween,
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: [
                          Text(copy.battleTitle,
                              style: Theme.of(context).textTheme.headlineSmall),
                          TextButton(
                              onPressed: () => onCompare(context),
                              child: Text(copy.battleAll)),
                        ]),
                    const SizedBox(height: 3),
                    Text(copy.battleSubtitle),
                    const SizedBox(height: 12),
                    SizedBox(
                        height: 178,
                        child: ListView(
                            scrollDirection: Axis.horizontal,
                            children: [
                              _BattleCard(
                                  title: copy.battleFirst,
                                  onTap: () => onCompare(context)),
                              _BattleCard(
                                  title: copy.battleSecond,
                                  onTap: () => onCompare(context)),
                            ])),
                  ]),
            ))),
      ),
    );
  }
}

class _BuyerCard extends StatelessWidget {
  const _BuyerCard({required this.copy, required this.onTap});
  final AppLocalizations copy;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Container(
        constraints: const BoxConstraints(minHeight: 248),
        decoration: BoxDecoration(
            gradient: const LinearGradient(
                colors: [Color(0xFFDDEFFF), Color(0xFFAED7FC)]),
            borderRadius: BorderRadius.circular(20),
            boxShadow: const [
              BoxShadow(
                  color: Color(0x1A256CB0),
                  blurRadius: 15,
                  offset: Offset(0, 7))
            ]),
        clipBehavior: Clip.antiAlias,
        child: Stack(children: [
          Positioned(
              right: -75,
              bottom: -26,
              width: 390,
              child: SvgPicture.asset('assets/buyer-road.svg')),
          Positioned.fill(
              child: DecoratedBox(
                  decoration: BoxDecoration(
                      gradient: LinearGradient(colors: [
            const Color(0xFFECF6FF),
            const Color(0xFFECF6FF).withValues(alpha: .88),
            Colors.transparent
          ], stops: const [
            0,
            .45,
            1
          ])))),
          Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(
                        width: 245,
                        child: Text(copy.buyCarTitle,
                            style: const TextStyle(
                                fontSize: 25,
                                height: 1.06,
                                fontWeight: FontWeight.w900,
                                color: Color(0xFF064BBF)))),
                    const SizedBox(height: 8),
                    SizedBox(
                        width: 220,
                        child: Text(copy.buyCarSubtitle,
                            style: const TextStyle(
                                fontSize: 13,
                                height: 1.25,
                                color: AppTheme.ink))),
                    const SizedBox(height: 34),
                    SizedBox(
                        width: 190,
                        height: 48 * MediaQuery.textScalerOf(context).scale(1),
                        child: FilledButton(
                            onPressed: onTap,
                            child: Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Flexible(
                                      child: Text(copy.buyCarCta,
                                          overflow: TextOverflow.ellipsis)),
                                  const SizedBox(width: 5),
                                  const Icon(Icons.arrow_forward_rounded,
                                      size: 18)
                                ]))),
                  ])),
        ]),
      );
}

class _CheckCard extends StatelessWidget {
  const _CheckCard({required this.copy, required this.onTap});
  final AppLocalizations copy;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Container(
        constraints: const BoxConstraints(minHeight: 260),
        decoration: BoxDecoration(
            gradient: const LinearGradient(
                colors: [Color(0xFF061726), Color(0xFF173C61)]),
            borderRadius: BorderRadius.circular(20)),
        clipBehavior: Clip.antiAlias,
        child: Stack(children: [
          Positioned(
              right: -100,
              bottom: -12,
              width: 340,
              child: Opacity(
                  opacity: .43,
                  child: SvgPicture.asset('assets/buyer-road.svg'))),
          Positioned.fill(
              child: DecoratedBox(
                  decoration: BoxDecoration(
                      gradient: LinearGradient(colors: [
            AppTheme.navy,
            AppTheme.navy.withValues(alpha: .75),
            Colors.transparent
          ], stops: const [
            0,
            .5,
            1
          ])))),
          Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(
                        width: 245,
                        child: Text(copy.checkCarTitle,
                            style: const TextStyle(
                                fontSize: 24,
                                height: 1.05,
                                fontWeight: FontWeight.w900,
                                color: Colors.white))),
                    const SizedBox(height: 10),
                    SizedBox(
                        width: 240,
                        child: Text(copy.checkCarSubtitle,
                            style: const TextStyle(
                                color: Color(0xFFDDEBFA),
                                fontSize: 13,
                                height: 1.25))),
                    const SizedBox(height: 34),
                    SizedBox(
                        width: 230,
                        height: 48 * MediaQuery.textScalerOf(context).scale(1),
                        child: FilledButton(
                            onPressed: onTap,
                            child: Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Flexible(
                                      child: Text(copy.checkCarCta,
                                          maxLines: 2,
                                          textAlign: TextAlign.center)),
                                  const SizedBox(width: 6),
                                  const Icon(Icons.arrow_forward_rounded,
                                      size: 18)
                                ]))),
                  ])),
        ]),
      );
}

class _BattleCard extends StatelessWidget {
  const _BattleCard({required this.title, required this.onTap});
  final String title;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => SizedBox(
      width: 220,
      child: Padding(
        padding: const EdgeInsets.only(right: 10),
        child: Material(
          color: AppTheme.navy,
          borderRadius: BorderRadius.circular(16),
          clipBehavior: Clip.antiAlias,
          child: InkWell(
              onTap: onTap,
              child: Stack(children: [
                Positioned(
                    top: 0,
                    right: -45,
                    width: 240,
                    child: Opacity(
                        opacity: .75,
                        child: SvgPicture.asset('assets/buyer-road.svg'))),
                Positioned.fill(
                    child: DecoratedBox(
                        decoration: BoxDecoration(
                            gradient: LinearGradient(
                                begin: Alignment.topCenter,
                                end: Alignment.bottomCenter,
                                colors: [
                      Colors.transparent,
                      AppTheme.navy.withValues(alpha: .95)
                    ],
                                stops: const [
                      .25,
                      .8
                    ])))),
                Positioned(
                    left: 14,
                    right: 14,
                    bottom: 13,
                    child: Text(title,
                        maxLines: 3,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w800,
                            fontSize: 15))),
              ])),
        ),
      ));
}
