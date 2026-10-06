// The Garage (product phase, stage 2): the owner's cars, next services, the service log and the
// "My car" feed. Shown only while the API advertises the garage_v1 flag (client-config
// "garage_v1"); production without the flag never loads or renders anything from here.
import {api, downloadFile} from './api.js?v=0.11.0';

const C = {
  garage: ['Гараж', 'Qaraj', 'Garage'],
  subtitle: ['Моя машина под присмотром эксперта', 'Avtomobilim ekspert nəzarətində', 'My car, watched by an expert'],
  add: ['Добавить машину', 'Avtomobil əlavə et', 'Add a car'],
  empty: ['В гараже пока нет машин. Добавьте свою — по VIN или выбором из каталога.', 'Qarajda hələ avtomobil yoxdur. Öz avtomobilinizi əlavə edin — VIN ilə və ya kataloqdan seçərək.', 'No cars yet. Add yours — by VIN or from the catalog.'],
  feed: ['Лента «Моя машина»', '«Avtomobilim» lenti', '"My car" feed'],
  feedEmpty: ['Новых уведомлений нет', 'Yeni bildiriş yoxdur', 'No new notices'],
  byVin: ['По VIN', 'VIN ilə', 'By VIN'],
  byCatalog: ['Из каталога', 'Kataloqdan', 'From the catalog'],
  vinLabel: ['VIN (17 знаков)', 'VIN (17 simvol)', 'VIN (17 characters)'],
  decode: ['Расшифровать', 'Deşifrə et', 'Decode'],
  vinNote: ['Расшифровка по локальной базе NHTSA vPIC, без внешних запросов.', 'Deşifrə yerli NHTSA vPIC bazası ilə, xarici sorğu olmadan.', 'Decoded from a local copy of NHTSA vPIC, no external request.'],
  make: ['Марка', 'Marka', 'Make'], model: ['Модель', 'Model', 'Model'], year: ['Год', 'İl', 'Year'],
  choose: ['Выберите', 'Seçin', 'Choose'],
  configuration: ['Двигатель, коробка, привод', 'Mühərrik, qutu, ötürücü', 'Engine, transmission, drive'],
  noConfig: ['Этой машины нет в нашей базе. Выберите конфигурацию из каталога.', 'Bu avtomobil bazamızda yoxdur. Kataloqdan konfiqurasiya seçin.', 'This car is not in our database. Choose a configuration from the catalog.'],
  decoded: ['VIN расшифрован', 'VIN deşifrə edildi', 'VIN decoded'],
  checkDigit: ['Контрольный знак VIN не сходится — проверьте ввод.', 'VIN-in nəzarət simvolu uyğun gəlmir — daxil etdiyinizi yoxlayın.', 'The VIN check digit does not match — please check the input.'],
  odometer: ['Пробег сейчас', 'İndiki yürüş', 'Current odometer'],
  monthly: ['Пробег в месяц (в среднем)', 'Aylıq yürüş (orta)', 'Distance per month (average)'],
  region: ['Где ездит машина', 'Avtomobil harada sürülür', 'Where the car is driven'],
  regions: {US: ['США / Канада', 'ABŞ / Kanada', 'US / Canada'], AZ: ['Азербайджан', 'Azərbaycan', 'Azerbaijan'], CIS: ['СНГ', 'MDB', 'CIS']},
  inService: ['Начало эксплуатации (если знаете)', 'İstismara başlama (bilirsinizsə)', 'In service since (if known)'],
  history: ['Когда меняли?', 'Nə vaxt dəyişilib?', 'When was it last done?'],
  historyNote: ['«Не знаю» — посчитаем по регламенту от текущего пробега и пометим как неподтверждённое.', '«Bilmirəm» — indiki yürüşdən reqlamentə görə hesablayıb təsdiqlənməmiş kimi qeyd edəcəyik.', '"Don\'t know" — we count by the schedule from the current mileage and mark it as not confirmed.'],
  dontKnow: ['Не знаю', 'Bilmirəm', "Don't know"],
  date: ['Дата', 'Tarix', 'Date'],
  save: ['Сохранить', 'Yadda saxla', 'Save'],
  next: ['Ближайшие работы', 'Yaxın işlər', 'Coming up'],
  oil: ['Моторное масло', 'Mühərrik yağı', 'Engine oil'],
  oilInterval: ['Ваш интервал замены', 'Sizin dəyişmə intervalınız', 'Your change interval'],
  months: ['мес.', 'ay', 'months'],
  manualSays: ['В руководстве', 'Təlimatda', 'The manual says'],
  onboardReset: ['Машина просит ТО — масло заменено', 'Avtomobil TXQ istəyir — yağ dəyişildi', 'The car asked for service — oil changed'],
  conditions: ['Условия эксплуатации', 'İstismar şəraiti', 'Driving conditions'],
  normal: ['Нормальные', 'Normal', 'Normal'], severe: ['Тяжёлые', 'Ağır', 'Severe'],
  conditionsNote: ['Для AZ/СНГ по умолчанию тяжёлые условия, для США — нормальные.', 'AZ/MDB üçün susmaya görə ağır şərait, ABŞ üçün — normal.', 'AZ / CIS default to severe conditions, the US to normal.'],
  mileage: ['Пробег', 'Yürüş', 'Mileage'],
  estimated: ['оценка', 'təxmini', 'estimate'],
  perMonth: ['в месяц', 'ayda', 'per month'],
  update: ['Уточнить', 'Dəqiqləşdir', 'Update'],
  log: ['Журнал работ', 'İş jurnalı', 'Service log'],
  logAdd: ['Записать работу', 'İşi qeyd et', 'Log a job'],
  job: ['Работа', 'İş', 'Job'],
  logEmpty: ['Записей пока нет', 'Hələ qeyd yoxdur', 'No records yet'],
  pdf: ['Журнал обслуживания (PDF)', 'Texniki xidmət jurnalı (PDF)', 'Service log (PDF)'],
  recalls: ['Отзывные кампании', 'Geri çağırma kampaniyaları', 'Recalls'],
  noRecalls: ['Кампаний по этой конфигурации в нашей базе нет', 'Bu konfiqurasiya üzrə bazamızda kampaniya yoxdur', 'No campaigns for this configuration in our database'],
  issues: ['Известные проблемы', 'Məlum problemlər', 'Known issues'],
  symptoms: ['Симптомы', 'Əlamətlər', 'Symptoms'], check: ['Что проверить', 'Nəyi yoxlamalı', 'What to check'],
  fluids: ['Жидкости и объёмы', 'Mayelər və həcmlər', 'Fluids and capacities'],
  sources: ['Источник', 'Mənbə', 'Source'],
  remove: ['Удалить', 'Sil', 'Delete'],
  statuses: {OVERDUE: ['Просрочено', 'Gecikib', 'Overdue'], SOON: ['Скоро', 'Tezliklə', 'Soon'], CHECK: ['Проверить', 'Yoxlatmaq', 'Check'],
             OK: ['По плану', 'Plan üzrə', 'On track'], ON_SIGNAL: ['По бортовой системе', 'Bort sistemi ilə', 'Onboard system'],
             SET_INTERVAL: ['Задайте интервал', 'İntervalı təyin edin', 'Set interval'], NO_INTERVAL: ['Без интервала', 'İntervalsız', 'No interval'],
             DONE: ['Выполнено', 'Edilib', 'Done']},
  records: {DONE: ['выполнено', 'edilib', 'done'], UNKNOWN: ['дата неизвестна', 'tarix məlum deyil', 'date unknown'], ONBOARD_RESET: ['по сигналу бортовой системы', 'bort sisteminin siqnalı ilə', 'on the onboard signal']},
  severeMark: ['тяжёлые условия', 'ağır şərait', 'severe'],
  back: ['Назад', 'Geri', 'Back'],
  open: ['Открыть', 'Aç', 'Open'],
  urgent: ['требуют внимания', 'diqqət tələb edir', 'need attention'],
  subscription: ['Подписка', 'Abunə', 'Subscription'],
  mechanic: ['Спросить механика', 'Mexanikdən soruş', 'Ask the mechanic'],
  mechanicNote: ['Отвечает только по данным вашей машины. Чего нет в данных — так и скажет.', 'Yalnız avtomobilinizin məlumatlarına əsasən cavab verir. Məlumatda olmayanı açıq deyir.', 'Answers only from your car\'s data. If it is not in the data, it says so.'],
  ask: ['Спросить', 'Soruş', 'Ask'],
  askPlaceholder: ['Например: какое масло заливать?', 'Məsələn: hansı yağ tökmək lazımdır?', 'For example: which oil should I use?'],
  examples: [['Какое масло заливать?', 'Hansı yağ tökməli?', 'Which oil should I use?'], ['Что проверить перед зимой?', 'Qışdan əvvəl nəyi yoxlamalı?', 'What should I check before winter?'], ['Какая жидкость в коробке?', 'Qutuda hansı maye var?', 'Which transmission fluid?']],
  general: ['Общий совет (не из данных машины)', 'Ümumi məsləhət (avtomobilin məlumatlarından deyil)', 'General advice (not from your car\'s data)'],
  notInData: ['Нет в данных', 'Məlumatda yoxdur', 'Not in the data'],
  questionsLeft: ['вопросов сегодня', 'bu gün sual', 'questions today'],
};
const LANG_INDEX = {ru: 0, az: 1, en: 2};
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));

