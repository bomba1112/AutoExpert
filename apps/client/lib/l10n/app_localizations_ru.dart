// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Russian (`ru`).
class AppLocalizationsRu extends AppLocalizations {
  AppLocalizationsRu([String locale = 'ru']) : super(locale);

  @override
  String get chooseLanguage => 'Выберите язык';

  @override
  String get languageCanChange =>
      'Язык интерфейса и отчёта позже можно менять отдельно.';

  @override
  String get continueLabel => 'Продолжить';

  @override
  String get changeLanguage => 'Изменить язык';

  @override
  String get homeEyebrow => 'Покупка автомобиля на основе фактов';

  @override
  String get homeTitle => 'Твой честный автоэксперт без предвзятости';

  @override
  String get homeSubtitle =>
      'Реальные данные. Экспертный анализ. Для правильного выбора.';

  @override
  String get checkVehicle => 'Проверить автомобиль';

  @override
  String get checkVehicleDescription =>
      'Получить персональный анализ перед покупкой.';

  @override
  String get compareVehicles => 'Сравнить автомобили';

  @override
  String get compareVehiclesDescription =>
      'Сравнить до трёх вариантов под одинаковые условия.';

  @override
  String get myReports => 'Мои отчёты';

  @override
  String get myReportsDescription =>
      'Открыть купленные отчёты без повторной генерации.';

  @override
  String get vinInputTitle => 'Проверить конкретный автомобиль';

  @override
  String get vinInputDescription =>
      'Введите VIN из 17 символов. Предварительная проверка покажет только подтверждённые сведения.';

  @override
  String get vinInvalid => 'Проверьте VIN и его контрольную цифру';

  @override
  String get vinStartCheck => 'Проверить VIN';

  @override
  String get vinPreviewTitle => 'Предварительная проверка';

  @override
  String get vinAuctions => 'Аукционные записи';

  @override
  String get vinDamage => 'Сведения о повреждениях';

  @override
  String get vinOdometer => 'События пробега';

  @override
  String get vinTitleRecords => 'Записи о статусе собственности';

  @override
  String get vinTheft => 'Записи об угоне';

  @override
  String get vinRegistration => 'Регистрационные события';

  @override
  String get vinSales => 'История продаж';

  @override
  String get vinPhotoCount => 'Подтверждено фотографий';

  @override
  String get vinOdometerEventCount => 'Подтверждено событий пробега';

  @override
  String get vinCoverageAfterRequest =>
      'Состав конкретных записей определяется после запроса провайдера.';

  @override
  String get vinPrice => 'Стоимость отчёта';

  @override
  String get vinMockPayment => 'Тестовая оплата и отчёт';

  @override
  String get vinNoRealCharge => 'Тестовый режим: деньги не списываются.';

  @override
  String get vinPurchaseUnavailable => 'Покупка отчёта сейчас недоступна.';

  @override
  String get vinOpenReport => 'Открыть отчёт';

  @override
  String get vinReportTitle => 'История автомобиля';

  @override
  String get vinMileageAnomaly =>
      'Обнаружена аномалия последовательности пробега. Проверьте исходные записи.';

  @override
  String get vinPhotos => 'Фотографии событий';

  @override
  String get vinEvidenceNotice =>
      'Выводы ограничены записями и покрытием источника на дату отчёта.';

  @override
  String get vinRequestFailed =>
      'Не удалось завершить запрос. Повторите попытку; сохранённый отчёт можно открыть позже.';

  @override
  String get vinProcessing =>
      'Отчёт обрабатывается. Проверьте состояние позже — повторной оплаты не требуется.';

  @override
  String get vinPaymentRecovery =>
      'Оплата зарегистрирована, но отчёт не готов. Состояние сохранено для восстановления или возврата.';

  @override
  String get vinRefreshStatus => 'Обновить состояние';

  @override
  String get vinRetryReport => 'Повторить получение отчёта';

  @override
  String get vinDemoNotice =>
      'Это изолированная демонстрация на тестовых данных. Реальные провайдеры и списания не подключены.';

  @override
  String get vinDemoOnly =>
      'В этом тестовом сценарии доступен только VIN 3FA6P0HD0KR114795';

  @override
  String get vinRetailPhoto => 'Фотография объявления';

  @override
  String get vinWholesalePhoto => 'Аукционная фотография';

  @override
  String get vinHistoricalPhoto => 'Историческая фотография';

  @override
  String get vinSource => 'Источник';

