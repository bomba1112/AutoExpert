import {api, downloadReportPdf} from './api.js?v=0.11.0';

// Views of the existing client. Reports, research, auth and PDF use the same API.
export function createBuyerViews({root, state, layout, go, esc, ensureSession, handleError, showToast, startMockVinHistory, mockVinHistoryCards, garageEntrance}) {
  const KEY = 'autoexpert.buyer.v1';
  let saved = {};
  try {saved = JSON.parse(localStorage.getItem(KEY) || '{}');} catch {}
  const basket = saved.basket || [];
  let form = saved.form || {market: 'UNKNOWN'};
  let activeListing = saved.listing || null;
  let parentId = saved.parent || null;
  let currentReport = null;
  const pending = new Set();
  const l = (ru, az, en) => ({ru, az, en}[state.language] || ru);
  const powertrainLabel = value => ({ICE:l('Двигатель внутреннего сгорания','Daxiliyanma mühərriki','Combustion engine'),HEV:l('Гибрид без внешней зарядки','Xaricdən şarj olunmayan hibrid','Non-plug-in hybrid'),PHEV:l('Заряжаемый гибрид','Şarj olunan hibrid','Plug-in hybrid'),BEV:l('Электромобиль','Elektromobil','Battery electric'),MHEV:l('Мягкий гибрид','Yüngül hibrid','Mild hybrid')}[value] || '');
  const marketLabel = value => ({USA:l('США','ABŞ','USA'),UNKNOWN:l('Выберите рынок','Bazarı seçin','Choose a market'),EU:l('Европа','Avropa','Europe'),JAPAN:l('Япония','Yaponiya','Japan'),KOREA:l('Корея','Koreya','Korea')}[value] || value);
  function candidateLabel(c) {
    const raw = c.transmission || '';
    const transmission = /\(AV/i.test(raw) ? l('Бесступенчатая, ручной режим','Pilləsiz, əl rejimi','Continuously variable, select shift') : /variable|cvt/i.test(raw) ? l('Бесступенчатая','Pilləsiz','Continuously variable transmission') : /manual/i.test(raw) ? l('Механическая','Mexaniki','Manual') : c.powertrain_type === 'BEV' ? l('Редуктор','Reduktor','Reduction gear') : /automatic/i.test(raw) ? l('Автоматическая','Avtomatik','Automatic') : '';
    const drive = /front|fwd/i.test(c.drivetrain || '') ? l('Передний привод','Ön ötürücü','Front-wheel drive') : /rear|rwd/i.test(c.drivetrain || '') ? l('Задний привод','Arxa ötürücü','Rear-wheel drive') : /wheel|awd|4wd/i.test(c.drivetrain || '') ? l('Полный привод','Tam ötürücü','All driven wheels') : '';
    const engine = (c.engine || '').match(/^\d+(?:\.\d+)?\s*L/i)?.[0] || '';
    return [c.label.split(' · ')[0],powertrainLabel(c.powertrain_type),engine,transmission,drive].filter(Boolean).join(' · ');
  }
  const save = () => localStorage.setItem(KEY, JSON.stringify({basket, form, listing: activeListing, parent: parentId}));
  const button = (label, action, id = '', style = 'secondary') => `<button class="button ${style}" data-baction="${action}" data-id="${esc(id)}">${esc(label)}</button>`;
  const show = (html, active = '') => {root.innerHTML = layout(`<div class="buyer-view">${html}</div>`, {active});};
  const heading = (title, sub = '') => `<section class="buyer-heading"><h1>${esc(title)}</h1>${sub ? `<p>${esc(sub)}</p>` : ''}</section>`;
  const busy = text => show(`<div class="buyer-progress" role="status"><span class="activity-ring"></span><h2>${esc(text)}</h2><p>${esc(l('Получаем доступные сведения из источников. Это может занять несколько минут.', 'Mənbələrdən mövcud məlumatları alırıq. Bu bir neçə dəqiqə çəkə bilər.', 'Retrieving available source data. This may take a few minutes.'))}</p>${button(l('На главную', 'Ana səhifə', 'Home'), 'home')}</div>`);
  const money = d => d.price ? `${Number(d.price).toLocaleString(state.language)} ${d.currency || ''}` : '—';
  const titleFor = d => [d.year, d.make, d.model].filter(Boolean).join(' ');
  const input = (key, label, type = 'text', attrs = '') => `<label>${esc(label)}<input name="${key}" type="${type}" value="${esc(form[key] || '')}" ${attrs}></label>`;
  const safeUrl = value => {try {const u = new URL(value); return ['https:', 'http:'].includes(u.protocol) ? u.href : '';} catch {return '';}};
  const photo = (p, cls = '') => p && safeUrl(p.url) ? `<figure class="listing-photo ${cls}"><img src="${esc(safeUrl(p.url))}" referrerpolicy="no-referrer" loading="lazy" alt="${esc(l('Фото объявления', 'Elan şəkli', 'Listing photograph'))}"><figcaption>${esc(l('Фото объявления · продавец', 'Elan şəkli · satıcı', 'Listing photo · seller'))}</figcaption></figure>` : '';

  function home() {
    show(heading('Auto Expert', l('Разберитесь в автомобиле до покупки', 'Avtomobili almadan əvvəl tanıyın', 'Understand a car before you buy')) +
      `<div class="buyer-entrances">${[
        [l('Узнать об автомобиле', 'Avtomobil haqqında öyrən', 'Explore a car'), l('Характеристики, сильные и слабые стороны, отзывы', 'Xüsusiyyətlər, üstünlüklər, zəif cəhətlər və rəylər', 'Specifications, strengths, weaknesses and owner reviews'), 'model', '01'],
        [l('Проверить объявление или VIN', 'Elanı və ya VIN-i yoxla', 'Check a listing or VIN'), l('Разбор конкретного предложения', 'Konkret təklifin təhlili', 'Understand a specific offer'), 'offer', '02'],
        [l('Сравнить автомобили', 'Avtomobilləri müqayisə et', 'Compare cars'), l('Выберите между двумя или тремя вариантами', 'İki və ya üç variant arasında seçim edin', 'Choose between two or three options'), 'compare', '03'],
      ].map(([title, sub, action, n]) => `<button class="buyer-entrance" data-baction="${action}"><span class="entrance-number">${n}</span><span><strong>${esc(title)}</strong><small>${esc(sub)}</small></span><span class="entrance-arrow">›</span></button>`).join('')}${garageEntrance ? garageEntrance() : ''}</div>
      <p class="buyer-footnote">${esc(l('VIN необязателен. Начните с автомобиля, который вам интересен.', 'VIN məcburi deyil. Maraqlandığınız avtomobildən başlayın.', 'VIN is optional. Start with the car you are considering.'))}</p>`, 'home');
  }

  function model() {
    show(heading(l('Какой автомобиль вас интересует?', 'Hansı avtomobillə maraqlanırsınız?', 'Which car are you considering?'), activeListing ? l('Версия для разбора сохранённого объявления', 'Saxlanmış elanın təhlili üçün versiya', 'Configuration for the saved listing') : l('VIN не нужен', 'VIN lazım deyil', 'No VIN needed')) +
      `<form id="buyer-model-form"><div class="buyer-card"><label>${esc(l('Опишите автомобиль', 'Avtomobili təsvir edin', 'Describe the car'))}<input name="free_text" value="${esc(form.free_text || '')}" placeholder="Toyota Corolla 2020 1.8 hybrid USA"></label>${button(l('Заполнить параметры', 'Parametrləri doldur', 'Fill parameters'), 'parse-text')}</div>
      <div class="buyer-card buyer-fields">${input('make', l('Марка', 'Marka', 'Make'), 'text', 'required autocomplete="off"')}${input('model', l('Модель', 'Model', 'Model'), 'text', 'required')}${input('year', l('Год', 'İl', 'Year'), 'number', 'required min="1981" max="2100" inputmode="numeric"')}
      <label>${esc(l('Исходный рынок', 'İlkin bazar', 'Original market'))}<select name="market">${[['UNKNOWN', l('Не знаю', 'Bilmirəm', 'Unknown')], ['USA', l('США', 'ABŞ', 'USA')], ['EU', l('Европа', 'Avropa', 'Europe')], ['JAPAN', l('Япония', 'Yaponiya', 'Japan')], ['KOREA', l('Корея', 'Koreya', 'Korea')]].map(([v, label]) => `<option value="${v}" ${form.market === v ? 'selected' : ''}>${esc(label)}</option>`).join('')}</select></label>
      <p class="field-help">${esc(l('Рынок продажи новой машины отличается от страны сборки и страны ваших поездок.', 'Yeni avtomobilin satış bazarı istehsal ölkəsindən və istifadə ölkəsindən fərqlənir.', 'The original sales market differs from the manufacturing country and where you drive.'))}</p>
      <details><summary>${esc(l('Уточнить версию · необязательно', 'Versiyanı dəqiqləşdir · istəyə görə', 'Refine configuration · optional'))}</summary><div class="buyer-fields">${input('engine_hint', l('Объём или двигатель', 'Həcm və ya mühərrik', 'Engine or displacement'))}
      <label>${esc(l('Силовая установка', 'Güc qurğusu', 'Powertrain'))}<select name="powertrain_hint">${[['', l('Не знаю', 'Bilmirəm', 'Unknown')], ['ICE', l('Бензин / дизель', 'Benzin / dizel', 'Gasoline / diesel')], ['HEV', l('Гибрид без зарядки', 'Şarjsız hibrid', 'Non-plug-in hybrid')], ['PHEV', l('Заряжаемый гибрид', 'Şarj olunan hibrid', 'Plug-in hybrid')], ['BEV', l('Электромобиль', 'Elektromobil', 'Electric')]].map(([v, label]) => `<option value="${v}" ${form.powertrain_hint === v ? 'selected' : ''}>${esc(label)}</option>`).join('')}</select></label>
      <label>${esc(l('Топливо','Yanacaq','Fuel'))}<select name="fuel_hint">${[['',l('Не знаю','Bilmirəm','Unknown')],['Gasoline',l('Бензин','Benzin','Gasoline')],['Diesel',l('Дизель','Dizel','Diesel')],['Electricity',l('Электроэнергия','Elektrik','Electricity')]].map(([v,label])=>`<option value="${v}" ${form.fuel_hint===v?'selected':''}>${esc(label)}</option>`).join('')}</select></label>${input('transmission_hint', l('Коробка', 'Sürətlər qutusu', 'Transmission'))}${input('drivetrain_hint', l('Привод', 'Ötürücü', 'Drivetrain'))}${input('trim_hint', l('Комплектация', 'Komplektasiya', 'Trim'))}</div></details></div>
      <button class="button gold full" type="submit">${esc(l('Продолжить', 'Davam et', 'Continue'))}</button></form>`);
  }

  function preview() {
    show(heading(l('Выбранный автомобиль', 'Seçilmiş avtomobil', 'Selected car')) + `<article class="buyer-card"><p class="eyebrow">${esc(l('Характеристики выбранной версии', 'Seçilmiş versiyanın xüsusiyyətləri', 'Selected configuration'))}</p><h2>${esc(titleFor(form))}</h2><p>${esc([form.engine_hint, powertrainLabel(form.powertrain_hint), form.transmission_hint, form.drivetrain_hint, form.trim_hint].filter(Boolean).join(' · '))}</p><p>${esc(l('Рынок', 'Bazar', 'Market'))}: ${esc(marketLabel(form.market))}</p>${button(l('Изменить', 'Dəyiş', 'Edit'), 'edit-model')}</article>
      ${form.market !== 'USA' && !form.reference_market ? `<div class="buyer-card"><p>${esc(l('Сейчас автоматический каталог модификаций доступен для США. Можно выбрать американскую версию для справочного сравнения. Это не подтверждает исходный рынок вашего автомобиля.', 'Hazırda avtomatik versiya kataloqu ABŞ üçün mövcuddur. İstinad müqayisəsi üçün ABŞ versiyasını seçə bilərsiniz. Bu, avtomobilinizin ilkin bazarını təsdiqləmir.', 'Automatic configuration lookup currently covers the USA. You can select a US reference configuration for comparison. This does not confirm your car’s original market.'))}</p>${button(l('Выбрать версию США как справочную', 'ABŞ versiyasını istinad kimi seç', 'Use a US reference configuration'), 'reference-market')}</div>` : button(l('Получить разбор', 'Təhlili al', 'Get analysis'), 'research-start', '', 'gold full')}`);
  }

  function offer() {
    show(heading(l('Объявление или VIN', 'Elan və ya VIN', 'Listing or VIN'), l('Ссылка определится автоматически. Номер кузова также поддерживается.', 'Keçid avtomatik tanınır. Kuzov nömrəsi də dəstəklənir.', 'Links are detected automatically. Frame numbers are also supported.')) +
      `<form id="buyer-offer-form"><div class="buyer-card buyer-fields"><label>${esc(l('Вставьте ссылку на объявление или VIN', 'Elan keçidini və ya VIN-i daxil edin', 'Paste a listing URL or VIN'))}<textarea name="offer_input" rows="3" required spellcheck="false">${esc(form.offer_input || '')}</textarea></label>
      <details><summary>${esc(l('Другой рынок / номер кузова', 'Digər bazar / kuzov nömrəsi', 'Other market / frame number'))}</summary><label>${esc(l('Тип номера', 'Nömrə növü', 'Identifier type'))}<select name="identifier_type"><option value="VIN">VIN</option><option value="FRAME_NUMBER">${esc(l('Номер кузова', 'Kuzov nömrəsi', 'Frame number'))}</option><option value="CHASSIS_NUMBER">${esc(l('Номер шасси', 'Şassi nömrəsi', 'Chassis number'))}</option></select></label><label>${esc(l('Рынок', 'Bazar', 'Market'))}<select name="identifier_market"><option value="USA">USA</option><option value="JAPAN">Japan</option><option value="EU">Europe</option><option value="KOREA">Korea</option></select></label></details></div><button class="button gold full" type="submit">${esc(l('Продолжить', 'Davam et', 'Continue'))}</button></form>`);
  }

  async function listing(id) {
    await ensureSession();
    const item = await api(`/reports/buyer/listings/${id}`);
    activeListing = id; save();
    const d = item.data || {};
    if (item.status === 'IMPORTED') {
      show(heading(l('Объявление получено', 'Elan alındı', 'Listing imported')) + `<article class="buyer-card">${photo(d.photos?.[0])}<h2>${esc(titleFor(d))}</h2><div class="offer-facts"><strong>${esc(money(d))}</strong><span>${esc(d.mileage_km?.toLocaleString(state.language) || '—')} km</span></div><p>${esc([d.engine, d.transmission, d.city].filter(Boolean).join(' · '))}</p><a href="${esc(safeUrl(item.source_url))}" target="_blank" rel="noopener noreferrer">${esc(new URL(item.source_url).hostname)} ↗</a><p class="field-help">${esc(l('Сведения продавца. VIN не требуется для разбора.', 'Satıcının məlumatı. Təhlil üçün VIN tələb olunmur.', 'Seller-supplied information. VIN is not required for analysis.'))}</p></article><div class="buyer-actions">${button(l('Разобрать предложение', 'Təklifi təhlil et', 'Analyze this offer'), 'listing-analyze', id, 'gold full')}${button(l('Уточнить данные', 'Məlumatı dəqiqləşdir', 'Refine details'), 'listing-edit', id)}</div>`);
    } else {
      show(heading(l('Ссылка сохранена', 'Keçid saxlanıldı', 'Link saved')) + `<div class="buyer-card"><p>${esc(l('Страница недоступна для разрешённого импорта либо не содержит распознаваемых характеристик. Можно продолжить по параметрам или вставить описание продавца.', 'Səhifə icazəli idxal üçün əlçatan deyil və ya tanınan xüsusiyyətlər yoxdur. Parametrlərlə davam edə və ya satıcının təsvirini daxil edə bilərsiniz.', 'The page is unavailable for permitted import or lacks recognizable vehicle metadata. Continue with parameters or paste the seller’s description.'))}</p><p class="source-link">${esc(item.source_url)}</p><p>${esc(reason(item.reason))}</p></div><form id="buyer-fallback-form"><label>${esc(l('Описание объявления', 'Elanın təsviri', 'Listing description'))}<textarea name="description" rows="6">${esc(d.description || '')}</textarea></label><input type="hidden" name="url" value="${esc(item.source_url)}"><button class="button secondary full">${esc(l('Сохранить описание и продолжить', 'Təsviri saxla və davam et', 'Save description and continue'))}</button></form>${button(l('Продолжить по параметрам', 'Parametrlərlə davam et', 'Continue with parameters'), 'listing-edit', id)}`);
    }
  }

  function reason(code) {
    if (['SOURCE_RESTRICTED', 'CROSS_SITE_REDIRECT'].includes(code)) return l('Источник ограничивает автоматический доступ.', 'Mənbə avtomatik girişi məhdudlaşdırır.', 'The source restricts automated access.');
    if (code === 'UNSAFE_URL') return l('Ссылка ведёт на служебный или локальный адрес. Загрузка запрещена.', 'Keçid daxili və ya lokal ünvana gedir. Yükləmə qadağandır.', 'The link points to an internal or local address. Loading is blocked.');
    return l('Автоматическое извлечение не выполнено.', 'Avtomatik çıxarış baş tutmadı.', 'Automatic extraction was not completed.');
  }

  async function startResearch(vehicle) {
    await ensureSession();
    const job = await api('/research/jobs', {method: 'POST', body: JSON.stringify({vehicle, language: state.language})});
    localStorage.setItem('autoexpert.buyer.job.' + job.id, JSON.stringify({listing: activeListing, parent: parentId, original_market: form.market}));
    go('/buyer-research/' + job.id);
  }

  async function research(id) {
    await ensureSession();
    let job = await api(`/research/jobs/${id}`);
    if (['QUEUED', 'RUNNING'].includes(job.status)) {
      busy(l('Подбираем версию и изучаем источники', 'Versiyanı seçir və mənbələri araşdırırıq', 'Matching configuration and researching sources'));
      if (pending.has(id)) return;
      pending.add(id);
      try {job = await api(`/research/jobs/${id}/execute`, {method: 'POST'});} finally {pending.delete(id);}
      if (location.hash !== '#/buyer-research/' + id) return;
    }
    if (job.resolution?.needs_user_selection) {
      show(heading(l('Уточните модификацию', 'Modifikasiyanı dəqiqləşdirin', 'Choose the configuration'), l('Это варианты, найденные в официальном каталоге. Запрошенные параметры могут не совпадать.', 'Bunlar rəsmi kataloqda tapılan variantlardır. Soruşulan parametrlər fərqlənə bilər.', 'These configurations were found in the official catalogue. Requested parameters may differ.')) + `<div class="buyer-variants">${job.resolution.candidates.map(c => `<button class="buyer-card variant-choice" data-baction="select-variant" data-id="${esc(id)}" data-candidate="${esc(c.id)}"><strong>${esc(candidateLabel(c))}</strong><small>${esc(l('Выбрать эту конфигурацию', 'Bu konfiqurasiyanı seç', 'Choose this configuration'))}</small></button>`).join('')}</div>${button(l('Изменить параметры', 'Parametrləri dəyiş', 'Edit parameters'), 'edit-model')}`);
      return;
    }
    if (!job.profile_id) {
      show(heading(l('Версия пока не определена', 'Versiya hələ müəyyən edilməyib', 'Configuration not yet resolved')) + `<div class="buyer-card"><p>${esc(l('В подключённых источниках не удалось подтвердить эту комбинацию. Ввод сохранён; попробуйте уточнить модель или рынок.', 'Qoşulmuş mənbələrdə bu kombinasiya təsdiqlənmədi. Daxil etdiyiniz məlumat saxlanıb; model və ya bazarı dəqiqləşdirin.', 'Connected sources could not confirm this combination. Your input is saved; refine the model or market.'))}</p>${button(l('Уточнить', 'Dəqiqləşdir', 'Refine'), 'edit-model')}</div>`); return;
    }
    busy(l('Готовим досье из найденных данных', 'Tapılan məlumatlardan hesabat hazırlanır', 'Preparing the dossier from retrieved data'));
    const related = JSON.parse(localStorage.getItem('autoexpert.buyer.job.' + id) || '{}');
    const report = await api('/reports/buyer/dossiers', {method: 'POST', body: JSON.stringify({job_id: id, language: state.language, listing_id: related.listing, parent_report_id: related.parent, preferences: {original_market: related.original_market}})});
    if (location.hash === '#/buyer-research/' + id) go('/buyer-report/' + report.id);
  }

  function sources(items) {
    return `<details class="buyer-card report-sources"><summary>${esc(l('Источники и применимость', 'Mənbələr və uyğunluq', 'Sources and applicability'))}</summary>${items.map(s => `<article id="source-${esc(s.id)}"><a href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener noreferrer">${esc(s.title)} ↗</a>${s.applicability_summary ? `<p>${esc(s.applicability_summary)}</p>` : ''}<small>${esc((s.retrieved_at || '').slice(0, 10))}</small></article>`).join('')}</details>`;
  }

  function sectionHtml(section, index) {
    const body = `<div class="buyer-section-body">${section.rows.length ? `<dl class="buyer-specs">${section.rows.map(r => `<div><dt>${esc(r.label)}</dt><dd>${esc(r.value)}</dd></div>`).join('')}</dl>` : ''}${section.paragraphs.map(p => `<p>${esc(p.text)}</p>`).join('')}${!section.rows.length && !section.paragraphs.length ? `<p class="muted">${esc(l('Подтверждённых подробностей пока нет в подключённых источниках.', 'Qoşulmuş mənbələrdə təsdiqlənmiş təfərrüat hələ yoxdur.', 'Confirmed details are not yet available from connected sources.'))}</p>` : ''}</div>`;
    if (section.key === 'expert_verdict') return `<section class="buyer-card buyer-verdict" id="expert-verdict"><p class="eyebrow">AUTO EXPERT</p><h2>${esc(section.title)}</h2>${body}</section>`;
    return `<details class="buyer-card buyer-section" ${index < 2 ? 'open' : ''}><summary><span class="section-number">${String(index + 1).padStart(2, '0')}</span><span>${esc(section.title)}</span></summary>${body}<button class="source-reference" data-baction="show-sources">${esc(l('Источники раздела', 'Bölmənin mənbələri', 'Section sources'))}</button></details>`;
  }

  async function report(id) {
    await ensureSession();
    currentReport = await api(`/reports/buyer/${id}?language=${state.language}`);
    const r = currentReport, p = r.projection;
    const comparison = r.kind === 'COMPARISON';
    const compareHead = comparison ? `<div class="comparison-sticky">${p.subtitle.split(' / ').map(s => `<span>${esc(s)}</span>`).join('')}</div>` : '';
    show(heading(p.title, p.subtitle) + `${r.photos.length ? photo(r.photos[0], 'hero') : ''}<div class="buyer-actions">${button(l('Спросить Auto Expert', 'Auto Expert-dən soruş', 'Ask Auto Expert'), 'chat', id, 'gold')}${button('PDF', 'pdf', id)}${comparison ? '' : button(l('Добавить к сравнению', 'Müqayisəyə əlavə et', 'Add to comparison'), 'basket-add', id)}</div>${p.notice ? `<p class="coverage-note">${esc(p.notice)}</p>` : ''}${compareHead}<div class="buyer-dossier ${comparison ? 'comparison-dossier' : ''}">${p.sections.map((section, index) => (section.key === 'expert_verdict' ? (r.photos.length > 1 ? `<details class="buyer-card"><summary>${esc(l('Фото объявления', 'Elan şəkilləri', 'Listing photos'))} · ${r.photos.length}</summary><div class="photo-gallery">${r.photos.slice(1).map(x => photo(x)).join('')}</div></details>` : '') : '') + sectionHtml(section, index)).join('')}</div>${sources(r.sources)}${r.kind === 'LISTING' && !p.vin ? button(l('Дополнить VIN-историей', 'VIN tarixçəsi ilə tamamla', 'Add VIN history'), 'append-vin', id) : ''}<p class="buyer-footnote">${esc(l('Сохранённый отчёт. Новое исследование создаёт отдельный снимок.', 'Saxlanmış hesabat. Yeni araşdırma ayrıca nüsxə yaradır.', 'Saved report. New research creates a separate snapshot.'))}</p>`, comparison ? 'compare' : 'reports');
  }

  async function compare() {
    await ensureSession();
    const reports = (await api('/reports/buyer')).filter(r => r.kind !== 'COMPARISON');
    for (let i=basket.length-1;i>=0;i--) if (!reports.some(r=>r.id===basket[i])) basket.splice(i,1); save();
    const selected = basket.map(id => reports.find(r => r.id === id)).filter(Boolean);
    show(heading(l('Сравнить автомобили', 'Avtomobilləri müqayisə et', 'Compare cars'), l('Два варианта достаточно. Третий — по желанию.', 'İki variant kifayətdir. Üçüncü istəyə görədir.', 'Two options are enough. A third is optional.')) + `<div class="basket-cards">${selected.map((r, i) => `<article class="buyer-card"><p class="eyebrow">${i + 1} / 3</p><h2>${esc(r.title)}</h2><p>${esc(kind(r.kind))}</p>${button(l('Убрать / заменить', 'Sil / əvəz et', 'Remove / replace'), 'basket-remove', r.id)}</article>`).join('')}</div>${selected.length < 3 ? `<div class="buyer-card"><h2>${esc(l('Добавить вариант', 'Variant əlavə et', 'Add an option'))}</h2><div class="buyer-actions">${button(l('По параметрам', 'Parametrlərlə', 'By parameters'), 'model')}${button(l('Ссылка или VIN', 'Keçid və ya VIN', 'Listing or VIN'), 'offer')}</div>${reports.filter(r => !basket.includes(r.id)).map(r => `<button class="saved-choice" data-baction="basket-select" data-id="${r.id}">${esc(r.title)}<span>＋</span></button>`).join('')}</div>` : ''}
      <form id="buyer-compare-form"><details class="buyer-card"><summary>${esc(l('Что для вас важно?', 'Sizin üçün nə vacibdir?', 'What matters to you?'))}</summary><div class="priority-chips">${[['economy','Экономичность','Qənaət','Economy'],['reliability','Надёжность','Etibarlılıq','Reliability'],['comfort','Комфорт','Komfort','Comfort'],['maintenance','Содержание','Qulluq xərci','Maintenance'],['space','Пространство','Genişlik','Space'],['performance','Динамика','Dinamika','Performance'],['resale','Перепродажа','Təkrar satış','Resale']].map(([v, ...text]) => `<label><input type="checkbox" name="priorities" value="${v}">${esc(l(...text))}</label>`).join('')}</div><div class="buyer-fields"><label>${esc(l('Пробег в месяц, км', 'Aylıq yürüş, km', 'Monthly distance, km'))}<input type="number" name="monthly_km" min="0" max="30000" inputmode="numeric"></label><label>${esc(l('Город эксплуатации', 'İstifadə şəhəri', 'City of use'))}<input name="city"></label><label>${esc(l('Дороги и маршруты', 'Yollar və marşrutlar', 'Roads and routes'))}<input name="roads"></label></div></details><button class="button gold full" ${selected.length < 2 ? 'disabled' : ''}>${esc(l('Сравнить выбранные', 'Seçilənləri müqayisə et', 'Compare selected cars'))}</button></form>`, 'compare');
  }

  const kind = k => ({MODEL: l('Модель без VIN', 'VIN-siz model', 'Model without VIN'), LISTING: l('Объявление', 'Elan', 'Listing'), VIN: 'VIN', COMPARISON: l('Сравнение', 'Müqayisə', 'Comparison')}[k]);
  async function reports() {
    await ensureSession();
    const [list, historyCards] = await Promise.all([api('/reports/buyer'), mockVinHistoryCards?.() || '']);
    show(heading(l('Мои отчёты', 'Hesabatlarım', 'My reports')) + list.map(r => `<article class="buyer-card"><p class="eyebrow">${esc(kind(r.kind))} · ${esc(r.language.toUpperCase())}</p><h2>${esc(r.title)}</h2><p>${esc(r.created_at.slice(0, 10))}</p>${button(l('Открыть', 'Aç', 'Open'), 'open-report', r.id)}</article>`).join('') + historyCards + (!list.length && !historyCards ? `<p>${esc(l('Здесь появятся ваши разборы и сравнения.', 'Təhlilləriniz və müqayisələriniz burada görünəcək.', 'Your analyses and comparisons will appear here.'))}</p>` : '') + button(l('Ранее сохранённые VIN-отчёты', 'Əvvəl saxlanmış VIN hesabatları', 'Previously saved VIN reports'), 'legacy-reports'), 'reports');
  }

  async function chat(id) {
    await ensureSession();
    const r = await api(`/reports/buyer/${id}?language=${state.language}`);
    show(heading('Auto Expert', r.projection.title) + `<p class="coverage-note">${esc(l('Ответы по источникам отчёта. В этой локальной версии используется ограниченный алгоритм, а не свободная беседа с языковой моделью.', 'Hesabat mənbələrinə əsaslanan cavablar. Bu lokal versiya dil modeli ilə sərbəst söhbət deyil, məhdud alqoritmdən istifadə edir.', 'Answers grounded in report sources. This local version uses a limited algorithm, not open-ended conversation with a language model.'))}</p><div class="buyer-chat-messages">${r.questions.map(q => `<article class="chat-bubble user">${esc(q.question)}</article><article class="chat-bubble assistant">${esc(q.answer)}</article>`).join('')}</div><div class="chat-suggestions">${[l('Какой бензин нужен?', 'Hansı benzin lazımdır?', 'What fuel is required?'), l('Что известно о проблемах этой коробки?', 'Bu qutunun problemləri barədə nə məlumdur?', 'What is known about transmission problems?'), l('Что меняется при 2000 км в месяц?', 'Ayda 2000 km olduqda nə dəyişir?', 'What changes at 2000 km per month?')].map(q => `<button data-baction="chat-suggestion" data-id="${id}" data-question="${esc(q)}">${esc(q)}</button>`).join('')}</div><form id="buyer-chat-form" data-id="${id}"><label class="sr-only" for="buyer-question">${esc(l('Вопрос', 'Sual', 'Question'))}</label><textarea id="buyer-question" name="question" rows="2" required maxlength="1000" placeholder="${esc(l('Спросить по этому отчёту', 'Bu hesabat barədə soruş', 'Ask about this report'))}"></textarea><button class="button gold">${esc(l('Отправить', 'Göndər', 'Send'))}</button></form>${button(l('Вернуться к отчёту', 'Hesabata qayıt', 'Back to report'), 'open-report', id)}`);
  }

  async function sendQuestion(id, question) {
    const node = root.querySelector('.buyer-chat-messages');
    node.insertAdjacentHTML('beforeend', `<article class="chat-bubble user">${esc(question)}</article>`);
    const reply = await api(`/reports/buyer/${id}/questions?language=${state.language}`, {method: 'POST', body: JSON.stringify({question})});
    if (location.hash === '#/buyer-chat/' + id) {node.insertAdjacentHTML('beforeend', `<article class="chat-bubble assistant">${esc(reply.answer)}</article>`); root.querySelector('[name=question]').value = ''; node.lastElementChild.scrollIntoView({block: 'center'});}
  }

  async function action(target) {
    const {baction: action, id} = target.dataset;
    if (action === 'home') go('/home');
    else if (action === 'model') {activeListing = null; parentId = null; save(); go('/manual');}
    else if (action === 'edit-model') go('/manual');
    else if (action === 'offer') {activeListing = null; parentId = null; save(); go('/vin');}
    else if (action === 'compare') go('/compare');
    else if (action === 'legacy-reports') go('/legacy-reports');
    else if (action === 'open-report') go('/buyer-report/' + id);
    else if (action === 'chat') go('/buyer-chat/' + id);
    else if (action === 'pdf') {target.disabled = true; try {await downloadReportPdf(id, null, state.language); showToast(l('PDF передан для сохранения', 'PDF saxlanmağa göndərildi', 'PDF sent for saving'));} finally {target.disabled = false;}}
    else if (action === 'append-vin') {parentId = id; activeListing = currentReport?.input.listing?.id || null; form.offer_input = ''; save(); go('/vin');}
    else if (action === 'show-sources') {const s = root.querySelector('.report-sources'); s.open = true; s.scrollIntoView({block: 'start'});}
    else if (action === 'reference-market') {form.reference_market = 'USA'; save(); preview();}
    else if (action === 'parse-text') {
      const text = root.querySelector('[name=free_text]').value.trim();
      const match = text.match(/^(.+?)\s+(19\d{2}|20\d{2})(.*)$/);
      if (!match) {showToast(l('Укажите марку, модель и год', 'Marka, model və ili daxil edin', 'Include make, model and year')); return;}
      const multi = ['Land Rover','Alfa Romeo','Mercedes-Benz','Mercedes Benz','Aston Martin'].find(make=>match[1].toLowerCase().startsWith(make.toLowerCase()+' ')); const names = match[1].split(/\s+/); form = {market: 'UNKNOWN', free_text: text, make: multi || names.shift(), model: multi ? match[1].slice(multi.length).trim() : names.join(' '), year: match[2]};
      const rest = match[3].toLowerCase(); form.fuel_hint = /diesel|дизел|dizel/.test(rest) ? 'Diesel' : /gasoline|бензин|benzin/.test(rest) ? 'Gasoline' : '';
      const engine = rest.match(/\b(\d[.,]\d)\b/); if (engine) form.engine_hint = engine[1].replace(',', '.');
      form.powertrain_hint = /plug|phev|заряжаем/.test(rest) ? 'PHEV' : /hybrid|hibrid|гибрид/.test(rest) ? 'HEV' : /electric|электро|elektrik/.test(rest) ? 'BEV' : '';
      if (/usa|сша|abş|us\b/.test(rest)) form.market = 'USA'; save(); model();
    } else if (action === 'research-start') {
      const vehicle = {make: form.make, model: form.model, year: Number(form.year), market: form.reference_market || form.market};
      for (const key of ['engine_hint', 'powertrain_hint', 'fuel_hint', 'transmission_hint', 'drivetrain_hint', 'trim_hint']) if (form[key]) vehicle[key] = form[key];
      target.disabled = true; await startResearch(vehicle);
    } else if (action === 'select-variant') {
      target.disabled = true; await api(`/research/jobs/${id}/variant-selection`, {method: 'POST', body: JSON.stringify({candidate_id: target.dataset.candidate})}); await research(id);
    } else if (action === 'listing-analyze' || action === 'listing-edit') {
      const item = await api(`/reports/buyer/listings/${id}`), d = item.data; activeListing = id; parentId = null;
      const volume = String(d.engine || '').match(/\d[.,]\d/);
      form = {offer_input: item.source_url, free_text: '', fuel_hint: '', make: d.make || '', model: d.model || '', year: d.year || '', engine_hint: volume?.[0] || '', market: /ABŞ|США|USA|Amerika/i.test(d.market_claim || '') ? 'USA' : 'UNKNOWN', powertrain_hint: /hibrid|гибрид/i.test(d.engine || '') ? 'HEV' : '', transmission_hint: '', drivetrain_hint: '', trim_hint: d.trim || '', reference_market: null}; save(); go('/manual');
    } else if (action.startsWith('basket-')) {
      if (action === 'basket-remove') basket.splice(basket.indexOf(id), 1);
      else if (!basket.includes(id)) {if (basket.length >= 3) {showToast(l('В сравнении уже три варианта', 'Müqayisədə artıq üç variant var', 'Three options are already selected')); return;} basket.push(id);}
      save(); if (action === 'basket-add') showToast(l('Добавлено к сравнению', 'Müqayisəyə əlavə edildi', 'Added to comparison')); else await compare();
    } else if (action === 'chat-suggestion') await sendQuestion(id, target.dataset.question);
  }

  root.addEventListener('click', e => {const target = e.target.closest('[data-baction]'); if (target && !target.disabled) {e.preventDefault(); void action(target).catch(handleError);}});
  root.addEventListener('input', e => {if (e.target.closest('#buyer-model-form, #buyer-offer-form') && e.target.name) {form[e.target.name] = e.target.value; if (e.target.name === 'market') form.reference_market = null; save();}});
  root.addEventListener('submit', e => {
    const f = e.target;
    if (!f.id.startsWith('buyer-')) return;
    e.preventDefault();
    void (async () => {
      const d = new FormData(f);
      if (f.id === 'buyer-model-form') {form = {...form, ...Object.fromEntries(d)}; save(); go('/buyer-preview');}
      else if (f.id === 'buyer-offer-form') {
        const value = String(d.get('offer_input')).trim(); form.offer_input = value; save();
        if (/^https?:\/\//i.test(value)) {await ensureSession(); busy(l('Получаем объявление', 'Elan alınır', 'Importing listing')); const result = await api('/reports/buyer/listings', {method: 'POST', body: JSON.stringify({url: value, language: state.language})}); go('/listing/' + result.id);}
        else {
          const frame = d.get('identifier_type') === 'VIN' && /^[A-Z0-9]{2,12}-[0-9]{4,12}$/i.test(value);
          const vin = value.toUpperCase();
          if (!frame && d.get('identifier_type') === 'VIN' && d.get('identifier_market') === 'USA'
              && state.meta?.demo_mode && vin === state.meta?.vin_demo?.sample_vin && startMockVinHistory) {
            await startMockVinHistory(vin);
          } else {
            await startResearch({identifier: vin, identifier_type: frame ? 'FRAME_NUMBER' : d.get('identifier_type'), market: frame ? 'JAPAN' : d.get('identifier_market')});
          }
        }
      } else if (f.id === 'buyer-fallback-form') {
        await ensureSession(); const result = await api('/reports/buyer/listings', {method: 'POST', body: JSON.stringify({url: d.get('url'), description: d.get('description'), language: state.language})}); activeListing = result.id; parentId = null; form = {market: 'UNKNOWN', offer_input: d.get('url')}; save(); go('/manual');
      } else if (f.id === 'buyer-compare-form') {
        const preferences = {priorities: d.getAll('priorities'), monthly_km: d.get('monthly_km') ? Number(d.get('monthly_km')) : null, city: d.get('city'), roads: d.get('roads')};
        busy(l('Сопоставляем выбранные автомобили', 'Seçilən avtomobillər müqayisə olunur', 'Comparing selected cars'));
        const result = await api('/reports/buyer/comparisons', {method: 'POST', body: JSON.stringify({report_ids: basket, language: state.language, preferences})}); go('/buyer-report/' + result.id);
      } else if (f.id === 'buyer-chat-form') {const btn = f.querySelector('button'); btn.disabled = true; try {await sendQuestion(f.dataset.id, d.get('question'));} finally {btn.disabled = false;}}
    })().catch(handleError);
  });

  return {async route(name, id) {
    const routes = {home, manual: model, vin: offer, listing, 'buyer-preview': preview, 'buyer-research': research, 'buyer-report': report, compare, 'saved-compare':compare, reports, 'buyer-chat': chat};
    if (!routes[name]) return false;
    await routes[name](id); return true;
  }};
}