export function garageCopy(language, key) {
  const entry = key.includes('.') ? key.split('.').reduce((o, k) => o?.[k], C) : C[key];
  return entry ? entry[LANG_INDEX[language] ?? 0] : key;
}

export function createGarageViews({root, state, layout, go, ensureSession, showToast, clubButton, lockedPanel}) {
  const t = key => garageCopy(state.language, key);
  const unit = () => (state.language === 'en' ? 'mi' : 'km');
  const enabled = () => Boolean(state.meta?.garage_v1?.enabled);
  const lang = () => `language=${encodeURIComponent(state.language || 'ru')}`;
  const draft = {decoded: null, candidates: [], chosen: null, catalog: null};

  function heading(title, subtitle, backAction = 'garage') {
    return `<section class="page-heading"><button class="back-button" data-action="${backAction}" aria-label="${escape(t('back'))}">‹</button><div><h1>${escape(title)}</h1>${subtitle ? `<p>${escape(subtitle)}</p>` : ''}</div></section>`;
  }

  function pill(status) {
    return `<span class="garage-pill ${escape(status.toLowerCase())}">${escape(t(`statuses.${status}`))}</span>`;
  }

  async function renderList() {
    await ensureSession();
    const [cars, feed] = await Promise.all([api(`/garage/vehicles?${lang()}`), api(`/garage/feed?${lang()}`)]);
    const unread = feed.filter(f => !f.read).length;
    root.innerHTML = layout(`
      <section class="garage">
        ${heading(t('garage'), t('subtitle'), 'home')}
        <div class="garage-cars">
          ${cars.length ? cars.map(c => `
            <button class="garage-car-card" data-action="garage-car" data-id="${escape(c.id)}">
              <span class="garage-car-title"><strong>${escape(c.nickname || c.title)}</strong><small>${escape(c.configuration || '')}</small></span>
              <span class="garage-car-meta"><span>${escape(c.mileage || '')}</span>${c.urgent ? `<span class="garage-pill soon">${c.urgent} ${escape(t('urgent'))}</span>` : ''}</span>
              ${c.next ? `<small class="garage-car-next">${escape(c.next)}</small>` : ''}
            </button>`).join('') : `<p class="garage-empty">${escape(t('empty'))}</p>`}
        </div>
        <div class="garage-actions">
          <button class="button primary" data-action="garage-add">＋ ${escape(t('add'))}</button>
          ${state.meta?.subscription_v1?.enabled ? `<button class="button" data-action="subscription">${escape(garageCopy(state.language, 'subscription'))}</button>` : ''}
          <button class="button" data-action="garage-feed">${escape(t('feed'))}${unread ? ` <span class="garage-count">${unread}</span>` : ''}</button>
        </div>
      </section>`, {active: 'garage'});
  }

  async function renderFeed() {
    await ensureSession();
    const feed = await api(`/garage/feed?${lang()}`);
    root.innerHTML = layout(`
      <section class="garage">
        ${heading(t('feed'), t('subtitle'))}
        <ul class="garage-feed">
          ${feed.length ? feed.map(f => `
            <li class="garage-feed-item ${f.read ? 'read' : ''} kind-${escape(f.kind.toLowerCase())}" data-action="garage-feed-open" data-id="${escape(f.id)}" data-vehicle="${escape(f.vehicle_id)}">
              <strong>${escape(f.title)}</strong><span>${escape(f.body)}</span><small>${escape(f.vehicle)}</small>
            </li>`).join('') : `<li class="garage-empty">${escape(t('feedEmpty'))}</li>`}
        </ul>
      </section>`, {active: 'garage'});
  }

  function options(values, selected, label) {
    return `<option value="">${escape(label)}</option>` + values.map(v => `<option value="${escape(v)}" ${String(v) === String(selected) ? 'selected' : ''}>${escape(v)}</option>`).join('');
  }

  async function renderAdd() {
    await ensureSession();
    draft.catalog = draft.catalog || await api('/garage/catalog');
    const makes = [...new Set(draft.catalog.map(r => r.make))].sort();
    const models = draft.make ? draft.catalog.filter(r => r.make === draft.make).map(r => r.model).sort() : [];
    const years = draft.model ? (draft.catalog.find(r => r.make === draft.make && r.model === draft.model)?.years || []).slice().reverse() : [];
    const decoded = draft.decoded;
    root.innerHTML = layout(`
      <section class="garage">
        ${heading(t('add'), t('subtitle'))}
        <form id="garage-vin-form" class="form-card garage-form">
          <h2>${escape(t('byVin'))}</h2>
          <label>${escape(t('vinLabel'))}<input id="garage-vin" name="vin" maxlength="17" autocomplete="off" value="${escape(draft.vin || '')}"></label>
          <button class="button" type="submit">${escape(t('decode'))}</button>
          <small>${escape(t('vinNote'))}</small>
          ${decoded ? `<p class="garage-decoded"><strong>${escape(t('decoded'))}:</strong> ${escape([decoded.make, decoded.model, decoded.model_year, decoded.displacement_l && `${decoded.displacement_l} L`, decoded.engine_model, decoded.transmission, decoded.trim].filter(Boolean).join(' · '))}${decoded.check_digit_ok === false ? `<br><span class="garage-warn">${escape(t('checkDigit'))}</span>` : ''}</p>` : ''}
        </form>
        <form id="garage-catalog-form" class="form-card garage-form">
          <h2>${escape(t('byCatalog'))}</h2>
          <div class="garage-row">
            <label>${escape(t('make'))}<select data-garage-pick="make">${options(makes, draft.make, t('choose'))}</select></label>
            <label>${escape(t('model'))}<select data-garage-pick="model" ${draft.make ? '' : 'disabled'}>${options(models, draft.model, t('choose'))}</select></label>
            <label>${escape(t('year'))}<select data-garage-pick="year" ${draft.model ? '' : 'disabled'}>${options(years, draft.year, t('choose'))}</select></label>
          </div>
        </form>
        ${draft.candidates.length || draft.searched ? `
        <form id="garage-add-form" class="form-card garage-form">
          <h2>${escape(t('configuration'))}</h2>
          ${draft.candidates.length ? `<div class="garage-choices">${draft.candidates.map((c, i) => `
            <label class="garage-choice"><input type="radio" name="configuration_key" value="${escape(c.configuration_key)}" ${(draft.chosen ? draft.chosen === c.configuration_key : i === 0) ? 'checked' : ''}>
              <span><strong>${escape(`${c.make} ${c.model} ${c.year}`)}</strong><small>${escape(c.label)}</small></span></label>`).join('')}</div>` : `<p class="garage-warn">${escape(t('noConfig'))}</p>`}
          ${draft.candidates.length ? `
          <div class="garage-row">
            <label>${escape(t('odometer'))} (${unit()})<input name="odometer" type="number" min="0" step="1" required></label>
            <label>${escape(t('monthly'))} (${unit()})<input name="monthly" type="number" min="0" step="1"></label>
          </div>
          <div class="garage-row">
            <label>${escape(t('region'))}<select name="region">${['US', 'AZ', 'CIS'].map(r => `<option value="${r}" ${r === defaultRegion() ? 'selected' : ''}>${escape(t(`regions.${r}`))}</option>`).join('')}</select></label>
            <label>${escape(t('inService'))}<input name="in_service_date" type="date"></label>
          </div>
          <fieldset class="garage-history">
            <legend>${escape(t('history'))}</legend>
            <small>${escape(t('historyNote'))}</small>
            ${HISTORY_JOBS.map(job => `
              <div class="garage-history-row" data-job="${job.key}">
                <span>${escape(job.label[LANG_INDEX[state.language] ?? 0])}</span>
                <input type="date" name="h_date_${job.key}" aria-label="${escape(t('date'))}">
                <input type="number" min="0" name="h_km_${job.key}" placeholder="${unit()}" aria-label="${escape(t('odometer'))}">
                <label class="garage-dont-know"><input type="checkbox" name="h_unknown_${job.key}" checked> ${escape(t('dontKnow'))}</label>
              </div>`).join('')}
          </fieldset>
          <button class="button primary" type="submit">${escape(t('save'))}</button>` : ''}
        </form>` : ''}
      </section>`, {active: 'garage'});
  }

  function defaultRegion() {
    return {en: 'US', az: 'AZ'}[state.language] || 'CIS';
  }

  async function renderCar(id) {
    await ensureSession();
    const v = await api(`/garage/vehicles/${encodeURIComponent(id)}?${lang()}`);
    state.garageVehicle = v;
    const oil = v.services.find(s => s.job === 'engine_oil_and_filter');
    const others = v.services.filter(s => s !== oil);
    const mechanic = state.meta?.ai_mechanic_v1?.enabled ? await api(`/garage/vehicles/${encodeURIComponent(id)}/mechanic`).catch(() => null) : null;
    const clubLink = clubButton ? await clubButton(id).catch(() => '') : '';
    const jobs = [...new Map([...v.main_jobs, ...v.services.map(s => ({job: s.job, label: s.label}))].map(j => [j.job, j])).values()];
    root.innerHTML = layout(`
      <section class="garage garage-car">
        ${heading(v.nickname || v.title, v.configuration || '')}
        ${v.vin ? `<p class="garage-vin">VIN ${escape(v.vin)}</p>` : ''}
        ${clubLink}
        <section class="garage-panel garage-summary">
          <div><span>${escape(t('mileage'))}</span><strong>${escape(v.mileage.text || '—')}</strong>${v.mileage.estimated ? `<small class="garage-mark">${escape(t('estimated'))}</small>` : ''}${v.mileage.monthly_text ? `<small>${escape(v.mileage.monthly_text)} ${escape(t('perMonth'))}</small>` : ''}</div>
          <form id="garage-odometer-form" class="garage-inline"><input name="value" type="number" min="0" placeholder="${unit()}" required><button class="button" type="submit">${escape(t('update'))}</button></form>
          <div class="garage-conditions">
            <span>${escape(t('conditions'))}</span>
            <div class="garage-toggle" role="group">
              ${['NORMAL', 'SEVERE'].map(c => `<button data-action="garage-conditions" data-value="${c}" class="${v.conditions.value === c ? 'selected' : ''}">${escape(t(c.toLowerCase()))}</button>`).join('')}
            </div>
            <small>${escape(v.conditions.note || t('conditionsNote'))}</small>
          </div>
        </section>
        ${v.schedule_note ? `<p class="garage-note">${escape(v.schedule_note)}</p>` : ''}
        ${oil ? oilPanel(oil) : ''}
        ${others.length ? `<section class="garage-panel">
          <h2>${escape(t('next'))}</h2>
          <ul class="garage-services">${others.map(serviceRow).join('')}</ul>
        </section>` : ''}
        ${v.fluids.length ? `<section class="garage-panel"><h2>${escape(t('fluids'))}</h2><dl class="garage-fluids">${v.fluids.map(f => `<div><dt>${escape(f.label)}</dt><dd>${escape([f.spec, f.capacity].filter(Boolean).join(' · '))}${f.secondary && v.labels ? ` <small class="garage-mark">${escape(v.labels.secondary)}</small>` : ''}</dd></div>`).join('')}</dl></section>` : ''}
        <section class="garage-panel">
          <h2>${escape(t('recalls'))}</h2>
          ${v.recalls.length ? `<ul class="garage-recalls">${v.recalls.map(r => `<li><strong>${escape(r.number)}</strong> ${r.label ? `<span class="garage-pill soon">${escape(r.label)}</span>` : ''}<span>${escape(r.component || '')}</span>${r.summary ? `<p>${escape(r.summary)}</p>` : ''}<small>${escape(r.note)}</small></li>`).join('')}</ul>` : `<p class="garage-empty">${escape(t('noRecalls'))}</p>`}
        </section>
        ${mechanic ? mechanicPanel(mechanic) : ''}
        ${v.locked?.PERSONAL_HINTS !== undefined && lockedPanel ? lockedPanel(v.locked.PERSONAL_HINTS) : ''}
        ${v.weak_points.length ? `<section class="garage-panel"><h2>${escape(t('issues'))}</h2><ul class="garage-issues">${v.weak_points.slice(0, 8).map(issueRow).join('')}</ul></section>` : ''}
        <section class="garage-panel">
          <h2>${escape(t('log'))}</h2>
          <form id="garage-record-form" class="garage-record-form">
            <select name="job" aria-label="${escape(t('job'))}">${jobs.map(j => `<option value="${escape(j.job)}">${escape(j.label)}</option>`).join('')}</select>
            <input name="performed_on" type="date" value="${new Date().toISOString().slice(0, 10)}" aria-label="${escape(t('date'))}">
            <input name="odometer" type="number" min="0" placeholder="${unit()}" aria-label="${escape(t('odometer'))}">
            <button class="button" type="submit">${escape(t('logAdd'))}</button>
          </form>
          ${v.log.length ? `<ul class="garage-log">${v.log.map(r => `<li><span>${escape(r.on || '—')}</span><span>${escape(r.km_text || '')}</span><strong>${escape(r.label)}</strong><small>${escape(t(`records.${r.status}`))}</small><button class="link-button" data-action="garage-record-delete" data-id="${escape(r.id)}" aria-label="${escape(t('remove'))}">×</button></li>`).join('')}</ul>` : `<p class="garage-empty">${escape(t('logEmpty'))}</p>`}
          <button class="button" data-action="garage-pdf">${escape(t('pdf'))}</button>
        </section>
        <button class="link-button garage-delete" data-action="garage-delete">${escape(t('remove'))}</button>
      </section>`, {active: 'garage'});
  }

  function serviceRow(s) {
    const fluid = s.fluid ? `<small class="garage-fluid">${escape([s.fluid.spec, s.fluid.capacity].filter(Boolean).join(' · '))}</small>` : '';
    return `<li class="garage-service status-${escape(s.status.toLowerCase())}">
      <div class="garage-service-head"><strong>${escape(s.label)}${s.action_label ? ` · ${escape(s.action_label)}` : ''}</strong>${pill(s.status)}</div>
      <span class="garage-when">${escape(s.when)}</span>
      ${s.advice ? `<p class="garage-advice">${escape(s.advice)}</p>` : ''}
      ${fluid}
      <small class="garage-interval">${escape(s.interval || '')}${s.severe ? ` · ${escape(t('severeMark'))}` : ''}</small>
      ${s.unconfirmed_note ? `<small class="garage-mark">${escape(s.unconfirmed_note)}</small>` : ''}
      ${s.secondary && state.garageVehicle?.labels ? `<small class="garage-mark">${escape(state.garageVehicle.labels.secondary)}</small>` : ''}
    </li>`;
  }

  function oilPanel(oil) {
    const per = oil.owner_interval || {};
    const shownKm = per.km ? Math.round(state.language === 'en' ? per.km / 1.609344 : per.km) : '';
    return `<section class="garage-panel garage-oil">
      <div class="garage-service-head"><h2>${escape(t('oil'))}</h2>${pill(oil.status)}</div>
      <span class="garage-when">${escape(oil.when)}</span>
      ${oil.fluid ? `<small class="garage-fluid">${escape([oil.fluid.spec, oil.fluid.capacity].filter(Boolean).join(' · '))}</small>` : ''}
      ${oil.unconfirmed_note ? `<small class="garage-mark">${escape(oil.unconfirmed_note)}</small>` : ''}
      <form id="garage-oil-form" class="garage-inline">
        <label>${escape(t('oilInterval'))}<span><input name="oil_interval" type="number" min="0" value="${escape(shownKm)}" placeholder="${unit()}"> ${unit()} · <input name="oil_interval_months" type="number" min="0" max="60" value="${escape(per.months || '')}"> ${escape(t('months'))}</span></label>
        <button class="button" type="submit">${escape(t('save'))}</button>
      </form>
      ${oil.hints?.length ? `<p class="garage-hints"><span>${escape(t('manualSays'))}:</span> ${oil.hints.map(h => escape([h.interval, h.max_interval && `≤ ${h.max_interval}`, h.system, h.severe ? t('severeMark') : ''].filter(Boolean).join(' · '))).join('; ')}</p>` : ''}
      ${oil.onboard ? `<button class="button" data-action="garage-onboard-reset">${escape(t('onboardReset'))}</button>` : ''}
    </section>`;
  }

  function mechanicPanel(m) {
    const examples = C.examples.map(e => e[LANG_INDEX[state.language] ?? 0]);
    return `<section class="garage-panel garage-mechanic" id="garage-mechanic">
      <div class="garage-service-head"><h2>${escape(t('mechanic'))}</h2><small class="garage-limit">${m.used}/${m.limit} ${escape(t('questionsLeft'))}</small></div>
      <small>${escape(t('mechanicNote'))}</small>
      <div class="garage-mechanic-thread">${m.items.map(answerHtml).join('')}</div>
      <div class="garage-examples">${examples.map(e => `<button class="garage-chip" data-action="garage-mechanic-example" data-question="${escape(e)}">${escape(e)}</button>`).join('')}</div>
      <form id="garage-mechanic-form" class="garage-inline garage-ask">
        <input name="question" maxlength="600" required placeholder="${escape(t('askPlaceholder'))}">
        <button class="button primary" type="submit">${escape(t('ask'))}</button>
      </form>
    </section>`;
  }

  function answerHtml(a) {
    const facts = a.answer?.length ? `<ul class="garage-answer">${a.answer.map(item => `<li>${escape(item.text)}
      <small class="garage-cite">${item.facts.map(f => escape([f.source, f.note].filter(Boolean).join(' · ') || f.id)).join(' | ')}</small></li>`).join('')}</ul>` : '';
    const general = a.general?.length ? `<div class="garage-general"><strong>${escape(t('general'))}</strong>${a.general.map(g => `<p>${escape(g.text)}</p>`).join('')}</div>` : '';
    const missing = a.not_in_data?.length ? `<div class="garage-missing"><strong>${escape(t('notInData'))}</strong>${a.not_in_data.map(x => `<p>${escape(x)}</p>`).join('')}</div>` : '';
    return `<article class="garage-qa"><p class="garage-question">${escape(a.question)}</p>${a.mode_note ? `<small class="garage-mark">${escape(a.mode_note)}</small>` : ''}${facts}${general}${missing}<small class="garage-disclaimer">${escape(a.disclaimer || '')}</small></article>`;
  }

  function issueRow(i) {
    return `<li><strong>${escape(i.title)}</strong>${i.note ? ` <small class="garage-mark">${escape(i.note)}</small>` : ''}
      ${i.typical ? `<small class="garage-typical">${escape(i.typical)}</small>` : ''}
      ${i.symptoms?.length ? `<span><em>${escape(t('symptoms'))}:</em> ${escape(i.symptoms.slice(0, 3).join('; '))}</span>` : ''}
      ${i.how_to_check ? `<span><em>${escape(t('check'))}:</em> ${escape(i.how_to_check)}</span>` : ''}</li>`;
  }

  async function submitVin(form) {
    const vin = new FormData(form).get('vin').trim().toUpperCase();
    draft.vin = vin;
    const result = await api(`/garage/vin/${encodeURIComponent(vin)}?${lang()}`);
    draft.decoded = result.decode.valid ? result.decode : null;
    draft.candidates = result.candidates;
    draft.searched = true;
    if (!result.decode.valid) showToast(result.decode.errors.join(', '));
    await renderAdd();
  }

  async function submitAdd(form) {
    const data = new FormData(form);
    const history = HISTORY_JOBS.map(job => {
      const unknown = data.get(`h_unknown_${job.key}`) === 'on';
      const on = data.get(`h_date_${job.key}`);
      const km = data.get(`h_km_${job.key}`);
      if (unknown && !on && !km) return {job: job.key, status: 'UNKNOWN'};
      if (!on && !km) return null;
      return {job: job.key, status: 'DONE', performed_on: on || null, odometer: km ? Number(km) : null};
    }).filter(Boolean);
    const body = {configuration_key: data.get('configuration_key'), vin: draft.decoded?.vin || null, odometer: Number(data.get('odometer')),
                  unit: unit(), monthly: data.get('monthly') ? Number(data.get('monthly')) : null, region: data.get('region'),
                  in_service_date: data.get('in_service_date') || null, history};
    const view = await api(`/garage/vehicles?${lang()}`, {method: 'POST', body: JSON.stringify(body)});
    Object.assign(draft, {decoded: null, candidates: [], chosen: null, searched: false, vin: '', make: '', model: '', year: ''});
    go(`/garage-car/${view.id}`);
  }

  async function patchVehicle(body) {
    const id = state.garageVehicle.id;
    await api(`/garage/vehicles/${encodeURIComponent(id)}?${lang()}`, {method: 'PATCH', body: JSON.stringify({unit: unit(), ...body})});
    await renderCar(id);
  }

  async function submit(form) {
    const data = new FormData(form);
    const id = state.garageVehicle?.id;
    if (form.id === 'garage-vin-form') return submitVin(form);
    if (form.id === 'garage-add-form') return submitAdd(form);
    if (form.id === 'garage-odometer-form') {
      await api(`/garage/vehicles/${encodeURIComponent(id)}/odometer?${lang()}`, {method: 'POST', body: JSON.stringify({value: Number(data.get('value')), unit: unit()})});
      return renderCar(id);
    }
    if (form.id === 'garage-oil-form') {
      return patchVehicle({oil_interval: data.get('oil_interval') ? Number(data.get('oil_interval')) : null,
                           oil_interval_months: data.get('oil_interval_months') ? Number(data.get('oil_interval_months')) : null});
    }
    if (form.id === 'garage-mechanic-form') {
      const button = form.querySelector('button');
      button.disabled = true;
      try {
        await api(`/garage/vehicles/${encodeURIComponent(id)}/mechanic?${lang()}`, {method: 'POST', body: JSON.stringify({question: data.get('question')})});
      } catch (error) {
        if (error.status === 402) throw error;
        showToast(error.payload?.detail?.message || error.message);
      }
      await renderCar(id);
      document.querySelector('#garage-mechanic')?.scrollIntoView({block: 'start'});
      return true;
    }
    if (form.id === 'garage-record-form') {
      await api(`/garage/vehicles/${encodeURIComponent(id)}/records?${lang()}`, {method: 'POST', body: JSON.stringify({
        job: data.get('job'), performed_on: data.get('performed_on') || null, odometer: data.get('odometer') ? Number(data.get('odometer')) : null, unit: unit()})});
      return renderCar(id);
    }
    return false;
  }

  return {
    enabled,
    async route(name, id) {
      if (!enabled() || !['garage', 'garage-add', 'garage-car', 'garage-feed'].includes(name)) return false;
      if (name === 'garage') await renderList();
      else if (name === 'garage-add') await renderAdd();
      else if (name === 'garage-feed') await renderFeed();
      else await renderCar(id);
      return true;
    },
    async action(target) {
      const action = target.dataset.action;
      if (!action?.startsWith('garage') || !enabled()) return false;
      const id = state.garageVehicle?.id;
      if (action === 'garage') go('/garage');
      else if (action === 'garage-add') go('/garage-add');
      else if (action === 'garage-feed') go('/garage-feed');
      else if (action === 'garage-car') go(`/garage-car/${target.dataset.id}`);
      else if (action === 'garage-feed-open') {
        await api(`/garage/feed/${encodeURIComponent(target.dataset.id)}/read`, {method: 'POST'});
        go(`/garage-car/${target.dataset.vehicle}`);
      } else if (action === 'garage-mechanic-example') {
        const form = document.querySelector('#garage-mechanic-form');
        form.question.value = target.dataset.question;
        await submit(form);
      } else if (action === 'garage-conditions') await patchVehicle({conditions: target.dataset.value});
      else if (action === 'garage-onboard-reset') {
        const km = state.garageVehicle.mileage.km;
        await api(`/garage/vehicles/${encodeURIComponent(id)}/onboard-reset?${lang()}`, {method: 'POST', body: JSON.stringify({value: km || 0, unit: 'km'})});
        await renderCar(id);
      } else if (action === 'garage-record-delete') {
        await api(`/garage/vehicles/${encodeURIComponent(id)}/records/${encodeURIComponent(target.dataset.id)}?${lang()}`, {method: 'DELETE'});
        await renderCar(id);
      } else if (action === 'garage-pdf') {
        const v = state.garageVehicle;
        await downloadFile(`/garage/vehicles/${encodeURIComponent(id)}/service-log.pdf?${lang()}`, `AutoExpert_service_log_${v.title.replaceAll(' ', '_')}.pdf`);
      } else if (action === 'garage-delete') {
        await api(`/garage/vehicles/${encodeURIComponent(id)}`, {method: 'DELETE'});
        go('/garage');
      }
      return true;
    },
    async change(target) {
      const field = target.dataset.garagePick;
      if (!field || !enabled()) return false;
      draft[field] = target.value;
      if (field === 'make') {draft.model = ''; draft.year = '';}
      if (field === 'model') draft.year = '';
      draft.candidates = [];
      draft.searched = false;
      if (draft.make && draft.model && draft.year) {
        draft.candidates = await api(`/garage/catalog/configurations?make=${encodeURIComponent(draft.make)}&model=${encodeURIComponent(draft.model)}&year=${encodeURIComponent(draft.year)}&${lang()}`);
        draft.decoded = null;
        draft.searched = true;
      }
      await renderAdd();
      return true;
    },
    submit,
    homeCard() {
      if (!enabled()) return '';
      return `<button class="buyer-entrance garage-entrance" data-action="garage"><span class="entrance-number">04</span><span><strong>${escape(t('garage'))}</strong><small>${escape(t('subtitle'))}</small></span><span class="entrance-arrow">›</span></button>`;
    },
    navLabel: () => t('garage'),
  };
}

// The main jobs asked about when a car is added; jobs the car's schedule does not have are simply
// not reminded (the server keeps only the jobs of the schedule).
const HISTORY_JOBS = [
  {key: 'engine_oil_and_filter', label: ['Масло и фильтр', 'Yağ və filtr', 'Oil and filter']},
  {key: 'spark_plugs', label: ['Свечи зажигания', 'Alışdırma şamları', 'Spark plugs']},
  {key: 'transmission_fluid', label: ['Жидкость АКПП', 'Avtomatik qutunun mayesi', 'Transmission fluid']},
  {key: 'engine_coolant', label: ['Охлаждающая жидкость', 'Soyuducu maye', 'Coolant']},
  {key: 'brake_fluid', label: ['Тормозная жидкость', 'Əyləc mayesi', 'Brake fluid']},
  {key: 'timing_belt', label: ['Ремень ГРМ', 'Qazpaylama kəməri', 'Timing belt']},
  {key: 'engine_air_filter', label: ['Воздушный фильтр', 'Hava filtri', 'Engine air filter']},
  {key: 'cabin_air_filter', label: ['Салонный фильтр', 'Salon filtri', 'Cabin air filter']},
];