  @override
  String get vinDemoSource => 'Тестовый источник';

  @override
  String get navHome => 'Главная';

  @override
  String get navCompare => 'Сравнения';

  @override
  String get navCheck => 'Проверить';

  @override
  String get navReports => 'Мои отчёты';

  @override
  String get buyCarTitle => 'Хочу приобрести машину';

  @override
  String get buyCarSubtitle =>
      'Подберём по бюджету, рынку, условиям и приоритетам.';

  @override
  String get buyCarCta => 'Начать подбор';

  @override
  String get checkCarTitle => 'Проверить конкретную машину';

  @override
  String get checkCarSubtitle =>
      'VIN, объявление или ваши данные. Сверим то, что действительно известно.';

  @override
  String get checkCarCta => 'Проверить авто';

  @override
  String get battleTitle => 'Битва поколений';

  @override
  String get battleAll => 'Все сравнения';

  @override
  String get battleSubtitle => 'Популярные споры. Честный разбор без фантазии.';

  @override
  String get battleFirst => 'Mercedes W210 vs новый китаец';

  @override
  String get battleSecond => 'Passat B7 vs Hyundai Elantra';

  @override
  String get checkTabTurbo => 'Turbo.az';

  @override
  String get checkTabManual => 'Вручную';

  @override
  String get listingResultTitle => 'Объявление';

  @override
  String get listingOwnInput => 'Ваши сведения';

  @override
  String get listingOpenOriginal => 'Открыть оригинал';

  @override
  String get listingSellerClaims => 'Указано в объявлении';

  @override
  String get listingEngine => 'Двигатель';

  @override
  String get listingFuel => 'Топливо';

  @override
  String get listingTransmission => 'Коробка';

  @override
  String get listingDrivetrain => 'Привод';

  @override
  String get listingBody => 'Кузов';

  @override
  String get listingMarket => 'Рынок';

  @override
  String get listingColor => 'Цвет';

  @override
  String get listingSellerType => 'Продавец';

  @override
  String get listingMatchTitle => 'Сопоставление Auto Expert';

  @override
  String get listingExact =>
      'Эта версия согласуется с подтверждённой конфигурацией Auto Expert.';

  @override
  String get listingMultiple =>
      'Под описание подходят несколько версий. Уточните одну деталь перед выбором.';

  @override
  String get listingConflict =>
      'Некоторые сведения объявления расходятся с подтверждёнными версиями. Проверьте VIN или документы автомобиля.';

  @override
  String get listingOutOfScope => 'Проверить автомобиль по VIN';

  @override
  String get listingNoMatch =>
      'Проверьте написание модели или добавьте параметры. Проверку истории по VIN можно продолжить.';

  @override
  String get listingClaimed => 'В объявлении';

  @override
  String get listingCatalogValue => 'В каталоге подтверждено';

  @override
  String get listingCheckVin => 'Проверить историю по VIN';

  @override
  String get listingAddVin => 'Добавить VIN и проверить историю';

  @override
  String get listingAddCompare => 'Добавить к сравнению';

  @override
  String get listingManualTitle => 'Введите данные автомобиля';

  @override
  String get listingUrlTitle => 'Ссылка Turbo.az';

  @override
  String get listingManualSubtitle =>
      'Заполните то, что указано продавцом. Мы сохраним это как заявление, отдельно от подтверждённых технических данных.';

  @override
  String get listingUrlSubtitle =>
      'Добавьте одно объявление. Ссылка служит ориентиром; страницу приложение не загружает.';

  @override
  String get listingInvalidUrl =>
      'Введите безопасную ссылку https://turbo.az на одно объявление.';

  @override
  String get listingEnterUrl => 'Вставьте ссылку Turbo.az.';

  @override
  String get listingEnterContent =>
      'Вставьте текст объявления или выберите локальный файл.';

  @override
  String get listingTooLarge => 'Файл или текст превышает допустимый размер.';

  @override
  String get listingRequestFailed =>
      'Не удалось обработать материалы объявления. Проверьте ввод и повторите попытку.';

  @override
  String get listingFileFailed =>
      'Не удалось прочитать файл. Выберите .html или .txt в UTF-8.';

  @override
  String get listingNeedMakeModel => 'Укажите марку и модель.';

  @override
  String get listingUrlLabel => 'Ссылка на объявление';

  @override
  String get listingAddLink => 'Сохранить ссылку';

