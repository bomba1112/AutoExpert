import {EN, pickText} from './en-text.js?v=0.14.0';
import {api} from './api.js?v=0.14.0';
import {localizeTechnicalValue} from './catalog-display.js?v=0.9.1';

// Consumer listing intake deliberately accepts only material supplied by the user.
// The server owns validation, parsing, persistence, and catalog matching.
export function createListingViews({root, state, layout, go, esc, ensureSession, showToast, addCatalogVariant}) {
  const copy = {
    ru: {
      check: 'Проверить конкретную машину', checkShort: 'Проверка', checkSub: 'Начните с VIN, объявления или известных вам параметров.',
      vin: 'VIN', turbo: 'Ссылка Turbo.az', manual: 'Ввести вручную',
      vinLead: 'Проверка по VIN', vinHelp: 'Состав проверки зависит от предварительного ответа источника.', vinQaHelp: 'Для тестового VIN доступен демонстрационный отчёт.',
      vinLabel: 'VIN автомобиля', vinButton: 'Проверить VIN', demoVin: 'Подставить тестовый VIN', vinPlaceholder: 'VIN из 17 символов',
      linkLead: 'Одно объявление Turbo.az', linkHelp: 'Ссылка сохраняется как источник и автоматически не загружается. Для сопоставления вставьте текст объявления, сохранённую HTML-страницу или заполните поля вручную. Массовый сбор и подключение к Turbo.az выключены.',
      sourceUrl: 'Ссылка на объявление', sourcePlaceholder: 'https://turbo.az/autos/12345678',
      content: 'Текст объявления', contentHelp: 'Вставьте описание и основные параметры из объявления. Данные продавца будут показаны отдельно от проверенных характеристик.',
      file: 'Сохранённая HTML-страница', fileHelp: 'Можно загрузить один HTML-файл, который вы сохранили или вправе передать.',
      import: 'Импортировать объявление', manualLead: 'Основные параметры', manualHelp: 'Укажите то, что известно. Пустые поля не будут добавлены в профиль.',
      make: 'Марка', model: 'Модель', year: 'Год', listingId: 'Номер объявления', engine: 'Двигатель / объём', fuel: 'Топливо', transmission: 'Коробка, как указано продавцом',
      drivetrain: 'Привод', body: 'Кузов', market: 'Заявленный рынок происхождения', price: 'Цена', currency: 'Валюта', mileage: 'Пробег', mileage_unit: 'Единица пробега',
      city: 'Город', color: 'Цвет', owners: 'Количество владельцев', condition: 'Состояние', seller_type: 'Тип продавца', description: 'Описание продавца',
      saveManual: 'Сопоставить с каталогом', optional: 'Необязательно',
      listing: 'Профиль объявления', turboBadge: 'Turbo.az · объявление', manualBadge: 'Данные пользователя', original: 'Открыть оригинал',
      seller: 'Указано в объявлении', match: 'Сопоставление Auto Expert',
      claimNote: 'Это сведения из объявления. Характеристики автомобиля подтверждаются отдельно.',
      exact: 'Найдена соответствующая версия в каталоге Auto Expert',
      multiple: 'Подходят несколько версий', conflict: 'Параметры объявления и каталога расходятся',
      out: 'Проверить автомобиль по VIN', noMatch: 'Можно продолжить проверку по VIN или уточнить параметры объявления.',
      conflictSeller: 'В объявлении указано', conflictCatalog: 'Для выбранного года в каталоге Auto Expert подтверждено',
      conflictNext: 'Перед покупкой проверьте VIN или документы автомобиля.',
      question: 'Что уточнить', chooseModel: 'Выбрать модель вручную', moreDetails: 'Добавить сведения',
      withVin: 'Проверить историю по VIN', withoutVin: 'Добавить VIN и проверить историю', addCompare: 'Добавить к сравнению',
      referenceTitle: 'Ссылка сохранена', referenceHelp: 'Автоматической загрузки по ссылке нет. Для сопоставления вставьте текст объявления, загрузите сохранённую страницу или заполните основные поля.',
      submitContent: 'Сопоставить объявление', back: 'Назад',
      invalidUrl: 'Укажите прямую ссылку https://turbo.az на одно объявление.',
      fileTooLarge: 'Файл превышает допустимый размер 256 КБ.', textTooLarge: 'Текст объявления превышает 60 КБ.', fileType: 'Выберите файл .html или .htm.',
      busy: 'Сопоставляем объявление…', submitError: 'Не удалось обработать объявление. Проверьте ссылку или заполненные поля.',
      selected: 'Добавлено к сравнению', comparison: 'Сравнение машин', compareLimit: 'В сравнении может быть до трёх машин.', compareThis: 'Сравнить эту версию',
    },
    az: {
      check: 'Konkret avtomobili yoxlayın', checkShort: 'Yoxlama', checkSub: 'VIN, elan və ya bildiyiniz göstəricilərlə başlayın.',
      vin: 'VIN', turbo: 'Turbo.az keçidi', manual: 'Əllə daxil et',
      vinLead: 'VIN üzrə yoxlama', vinHelp: 'Yoxlamanın məzmunu mənbənin ilkin cavabından asılıdır.', vinQaHelp: 'Test VIN-i üçün nümunə hesabat mövcuddur.',
      vinLabel: 'Avtomobilin VIN kodu', vinButton: 'VIN-i yoxla', demoVin: 'Test VIN-ini daxil et', vinPlaceholder: '17 simvollu VIN',
      linkLead: 'Bir Turbo.az elanı', linkHelp: 'Keçid mənbə kimi saxlanılır və avtomatik yüklənmir. Uyğunlaşdırmaq üçün elan mətnini, saxladığınız HTML səhifəsini daxil edin və ya sahələri əllə doldurun. Kütləvi toplama və Turbo.az bağlantısı söndürülüb.',
      sourceUrl: 'Elanın keçidi', sourcePlaceholder: 'https://turbo.az/autos/12345678',
      content: 'Elanın mətni', contentHelp: 'Təsviri və əsas göstəriciləri daxil edin. Satıcının bildirdikləri yoxlanmış texniki göstəricilərdən ayrı göstəriləcək.',
      file: 'Saxlanmış HTML səhifəsi', fileHelp: 'Saxladığınız və ya təqdim etməyə icazəniz olan bir HTML faylı yükləyə bilərsiniz.',
      import: 'Elanı əlavə et', manualLead: 'Əsas göstəricilər', manualHelp: 'Bildiyiniz məlumatları daxil edin. Boş sahələr profilə əlavə olunmayacaq.',
      make: 'Marka', model: 'Model', year: 'İl', listingId: 'Elan nömrəsi', engine: 'Mühərrik / həcm', fuel: 'Yanacaq', transmission: 'Satıcının göstərdiyi sürətlər qutusu',
      drivetrain: 'Ötürücü', body: 'Kuzov', market: 'Bildirilən ilkin bazar', price: 'Qiymət', currency: 'Valyuta', mileage: 'Yürüş', mileage_unit: 'Yürüş vahidi',
      city: 'Şəhər', color: 'Rəng', owners: 'Sahiblərin sayı', condition: 'Vəziyyət', seller_type: 'Satıcı növü', description: 'Satıcının təsviri',
      saveManual: 'Kataloqla uyğunlaşdır', optional: 'İstəyə görə',
      listing: 'Elanın profili', turboBadge: 'Turbo.az · elan', manualBadge: 'İstifadəçi məlumatları', original: 'Orijinal elanı aç',
      seller: 'Elanda göstərilənlər', match: 'Auto Expert uyğunlaşdırması',
      claimNote: 'Bunlar elanda verilən məlumatlardır. Avtomobilin texniki göstəriciləri ayrıca təsdiqlənir.',
      exact: 'Auto Expert kataloqunda uyğun versiya tapıldı',
      multiple: 'Bir neçə versiya uyğun gəlir', conflict: 'Elan və kataloq göstəriciləri fərqlənir',
      out: 'Avtomobili VIN üzrə yoxla', noMatch: 'VIN üzrə yoxlamaya davam edə və ya elanın göstəricilərini dəqiqləşdirə bilərsiniz.',
      conflictSeller: 'Elanda göstərilib', conflictCatalog: 'Seçilmiş il üçün Auto Expert kataloqunda təsdiqlənib',
      conflictNext: 'Almazdan əvvəl VIN-i və ya avtomobilin sənədlərini yoxlayın.',
      question: 'Nəyi dəqiqləşdirməli', chooseModel: 'Modeli əllə seç', moreDetails: 'Məlumat əlavə et',
      withVin: 'VIN üzrə tarixçəni yoxla', withoutVin: 'VIN əlavə et və tarixçəni yoxla', addCompare: 'Müqayisəyə əlavə et',
      referenceTitle: 'Keçid saxlandı', referenceHelp: 'Keçid üzrə avtomatik yükləmə yoxdur. Uyğunlaşdırmaq üçün elan mətnini daxil edin, saxlanmış səhifəni yükləyin və ya əsas sahələri doldurun.',
      submitContent: 'Elanı uyğunlaşdır', back: 'Geri',
      invalidUrl: 'Bir elana aid https://turbo.az keçidini daxil edin.',
      fileTooLarge: 'Fayl 256 KB limitini aşır.', textTooLarge: 'Elan mətni 60 KB limitini aşır.', fileType: '.html və ya .htm faylı seçin.',
      busy: 'Elan uyğunlaşdırılır…', submitError: 'Elan işlənmədi. Keçidi və ya daxil etdiyiniz məlumatları yoxlayın.',
      selected: 'Müqayisəyə əlavə olundu', comparison: 'Avtomobillərin müqayisəsi', compareLimit: 'Müqayisədə ən çox üç avtomobil ola bilər.', compareThis: 'Bu versiyanı müqayisə et',
    },
  };
  const t = key => (state.language === 'en' ? EN[copy.ru[key]] : copy[state.language][key]) || key;
  const visible = value => value !== null && value !== undefined && String(value).trim() && !['UNKNOWN', 'UNRESOLVED', '—'].includes(String(value).trim().toUpperCase());
  const technicalLabels = {
    GASOLINE:['Бензин','Benzin'], GASOLINE_NA:['Бензин без турбины','Turbosuz benzin'], GASOLINE_TURBO:['Бензин турбо','Turbo benzin'], DIESEL:['Дизель','Dizel'], HEV:['Гибрид','Hibrid'], PHEV:['Заряжаемый гибрид','Şarj olunan hibrid'], BEV:['Электро','Elektrik'],
    AT:['Классический автомат','Klassik avtomat'], CVT:['Вариатор','Variator'], IVT:['Вариатор','Variator'], DCT:['Роботизированная коробка','Robotlaşdırılmış sürətlər qutusu'], MANUAL:['Механика','Mexaniki'], AUTOMATIC_UNSPECIFIED:['Автомат','Avtomat'],
    FWD:['Передний привод','Ön ötürücü'], RWD:['Задний привод','Arxa ötürücü'], AWD:['Полный привод','Tam ötürücü'], '4WD':['Полный привод 4WD','Tam ötürücü 4WD'], PART_TIME_4WD:['Подключаемый полный привод','Qoşulan tam ötürücü'],
    SEDAN:['Седан','Sedan'], HATCHBACK:['Хетчбэк','Hetçbek'], WAGON:['Универсал','Universal'], COUPE:['Купе','Kupe'], SUV:['Внедорожник','Yolsuzluq avtomobili'], CROSSOVER:['Кроссовер','Krossover'], MINIVAN:['Минивэн','Miniven'], PICKUP:['Пикап','Pikap'],
  };
  const catalogValue = value => {
    const label=technicalLabels[String(value).toUpperCase()];
    if(label)return pickText(state.language,label[0],label[1],label[2]);
    return /^[A-Z][A-Z0-9_]+$/.test(String(value))?'':String(value);
  };
  const candidateValue = (candidate,key) => {
    const technicalKey=key==='engine'?'engine_description':key==='transmission'?'transmission_description':key;
    const source=candidate[key] || (key==='engine'?candidate.engine_displacement:key==='transmission'?candidate.transmission_family:'') || '';
    const sourceKey=key==='engine'&&!candidate.engine?'engine_displacement':key==='transmission'&&!candidate.transmission?'transmission_family':technicalKey;
    return localizeTechnicalValue(sourceKey,source,state.language,candidate);
  };
  const conflictValue = (field,value) => field==='engine'&&/^\d+(?:[.,]\d+)?$/.test(String(value))?String(value).replace('.',',')+(pickText(state.language, ' л', ' l', ' L')):localizeTechnicalValue(field==='engine'?'engine_description':field==='transmission'?'transmission_description':field,value,state.language);
  const localizedQuestion = value => String(value).replace(/\b(?:GASOLINE_NA|GASOLINE_TURBO|GASOLINE|DIESEL|HEV|PHEV|BEV|FWD|RWD|AWD|4WD|PART_TIME_4WD|SEDAN|HATCHBACK|WAGON|COUPE|SUV|CROSSOVER|MINIVAN|PICKUP|AT|CVT|IVT|DCT|MANUAL)\b/g,code=>catalogValue(code));
  const safeOriginal = value => {
    if(typeof value!=='string'||value.length>2000||/[\s\u0000-\u001f\u007f]/.test(value))return '';
    try {
      const raw=/^https:\/\/([^/?#]+)([^?#]*)/i.exec(value);
      const u=new URL(value);
      const host=u.hostname.toLowerCase();
      if(!raw||u.protocol!=='https:'||!['turbo.az','www.turbo.az','ru.turbo.az','en.turbo.az'].includes(host)||raw[1].toLowerCase()!==host||u.username||u.password)return '';
      if(!/^\/autos\/[0-9]{4,12}(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?\/?$/i.test(raw[2]))return '';
      return `https://${host}${raw[2].toLowerCase().replace(/\/$/,'')}`;
    } catch {return '';}
  };
  let lastResult = null;
  let selectedTab = 'vin';

  const tabs = () => `<div class="intake-tabs" role="tablist" aria-label="${esc(t('check'))}">${[['vin','vin'],['turbo','turbo'],['manual','manual']].map(([key,label]) => `<button type="button" role="tab" aria-selected="${selectedTab===key}" class="intake-tab ${selectedTab===key?'active':''}" data-listing-tab="${key}">${esc(t(label))}</button>`).join('')}</div>`;
  const field = (name, type='text', required=false, attributes='') => `<label>${esc(t(name))}<input name="${name}" type="${type}" ${required?'required':''} ${attributes}></label>`;
  const manualFields = (sourceUrl='') => `<form id="listing-manual-form" class="intake-form"><input type="hidden" name="source_url" value="${esc(sourceUrl)}"><div class="intake-form-grid">${field('make','text',true,'maxlength="80"')}${field('model','text',true,'maxlength="80"')}${field('year','number',false,'min="1900" max="2100"')}${field('engine')}${field('fuel')}${field('transmission')}${field('drivetrain')}${field('body')}${field('market')}${field('price','number',false,'min="0" step="0.01"')}${field('currency','text',false,'maxlength="3"')}${field('mileage','number',false,'min="0"')}${field('mileage_unit')}${field('city')}${field('color')}${field('owners','number',false,'min="0"')}${field('condition')}${field('seller_type')}${field('vin','text',false,'maxlength="17"')}</div><label>${esc(t('description'))}<textarea name="description" rows="4" maxlength="5000"></textarea></label><button class="button primary full" type="submit">${esc(t('saveManual'))} →</button></form>`;
  function check(tab='vin') {
    selectedTab = ['vin','turbo','manual'].includes(tab) ? tab : 'vin';
    const sample = state.meta?.qa_mode === true ? state.meta?.vin_demo?.sample_vin : null;
    const prefillVin=sessionStorage.getItem('autoexpert.listing.prefill_vin')||'';
    const sourceUrl=selectedTab==='manual'?(sessionStorage.getItem('autoexpert.listing.source_url')||''):'';
    if(selectedTab==='vin')sessionStorage.removeItem('autoexpert.listing.prefill_vin');
    if(selectedTab==='manual')sessionStorage.removeItem('autoexpert.listing.source_url');
    root.innerHTML = layout(`<div class="intake-view"><div class="page-top"><button type="button" class="icon-button" data-listing-action="home" aria-label="${esc(t('back'))}">←</button><strong>${esc(t('checkShort'))}</strong></div><header class="intake-heading"><span class="intake-kicker">AUTO EXPERT</span><h1>${esc(t('check'))}</h1><p>${esc(t('checkSub'))}</p></header>${tabs()}<section class="intake-panel" role="tabpanel">${selectedTab==='vin' ? `<div class="intake-panel-head"><span class="intake-mode-icon">⌕</span><div><h2>${esc(t('vinLead'))}</h2><p>${esc(t('vinHelp'))}${sample?` ${esc(t('vinQaHelp'))}`:''}</p></div></div><form id="vin-form" class="intake-form"><input type="hidden" id="identifier-market" name="market" value="USA"><input type="hidden" id="identifier-type" name="identifier_type" value="VIN"><label>${esc(t('vinLabel'))}<input id="vin" class="vin-input" name="vin" inputmode="text" autocomplete="off" autocapitalize="characters" spellcheck="false" maxlength="17" placeholder="${esc(sample||t('vinPlaceholder'))}" value="${esc(prefillVin)}" required></label>${sample?`<button type="button" class="text-button" data-action="use-demo-vin">${esc(t('demoVin'))}</button>`:''}<button class="button primary full" type="submit">${esc(t('vinButton'))} →</button></form>` : selectedTab==='turbo' ? `<div class="intake-panel-head"><span class="intake-mode-icon">↗</span><div><h2>${esc(t('linkLead'))}</h2><p>${esc(t('linkHelp'))}</p></div></div><form id="listing-import-form" class="intake-form"><label>${esc(t('sourceUrl'))}<input name="source_url" type="url" maxlength="2000" inputmode="url" autocomplete="url" placeholder="${esc(t('sourcePlaceholder'))}"></label><div class="intake-divider"><span>${esc(t('optional'))}</span></div><label>${esc(t('content'))}<textarea name="text" rows="7" maxlength="60000" placeholder="Toyota Camry 2020, 2.5 benzin, avtomat…"></textarea><small>${esc(t('contentHelp'))}</small></label><label class="intake-file">${esc(t('file'))}<input name="html_file" type="file" accept=".html,.htm,text/html"><small>${esc(t('fileHelp'))}</small></label><button class="button primary full" type="submit">${esc(t('import'))} →</button></form>` : `<div class="intake-panel-head"><span class="intake-mode-icon">✎</span><div><h2>${esc(t('manualLead'))}</h2><p>${esc(t('manualHelp'))}</p></div></div>${manualFields(sourceUrl)}`}</section></div>`, {active:'check'});
  }
  const claimLabels = {listing_id:'listingId',engine:'engine',engine_volume:'engine',fuel:'fuel',transmission:'transmission',drivetrain:'drivetrain',body:'body',market:'market',color:'color',owners:'owners',condition:'condition',seller_type:'seller_type',description:'description',vin:'vin'};
  function renderClaims(claims) {
    const seen = new Set();
    return claims.filter(c=>visible(c.raw_value) && claimLabels[c.field_name] && !seen.has(c.field_name) && seen.add(c.field_name)).map(c => `<div><dt>${esc(t(claimLabels[c.field_name]))}</dt><dd>${esc(c.raw_value)}</dd></div>`).join('');
  }
  function claimValue(claims, key) { return claims.find(c=>c.field_name===key && visible(c.raw_value))?.raw_value || ''; }
  function matching(match) {
    if (!match || match.status==='NO_MATCH') return `<div class="matching-state"><p>${esc(t('noMatch'))}</p><button class="text-button" data-listing-action="manual">${esc(t('chooseModel'))} →</button></div>`;
    const candidates = Array.isArray(match.candidates) ? match.candidates : [];
    const cards = candidates.slice(0,3).map(c=>{const specification=['engine','transmission','drivetrain'].map(k=>candidateValue(c,k)).filter(visible).join(' · ');return `<article class="match-candidate"><span class="match-candidate-mark" aria-hidden="true">${match.status==='CLAIM_CONFLICT'?'!':'✓'}</span><div><strong>${esc([c.make,c.model,c.year].filter(visible).join(' '))}</strong>${specification?`<p>${esc(specification)}</p>`:''}<div class="match-specs">${['body','fuel'].map(k=>candidateValue(c,k)).filter(visible).map(value=>`<span>${esc(value)}</span>`).join('')}</div>${match.status==='MULTIPLE_CANDIDATES'&&c.variant_id?`<button class="text-button" data-listing-action="compare" data-variant-id="${esc(c.variant_id)}" data-variant-title="${esc([c.make,c.model,c.year].filter(visible).join(' '))}">${esc(t('compareThis'))} →</button>`:''}</div></article>`;}).join('');
    if (match.status==='EXACT_MATCH') return `<div class="matching-state exact"><h3>${esc(t('exact'))}</h3>${cards}</div>`;
    if (match.status==='MULTIPLE_CANDIDATES') return `<div class="matching-state multiple"><h3>${esc(t('multiple'))}</h3>${cards}${visible(match.question)?`<div class="matching-question"><strong>${esc(t('question'))}</strong><p>${esc(localizedQuestion(match.question))}</p></div>`:''}</div>`;
    if (match.status==='CLAIM_CONFLICT') return `<div class="matching-state conflict"><h3>${esc(t('conflict'))}</h3>${(match.conflicts||[]).map(c=>`<div class="matching-conflict"><span>${esc(t('conflictSeller'))}: <strong>${esc(c.claimed)}</strong></span>${(c.catalog_values||[]).map(v=>conflictValue(c.field_name,v)).filter(visible).length?`<span>${esc(t('conflictCatalog'))}: <strong>${esc(c.catalog_values.map(v=>conflictValue(c.field_name,v)).filter(visible).join(', '))}</strong></span>`:''}</div>`).join('')}<p>${esc(t('conflictNext'))}</p>${cards}</div>`;
    return `<div class="matching-state"><p>${esc(t('noMatch'))}</p></div>`;
  }
  function result(data) {
    lastResult=data;
    const claims=Array.isArray(data.claims)?data.claims:[];
    const c=k=>claimValue(claims,k);
    const title=[c('make'),c('model')].filter(Boolean).join(' ');
    const subtitle=[c('year'),c('city')].filter(Boolean).join(' · ');
    const price=c('price');
    const normalizedVin=claims.find(claim=>claim.field_name==='vin'&&/^[A-HJ-NPR-Z0-9]{17}$/.test(String(claim.normalized_value||'')))?.normalized_value||'';
    const priceDisplay=price && visible(c('currency')) && !/(?:\bAZN\b|₼|\bUSD\b|\$|\bEUR\b|€)/i.test(price)?`${price} ${c('currency')}`:price;
    const mileageDisplay=c('mileage') && visible(c('mileage_unit')) && !/(?:\bkm\b|км|\bmi\b|миль|miles)/i.test(c('mileage'))?`${c('mileage')} ${c('mileage_unit')}`:c('mileage');
    const sellerRows=renderClaims(claims);
    const url=safeOriginal(data.snapshot?.source_url);
    const hasContent=data.next_step!=='PROVIDE_CONTENT';
    const neutralMatch=!['EXACT_MATCH','MULTIPLE_CANDIDATES','CLAIM_CONFLICT'].includes(data.match?.status);
    root.innerHTML=layout(`<div class="intake-view listing-result"><div class="page-top"><button type="button" class="icon-button" data-listing-action="check" aria-label="${esc(t('back'))}">←</button><strong>${esc(t('listing'))}</strong></div><section class="listing-hero"><span class="listing-source">${esc(t(url?'turboBadge':'manualBadge'))}</span><div class="listing-art" aria-hidden="true"><img src="/preview/assets/buyer-road.svg" alt=""></div><div class="listing-hero-content"><h1>${esc(title || (hasContent?t('listing'):t('referenceTitle')))}</h1>${subtitle?`<p>${esc(subtitle)}</p>`:''}${price?`<strong class="listing-price">${esc(priceDisplay)}</strong>`:''}${c('mileage')?`<span class="listing-mileage">${esc(mileageDisplay)}</span>`:''}${url?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer" class="listing-original">${esc(t('original'))} ↗</a>`:''}</div></section>${hasContent ? `${sellerRows?`<section class="listing-card"><div class="listing-section-heading"><span class="listing-section-icon">☷</span><h2>${esc(t('seller'))}</h2></div><p class="listing-section-note">${esc(t('claimNote'))}</p><dl class="listing-claims">${sellerRows}</dl></section>`:''}<section class="listing-card"><div class="listing-section-heading"><span class="listing-section-icon blue">✓</span><h2>${esc(t('match'))}</h2></div>${matching(data.match)}</section><div class="listing-actions"><button class="button primary full" data-listing-action="vin" data-vin="${esc(normalizedVin)}">${esc(t(neutralMatch?'out':normalizedVin?'withVin':'withoutVin'))} →</button>${data.match?.status==='EXACT_MATCH'&&data.match.candidates?.[0]?.variant_id?`<button class="button secondary full" data-listing-action="compare" data-variant-id="${esc(data.match.candidates[0].variant_id)}" data-variant-title="${esc([data.match.candidates[0].make,data.match.candidates[0].model,data.match.candidates[0].year].filter(visible).join(' '))}">${esc(t('addCompare'))}</button>`:'' }</div>` : `<section class="listing-card listing-next"><h2>${esc(t('referenceTitle'))}</h2><p>${esc(t('referenceHelp'))}</p><form id="listing-enrich-form" class="intake-form"><label>${esc(t('content'))}<textarea name="text" rows="7" maxlength="60000"></textarea></label><label class="intake-file">${esc(t('file'))}<input name="html_file" type="file" accept=".html,.htm,text/html"></label><button class="button primary full" type="submit">${esc(t('submitContent'))} →</button></form><button class="text-button" data-listing-action="manual" data-source-url="${esc(url)}">${esc(t('manual'))} →</button></section>`}</div>`,{active:'check'});
  }
  async function loadResult(id) {await ensureSession();const data=await api(`/listings/intake/${encodeURIComponent(id)}`);result(data);}
  async function send(payload) {
    await ensureSession();
    const data=await api('/listings/intake',{method:'POST',body:JSON.stringify({...payload,language:state.language})});
    go(`/listing-result/${encodeURIComponent(data.id)}`);
  }
  async function filePayload(form) {
    const file=form.elements.html_file?.files?.[0];
    if(!file)return null;
    if(!/\.html?$/i.test(file.name) || !['text/html',''].includes(file.type))throw new Error(t('fileType'));
    if(file.size>256000)throw new Error(t('fileTooLarge'));
    return await file.text();
  }
  async function submitImport(form,sourceUrl='') {
    const d=new FormData(form);
    const url=(d.get('source_url')||sourceUrl||'').trim();
    const text=(d.get('text')||'').trim();
    const html=await filePayload(form);
    if(new TextEncoder().encode(text).byteLength>60000)throw new Error(t('textTooLarge'));
    if(url && !safeOriginal(url))throw new Error(t('invalidUrl'));
    if(!url && !text && !html)throw new Error(t('content'));
    await send(html?{input_type:'HTML_SNAPSHOT',source_url:url||undefined,html}:text?{input_type:'TEXT',source_url:url||undefined,text}:{input_type:'URL_REFERENCE',source_url:url});
  }
  root.addEventListener('click',event=>{
    const tab=event.target.closest('[data-listing-tab]');if(tab){event.preventDefault();go('/check/'+tab.dataset.listingTab);return;}
    const target=event.target.closest('[data-listing-action]');if(!target)return;
    event.preventDefault();
    const a=target.dataset.listingAction;
    if(a==='home')go('/home');
    if(a==='check')go(lastResult?.snapshot?.input_type==='MANUAL'?'/check/manual':'/check/turbo');
    if(a==='manual'){sessionStorage.setItem('autoexpert.listing.source_url',target.dataset.sourceUrl||'');go('/check/manual');}
    if(a==='vin'){sessionStorage.setItem('autoexpert.listing.prefill_vin',target.dataset.vin||'');go('/check/vin');}
    if(a==='compare'){
      if(addCatalogVariant?.(target.dataset.variantId,target.dataset.variantTitle)){showToast(t('selected'));go('/compare');}
      else showToast(t('compareLimit'));
    }
  });
  root.addEventListener('submit',event=>{
    const form=event.target;
    if(!['listing-import-form','listing-enrich-form','listing-manual-form'].includes(form.id))return;
    event.preventDefault();
    const button=form.querySelector('[type="submit"]');if(button)button.disabled=true;
    void(async()=>{
      if(form.id==='listing-manual-form'){
        const d=Object.fromEntries(new FormData(form));const url=d.source_url;delete d.source_url;
        const fields=Object.fromEntries(Object.entries(d).filter(([,v])=>visible(v)));
        await send({input_type:'MANUAL',source_url:url||undefined,fields});
      }else await submitImport(form,form.id==='listing-enrich-form'?lastResult?.snapshot?.source_url:'');
    })().catch(error=>showToast(error.message && Object.keys(copy.ru).map(t).includes(error.message)?error.message:t('submitError'))).finally(()=>{if(button)button.disabled=false;});
  });
  return {route(name,id){if(name==='check'||name==='check-legacy'){check(id);return true;}if(name==='manual'){check('manual');return true;}if(name==='listing-result'){return loadResult(id).then(()=>true);}return false;},check,result};
}
