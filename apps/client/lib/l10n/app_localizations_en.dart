// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get chooseLanguage => 'Choose your language';

  @override
  String get languageCanChange =>
      'Interface and report language can be changed separately later.';

  @override
  String get continueLabel => 'Continue';

  @override
  String get changeLanguage => 'Change language';

  @override
  String get homeEyebrow => 'Evidence-based car buying';

  @override
  String get homeTitle => 'Know the car before you buy it.';

  @override
  String get homeSubtitle =>
      'Technical evidence, your local market, ownership costs, and your real driving conditions in one expert report.';

  @override
  String get checkVehicle => 'Check a vehicle';

  @override
  String get checkVehicleDescription => 'Get a personalized purchase analysis.';

  @override
  String get compareVehicles => 'Compare vehicles';

  @override
  String get compareVehiclesDescription =>
      'Compare up to three options for the same usage profile.';

  @override
  String get myReports => 'My reports';

  @override
  String get myReportsDescription =>
      'Open purchased reports without generating them again.';

  @override
  String get vinInputTitle => 'Check a specific vehicle';

  @override
  String get vinInputDescription =>
      'Enter the 17-character VIN. The preliminary check shows only confirmed information.';

  @override
  String get vinInvalid => 'Check the VIN and its check digit';

  @override
  String get vinStartCheck => 'Check VIN';

  @override
  String get vinPreviewTitle => 'Preliminary check';

  @override
  String get vinAuctions => 'Auction records';

  @override
  String get vinDamage => 'Damage records';

  @override
  String get vinOdometer => 'Mileage events';

  @override
  String get vinTitleRecords => 'Title records';

  @override
  String get vinTheft => 'Theft records';

  @override
  String get vinRegistration => 'Registration events';

  @override
  String get vinSales => 'Sales history';

  @override
  String get vinPhotoCount => 'Confirmed photos';

  @override
  String get vinOdometerEventCount => 'Confirmed mileage events';

  @override
  String get vinCoverageAfterRequest =>
      'Specific record availability is determined after the provider request.';

  @override
  String get vinPrice => 'Report price';

  @override
  String get vinMockPayment => 'Test payment and report';

  @override
  String get vinNoRealCharge => 'Test mode: no money is charged.';

  @override
  String get vinPurchaseUnavailable =>
      'Report purchase is currently unavailable.';

  @override
  String get vinOpenReport => 'Open report';

  @override
  String get vinReportTitle => 'Vehicle history';

  @override
  String get vinMileageAnomaly =>
      'An anomaly in the mileage sequence was found. Review the source records.';

  @override
  String get vinPhotos => 'Event photos';

  @override
  String get vinEvidenceNotice =>
      'Conclusions are limited by source records and coverage at report time.';

  @override
  String get vinRequestFailed =>
      'The request could not be completed. Try again; a saved report can be opened later.';

  @override
  String get vinProcessing =>
      'The report is being prepared. Check its status later; no second payment is needed.';

  @override
  String get vinPaymentRecovery =>
      'Payment was recorded but the report is not ready. Its status is saved for recovery or refund.';

  @override
  String get vinRefreshStatus => 'Refresh status';

  @override
  String get vinRetryReport => 'Retry report request';

  @override
  String get vinDemoNotice =>
      'This is an isolated demonstration with fixture data. Live providers and payments are not connected.';

  @override
  String get vinDemoOnly =>
      'Only VIN 3FA6P0HD0KR114795 is available in this test scenario';

  @override
  String get vinRetailPhoto => 'Listing photo';

  @override
  String get vinWholesalePhoto => 'Auction photo';

  @override
  String get vinHistoricalPhoto => 'Historical photo';

  @override
  String get vinSource => 'Source';

  @override
  String get vinDemoSource => 'Test source';

  @override
  String get navHome => 'Home';

  @override
  String get navCompare => 'Compare';

  @override
  String get navCheck => 'Check';

  @override
  String get navReports => 'Reports';

  @override
  String get buyCarTitle => 'I want to buy a car';

  @override
  String get buyCarSubtitle =>
      'Find a fit for your budget, market and priorities.';

  @override
  String get buyCarCta => 'Start choosing';

  @override
  String get checkCarTitle => 'Check a specific car';

  @override
  String get checkCarSubtitle =>
      'VIN, listing or your details. Compare only what is supported.';

  @override
  String get checkCarCta => 'Check a car';

  @override
  String get battleTitle => 'Generation battle';

  @override
  String get battleAll => 'All comparisons';

  @override
  String get battleSubtitle => 'Popular comparisons. Evidence over guesses.';

  @override
  String get battleFirst => 'Mercedes W210 vs a new Chinese car';

  @override
  String get battleSecond => 'Passat B7 vs Hyundai Elantra';

  @override
  String get checkTabTurbo => 'Turbo.az link';

  @override
  String get checkTabManual => 'Enter manually';

  @override
  String get listingResultTitle => 'Listing';

  @override
  String get listingOwnInput => 'Your details';

  @override
  String get listingOpenOriginal => 'Open original';

  @override
  String get listingSellerClaims => 'Listed by seller';

  @override
  String get listingEngine => 'Engine';

  @override
  String get listingFuel => 'Fuel';

  @override
  String get listingTransmission => 'Transmission';

  @override
  String get listingDrivetrain => 'Drive';

  @override
  String get listingBody => 'Body';

  @override
  String get listingMarket => 'Market';

  @override
  String get listingColor => 'Color';

  @override
  String get listingSellerType => 'Seller';

  @override
  String get listingMatchTitle => 'Auto Expert match';

  @override
  String get listingExact =>
      'This version agrees with a confirmed Auto Expert configuration.';

  @override
  String get listingMultiple =>
      'Several versions fit this description. Clarify one detail before choosing.';

  @override
  String get listingConflict =>
      'Some listing details differ from confirmed versions. Check the VIN or vehicle documents.';

  @override
  String get listingOutOfScope => 'Check vehicle by VIN';

  @override
  String get listingNoMatch =>
      'Check the model spelling or add details. VIN history can still be checked.';

  @override
  String get listingClaimed => 'Listing says';

  @override
  String get listingCatalogValue => 'Catalog confirms';

  @override
  String get listingCheckVin => 'Check history by VIN';

  @override
  String get listingAddVin => 'Add VIN and check history';

  @override
  String get listingAddCompare => 'Add to comparison';

  @override
  String get listingManualTitle => 'Enter vehicle details';

  @override
  String get listingUrlTitle => 'Turbo.az link';

  @override
  String get listingManualSubtitle =>
      'Enter the seller\'s details. They stay separate from confirmed technical facts.';

  @override
  String get listingUrlSubtitle =>
      'Add one listing. The link is a reference; the app does not download the page.';

  @override
  String get listingInvalidUrl =>
      'Enter a safe https://turbo.az link to one listing.';

  @override
  String get listingEnterUrl => 'Paste the Turbo.az link.';

  @override
  String get listingEnterContent =>
      'Paste listing text or choose a local file.';

  @override
  String get listingTooLarge => 'The file or text exceeds the size limit.';

  @override
  String get listingRequestFailed =>
      'The listing could not be processed. Check the input and try again.';

  @override
  String get listingFileFailed =>
      'Could not read the file. Choose a UTF-8 .html or .txt file.';

  @override
  String get listingNeedMakeModel => 'Enter make and model.';

  @override
  String get listingUrlLabel => 'Listing link';

  @override
  String get listingAddLink => 'Save link';

  @override
  String get listingReferenceOnly =>
      'The link is saved as a reference. To match the car, paste text, choose a saved page, or fill the fields manually.';

  @override
  String get listingText => 'Text';

  @override
  String get listingHtml => 'HTML';

  @override
  String get listingTextLabel => 'Paste listing text';

  @override
  String get listingHtmlLabel => 'Paste saved page HTML';

  @override
  String get listingChooseFile => 'Choose saved page';

  @override
  String get listingAnalyze => 'Match listing';

  @override
  String get listingMake => 'Make';

  @override
  String get listingModel => 'Model';

  @override
  String get listingYear => 'Year';

  @override
  String get listingPrice => 'Price';

  @override
  String get listingCurrency => 'Currency';

  @override
  String get listingMileage => 'Mileage';

  @override
  String get listingMileageUnit => 'Mileage unit';

  @override
  String get listingMoreFields => 'Additional details';

  @override
  String get listingCity => 'City';

  @override
  String get listingOwners => 'Owners (seller claim)';

  @override
  String get listingCondition => 'Condition (seller claim)';

  @override
  String get listingDescription => 'Seller description';

  @override
  String get buyerTitle => 'Find a car';

  @override
  String get buyerStepParameters => 'Parameters';

  @override
  String get buyerStepResults => 'Results';

  @override
  String get buyerHeading => 'Find a car for you';

  @override
  String get buyerSubtitle =>
      'Choose what matters to see confirmed versions and checks to make.';

  @override
  String get buyerQuery => 'Make or model';

  @override
  String get buyerBudget => 'Budget AZN';

  @override
  String get buyerYearFrom => 'Year from';

  @override
  String get buyerYearTo => 'Year to';

  @override
  String get buyerMarket => 'Original market';

  @override
  String get buyerBody => 'Body';

  @override
  String get buyerSedan => 'Sedan';

  @override
  String get buyerCrossover => 'Crossover';

  @override
  String get buyerHatchback => 'Hatchback';

  @override
  String get buyerEngine => 'Engine type';

  @override
  String get buyerAny => 'Any';

  @override
  String get buyerGasolineNa => 'Gasoline non-turbo';

  @override
  String get buyerGasolineTurbo => 'Gasoline turbo';

  @override
  String get buyerDiesel => 'Diesel';

  @override
  String get buyerHybrid => 'Hybrid';

  @override
  String get buyerElectric => 'Electric';

  @override
  String get buyerGearbox => 'Transmission';

  @override
  String get buyerAt => 'Automatic AT';

  @override
  String get buyerCvt => 'CVT';

  @override
  String get buyerDct => 'DCT';

  @override
  String get buyerManual => 'Manual';

  @override
  String get buyerShowMatches => 'Show matching cars';

  @override
  String get buyerSearchFailed => 'Search failed. Try again.';

  @override
  String get buyerResultsTitle => 'Matching options';

  @override
  String get buyerTopLabel => 'Closest to your request';

  @override
  String get buyerCompetitors => 'Other matching models';

  @override
  String get buyerNeedsConfirmation =>
      'Options that need confirmation for your selected criteria';

  @override
  String get buyerNoResults => 'Try changing one selected parameter.';

  @override
  String get buyerOpenProfile => 'Open profile';

  @override
  String get profileTitle => 'Vehicle profile';

  @override
  String get profileLoadFailed => 'Could not open profile. Try again.';

  @override
  String get profileEngineOil => 'Engine oil';

  @override
  String get profileInspectionAdvice =>
      'Before buying, verify VIN and documents, inspect the body, cold start, electronics, test drive and service history.';

  @override
  String get compareTitle => 'Generation battle';

  @override
  String get compareChoose => 'Choose two confirmed versions to compare.';

  @override
  String get compareAdd => 'Add a vehicle';

  @override
  String get compareRun => 'Compare selected';

  @override
  String get compareFailed => 'Comparison failed. Try again.';
}