  @override
  String get listingReferenceOnly =>
      'Ссылка сохранена как источник. Для сопоставления вставьте текст, выберите сохранённую страницу или заполните поля вручную.';

  @override
  String get listingText => 'Текст';

  @override
  String get listingHtml => 'HTML';

  @override
  String get listingTextLabel => 'Вставьте текст объявления';

  @override
  String get listingHtmlLabel => 'Вставьте HTML сохранённой страницы';

  @override
  String get listingChooseFile => 'Выбрать сохранённую страницу';

  @override
  String get listingAnalyze => 'Сопоставить объявление';

  @override
  String get listingMake => 'Марка';

  @override
  String get listingModel => 'Модель';

  @override
  String get listingYear => 'Год';

  @override
  String get listingPrice => 'Цена';

  @override
  String get listingCurrency => 'Валюта';

  @override
  String get listingMileage => 'Пробег';

  @override
  String get listingMileageUnit => 'Единица пробега';

  @override
  String get listingMoreFields => 'Дополнительные сведения';

  @override
  String get listingCity => 'Город';

  @override
  String get listingOwners => 'Владельцы (по объявлению)';

  @override
  String get listingCondition => 'Состояние (по объявлению)';

  @override
  String get listingDescription => 'Описание продавца';

  @override
  String get buyerTitle => 'Подбор машины';

  @override
  String get buyerStepParameters => 'Параметры';

  @override
  String get buyerStepResults => 'Результаты';

  @override
  String get buyerHeading => 'Подберём машину под вас';

  @override
  String get buyerSubtitle =>
      'Выберите важное — покажем подтверждённые версии и то, что стоит проверить.';

  @override
  String get buyerQuery => 'Марка или модель';

  @override
  String get buyerBudget => 'Бюджет AZN';

  @override
  String get buyerYearFrom => 'Год от';

  @override
  String get buyerYearTo => 'Год до';

  @override
  String get buyerMarket => 'Рынок происхождения';

  @override
  String get buyerBody => 'Кузов';

  @override
  String get buyerSedan => 'Седан';

  @override
  String get buyerCrossover => 'Кроссовер';

  @override
  String get buyerHatchback => 'Хэтчбек';

  @override
  String get buyerEngine => 'Тип двигателя';

  @override
  String get buyerAny => 'Не важно';

  @override
  String get buyerGasolineNa => 'Бензин без турбины';

  @override
  String get buyerGasolineTurbo => 'Бензин турбо';

  @override
  String get buyerDiesel => 'Дизель';

  @override
  String get buyerHybrid => 'Гибрид';

  @override
  String get buyerElectric => 'Электро';

  @override
  String get buyerGearbox => 'Коробка передач';

  @override
  String get buyerAt => 'Обычный автомат AT';

  @override
  String get buyerCvt => 'Вариатор CVT';

  @override
  String get buyerDct => 'Робот DCT';

  @override
  String get buyerManual => 'Механика';

  @override
  String get buyerShowMatches => 'Показать подходящие машины';

  @override
  String get buyerSearchFailed =>
      'Не удалось выполнить подбор. Повторите запрос.';

  @override
  String get buyerResultsTitle => 'Подходящие варианты';

  @override
  String get buyerTopLabel => 'Ближе всего к вашему запросу';

  @override
  String get buyerCompetitors => 'Другие подходящие модели';

  @override
  String get buyerNeedsConfirmation =>
      'Есть варианты, для которых нужно уточнить выбранные условия';

  @override
  String get buyerNoResults =>
      'Попробуйте изменить один из выбранных параметров.';

  @override
  String get buyerOpenProfile => 'Открыть профиль';

  @override
  String get profileTitle => 'Профиль автомобиля';

  @override
  String get profileLoadFailed =>
      'Не удалось открыть профиль. Попробуйте ещё раз.';

  @override
  String get profileEngineOil => 'Моторное масло';

  @override
  String get profileInspectionAdvice =>
      'Перед покупкой сверьте VIN и документы, осмотрите кузов, проверьте холодный запуск, электронику, тест-драйв и сервисную историю.';

  @override
  String get compareTitle => 'Битва поколений';

  @override
  String get compareChoose =>
      'Выберите две подтверждённые версии для сравнения.';

  @override
  String get compareAdd => 'Добавить автомобиль';

  @override
  String get compareRun => 'Сравнить выбранные';

  @override
  String get compareFailed =>
      'Не удалось выполнить сравнение. Повторите попытку.';
}
