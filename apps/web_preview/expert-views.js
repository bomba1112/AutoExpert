// "Проверить конкретную машину" and "Мнение Auto Expert" (UI-by-reference prompt, sections 2.1 and 3):
// one field for a VIN, a plate or a listing link (recognised by itself), a manual form, and the
// opinion screen. The listing text is asked for only when the site could not be read.
import {pickText} from './en-text.js?v=0.14.0';
import {api} from './api.js?v=0.14.0';
import {detectInput, flag, money, region} from './ui-config.js?v=0.14.0';
import {icon, carPhoto, photoCredit} from './visual.js?v=0.14.0';

const STORE = 'autoexpert.expert.request';
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));

export function createExpertViews({root, state, layout, go, ensureSession, showToast, garage = null, usTech = null}) {
  const enabled = () => state.meta?.expert_opinion_v1?.enabled === true;
  const p = (ru, az, en) => pickText(state.language, ru, az, en);
  const lang = () => (['az', 'en'].includes(state.language) ? state.language : 'ru');
  const az = () => region(state) === 'AZ';
  let last = null;  // {request, result}

  const kindLabel = kind => ({
    LINK: p('Ссылка на объявление', 'Elan keçidi', 'Listing link'),
    VIN: 'VIN',
    PLATE: p('Госномер', 'Dövlət nömrəsi', 'Plate number'),
    TEXT: p('Марка, модель и год', 'Marka, model və il', 'Make, model and year'),
    UNKNOWN: p('Не распознано', 'Tanınmadı', 'Not recognised'),
  })[kind] || '';

  function placeholder() {
    return az()
      ? p('VIN, госномер или ссылка Turbo.az', 'VIN, dövlət nömrəsi və ya Turbo.az keçidi', 'VIN, plate or Turbo.az link')
      : p('VIN или госномер', 'VIN və ya dövlət nömrəsi', 'VIN or plate number');
  }

  // the one field (the home card uses it too)
  function checkField(id = 'expert-check') {
    return `<form id="${id}" class="ae-check-field" data-expert-form autocomplete="off">
      <label class="sr-only" for="${id}-q">${escape(placeholder())}</label>
      <span class="ae-check-icon">${icon('search')}</span>
      <input id="${id}-q" name="q" maxlength="600" placeholder="${escape(placeholder())}" spellcheck="false" autocapitalize="characters" required>
      <button class="ae-check-go" type="submit" aria-label="${escape(p('Проверить', 'Yoxla', 'Check'))}">${icon('arrow-right')}</button>
      <output class="ae-check-kind" data-expert-kind aria-live="polite"></output>
    </form>`;
  }

  function page(html, active = 'check') {
    root.innerHTML = layout(`<div class="catalog-view ae-view">${html}</div>`, {active});
  }

  function top(title, back = 'home') {
    return `<div class="page-top"><button class="icon-button" data-expert="${back}" aria-label="${escape(p('Назад', 'Geri', 'Back'))}">${icon('arrow-left')}</button><strong>${escape(title)}</strong><span></span></div>`;
  }

  function check() {
    const fuels = [['', p('Не знаю', 'Bilmirəm', "Don't know")], ['Benzin', p('Бензин', 'Benzin', 'Gasoline')], ['Dizel', p('Дизель', 'Dizel', 'Diesel')], ['Hibrid', p('Гибрид', 'Hibrid', 'Hybrid')], ['Elektro', p('Электро', 'Elektro', 'Electric')]];
    const boxes = [['', p('Не знаю', 'Bilmirəm', "Don't know")], ['Avtomat', p('Автомат', 'Avtomat', 'Automatic')], ['Variator', p('Вариатор', 'Variator', 'CVT')], ['Robot', p('Робот', 'Robot', 'Dual-clutch')], ['Mexaniki', p('Механика', 'Mexaniki', 'Manual')]];
    const options = list => list.map(([v, label]) => `<option value="${escape(v)}">${escape(label)}</option>`).join('');
    page(`${top(p('Проверить машину', 'Avtomobili yoxla', 'Check a car'))}
      <section class="ae-hero-dark">
        <h1>${escape(p('Проверить конкретную машину', 'Konkret avtomobili yoxla', 'Check a specific car'))}</h1>
        <p>${escape(az() ? p('Вставьте VIN, госномер или ссылку на объявление Turbo.az — мы сами поймём, что это.', 'VIN, dövlət nömrəsi və ya Turbo.az elanının keçidini daxil edin — nə olduğunu özümüz anlayacağıq.', 'Paste a VIN, a plate or a Turbo.az listing link — we work out which it is.') : p('Вставьте VIN или госномер — мы сами поймём, что это.', 'VIN və ya dövlət nömrəsini daxil edin.', 'Paste a VIN or a plate number — we work out which it is.'))}</p>
        ${checkField()}
        <ul class="ae-check-gives">${[p('Что за версия', 'Hansı versiya', 'Which version'), p('Слабые места', 'Zəif yerlər', 'Weak points'), p('Отзывные кампании', 'Geri çağırmalar', 'Recalls'), p('ТО по пробегу', 'Yürüşə görə TXQ', 'Service by mileage')].map(x => `<li>${escape(x)}</li>`).join('')}</ul>
      </section>
      <details class="catalog-card ae-manual" ${last?.request?.manual ? 'open' : ''}>
        <summary>${escape(p('Нет VIN и ссылки? Ввести вручную', 'VIN və keçid yoxdur? Əllə daxil edin', 'No VIN or link? Enter it yourself'))}</summary>
        <form id="expert-manual" class="ae-manual-form">
          <div class="form-pair"><label>${escape(p('Марка', 'Marka', 'Make'))}<input name="make" required maxlength="60" placeholder="Toyota"></label><label>${escape(p('Модель', 'Model', 'Model'))}<input name="model" required maxlength="80" placeholder="Camry"></label></div>
          <div class="form-pair"><label>${escape(p('Год', 'İl', 'Year'))}<input name="year" type="number" min="1980" max="2100" inputmode="numeric" placeholder="2018"></label><label>${escape(p('Объём, л', 'Həcm, l', 'Engine, L'))}<input name="engine" inputmode="decimal" maxlength="10" placeholder="2.5"></label></div>
          <div class="form-pair"><label>${escape(p('Топливо', 'Yanacaq', 'Fuel'))}<select name="fuel">${options(fuels)}</select></label><label>${escape(p('Коробка', 'Sürətlər qutusu', 'Gearbox'))}<select name="transmission">${options(boxes)}</select></label></div>
          <label>${escape(p('Пробег, км', 'Yürüş, km', 'Mileage, km'))}<input name="mileage_km" type="number" min="0" max="3000000" inputmode="numeric"></label>
          <button class="button primary full" type="submit">${escape(p('Получить мнение', 'Rəy al', 'Get the opinion'))}${icon('arrow-right')}</button>
          <p class="catalog-note">${escape(p('Обязательны только марка и модель. Остальное — если знаете.', 'Yalnız marka və model məcburidir.', 'Only the make and the model are required.'))}</p>
        </form>
      </details>
      ${flag('listingPaste') && az() ? `<button class="button secondary full" data-expert="legacy-check">${escape(p('Вставить текст объявления (старый путь)', 'Elan mətni (köhnə yol)', 'Paste listing text (old path)'))}</button>` : ''}`);
  }

  async function request(body) {
    await ensureSession();
    last = {request: body, result: null};
    try { sessionStorage.setItem(STORE, JSON.stringify(body)); } catch {}
    go('/opinion');
  }

  async function opinion() {
    // the stored request is the truth: a result kept in memory is reused only for the very same request,
    // so an opinion never shows the car of an earlier check
    let body = null;
    try { body = JSON.parse(sessionStorage.getItem(STORE) || 'null'); } catch { body = null; }
    body = body || last?.request;
    if (!body) { go('/check'); return; }
    if (last && JSON.stringify(last.request) !== JSON.stringify(body)) last = null;
    page(`${top(p('Мнение Auto Expert', 'Auto Expert rəyi', 'Auto Expert opinion'), 'check')}<p class="catalog-loading" role="status">${escape(body.query && detectInput(body.query) === 'LINK' ? p('Открываем объявление и сверяем с базой…', 'Elanı açırıq və bazayla tutuşdururuq…', 'Opening the listing and checking it against our database…') : p('Сверяем с базой…', 'Bazayla tutuşdururuq…', 'Checking against our database…'))}</p>`);
    await ensureSession();
    const result = last?.result ? last.result : await api('/expert/opinion', {method: 'POST', body: JSON.stringify({...body, language: lang()})});
    last = {request: body, result};
    page(`${top(p('Мнение Auto Expert', 'Auto Expert rəyi', 'Auto Expert opinion'), 'check')}${result.status === 'OK' ? opinionHtml(result) : problemHtml(result, body)}`);
  }

  const row = (label, value) => value === null || value === undefined || value === '' ? '' : `<div><dt>${escape(label)}</dt><dd>${escape(value)}</dd></div>`;
  const km = value => (value || value === 0) ? `${Number(value).toLocaleString(lang() === 'en' ? 'en-US' : 'ru-RU')} ${p('км', 'km', 'km')}` : '';

  function sellerHtml(r) {
    const c = r.claims || {}, raw = c.raw || {};
    const price = c.price ? (c.currency === 'AZN' || !c.currency ? (az() ? money(c.price, state) : `${Math.round(c.price).toLocaleString()} ${c.currency || 'AZN'}`) : `${Math.round(c.price).toLocaleString()} ${c.currency}`) : '';
    const rows = [
      row(p('Цена', 'Qiymət', 'Price'), price),
      row(p('Пробег', 'Yürüş', 'Mileage'), km(c.mileage_km)),
      row(p('Двигатель', 'Mühərrik', 'Engine'), raw.engine || (c.displacement_l ? `${c.displacement_l} L` : '')),
      row(p('Коробка', 'Sürətlər qutusu', 'Gearbox'), raw.transmission || c.transmission),
      row(p('Привод', 'Ötürücü', 'Drive'), raw.drivetrain || c.drivetrain),
      row(p('Для какого рынка собран', 'Hansı bazar üçün yığılıb', 'Built for'), raw.market_claim),
      row(p('Город', 'Şəhər', 'City'), c.city),
      row('VIN', c.vin),
    ].join('');
    if (!rows && !c.description) return '';
    return `<section class="catalog-card ae-seller">${['LINK', 'PASTED_TEXT'].includes(r.source?.kind) ? `<h2>${escape(p('Указано в объявлении', 'Elanda göstərilib', 'Stated in the listing'))}</h2><p class="catalog-note">${escape(p('Это слова продавца — мы их не подтверждаем, а сверяем с базой.', 'Bu satıcının sözləridir — təsdiqləmirik, bazayla tutuşdururuq.', "The seller's words — not confirmed by us; checked against our database."))}</p>` : `<h2>${escape(p('Вы указали', 'Siz göstərdiniz', 'You entered'))}</h2>`}<dl class="ae-rows">${rows}</dl>${c.description ? `<details><summary>${escape(p('Описание продавца', 'Satıcının təsviri', "Seller's description"))}</summary><p>${escape(c.description)}</p></details>` : ''}</section>`;
  }

  function opinionHtml(r) {
    const photo = r.source?.photos?.[0]?.url;
    const title = `${r.make} ${r.model} ${r.year}`;
    const confirmed = r.confirmed;
    const checklist = r.checklist || [];
    const service = r.next_service || [];
    return `
      <section class="ae-car-hero">${photo ? `<img class="ae-photo" src="${escape(photo)}" alt="${escape(title)}" loading="lazy" referrerpolicy="no-referrer">` : `${carPhoto(r.make, r.model, r.year, {alt: title})}${photoCredit(r.make, r.model, r.year, lang())}`}
        <div class="ae-car-hero-text"><h1>${escape(title)}</h1><p>${escape([r.configuration?.label, r.configuration?.generation && `${p('поколение', 'nəsil', 'generation')} ${r.configuration.generation}`].filter(Boolean).join(' · '))}</p></div></section>
      <p class="ae-badges"><span class="ae-badge ${confirmed ? 'ok' : 'warn'}">${escape(confirmed ? p('Модификация подтверждена', 'Modifikasiya təsdiqlənib', 'Version confirmed') : p('Нужно уточнить версию', 'Versiyanı dəqiqləşdirmək lazımdır', 'The version needs confirming'))}</span><span class="ae-badge">${escape(r.source?.kind === 'LINK' ? p('По объявлению', 'Elana görə', 'From the listing') : r.source?.kind === 'VIN' ? p('По VIN · NHTSA vPIC', 'VIN üzrə · NHTSA vPIC', 'By VIN · NHTSA vPIC') : p('По вашим данным', 'Sizin məlumatlara görə', 'From your details'))}</span></p>
      <section class="ae-verdict"><p class="ae-eyebrow">${escape(p('Вывод Auto Expert', 'Auto Expert nəticəsi', 'Auto Expert conclusion'))}</p><ul>${(r.summary || []).map(s => `<li>${escape(s)}</li>`).join('')}</ul></section>
      ${(r.discrepancies || []).length ? `<section class="catalog-card ae-warn-card"><h2>${escape(p('Расхождения с базой', 'Bazayla uyğunsuzluqlar', 'Discrepancies with our database'))}</h2><ul>${r.discrepancies.map(d => `<li>${escape(d.text)}</li>`).join('')}</ul></section>` : ''}
      ${(r.notes || []).map(n => `<p class="catalog-notice">${escape(n)}</p>`).join('')}
      ${!confirmed && r.alternatives?.length ? `<details class="catalog-card"><summary>${escape(p('Какие ещё версии подходят', 'Başqa hansı versiyalar uyğundur', 'Other versions that fit'))} · ${r.alternatives.length}</summary><ul>${r.alternatives.map(a => `<li>${escape(a)}</li>`).join('')}</ul><p class="catalog-note">${escape(p('Мнение ниже — по первой версии; точнее скажет VIN.', 'Aşağıdakı rəy birinci versiyaya görədir; VIN daha dəqiq deyəcək.', 'The opinion below is for the first version; the VIN tells more exactly.'))}</p></details>` : ''}
      ${sellerHtml(r)}
      ${checklist.length ? `<section class="catalog-card ae-checklist"><h2>${escape(p('Что проверить при осмотре', 'Baxışda nəyi yoxlamalı', 'What to check at the inspection'))}</h2><ol>${checklist.map((c, i) => `<li><label><input type="checkbox" data-expert-check="${i}"><span>${escape(c.text)}${c.note ? ` <small class="us-tech-badge secondary">${escape(c.note)}</small>` : ''}</span></label></li>`).join('')}</ol>${r.checklist_more ? `<p class="catalog-note">${escape(p(`Ещё ${r.checklist_more} — в разделах «Слабые места» и «Сервисные кампании» ниже`, `Daha ${r.checklist_more} — aşağıda «Zəif yerlər» və «Servis kampaniyaları» bölmələrində`, `${r.checklist_more} more in the weak points and recalls below`))}</p>` : ''}</section>` : ''}
      ${service.length ? `<section class="catalog-card ae-service"><h2>${escape(['LINK', 'PASTED_TEXT'].includes(r.source?.kind) ? p('Ближайшее ТО по пробегу из объявления', 'Elandakı yürüşə görə ən yaxın TXQ', "Next service by the listing's mileage") : p('Ближайшее ТО по пробегу', 'Yürüşə görə ən yaxın TXQ', 'Next service by mileage'))}</h2><dl class="ae-rows">${service.map(s => `<div><dt>${escape(s.label)}${s.fluid?.spec ? `<small>${escape(s.fluid.spec)}${s.fluid.secondary ? ` · ${escape(r.labels?.secondary || '')}` : ''}</small>` : ''}</dt><dd>${escape(s.status === 'CHECK' ? p('проверить сейчас', 'indi yoxlayın', 'check now') : s.next_km ? `${p('на', '', 'at')} ${km(s.next_km)}`.trim() : '')}${s.interval ? `<small>${escape(s.interval)}</small>` : ''}</dd></div>`).join('')}</dl><p class="catalog-note">${escape(service[0]?.note || '')}</p></section>` : ''}
      ${(r.weak_points || []).length ? `<details class="catalog-card ae-weak"><summary>${escape(p('Слабые места этой версии', 'Bu versiyanın zəif yerləri', 'Weak points of this version'))} · ${r.weak_points.length}</summary>${r.weak_points.map(w => `<article><h3>${escape(w.title)}${w.note ? ` <small class="us-tech-badge secondary">${escape(w.note)}</small>` : ''}</h3><p class="catalog-note">${escape([w.severity, w.probability].filter(Boolean).join(' · '))}</p>${w.symptoms?.length ? `<p>${escape(w.symptoms.join('; '))}</p>` : ''}</article>`).join('')}</details>` : ''}
      ${(r.campaigns || []).length ? `<details class="catalog-card ae-recalls"><summary>${escape(p('Сервисные кампании (отзывы)', 'Servis kampaniyaları', 'Recalls'))} · ${r.campaigns.length}</summary>${r.campaigns.map(c => `<article><h3>${escape(c.number)}${c.component ? ` · ${escape(c.component)}` : ''}</h3>${c.summary ? `<p>${escape(c.summary)}</p>` : ''}<p class="catalog-note">${escape(c.note || '')}</p></article>`).join('')}</details>` : ''}
      <div class="catalog-actions">
        ${r.claims?.vin ? `<button class="button primary full" data-expert="vin-history" data-vin="${escape(r.claims.vin)}">${escape(p('Проверить историю по VIN', 'VIN üzrə tarixçəni yoxla', 'Check the history by VIN'))}</button>` : ''}
        ${usTech?.enabled() && r.configuration?.key ? `<button class="button secondary full" data-expert="configuration" data-key="${escape(r.configuration.key)}">${escape(p('Вся техническая информация', 'Bütün texniki məlumat', 'All technical details'))}</button>` : ''}
        ${garage?.enabled() && r.configuration?.key ? `<button class="button secondary full" data-expert="garage" data-key="${escape(r.configuration.key)}">${escape(p('Добавить в мой гараж', 'Qarajıma əlavə et', 'Add to my garage'))}</button>` : ''}
        <button class="button secondary full" data-expert="check">${escape(p('Проверить другую машину', 'Başqa avtomobili yoxla', 'Check another car'))}</button>
      </div>`;
  }

  function problemHtml(r, body) {
    const tone = r.status === 'MODEL_MISMATCH' ? 'ae-error-card' : 'ae-warn-card';
    const titles = {
      MODEL_MISMATCH: p('Модель не совпадает', 'Model uyğun gəlmir', 'The model does not match'),
      MODEL_NOT_IN_BASE: p('Этой модели пока нет в базе', 'Bu model hələ bazada yoxdur', 'This model is not in our database yet'),
      YEAR_NOT_IN_BASE: p('Этого года пока нет в базе', 'Bu il hələ bazada yoxdur', 'This year is not in our database yet'),
      LISTING_UNAVAILABLE: p('Объявление не открылось', 'Elan açılmadı', 'The listing did not open'),
      LISTING_UNREADABLE: p('Объявление не удалось прочитать', 'Elanı oxumaq olmadı', 'The listing could not be read'),
      PLATE_UNAVAILABLE: p('Проверка по госномеру', 'Dövlət nömrəsi ilə yoxlama', 'Checking by plate'),
      VIN_UNKNOWN: p('VIN не расшифрован', 'VIN deşifrə edilmədi', 'The VIN was not decoded'),
      INPUT_UNKNOWN: p('Не удалось понять, что вставлено', 'Nə daxil edildiyini anlamadıq', 'We could not tell what was pasted'),
    };
    const claims = r.claims && (r.claims.make || r.claims.model) ? `<p class="catalog-note">${escape(p('В объявлении', 'Elanda', 'In the listing'))}: ${escape([r.claims.make, r.claims.model, r.claims.year].filter(Boolean).join(' '))}</p>` : '';
    const paste = r.paste_text ? `<form id="expert-paste" class="catalog-card"><h2>${escape(p('Вставьте текст объявления', 'Elanın mətnini daxil edin', 'Paste the listing text'))}</h2><p class="catalog-note">${escape(p('Откройте объявление, выделите всё (Ctrl+A), скопируйте и вставьте сюда.', 'Elanı açın, hamısını seçin (Ctrl+A), kopyalayıb bura yapışdırın.', 'Open the listing, select all (Ctrl+A), copy and paste it here.'))}</p><textarea name="text" rows="8" maxlength="60000" required></textarea><button class="button primary full" type="submit">${escape(p('Разобрать текст', 'Mətni təhlil et', 'Analyse the text'))}</button></form>` : '';
    return `<section class="catalog-card ${tone}" role="alert"><h2>${escape(titles[r.status] || r.status)}</h2><p>${escape(r.message || '')}</p>${claims}${r.years?.length ? `<p class="catalog-note">${escape(p('Есть годы', 'Mövcud illər', 'Available years'))}: ${escape(r.years.join(', '))}</p>` : ''}</section>${['MODEL_NOT_IN_BASE', 'YEAR_NOT_IN_BASE'].includes(r.status) && r.claims ? sellerHtml(r) : ''}${paste}
      <div class="catalog-actions"><button class="button primary full" data-expert="check">${escape(p('Проверить другую машину', 'Başqa avtomobili yoxla', 'Check another car'))}</button>${body?.query && r.status === 'MODEL_NOT_IN_BASE' ? `<button class="button secondary full" data-expert="pick">${escape(p('Подобрать похожие в каталоге', 'Kataloqda oxşarlarını seç', 'Find similar cars in the catalogue'))}</button>` : ''}</div>`;
  }

  // live hint under the field: what was recognised
  root.addEventListener('input', e => {
    const form = e.target.closest?.('[data-expert-form]');
    if (!form) return;
    const kind = detectInput(e.target.value);
    const out = form.querySelector('[data-expert-kind]');
    if (out) out.textContent = kind ? kindLabel(kind) : '';
  });

  root.addEventListener('submit', e => {
    const form = e.target;
    if (!form.matches?.('[data-expert-form], #expert-manual, #expert-paste')) return;
    e.preventDefault();
    if (!enabled()) { go('/check'); return; }
    const data = new FormData(form);
    let body;
    if (form.id === 'expert-manual') {
      const manual = Object.fromEntries([...data].filter(([, v]) => v !== '').map(([k, v]) => [k, ['year', 'mileage_km'].includes(k) ? Number(v) : String(v).trim()]));
      body = {manual};
    } else if (form.id === 'expert-paste') {
      body = {text: String(data.get('text') || '')};
    } else {
      const q = String(data.get('q') || '').trim();
      if (!q) return;
      body = {query: q};
    }
    void request(body).catch(error => {
      if (error?.loginRequired || error?.status === 401) { go('/profile'); return; }
      showToast(error?.message || p('Ошибка', 'Xəta', 'Error'));
    });
  });

  root.addEventListener('click', e => {
    const target = e.target.closest?.('[data-expert]');
    if (!target) return;
    e.preventDefault();
    const action = target.dataset.expert;
    if (action === 'home') go('/home');
    else if (action === 'check') go('/check');
    else if (action === 'legacy-check') go('/check-legacy/turbo');
    else if (action === 'pick') go('/pick');
    else if (action === 'vin-history') go(`/vin-report/${encodeURIComponent(target.dataset.vin)}`);
    else if (action === 'configuration') go(`/us-tech/${encodeURIComponent(target.dataset.key)}`);
    else if (action === 'garage') {
      const r = last?.result || {};
      garage?.prefill({make: r.make, model: r.model, year: r.year, configuration_key: target.dataset.key, label: r.configuration?.label, vin: r.claims?.vin});
    }
  });

  return {
    enabled,
    checkField,
    render: (result, body = {}) => (result.status === 'OK' ? opinionHtml(result) : problemHtml(result, body)),
    async route(name) {
      if (!enabled() || !['check', 'opinion'].includes(name)) return false;
      if (name === 'check') check();
      else await opinion();
      return true;
    },
  };
}
