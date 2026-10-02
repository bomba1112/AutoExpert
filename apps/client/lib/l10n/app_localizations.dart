import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_az.dart';
import 'app_localizations_en.dart';
import 'app_localizations_ru.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
      : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('az'),
    Locale('en'),
    Locale('ru')
  ];

  /// No description provided for @chooseLanguage.
  ///
  /// In en, this message translates to:
  /// **'Choose your language'**
  String get chooseLanguage;

  /// No description provided for @languageCanChange.
  ///
  /// In en, this message translates to:
  /// **'Interface and report language can be changed separately later.'**
  String get languageCanChange;

  /// No description provided for @continueLabel.
  ///
  /// In en, this message translates to:
  /// **'Continue'**
  String get continueLabel;

  /// No description provided for @changeLanguage.
  ///
  /// In en, this message translates to:
  /// **'Change language'**
  String get changeLanguage;

  /// No description provided for @homeEyebrow.
  ///
  /// In en, this message translates to:
  /// **'Evidence-based car buying'**
  String get homeEyebrow;

  /// No description provided for @homeTitle.
  ///
  /// In en, this message translates to:
  /// **'Know the car before you buy it.'**
  String get homeTitle;

  /// No description provided for @homeSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Technical evidence, your local market, ownership costs, and your real driving conditions in one expert report.'**
  String get homeSubtitle;

  /// No description provided for @checkVehicle.
  ///
  /// In en, this message translates to:
  /// **'Check a vehicle'**
  String get checkVehicle;

  /// No description provided for @checkVehicleDescription.
  ///
  /// In en, this message translates to:
  /// **'Get a personalized purchase analysis.'**
  String get checkVehicleDescription;

  /// No description provided for @compareVehicles.
  ///
  /// In en, this message translates to:
  /// **'Compare vehicles'**
  String get compareVehicles;

  /// No description provided for @compareVehiclesDescription.
  ///
  /// In en, this message translates to:
  /// **'Compare up to three options for the same usage profile.'**
  String get compareVehiclesDescription;

  /// No description provided for @myReports.
  ///
  /// In en, this message translates to:
  /// **'My reports'**
  String get myReports;

  /// No description provided for @myReportsDescription.
  ///
  /// In en, this message translates to:
  /// **'Open purchased reports without generating them again.'**
  String get myReportsDescription;

  /// No description provided for @vinInputTitle.
  ///
  /// In en, this message translates to:
  /// **'Check a specific vehicle'**
  String get vinInputTitle;

  /// No description provided for @vinInputDescription.
  ///
  /// In en, this message translates to:
  /// **'Enter the 17-character VIN. The preliminary check shows only confirmed information.'**
  String get vinInputDescription;

  /// No description provided for @vinInvalid.
  ///
  /// In en, this message translates to:
  /// **'Check the VIN and its check digit'**
  String get vinInvalid;

  /// No description provided for @vinStartCheck.
  ///
  /// In en, this message translates to:
  /// **'Check VIN'**
  String get vinStartCheck;

  /// No description provided for @vinPreviewTitle.
  ///
  /// In en, this message translates to:
  /// **'Preliminary check'**
  String get vinPreviewTitle;

  /// No description provided for @vinAuctions.
  ///
  /// In en, this message translates to:
  /// **'Auction records'**
  String get vinAuctions;

  /// No description provided for @vinDamage.
  ///
  /// In en, this message translates to:
  /// **'Damage records'**
  String get vinDamage;

  /// No description provided for @vinOdometer.
  ///
  /// In en, this message translates to:
  /// **'Mileage events'**
  String get vinOdometer;

  /// No description provided for @vinTitleRecords.
  ///
  /// In en, this message translates to:
  /// **'Title records'**
  String get vinTitleRecords;

  /// No description provided for @vinTheft.
  ///
  /// In en, this message translates to:
  /// **'Theft records'**
  String get vinTheft;

  /// No description provided for @vinRegistration.
  ///
  /// In en, this message translates to:
  /// **'Registration events'**
  String get vinRegistration;

  /// No description provided for @vinSales.
  ///
  /// In en, this message translates to:
  /// **'Sales history'**
  String get vinSales;

  /// No description provided for @vinPhotoCount.
  ///
  /// In en, this message translates to:
  /// **'Confirmed photos'**
  String get vinPhotoCount;

  /// No description provided for @vinOdometerEventCount.
  ///
  /// In en, this message translates to:
  /// **'Confirmed mileage events'**
  String get vinOdometerEventCount;

  /// No description provided for @vinCoverageAfterRequest.
  ///
  /// In en, this message translates to:
  /// **'Specific record availability is determined after the provider request.'**
  String get vinCoverageAfterRequest;

  /// No description provided for @vinPrice.
  ///
  /// In en, this message translates to:
  /// **'Report price'**
  String get vinPrice;

  /// No description provided for @vinMockPayment.
  ///
  /// In en, this message translates to:
  /// **'Test payment and report'**
  String get vinMockPayment;

  /// No description provided for @vinNoRealCharge.
  ///
  /// In en, this message translates to:
  /// **'Test mode: no money is charged.'**
  String get vinNoRealCharge;

  /// No description provided for @vinPurchaseUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Report purchase is currently unavailable.'**
  String get vinPurchaseUnavailable;

  /// No description provided for @vinOpenReport.
  ///
  /// In en, this message translates to:
  /// **'Open report'**
  String get vinOpenReport;

  /// No description provided for @vinReportTitle.
  ///
  /// In en, this message translates to:
  /// **'Vehicle history'**
  String get vinReportTitle;

  /// No description provided for @vinMileageAnomaly.
  ///
  /// In en, this message translates to:
  /// **'An anomaly in the mileage sequence was found. Review the source records.'**
  String get vinMileageAnomaly;

  /// No description provided for @vinPhotos.
  ///
  /// In en, this message translates to:
  /// **'Event photos'**
  String get vinPhotos;

  /// No description provided for @vinEvidenceNotice.
  ///
  /// In en, this message translates to:
  /// **'Conclusions are limited by source records and coverage at report time.'**
  String get vinEvidenceNotice;

  /// No description provided for @vinRequestFailed.
  ///
  /// In en, this message translates to:
  /// **'The request could not be completed. Try again; a saved report can be opened later.'**
  String get vinRequestFailed;

  /// No description provided for @vinProcessing.
  ///
  /// In en, this message translates to:
  /// **'The report is being prepared. Check its status later; no second payment is needed.'**
  String get vinProcessing;

  /// No description provided for @vinPaymentRecovery.
  ///
  /// In en, this message translates to:
  /// **'Payment was recorded but the report is not ready. Its status is saved for recovery or refund.'**
  String get vinPaymentRecovery;

  /// No description provided for @vinRefreshStatus.
  ///
  /// In en, this message translates to:
  /// **'Refresh status'**
  String get vinRefreshStatus;

  /// No description provided for @vinRetryReport.
  ///
  /// In en, this message translates to:
  /// **'Retry report request'**
  String get vinRetryReport;

  /// No description provided for @vinDemoNotice.
  ///
  /// In en, this message translates to:
  /// **'This is an isolated demonstration with fixture data. Live providers and payments are not connected.'**
  String get vinDemoNotice;

  /// No description provided for @vinDemoOnly.
  ///
  /// In en, this message translates to:
  /// **'Only VIN 3FA6P0HD0KR114795 is available in this test scenario'**
  String get vinDemoOnly;

  /// No description provided for @vinRetailPhoto.
  ///
  /// In en, this message translates to:
  /// **'Listing photo'**
  String get vinRetailPhoto;

  /// No description provided for @vinWholesalePhoto.
  ///
  /// In en, this message translates to:
  /// **'Auction photo'**
  String get vinWholesalePhoto;

  /// No description provided for @vinHistoricalPhoto.
  ///
  /// In en, this message translates to:
  /// **'Historical photo'**
  String get vinHistoricalPhoto;

  /// No description provided for @vinSource.
  ///
  /// In en, this message translates to:
  /// **'Source'**
  String get vinSource;

  /// No description provided for @vinDemoSource.
  ///
  /// In en, this message translates to:
  /// **'Test source'**
  String get vinDemoSource;

  /// No description provided for @navHome.
  ///
  /// In en, this message translates to:
  /// **'Home'**
  String get navHome;

  /// No description provided for @navCompare.
  ///
  /// In en, this message translates to:
  /// **'Compare'**
  String get navCompare;

  /// No description provided for @navCheck.
  ///
  /// In en, this message translates to:
  /// **'Check'**
  String get navCheck;

  /// No description provided for @navReports.
  ///
  /// In en, this message translates to:
  /// **'Reports'**
  String get navReports;

  /// No description provided for @buyCarTitle.
  ///
  /// In en, this message translates to:
  /// **'I want to buy a car'**
  String get buyCarTitle;

  /// No description provided for @buyCarSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Find a fit for your budget, market and priorities.'**
  String get buyCarSubtitle;

  /// No description provided for @buyCarCta.
  ///
  /// In en, this message translates to:
  /// **'Start choosing'**
  String get buyCarCta;

  /// No description provided for @checkCarTitle.
  ///
  /// In en, this message translates to:
  /// **'Check a specific car'**
  String get checkCarTitle;

  /// No description provided for @checkCarSubtitle.
  ///
  /// In en, this message translates to:
  /// **'VIN, listing or your details. Compare only what is supported.'**
  String get checkCarSubtitle;

  /// No description provided for @checkCarCta.
  ///
  /// In en, this message translates to:
  /// **'Check a car'**
  String get checkCarCta;

  /// No description provided for @battleTitle.
  ///
  /// In en, this message translates to:
  /// **'Generation battle'**
  String get battleTitle;

  /// No description provided for @battleAll.
  ///
  /// In en, this message translates to:
  /// **'All comparisons'**
  String get battleAll;

  /// No description provided for @battleSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Popular comparisons. Evidence over guesses.'**
  String get battleSubtitle;

  /// No description provided for @battleFirst.
  ///
  /// In en, this message translates to:
  /// **'Mercedes W210 vs a new Chinese car'**
  String get battleFirst;

  /// No description provided for @battleSecond.
  ///
  /// In en, this message translates to:
  /// **'Passat B7 vs Hyundai Elantra'**
  String get battleSecond;

  /// No description provided for @checkTabTurbo.
  ///
  /// In en, this message translates to:
  /// **'Turbo.az link'**
  String get checkTabTurbo;

  /// No description provided for @checkTabManual.
  ///
  /// In en, this message translates to:
  /// **'Enter manually'**
  String get checkTabManual;

  /// No description provided for @listingResultTitle.
  ///
  /// In en, this message translates to:
  /// **'Listing'**
  String get listingResultTitle;

  /// No description provided for @listingOwnInput.
  ///
  /// In en, this message translates to:
  /// **'Your details'**
  String get listingOwnInput;

  /// No description provided for @listingOpenOriginal.
  ///
  /// In en, this message translates to:
  /// **'Open original'**
  String get listingOpenOriginal;

  /// No description provided for @listingSellerClaims.
  ///
  /// In en, this message translates to:
  /// **'Listed by seller'**
  String get listingSellerClaims;

  /// No description provided for @listingEngine.
  ///
  /// In en, this message translates to:
  /// **'Engine'**
  String get listingEngine;

  /// No description provided for @listingFuel.
  ///
  /// In en, this message translates to:
  /// **'Fuel'**
  String get listingFuel;

  /// No description provided for @listingTransmission.
  ///
  /// In en, this message translates to:
  /// **'Transmission'**
  String get listingTransmission;

  /// No description provided for @listingDrivetrain.
  ///
  /// In en, this message translates to:
  /// **'Drive'**
  String get listingDrivetrain;

  /// No description provided for @listingBody.
  ///
  /// In en, this message translates to:
  /// **'Body'**
  String get listingBody;

  /// No description provided for @listingMarket.
  ///
  /// In en, this message translates to:
  /// **'Market'**
  String get listingMarket;

  /// No description provided for @listingColor.
  ///
  /// In en, this message translates to:
  /// **'Color'**
  String get listingColor;

  /// No description provided for @listingSellerType.
  ///
  /// In en, this message translates to:
  /// **'Seller'**
  String get listingSellerType;

  /// No description provided for @listingMatchTitle.
  ///
  /// In en, this message translates to:
  /// **'Auto Expert match'**
  String get listingMatchTitle;

  /// No description provided for @listingExact.
  ///
  /// In en, this message translates to:
  /// **'This version agrees with a confirmed Auto Expert configuration.'**
  String get listingExact;

  /// No description provided for @listingMultiple.
  ///
  /// In en, this message translates to:
  /// **'Several versions fit this description. Clarify one detail before choosing.'**
  String get listingMultiple;

  /// No description provided for @listingConflict.
  ///
  /// In en, this message translates to:
  /// **'Some listing details differ from confirmed versions. Check the VIN or vehicle documents.'**
  String get listingConflict;

  /// No description provided for @listingOutOfScope.
  ///
  /// In en, this message translates to:
  /// **'Check vehicle by VIN'**
  String get listingOutOfScope;

  /// No description provided for @listingNoMatch.
  ///
  /// In en, this message translates to:
  /// **'Check the model spelling or add details. VIN history can still be checked.'**
  String get listingNoMatch;

  /// No description provided for @listingClaimed.
  ///
  /// In en, this message translates to:
  /// **'Listing says'**
  String get listingClaimed;

  /// No description provided for @listingCatalogValue.
  ///
  /// In en, this message translates to:
  /// **'Catalog confirms'**
  String get listingCatalogValue;

  /// No description provided for @listingCheckVin.
  ///
  /// In en, this message translates to:
  /// **'Check history by VIN'**
  String get listingCheckVin;

  /// No description provided for @listingAddVin.
  ///
  /// In en, this message translates to:
  /// **'Add VIN and check history'**
  String get listingAddVin;

  /// No description provided for @listingAddCompare.
  ///
  /// In en, this message translates to:
  /// **'Add to comparison'**
  String get listingAddCompare;

  /// No description provided for @listingManualTitle.
  ///
  /// In en, this message translates to:
  /// **'Enter vehicle details'**
  String get listingManualTitle;

  /// No description provided for @listingUrlTitle.
  ///
  /// In en, this message translates to:
  /// **'Turbo.az link'**
  String get listingUrlTitle;

  /// No description provided for @listingManualSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Enter the seller\'s details. They stay separate from confirmed technical facts.'**
  String get listingManualSubtitle;

  /// No description provided for @listingUrlSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Add one listing. The link is a reference; the app does not download the page.'**
  String get listingUrlSubtitle;

  /// No description provided for @listingInvalidUrl.
  ///
  /// In en, this message translates to:
  /// **'Enter a safe https://turbo.az link to one listing.'**
  String get listingInvalidUrl;

  /// No description provided for @listingEnterUrl.
  ///
  /// In en, this message translates to:
  /// **'Paste the Turbo.az link.'**
  String get listingEnterUrl;

  /// No description provided for @listingEnterContent.
  ///
  /// In en, this message translates to:
  /// **'Paste listing text or choose a local file.'**
  String get listingEnterContent;

  /// No description provided for @listingTooLarge.
  ///
  /// In en, this message translates to:
  /// **'The file or text exceeds the size limit.'**
  String get listingTooLarge;

  /// No description provided for @listingRequestFailed.
  ///
  /// In en, this message translates to:
  /// **'The listing could not be processed. Check the input and try again.'**
  String get listingRequestFailed;

  /// No description provided for @listingFileFailed.
  ///
  /// In en, this message translates to:
  /// **'Could not read the file. Choose a UTF-8 .html or .txt file.'**
  String get listingFileFailed;

  /// No description provided for @listingNeedMakeModel.
  ///
  /// In en, this message translates to:
  /// **'Enter make and model.'**
  String get listingNeedMakeModel;

  /// No description provided for @listingUrlLabel.
  ///
  /// In en, this message translates to:
  /// **'Listing link'**
  String get listingUrlLabel;

  /// No description provided for @listingAddLink.
  ///
  /// In en, this message translates to:
  /// **'Save link'**
  String get listingAddLink;

  /// No description provided for @listingReferenceOnly.
  ///
  /// In en, this message translates to:
  /// **'The link is saved as a reference. To match the car, paste text, choose a saved page, or fill the fields manually.'**
  String get listingReferenceOnly;

  /// No description provided for @listingText.
  ///
  /// In en, this message translates to:
  /// **'Text'**
  String get listingText;

  /// No description provided for @listingHtml.
  ///
  /// In en, this message translates to:
  /// **'HTML'**
  String get listingHtml;

  /// No description provided for @listingTextLabel.
  ///
  /// In en, this message translates to:
  /// **'Paste listing text'**
  String get listingTextLabel;

  /// No description provided for @listingHtmlLabel.
  ///
  /// In en, this message translates to:
  /// **'Paste saved page HTML'**
  String get listingHtmlLabel;

  /// No description provided for @listingChooseFile.
  ///
  /// In en, this message translates to:
  /// **'Choose saved page'**
  String get listingChooseFile;

  /// No description provided for @listingAnalyze.
  ///
  /// In en, this message translates to:
  /// **'Match listing'**
  String get listingAnalyze;

  /// No description provided for @listingMake.
  ///
  /// In en, this message translates to:
  /// **'Make'**
  String get listingMake;

  /// No description provided for @listingModel.
  ///
  /// In en, this message translates to:
  /// **'Model'**
  String get listingModel;

  /// No description provided for @listingYear.
  ///
  /// In en, this message translates to:
  /// **'Year'**
  String get listingYear;

  /// No description provided for @listingPrice.
  ///
  /// In en, this message translates to:
  /// **'Price'**
  String get listingPrice;

  /// No description provided for @listingCurrency.
  ///
  /// In en, this message translates to:
  /// **'Currency'**
  String get listingCurrency;

  /// No description provided for @listingMileage.
  ///
  /// In en, this message translates to:
  /// **'Mileage'**
  String get listingMileage;

  /// No description provided for @listingMileageUnit.
  ///
  /// In en, this message translates to:
  /// **'Mileage unit'**
  String get listingMileageUnit;

  /// No description provided for @listingMoreFields.
  ///
  /// In en, this message translates to:
  /// **'Additional details'**
  String get listingMoreFields;

  /// No description provided for @listingCity.
  ///
  /// In en, this message translates to:
  /// **'City'**
  String get listingCity;

  /// No description provided for @listingOwners.
  ///
  /// In en, this message translates to:
  /// **'Owners (seller claim)'**
  String get listingOwners;

  /// No description provided for @listingCondition.
  ///
  /// In en, this message translates to:
  /// **'Condition (seller claim)'**
  String get listingCondition;

  /// No description provided for @listingDescription.
  ///
  /// In en, this message translates to:
  /// **'Seller description'**
  String get listingDescription;

  /// No description provided for @buyerTitle.
  ///
  /// In en, this message translates to:
  /// **'Find a car'**
  String get buyerTitle;

  /// No description provided for @buyerStepParameters.
  ///
  /// In en, this message translates to:
  /// **'Parameters'**
  String get buyerStepParameters;

  /// No description provided for @buyerStepResults.
  ///
  /// In en, this message translates to:
  /// **'Results'**
  String get buyerStepResults;

  /// No description provided for @buyerHeading.
  ///
  /// In en, this message translates to:
  /// **'Find a car for you'**
  String get buyerHeading;

  /// No description provided for @buyerSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Choose what matters to see confirmed versions and checks to make.'**
  String get buyerSubtitle;

  /// No description provided for @buyerQuery.
  ///
  /// In en, this message translates to:
  /// **'Make or model'**
  String get buyerQuery;

  /// No description provided for @buyerBudget.
  ///
  /// In en, this message translates to:
  /// **'Budget AZN'**
  String get buyerBudget;

  /// No description provided for @buyerYearFrom.
  ///
  /// In en, this message translates to:
  /// **'Year from'**
  String get buyerYearFrom;

  /// No description provided for @buyerYearTo.
  ///
  /// In en, this message translates to:
  /// **'Year to'**
  String get buyerYearTo;

  /// No description provided for @buyerMarket.
  ///
  /// In en, this message translates to:
  /// **'Original market'**
  String get buyerMarket;

  /// No description provided for @buyerBody.
  ///
  /// In en, this message translates to:
  /// **'Body'**
  String get buyerBody;

  /// No description provided for @buyerSedan.
  ///
  /// In en, this message translates to:
  /// **'Sedan'**
  String get buyerSedan;

  /// No description provided for @buyerCrossover.
  ///
  /// In en, this message translates to:
  /// **'Crossover'**
  String get buyerCrossover;

  /// No description provided for @buyerHatchback.
  ///
  /// In en, this message translates to:
  /// **'Hatchback'**
  String get buyerHatchback;

  /// No description provided for @buyerEngine.
  ///
  /// In en, this message translates to:
  /// **'Engine type'**
  String get buyerEngine;

  /// No description provided for @buyerAny.
  ///
  /// In en, this message translates to:
  /// **'Any'**
  String get buyerAny;

  /// No description provided for @buyerGasolineNa.
  ///
  /// In en, this message translates to:
  /// **'Gasoline non-turbo'**
  String get buyerGasolineNa;

  /// No description provided for @buyerGasolineTurbo.
  ///
  /// In en, this message translates to:
  /// **'Gasoline turbo'**
  String get buyerGasolineTurbo;

  /// No description provided for @buyerDiesel.
  ///
  /// In en, this message translates to:
  /// **'Diesel'**
  String get buyerDiesel;

  /// No description provided for @buyerHybrid.
  ///
  /// In en, this message translates to:
  /// **'Hybrid'**
  String get buyerHybrid;

  /// No description provided for @buyerElectric.
  ///
  /// In en, this message translates to:
  /// **'Electric'**
  String get buyerElectric;

  /// No description provided for @buyerGearbox.
  ///
  /// In en, this message translates to:
  /// **'Transmission'**
  String get buyerGearbox;

  /// No description provided for @buyerAt.
  ///
  /// In en, this message translates to:
  /// **'Automatic AT'**
  String get buyerAt;

  /// No description provided for @buyerCvt.
  ///
  /// In en, this message translates to:
  /// **'CVT'**
  String get buyerCvt;

  /// No description provided for @buyerDct.
  ///
  /// In en, this message translates to:
  /// **'DCT'**
  String get buyerDct;

  /// No description provided for @buyerManual.
  ///
  /// In en, this message translates to:
  /// **'Manual'**
  String get buyerManual;

  /// No description provided for @buyerShowMatches.
  ///
  /// In en, this message translates to:
  /// **'Show matching cars'**
  String get buyerShowMatches;

  /// No description provided for @buyerSearchFailed.
  ///
  /// In en, this message translates to:
  /// **'Search failed. Try again.'**
  String get buyerSearchFailed;

  /// No description provided for @buyerResultsTitle.
  ///
  /// In en, this message translates to:
  /// **'Matching options'**
  String get buyerResultsTitle;

  /// No description provided for @buyerTopLabel.
  ///
  /// In en, this message translates to:
  /// **'Closest to your request'**
  String get buyerTopLabel;

  /// No description provided for @buyerCompetitors.
  ///
  /// In en, this message translates to:
  /// **'Other matching models'**
  String get buyerCompetitors;

  /// No description provided for @buyerNeedsConfirmation.
  ///
  /// In en, this message translates to:
  /// **'Options that need confirmation for your selected criteria'**
  String get buyerNeedsConfirmation;

  /// No description provided for @buyerNoResults.
  ///
  /// In en, this message translates to:
  /// **'Try changing one selected parameter.'**
  String get buyerNoResults;

  /// No description provided for @buyerOpenProfile.
  ///
  /// In en, this message translates to:
  /// **'Open profile'**
  String get buyerOpenProfile;

  /// No description provided for @profileTitle.
  ///
  /// In en, this message translates to:
  /// **'Vehicle profile'**
  String get profileTitle;

  /// No description provided for @profileLoadFailed.
  ///
  /// In en, this message translates to:
  /// **'Could not open profile. Try again.'**
  String get profileLoadFailed;

  /// No description provided for @profileEngineOil.
  ///
  /// In en, this message translates to:
  /// **'Engine oil'**
  String get profileEngineOil;

  /// No description provided for @profileInspectionAdvice.
  ///
  /// In en, this message translates to:
  /// **'Before buying, verify VIN and documents, inspect the body, cold start, electronics, test drive and service history.'**
  String get profileInspectionAdvice;

  /// No description provided for @compareTitle.
  ///
  /// In en, this message translates to:
  /// **'Generation battle'**
  String get compareTitle;

  /// No description provided for @compareChoose.
  ///
  /// In en, this message translates to:
  /// **'Choose two confirmed versions to compare.'**
  String get compareChoose;

  /// No description provided for @compareAdd.
  ///
  /// In en, this message translates to:
  /// **'Add a vehicle'**
  String get compareAdd;

  /// No description provided for @compareRun.
  ///
  /// In en, this message translates to:
  /// **'Compare selected'**
  String get compareRun;

  /// No description provided for @compareFailed.
  ///
  /// In en, this message translates to:
  /// **'Comparison failed. Try again.'**
  String get compareFailed;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['az', 'en', 'ru'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'az':
      return AppLocalizationsAz();
    case 'en':
      return AppLocalizationsEn();
    case 'ru':
      return AppLocalizationsRu();
  }

  throw FlutterError(
      'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
      'an issue with the localizations generation tool. Please file an issue '
      'on GitHub with a reproducible sample app and the gen-l10n configuration '
      'that was used.');
}
