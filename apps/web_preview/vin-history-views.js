import {EN, pickText} from './en-text.js?v=0.10.0';
import {api, privateImageUrl} from './api.js?v=0.8.1';

// VIN-history checkout is intentionally separate from the legacy demo dossier.
// The server decides entitlement and which provider facts can be displayed.
export function createVinHistoryViews({root, state, layout, go, esc, ensureSession, showToast, maskVin, formatMoney}) {
  const assetUrls = new Map();
  const l = (ru, az, en) => pickText(state.language, ru, az, en);
  const qaMode = () => state.meta?.qa_mode === true;
  const title = (check) => [
    check.vehicle_identity?.model_year || check.vehicle_identity?.year,
    check.vehicle_identity?.make,
    check.vehicle_identity?.model,
  ].filter(Boolean).join(' ') || `VIN ${maskVin(check.vin)}`;
  const pending = new Set();

  function releaseAssets() {
    for (const url of assetUrls.values()) URL.revokeObjectURL(url);
    assetUrls.clear();
  }

  async function start(vin) {
    if (!qaMode()) return;
    await ensureSession();
    const check = await api('/vin/history/checks', {
      method: 'POST', body: JSON.stringify({vin, language: state.language}),
    });
    localStorage.setItem('autoexpert.vin_history.last_check', check.check_id);
    go(`/history-preview/${check.check_id}`);
  }

  async function route(name, id) {
    releaseAssets();
    if (!['history-preview', 'history-payment', 'history-report'].includes(name)) return false;
    if (!qaMode()) {go('/reports');return true;}
    await ensureSession();
    if (name === 'history-report') await renderReport(id);
    else {
      const check = await api(`/vin/history/checks/${encodeURIComponent(id)}`);
      if (name === 'history-payment') renderPayment(check);
      else renderPreview(check);
    }
    return true;
  }

  function renderPreview(check) {
    const p = check.preview || {};
    const signals = [];
    if (Number.isInteger(p.photo_count) && p.photo_count > 0) signals.push(l(`Подтверждено фотографий: ${p.photo_count}`, `Təsdiqlənmiş foto: ${p.photo_count}`));
    if (Number.isInteger(p.odometer_event_count) && p.odometer_event_count > 0) signals.push(l(`Подтверждено записей пробега: ${p.odometer_event_count}`, `Təsdiqlənmiş yürüş qeydləri: ${p.odometer_event_count}`));
    if (p.damage_records_available === true) signals.push(l('Подтверждены записи о повреждениях', 'Zədə qeydləri təsdiqlənib'));
    if (p.title_records_available === true) signals.push(l('Подтверждены записи о правовом статусе', 'Hüquqi status qeydləri təsdiqlənib'));
    const limitations = (p.coverage_limitations || []).filter(Boolean);
    const canContinue = qaMode() && check.is_mock && check.quote?.sellable && check.quote?.is_mock_scenario;
    const action = check.is_unlocked
      ? `<button class="button gold full" data-action="history-open" data-check="${esc(check.check_id)}">${esc(l('Открыть отчёт', 'Hesabatı aç'))}</button>`
      : canContinue
        ? `<button class="button gold full" data-action="history-pay" data-check="${esc(check.check_id)}">${esc(l('Продолжить к тестовой оплате', 'Test ödənişinə davam et'))}</button>`
        : `<p class="coverage-note">${esc(l('Оформление отчёта пока недоступно.', 'Hesabatın sifarişi hələlik mümkün deyil.'))}</p>`;
    root.innerHTML = layout(`
      <section class="page-heading"><button class="back-button" data-action="back">‹</button><div><h1>${esc(l('Проверка конкретной машины', 'Konkret avtomobilin yoxlanması'))}</h1><p>${esc(title(check))}</p></div></section>
      <section class="teaser-hero"><span class="eyebrow">VIN ${esc(maskVin(check.vin))}</span><h1>${esc(title(check))}</h1>${qaMode() && check.is_mock ? `<span class="pill">${esc(l('ТЕСТОВЫЙ ПРОВАЙДЕР', 'TEST PROVAYDER'))}</span>` : ''}
        ${signals.length ? `<div class="signal-grid">${signals.map(s => `<div class="signal"><strong>${esc(s)}</strong></div>`).join('')}</div>` : ''}
      </section>
      <section class="teaser-copy card"><strong>${esc(l('Что доступно до оплаты', 'Ödənişdən əvvəl nə məlumdur'))}</strong>
        <p>${esc(signals.length ? l('Показаны только сведения, подтверждённые предварительной проверкой.', 'Yalnız ilkin yoxlama ilə təsdiqlənən məlumatlar göstərilir.') : l('Состав конкретных записей определяется после запроса провайдера.', 'Konkret qeydlərin tərkibi provayder sorğusundan sonra müəyyən edilir.'))}</p>
        ${p.content_determined_after_purchase && signals.length ? `<p>${esc(l('Остальные записи определяются после запроса провайдера.', 'Digər qeydlər provayder sorğusundan sonra müəyyən edilir.'))}</p>` : ''}
        ${limitations.length ? `<p class="coverage-note">${esc(l('Покрытие источника ограничено; выводы относятся только к найденным записям.', 'Mənbə əhatəsi məhduddur; nəticələr yalnız tapılan qeydlərə aiddir.'))}</p>` : ''}
      </section>
      ${signals.length ? `<section class="locked-preview card"><div class="locked-preview-head"><span aria-hidden="true">🔒</span><div><h2>${esc(l('Защищённый отчёт', 'Qorunan hesabat'))}</h2><p>${esc(l('Ниже показаны только разделы, подтверждённые предварительной проверкой.', 'Aşağıda yalnız ilkin yoxlama ilə təsdiqlənən bölmələr göstərilir.'))}</p></div></div><div class="locked-capabilities">${signals.map(s=>`<div><span aria-hidden="true">▦</span><strong>${esc(s)}</strong><span aria-hidden="true">🔒</span></div>`).join('')}</div></section>` : ''}
      ${check.status === 'FAILED_RETRYABLE' ? `<button class="button secondary full" data-action="history-retry" data-check="${esc(check.check_id)}">${esc(l('Повторить получение отчёта', 'Hesabatı yenidən əldə et'))}</button>` : ''}
      <div class="sticky-actions v2-sticky">${action}${qaMode() && check.is_mock ? `<small>${esc(l('Демонстрационный сценарий: деньги не списываются.', 'Nümayiş ssenarisi: pul tutulmur.'))}</small>` : ''}</div>
    `, {nav: false});
  }

  function renderPayment(check) {
    if (check.is_unlocked) { go(`/history-report/${check.check_id}`); return; }
    if (!qaMode() || !check.is_mock || !check.quote?.sellable || !check.quote?.is_mock_scenario) {go(`/history-preview/${check.check_id}`); return;}
    root.innerHTML = layout(`
      <section class="page-heading"><button class="back-button" data-action="back">‹</button><div><h1>${esc(l('Тестовая оплата', 'Test ödənişi'))}</h1><p>${esc(title(check))}</p></div></section>
      <section class="payment-card"><div class="payment-shield">✓</div><span class="pill">MOCK / SANDBOX</span>
        <h2>${formatMoney(check.quote.retail_price_azn, check.quote.currency || 'AZN')}</h2>
        <p>${esc(l('Это проверка сценария без реального списания и без платного API-запроса.', 'Bu, real ödəniş və pullu API sorğusu olmadan ssenari yoxlamasıdır.'))}</p>
        <button class="button gold full" data-action="history-confirm" data-check="${esc(check.check_id)}">${esc(l('Получить тестовый отчёт', 'Test hesabatını al'))}</button>
      </section>
    `, {nav: false});
  }

  function mileageChart(points) {
    if (!Array.isArray(points) || points.length < 2) return '';
    const dated = points.filter(p => p.date && Number.isFinite(Number(p.mileage_km))).sort((a, b) => String(a.date).localeCompare(String(b.date)));
    if (dated.length < 2) return '';
    const max = Math.max(1, ...dated.map(p => Number(p.mileage_km)));
    const coordinates = dated.map((p, i) => {
      const x = 18 + i * 284 / (dated.length - 1);
      const y = 84 - Number(p.mileage_km) * 68 / max;
      return {x, y};
    });
    return `<section class="card"><strong>${esc(l('Хронология пробега', 'Yürüş xronologiyası'))}</strong>
      <svg viewBox="0 0 320 100" role="img" aria-label="${esc(l('График датированных показаний пробега', 'Tarixli yürüş göstəricilərinin qrafiki'))}"><path d="M18 84H302" stroke="#b8cbe6"/><polyline fill="none" stroke="#065bf3" stroke-width="3" points="${coordinates.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')}"/>${coordinates.map(p => `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4" fill="#065bf3"/>`).join('')}</svg>
      <div class="report-list">${dated.map(p => `<p>${esc(p.date)} · ${esc(new Intl.NumberFormat(state.language).format(Number(p.original_value ?? p.mileage_km)))} ${esc(p.original_unit || 'km')}</p>`).join('')}</div>
    </section>`;
  }

  async function renderReport(id) {
    const report = await api(`/vin/history/checks/${encodeURIComponent(id)}/report?language=${encodeURIComponent(state.language)}`);
    const sections = (report.sections || []).filter(s => Array.isArray(s.items) && s.items.length);
    const assets = report.assets || [];
    const photoTypeLabel = {
      RETAIL_PHOTO: l('Фото объявления', 'Elan fotosu'),
      WHOLESALE_PHOTO: l('Аукционное фото', 'Hərrac fotosu'),
      HISTORICAL_PHOTO: l('Историческое фото', 'Tarixi foto'),
    };
    root.innerHTML = layout(`
      <section class="report-cover v2-cover">${qaMode() && report.is_mock ? '<span class="pill">MOCK / SANDBOX</span>' : ''}<p class="eyebrow">VIN ${esc(maskVin(report.vin))}</p>
        <h1>${esc(title(report))}</h1><p>${esc(l('История конкретной машины', 'Konkret avtomobilin tarixçəsi'))}</p></section>
      ${report.mileage_anomaly ? `<section class="coverage-note">${esc(l('Обнаружена аномалия последовательности пробега. Проверьте исходные показания.', 'Yürüş ardıcıllığında uyğunsuzluq aşkarlandı. İlkin göstəriciləri yoxlayın.'))}</section>` : ''}
      ${mileageChart(report.odometer_points)}
      <div class="dossier-stack">${sections.map(s => `<section class="card"><h2>${esc(s.title)}</h2>${s.items.map(item => `<p>${item.date ? `<time>${esc(item.date)}</time> · ` : ''}${esc(item.text)}</p>`).join('')}</section>`).join('')}</div>
      ${assets.length ? `<section class="card"><h2>${esc(l('Фотографии из отчёта', 'Hesabat fotoları'))}</h2><div class="photo-gallery">${assets.map(asset => `<figure><button class="ghost-button" data-action="history-zoom" data-asset="${esc(asset.id)}"><img data-history-asset="${esc(asset.id)}" alt="${esc(asset.caption || photoTypeLabel[asset.photo_type] || l('Фото из отчёта', 'Hesabat fotosu'))}" loading="lazy"></button><figcaption>${esc([photoTypeLabel[asset.photo_type], asset.event_date, asset.source, asset.caption].filter(Boolean).join(' · '))}</figcaption></figure>`).join('')}</div></section>` : ''}
      <section class="coverage-note">${esc(qaMode() && report.is_mock ? l('Тестовый отчёт. Выводы ограничены подтверждёнными событиями источника.', 'Test hesabatı. Nəticələr mənbənin təsdiqlədiyi hadisələrlə məhdudlaşır.') : l('Выводы ограничены подтверждёнными событиями источника.', 'Nəticələr mənbənin təsdiqlədiyi hadisələrlə məhdudlaşır.'))}</section>
    `, {active: 'reports', wide: true});
    for (const asset of assets) {
      const assetId = asset.id;
      try {
        const url = await privateImageUrl(`/vin/history/checks/${encodeURIComponent(id)}/assets/${encodeURIComponent(assetId)}`);
        assetUrls.set(assetId, url);
        const image = root.querySelector(`[data-history-asset="${CSS.escape(assetId)}"]`);
        if (image) image.src = url;
      } catch { // Asset rights or access can change; never substitute a generic vehicle photo.
        root.querySelector(`[data-history-asset="${CSS.escape(assetId)}"]`)?.closest('button')?.remove();
      }
    }
  }

  async function savedCards() {
    await ensureSession();
    const checks = await api('/vin/history/checks');
    return checks.filter(check => qaMode() || !check.is_mock).map(check => `<article class="report-card"><div>${qaMode() && check.is_mock ? '<span class="pill">MOCK / SANDBOX</span>' : ''}<span class="status ${check.is_unlocked ? 'status-confirmed' : 'status-insufficient_data'}">${esc(check.is_unlocked ? l('Открыт', 'Açıqdır') : l('Ожидает', 'Gözləyir'))}</span></div>
      <h2>${esc(title(check))}</h2><code>${esc(maskVin(check.vin))}</code>
      <button class="button secondary full" data-action="history-open-saved" data-check="${esc(check.check_id)}" data-unlocked="${check.is_unlocked}">${esc(l('Открыть', 'Aç'))}</button></article>`).join('');
  }

  async function action(target) {
    const id = target.dataset.check;
    const action = target.dataset.action;
    if (action === 'history-pay') {go(`/history-payment/${id}`); return true;}
    if (action === 'history-open') {go(`/history-report/${id}`); return true;}
    if (action === 'history-open-saved') {go(`/${target.dataset.unlocked === 'true' ? 'history-report' : 'history-preview'}/${id}`); return true;}
    if (action === 'history-zoom') {
      const url = assetUrls.get(target.dataset.asset);
      if (url) window.open(url, '_blank', 'noopener');
      return true;
    }
    if (!['history-confirm', 'history-retry'].includes(action)) return false;
    if (!qaMode()) return true;
    if (pending.has(id)) return true;
    pending.add(id); target.disabled = true;
    try {
      const path = action === 'history-confirm' ? 'payments/mock' : 'retry';
      const check = await api(`/vin/history/checks/${encodeURIComponent(id)}/${path}`, {
        method: 'POST', body: action === 'history-confirm' ? JSON.stringify({simulate_failure: false}) : '{}',
      });
      if (check.is_unlocked && ['REPORT_READY', 'PARTIAL'].includes(check.status)) go(`/history-report/${id}`);
      else {go(`/history-preview/${id}`); showToast(l('Статус запроса обновлён', 'Sorğunun statusu yeniləndi'));}
    } finally {pending.delete(id); target.disabled = false;}
    return true;
  }

  return {start, route, savedCards, action};
}
