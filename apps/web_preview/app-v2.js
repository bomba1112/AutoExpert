import {EN, pickText, deviceLanguage} from './en-text.js?v=0.11.0';
import {
  ApiError,
  api,
  configureDeveloperAccess,
  downloadReportPdf,
  ensureDemoSession,
  fetchClientConfig,
  hasSession,
  trackEvent,
  vehiclePhotoUrl,
} from './api.js?v=0.11.0';
import {
  ResearchContinuation,
  executeResearchContinuation,
  useDemoPrecheck,
} from './research-flow.js?v=0.8.1';
import {createBuyerViews} from './buyer-views.js?v=0.11.0';
import {createCatalogViews} from './catalog-views.js?v=0.11.0';
import {createVinHistoryViews} from './vin-history-views.js?v=0.11.0';
import {createListingViews} from './listing-views.js?v=0.11.0';
import {createUsTechViews} from './us-tech-views.js?v=0.11.0';
import {createGarageViews} from './garage-views.js?v=0.11.0';
import {createClubViews} from './club-views.js?v=0.11.0';
import {createSubscriptionViews} from './subscription-views.js?v=0.11.0';

const root = document.querySelector('#app');
const toastNode = document.querySelector('#toast');
const LANGUAGE_KEY = 'autoexpert.ui.language';
// product phase, stage 1: RU, AZ and EN; the default follows the device (en -> EN, ru -> RU, az -> AZ, else EN)
const SUPPORTED_LANGUAGES = ['en', 'ru', 'az'];
function storedLanguage() {
  try { const value = localStorage.getItem(LANGUAGE_KEY); return SUPPORTED_LANGUAGES.includes(value) ? value : null; } catch { return null; }
}
const LAST_CHECK_KEY = 'autoexpert.v2.last_check';
const LAST_RESEARCH_JOB_KEY = 'autoexpert.v2.last_research_job';
const SIMULATE_PAYWALL_KEY = 'autoexpert.developer.simulate_user_paywall';
const researchContinuationsInFlight = new Set();

const state = {
  language: storedLanguage(),
  pendingLanguage: storedLanguage() || deviceLanguage(),
  copy: {},
  meta: null,
  simulateUserPaywall: false,
  routeVersion: 0,
};
const qaMode = () => state.meta?.qa_mode === true;
const historyViews = createVinHistoryViews({root, state, layout, go, esc, ensureSession, showToast, maskVin, formatMoney});
const buyerViews = createBuyerViews({
  root, state, layout, go, esc, ensureSession, handleError, showToast,
  startMockVinHistory: vin => historyViews.start(vin),
  mockVinHistoryCards: () => historyViews.savedCards(),
  garageEntrance: () => garageViews.homeCard() + (clubViews.enabled() ? `<button class="buyer-entrance" data-action="club"><span class="entrance-number">05</span><span><strong>${esc(clubViews.navLabel())}</strong><small>${esc(pickText(state.language, 'Владельцы таких же машин', 'Eyni avtomobillərin sahibləri', 'Owners of the same cars'))}</small></span><span class="entrance-arrow">›</span></button>` : ''),
});
const usTechViews = createUsTechViews({root, state, layout});
const clubViews = createClubViews({root, state, layout, go, ensureSession, showToast});
const subscriptionViews = createSubscriptionViews({root, state, layout, go, ensureSession, showToast});
const garageViews = createGarageViews({root, state, layout, go, ensureSession, showToast, clubButton: id => clubViews.vehicleRoomsButton(id), lockedPanel: n => subscriptionViews.enabled() ? subscriptionViews.lockedPanel(n) : ''});
const catalogViews = createCatalogViews({root, state, layout, go, esc, ensureSession, showToast, usTech: usTechViews});
const listingViews = createListingViews({root, state, layout, go, esc, ensureSession, showToast, addCatalogVariant:(id,title)=>catalogViews.addVariantToBasket(id,title)});

root.addEventListener('click', (event) => {
  const target = event.target.closest('[data-action]');
  if (!target || target.disabled || target.getAttribute('aria-disabled') === 'true') return;
  event.preventDefault();
  void handleAction(target).catch(handleError);
});

root.addEventListener('change', (event) => {
  if (event.target.dataset?.garagePick) void garageViews.change(event.target).catch(handleError);
});

root.addEventListener('submit', (event) => {
  if (event.target.id?.startsWith('garage-')) {
    event.preventDefault();
    void garageViews.submit(event.target).catch(handleError);
  } else if (event.target.id?.startsWith('club-')) {
    event.preventDefault();
    void clubViews.submit(event.target).catch(handleError);
  } else if (event.target.id === 'vin-form') {
    event.preventDefault();
    void submitVin().catch(handleError);
  } else if (event.target.id === 'research-form') {
    event.preventDefault();
    void submitResearch(event.target).catch(handleError);
  } else if (event.target.id === 'chat-form') {
    event.preventDefault();
    void submitChat(event.target).catch(handleError);
  }
});

root.addEventListener('input', (event) => {
  if (event.target.id !== 'vin') return;
  event.target.value = event.target.value.toUpperCase().replace(/\s/g, '');
  const counter = document.querySelector('[data-vin-count]');
  if (counter) counter.textContent = `${event.target.value.length}`;
});

window.addEventListener('hashchange', () => void route());
window.addEventListener('DOMContentLoaded', () => void boot());

async function boot() {
  await loadLanguage(state.language || deviceLanguage());
  try {
    state.meta = await fetchMeta();
  } catch (error) {
    renderServiceUnavailable(error);
    return;
  }
  const storedSimulation = localStorage.getItem(SIMULATE_PAYWALL_KEY);
  state.simulateUserPaywall = Boolean(state.meta.developer?.enabled) && (
    storedSimulation === null
      ? Boolean(state.meta.developer.simulate_user_paywall_default)
      : storedSimulation === 'true'
  );
  configureDeveloperAccess({
    enabled: state.meta.developer?.enabled,
    simulatePaywall: state.simulateUserPaywall,
  });
  if (hasSession()) void trackEvent('app_open', {client: 'web_preview_v2'});
  if (!location.hash) {
    location.hash = state.language ? '#/home' : '#/language';
    return;
  }
  await route();
}

async function route() {
  const version = ++state.routeVersion;
  const [name, id] = routeParts();
  if (!state.language && name !== 'language') {
    go('/language');
    return;
  }
  try {
    if (await historyViews.route(name, id)) {window.scrollTo({top: 0, behavior: 'auto'}); return;}
    if (await listingViews.route(name, id)) {window.scrollTo({top: 0, behavior: 'auto'}); return;}
    if (await usTechViews.route(name, id)) {window.scrollTo({top: 0, behavior: 'auto'}); return;}
    if (await garageViews.route(name, id)) {window.scrollTo({top: 0, behavior: 'auto'}); return;}
    if (await clubViews.route(name, id)) {window.scrollTo({top: 0, behavior: 'auto'}); return;}
    if (await subscriptionViews.route(name, id)) {window.scrollTo({top: 0, behavior: 'auto'}); return;}
    if (await catalogViews.route(name || 'home', id)) {window.scrollTo({top: 0, behavior: 'auto'}); return;}
    if (await buyerViews.route(name || 'home', id)) {window.scrollTo({top: 0, behavior: 'auto'}); return;}
    if (name === 'language') renderLanguage();
    else if (name === 'home' || !name) renderHome();
    else if (name === 'vin') renderVinInput();
    else if (name === 'manual') await renderManual();
    else if (name === 'research') await renderResearch(id);
    else if (name === 'analysis') renderAnalysis();
    else if (name === 'precheck') await renderPrecheck(id);
    else if (name === 'payment') await renderPayment(id);
    else if (name === 'report') await renderFullReport(id);
    else if (name === 'chat') await renderChat(id);
    else if (name === 'reports' || name === 'legacy-reports') await renderReports();
    else renderHome();
  } catch (error) {
    if (version === state.routeVersion) handleError(error);
  }
  if (version !== state.routeVersion) return;
  if (name === 'chat') scrollChatToBottom();
  else window.scrollTo({top: 0, behavior: 'auto'});
}

function routeParts() {
  return location.hash.replace(/^#\/?/, '').split('/').filter(Boolean);
}

function isCurrentRoute(name, id) {
  const current = routeParts();
  return current[0] === name && (id === undefined || current[1] === id);
}

function go(path) {
  const hash = `#${path.startsWith('/') ? path : `/${path}`}`;
  if (location.hash === hash) void route();
  else location.hash = hash;
}

async function fetchMeta() {
  const meta = await fetchClientConfig();
  if (meta.buyer_api_version !== 1 || meta.version !== '0.8.1') throw new ApiError(409, 'API_VERSION_MISMATCH: client 0.8.1');
  return meta;
}

async function loadLanguage(language) {
  const supported = ['az', 'ru', 'en'];
  const safe = supported.includes(language) ? language : 'en';
  const response = await fetch(`/preview/locales/${safe}.json?v=0.8.1`);
  if (!response.ok) throw new Error('Localization could not be loaded');
  state.copy = await response.json();
  document.documentElement.lang = safe;
}

function t(key, values = {}) {
  let value = state.copy[key] || key;
  for (const [name, replacement] of Object.entries(values)) {
    value = value.replaceAll(`{${name}}`, String(replacement));
  }
  return value;
}

function renderLanguage() {
  const chosen = state.pendingLanguage || state.language || deviceLanguage();
  root.innerHTML = `
    <main class="language-screen">
      <div class="brand-mark" aria-hidden="true"></div>
      <div style="height:28px"></div>
      <p class="eyebrow">AUTO EXPERT 2.0</p>
      <h1>${esc(t('languageTitle'))}</h1>
      <p class="lead">${esc(t('languageSubtitle'))}</p>
      <div class="language-grid" role="radiogroup" aria-label="Language">
        ${languageChoice('en', 'English', chosen)}
        ${languageChoice('az', 'Azərbaycan dili', chosen)}
        ${languageChoice('ru', 'Русский', chosen)}
      </div>
      <button class="button gold full" data-action="language-continue">${esc(t('continue'))}</button>
    </main>`;
}

function renderServiceUnavailable(error) {
  const mismatch = error?.status === 409;
  const title = mismatch ? ({ru:'Версии приложения и сервиса не совпадают',az:'Tətbiq və xidmət versiyaları uyğun deyil',en:'App and service versions do not match'}[state.language || 'ru']) : t('serviceUnavailableTitle');
  const description = mismatch ? ({ru:'Для этого приложения нужен локальный сервис 0.8.1. Запустите согласованную сборку.',az:'Bu tətbiq üçün 0.8.1 lokal xidməti lazımdır. Uyğun quruluşu başladın.',en:'This app requires local service 0.8.1. Start the matching build.'}[state.language || 'ru']) : t('serviceUnavailableDescription');
  const detail = state.meta?.developer?.diagnostics_visible || globalThis.AUTOEXPERT_ANDROID_ALPHA
    ? `<code>${esc(error?.message || 'Connection unavailable')}</code>` : '';
  root.innerHTML = `
    <main class="service-unavailable-screen">
      <div class="brand-mark" aria-hidden="true"></div>
      <p class="eyebrow">AUTO EXPERT 2.0</p>
      <h1>${esc(title)}</h1>
      <p class="lead">${esc(description)}</p>
      ${detail}
      <button class="button gold full" data-action="reconnect">${esc(t('reconnect'))}</button>
    </main>`;
}

function languageChoice(code, label, chosen) {
  return `
    <button class="language-option ${code === chosen ? 'active' : ''}"
      data-action="language-choice" data-language="${code}" role="radio"
      aria-checked="${code === chosen}">
      <span class="radio-dot" aria-hidden="true"></span>
      <strong>${esc(label)}</strong><span>${code.toUpperCase()}</span>
    </button>`;
}

function renderHome() {
  root.innerHTML = layout(`
    <section class="hero v2-hero">
      <p class="eyebrow">${esc(t('evidenceBasedDossier'))}</p>
      <h1>${esc(t('v2HomeTitle'))}</h1>
      <p class="lead">${esc(t('v2HomeSubtitle'))}</p>
    </section>
    <section class="method-grid" aria-label="${esc(t('checkVehicle'))}">
      ${methodCard('VIN', t('vinMethod'), t('vinMethodDescription'), 'vin-start')}
      ${methodCard('↗', t('listingMethod'), t('listingMethodDescription'), 'listing', true)}
      ${methodCard('⌕', t('manualMethod'), t('manualMethodDescription'), 'manual-start')}
    </section>
    <button class="action-card compact" data-action="reports">
      <span class="action-icon">▤</span>
      <span class="action-copy"><strong>${esc(t('myReports'))}</strong><span>${esc(t('vinReportsDescription'))}</span></span>
      <span class="chevron">›</span>
    </button>
  `, {active: 'home'});
}

function methodCard(icon, title, subtitle, action, disabled = false) {
  return `
    <button class="method-card" data-action="${action}" ${disabled ? 'aria-disabled="true"' : ''}>
      <span class="method-icon">${esc(icon)}</span>
      <span><strong>${esc(title)}</strong><small>${esc(subtitle)}</small></span>
      ${disabled ? `<span class="pill">${esc(t('p1'))}</span>` : '<span class="chevron">›</span>'}
    </button>`;
}

function renderVinInput(prefill = '') {
  root.innerHTML = layout(`
    ${backTitle(t('vinTitle'), t('vinSubtitle'))}
    <form id="vin-form" class="form-card vin-card">
      <div class="field-grid">
        <div><label for="identifier-market">${esc(t('market'))}</label><select id="identifier-market" name="market">
          ${marketOptions(true)}
        </select></div>
        <div><label for="identifier-type">${esc(t('identifierType'))}</label><select id="identifier-type" name="identifier_type">
          <option value="VIN">VIN</option><option value="CHASSIS_NUMBER">${esc(t('chassisNumber'))}</option><option value="FRAME_NUMBER">${esc(t('frameNumber'))}</option>
        </select></div>
      </div>
      <label for="vin">${esc(t('vinOrChassis'))}</label>
      <div class="vin-input-wrap">
        <input id="vin" name="vin" class="vin-input" inputmode="text" autocomplete="off"
          autocapitalize="characters" spellcheck="false" maxlength="30"
          value="${esc(prefill)}" placeholder="${esc(qaMode()?state.meta?.vin_demo?.sample_vin || 'VIN':'VIN · 17 символов')}" required>
        <span class="vin-count" data-vin-count>${prefill.length}</span>
      </div>
      <p class="helper">${esc(t('vinRules'))}</p>
      ${qaMode() && state.meta?.vin_demo ? `<button type="button" class="text-button" data-action="use-demo-vin">${esc(t('useDemoVin'))}</button>` : ''}
      <button class="button gold full" type="submit">${esc(t('checkVin'))}</button>
    </form>
    <section class="trust-card" ${state.meta?.developer?.enabled && !state.simulateUserPaywall ? 'hidden' : ''}>
      <strong>${esc(t('safeTeaserTitle'))}</strong>
      <p>${esc(t('safeTeaserDescription'))}</p>
    </section>
  `, {nav: false});
}

async function renderManual() {
  await ensureSession();
  if (!isCurrentRoute('manual')) return;
  root.innerHTML = layout(`
    ${backTitle(t('manualTitle'), t('manualSubtitle'))}
    <section class="real-data-banner">
      <span class="pill real-pill">${esc(t('officialSource'))}</span>
      <p>${esc(t('automaticResearchNotice'))}</p>
    </section>
    <form id="research-form" class="form-card research-form">
      <label for="research-make">${esc(t('make'))}</label>
      <input id="research-make" name="make" autocomplete="organization" value="Toyota" required maxlength="120">
      <label for="research-model">${esc(t('model'))}</label>
      <input id="research-model" name="model" autocomplete="off" value="Camry" required maxlength="120">
      <div class="field-grid">
        <div><label for="research-year">${esc(t('year'))}</label><input id="research-year" name="year" type="number" inputmode="numeric" min="1981" max="2100" value="2019" required></div>
        <div><label for="research-market">${esc(t('market'))}</label><select id="research-market" name="market">${marketOptions()}</select></div>
      </div>
      <label for="research-engine">${esc(t('engineHint'))}</label>
      <input id="research-engine" name="engine_hint" autocomplete="off" value="2.5" maxlength="80">
      <p class="helper">${esc(t('engineHintNotice'))}</p>
      <button class="button gold full" type="submit">${esc(t('researchVehicle'))}</button>
    </form>
  `, {nav: false});
}

async function submitResearch(form) {
  await ensureSession();
  const values = new FormData(form);
  const job = await api('/research/jobs', {
    method: 'POST',
    body: JSON.stringify({
      vehicle: {
        make: values.get('make'),
        model: values.get('model'),
        year: Number(values.get('year')),
        market: values.get('market'),
        engine_hint: values.get('engine_hint') || null,
      },
      language: state.language,
    }),
  });
  go(`/research/${job.id}`);
}

async function renderResearch(jobId) {
  await ensureSession();
  let job = await api(`/research/jobs/${jobId}`);
  if (!isCurrentRoute('research', jobId)) return;
  renderResearchState(job);
  if (job.status === 'QUEUED') {
    job = await api(`/research/jobs/${jobId}/execute`, {method: 'POST'});
    if (routeParts()[0] === 'research' && routeParts()[1] === jobId) {
      renderResearchState(job);
    }
  }
}

function renderResearchState(job) {
  const complete = Boolean(job.profile && job.dossier);
  const awaitingSelection = Boolean(job.resolution?.needs_user_selection && !job.profile);
  const failed = job.status === 'FAILED';
  const vehicle = job.requested_vehicle;
  const provider = Object.fromEntries(job.provider_steps.map((step) => [step.capability, step]));
  const sourceStatus = job.profile ? 'complete' : failed ? 'failed' : 'active';
  const dossierStatus = job.dossier ? 'complete' : failed ? 'failed' : '';
  root.innerHTML = layout(`
    <section class="analysis-screen research-progress">
      <div class="analysis-orbit"><span>AE</span></div>
      <p class="eyebrow">${esc(t('automaticResearchEyebrow'))}</p>
      <h1>${esc(vehicle.make ? `${vehicle.year} ${vehicle.make} ${vehicle.model}` : vehicle.identifier)}</h1>
      <p class="lead">${esc(t('researchRunning'))}</p>
      <div class="pipeline-list">
        ${researchStep(t('researchStageResolve'), provider.vehicle_identity, job.status)}
        ${researchStep(t('researchStageOfficial'), firstProviderStep(job), job.status)}
        ${researchStep(t('researchStageVariants'), provider.vehicle_variants, job.status)}
        ${researchStep(t('researchStageRefine'), {status: awaitingSelection ? 'active' : job.resolution ? 'complete' : ''}, job.status)}
        ${researchStep(t('researchStageSources'), {status: sourceStatus}, job.status)}
        ${researchStep(t('researchStageDossier'), {status: dossierStatus}, job.status)}
      </div>
      ${job.cache_hit ? `<div class="cache-hit">✓ ${esc(t('researchCacheHit'))}</div>` : ''}
      ${developerDiagnostics(job)}
      ${job.resolution?.unresolved_fields?.length ? `<div class="resolution-note"><strong>${esc(t('researchNeedsResolution'))}</strong><p>${esc([...new Set(job.resolution.unresolved_fields.map(friendlyUnresolvedField))].join(' · '))}</p></div>` : ''}
      ${awaitingSelection ? variantSelection(job) : ''}
      ${job.errors.length ? `<div class="error-card compact"><strong>${esc(t('providerUnavailable'))}</strong><p>${esc(t('researchPartialDescription'))}</p></div>` : ''}
      ${complete ? `<section class="research-result-card"><span class="pill real-pill">${esc(t('realModelDossier'))}</span><h2>${esc(t('researchReady'))}</h2><p>${esc(t('researchReadyDescription', {sources: job.profile.source_ids.length}))}</p><button class="button gold full" data-action="research-continue" data-job="${esc(job.id)}" data-profile="${esc(job.profile_id)}" data-vin="${esc(vehicle.identifier || '')}">${esc(state.meta?.developer?.enabled && !state.simulateUserPaywall ? t('openDeveloperDossier') : t('continueToVinDemo'))}</button></section>` : ''}
      ${failed ? `<button class="button secondary full" data-action="research-new">${esc(t('tryAgain'))}</button>` : ''}
      ${job.status === 'PARTIAL' && !job.profile && !awaitingSelection ? `<section class="research-result-card"><h2>${esc(t('researchPartialTitle'))}</h2><p>${esc(t('researchPartialDescription'))}</p><button class="button secondary full" data-action="research-new">${esc(t('tryAgain'))}</button></section>` : ''}
      <p class="helper center">${esc(t('noFakeDelay'))}</p>
    </section>
  `, {nav: false});
}

function developerDiagnostics(job) {
  if (!state.meta?.developer?.diagnostics_visible || !job.provider_steps.length) return '';
  return `<details class="developer-diagnostics">
    <summary>${esc(t('providerDiagnostics'))}</summary>
    <div>${job.provider_steps.map((step) => `<article>
      <strong>${esc(step.provider_id || step.capability)}</strong>
      <span>${esc(step.capability)} · ${esc(step.status)}</span>
      <small>${esc([
        step.http_status ? `HTTP ${step.http_status}` : '',
        Number.isFinite(step.latency_ms) ? `${step.latency_ms} ms` : '',
        Number.isFinite(step.records_count) ? `${step.records_count} records` : '',
        step.cache_hit ? 'cache hit' : '',
      ].filter(Boolean).join(' · ') || '—')}</small>
    </article>`).join('')}${job.errors.map(error => `<p>${esc(error)}</p>`).join('')}</div>
  </details>`;
}

function variantSelection(job) {
  return `<section class="variant-selection"><p class="eyebrow">${esc(t('chooseVariant'))}</p><h2>${esc(t('chooseVariantTitle'))}</h2><p>${esc(t('chooseVariantDescription'))}</p><div class="variant-options">${job.resolution.candidates.map((candidate) => `
    <button data-action="variant-select" data-job="${esc(job.id)}" data-candidate="${esc(candidate.id)}">
      <strong>${esc(candidate.label)}</strong>
      <small>${esc([candidate.engine, candidate.transmission, candidate.drivetrain].filter(Boolean).join(' · ') || t('detailsUnresolved'))}</small>
    </button>`).join('')}</div></section>`;
}

function firstProviderStep(job) {
  if (!job.provider_steps.length) return null;
  const failed = job.provider_steps.find((step) => step.status === 'FAILED');
  return failed || {
    status: job.provider_steps.every((step) => ['COMPLETE', 'CACHE_HIT'].includes(step.status))
      ? 'COMPLETE' : 'active',
  };
}

function friendlyUnresolvedField(value) {
  const names = {
    make: t('make'), model: t('model'), year: t('year'), generation: t('generation'),
    engine: t('engine'), engine_code: t('engine'), transmission: t('transmission'),
    drivetrain: t('drivetrain'), body: t('body'),
  };
  return names[value] || t('detailsUnresolved');
}

function marketOptions(includeCanada = false) {
  return ['USA', 'KOREA', 'JAPAN', 'EUROPE', 'CHINA'].map(code =>
    `<option value="${code}">${esc(t(code === 'USA' && includeCanada ? 'marketUsCanada' : `market${code}`))}</option>`,
  ).join('');
}

function researchStep(label, step, jobStatus) {
  const raw = step?.status || (jobStatus === 'RUNNING' ? 'active' : '');
  const status = ['COMPLETE', 'CACHE_HIT', 'complete'].includes(raw)
    ? 'complete' : ['FAILED', 'failed'].includes(raw) ? 'failed' : raw === 'active' ? 'active' : '';
  const icon = status === 'complete' ? '✓' : status === 'failed' ? '!' : '';
  return `<div class="pipeline-step ${status}"><span>${icon}</span><strong>${esc(label)}</strong></div>`;
}

function renderAnalysis() {
  root.innerHTML = layout(`
    <section class="analysis-screen">
      <div class="analysis-orbit"><span>VIN</span></div>
      <p class="eyebrow">AUTO EXPERT 2.0</p>
      <h1>${esc(t('analysisV2Title'))}</h1>
      <div class="pipeline-list">
        ${pipelineStep(t('stageResolve'), true)}
        ${pipelineStep(t('stagePrecheck'), true)}
        ${pipelineStep(t('stageDossier'), true)}
        ${pipelineStep(t('stageSafeTeaser'), true)}
      </div>
      <p class="helper center">${esc(t('noFakeDelay'))}</p>
    </section>
  `, {nav: false});
}

function pipelineStep(label, active) {
  return `<div class="pipeline-step ${active ? 'active' : ''}"><span></span><strong>${esc(label)}</strong></div>`;
}

async function startPrecheck(vin) {
  await ensureSession();
  go('/analysis');
  const teaser = await api('/vin/precheck', {
    method: 'POST',
    body: JSON.stringify({vin, language: state.language}),
  });
  localStorage.setItem(LAST_CHECK_KEY, teaser.check_id);
  go(`/${teaser.details_locked ? 'precheck' : 'report'}/${teaser.check_id}`);
}

async function continueCompletedResearch(jobId, profileId, vin = '') {
  if (researchContinuationsInFlight.has(jobId)) return;
  researchContinuationsInFlight.add(jobId);
  await ensureSession();
  go('/analysis');
  try {
    const continuation = await executeResearchContinuation(api, {
      developerMode: Boolean(state.meta?.developer?.enabled),
      simulateUserPaywall: state.simulateUserPaywall,
      jobId,
      profileId,
      language: state.language,
      vin,
    });
    const result = continuation.result;
    localStorage.setItem(LAST_RESEARCH_JOB_KEY, jobId);
    localStorage.setItem(LAST_CHECK_KEY, result.check_id);
    if (continuation.mode === ResearchContinuation.DEVELOPER_DOSSIER) {
      go(`/report/${result.check_id}`);
      return;
    }
    go(`/${result.details_locked ? 'precheck' : 'report'}/${result.check_id}`);
  } catch (error) {
    // A conflict is terminal for this user action. Never poll or retry it.
    if (error instanceof ApiError && error.status === 409) {
      renderError(error);
      return;
    }
    throw error;
  } finally {
    researchContinuationsInFlight.delete(jobId);
  }
}

async function submitVin() {
  const input = document.querySelector('#vin');
  const identifier = input.value.trim().toUpperCase();
  const market = document.querySelector('#identifier-market').value;
  const identifierType = document.querySelector('#identifier-type').value;
  const vinInvalid = identifierType === 'VIN' && (identifier.length !== 17 || /[IOQ]/.test(identifier));
  const localInvalid = identifierType !== 'VIN' && (identifier.length < 5 || identifier.length > 30);
  if (vinInvalid || localInvalid) {
    input.setCustomValidity(t('vinClientError'));
    input.reportValidity();
    input.setCustomValidity('');
    return;
  }
  try {
    // Until a licensed live history supplier is configured, only the explicit
    // fixture VIN enters the mock checkout. Other VINs keep the existing
    // technical-research path instead of implying paid history coverage.
    if (identifierType === 'VIN' && market === 'USA' &&
        qaMode() && identifier === state.meta?.vin_demo?.sample_vin) {
      await historyViews.start(identifier);
      return;
    }
    if (useDemoPrecheck({developerMode: Boolean(state.meta?.developer?.enabled),
      simulateUserPaywall: state.simulateUserPaywall, identifier,
      sampleVin: qaMode()?state.meta?.vin_demo?.sample_vin:null, market, identifierType})) {
      await startPrecheck(identifier);
      return;
    }
    await ensureSession();
    const job = await api('/research/jobs', {
      method: 'POST',
      body: JSON.stringify({vehicle: {identifier, identifier_type: identifierType, market}, language: state.language}),
    });
    go(`/research/${job.id}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 422 && /checksum/i.test(error.message)) {
      history.replaceState(null, '', '#/vin');
      renderVinInput(identifier);
      showToast(t('vinChecksumError'));
      return;
    }
    throw error;
  }
}

async function renderPrecheck(checkId) {
  await ensureSession();
  const teaser = await api(`/vin/${checkId}/precheck`);
  if (!isCurrentRoute('precheck', checkId)) return;
  if (!qaMode() && teaser.demo_notice) {go('/reports');return;}
  if (teaser.developer_mode && !teaser.simulate_user_paywall && !teaser.details_locked) {
    go(`/report/${checkId}`);
    return;
  }
  const vehicle = teaser.vehicle;
  const vehicleTitle = vehicle
    ? [vehicle.year, vehicle.make, vehicle.model,
      /UNRESOLVED|DEMO identity/i.test(vehicle.engine || '') ? null : vehicle.engine,
      vehicle.market].filter(Boolean).join(' ')
    : teaser.vin;
  root.innerHTML = layout(`
    ${backTitle(t('vehicleIdentified'), vehicleTitle)}
    ${qaMode() && teaser.demo_notice ? `<section class="demo-alert"><strong>DEMO DATA</strong><span>${esc(teaser.demo_notice)}</span></section>` : ''}
    <section class="teaser-hero">
      <span class="eyebrow">VIN ${esc(maskVin(teaser.vin))}</span>
      <h1>${esc(vehicleTitle)}</h1>
      ${teaser.found ? `<div class="signal-grid">
        ${signal('📷', t('photosFound', {count: teaser.photos_count}))}
        ${signal('🏷️', t('auctionsFound', {count: teaser.auctions_count}))}
        ${signal('🔴', t('salvageDetected'), teaser.has_salvage_title ? 'danger' : '')}
        ${signal('⚠️', t('attentionRecords'), 'warning')}
      </div>` : ''}
    </section>
    ${teaser.records_count === 0 ? noRecordsBlock(teaser) : teaserContent(teaser)}
  `, {nav: false});
}

function teaserContent(teaser) {
  const preview = safeDataImage(teaser.blurred_preview_data_url);
  return `
    <section class="locked-visual">
      ${preview ? `<img src="${preview}" alt="${esc(t('blurredPreviewAlt'))}">` : ''}
      <div class="lock-badge">🔒 ${esc(t('serverLocked'))}</div>
      <div class="hidden-count">${esc(t('hiddenPhotos', {count: teaser.hidden_photos_count}))}</div>
    </section>
    <section class="teaser-copy card">
      <strong>${esc(t('recordsFound', {count: teaser.records_count}))}</strong>
      <p>${esc(t('lockedPayloadNotice'))}</p>
    </section>
    <div class="sticky-actions v2-sticky">
      ${teaser.details_locked ? `
        <button class="button gold full" data-action="unlock" data-check="${esc(teaser.check_id)}">
          ${esc(t('unlockHistory'))} — ${formatMoney(teaser.price, teaser.currency)}
        </button>
        <small>${esc(t('testModeNoCharge'))}</small>` : `
        <button class="button gold full" data-action="open-full" data-check="${esc(teaser.check_id)}">${esc(t('openFullReport'))}</button>`}
    </div>`;
}

function noRecordsBlock(teaser) {
  return `
    <section class="no-records-card">
      <div class="no-records-icon">✓</div>
      <h2>${esc(t('noRecordsTitle'))}</h2>
      <p>${esc(teaser.no_records_message)}</p>
      <p class="caution">${esc(teaser.caution_message)}</p>
      <button class="button secondary full" data-action="home">${esc(t('goHome'))}</button>
    </section>`;
}

function signal(icon, text, tone = '') {
  return `<div class="signal ${tone}"><span>${icon}</span><strong>${esc(text)}</strong></div>`;
}

async function renderPayment(checkId) {
  if (!qaMode()) {go('/reports');return;}
  const teaser = await api(`/vin/${checkId}/precheck`);
  if (!isCurrentRoute('payment', checkId)) return;
  if (!teaser.details_locked) {
    go(`/report/${checkId}`);
    return;
  }
  root.innerHTML = layout(`
    ${backTitle(t('demoPaymentTitle'), t('demoPaymentSubtitle'))}
    <section class="payment-card">
      <div class="payment-shield">✓</div>
      <span class="pill">DEMO / TEST PAYMENT</span>
      <h2>${formatMoney(teaser.price, teaser.currency)}</h2>
      <p>${esc(t('testModeNoCharge'))}</p>
      <div class="payment-row"><span>${esc(t('product'))}</span><strong>VIN CHECK 1</strong></div>
      <div class="payment-row"><span>${esc(t('records'))}</span><strong>${teaser.records_count}</strong></div>
      <button class="button gold full" data-action="unlock-confirm" data-check="${esc(checkId)}">${esc(t('unlockDemoReport'))}</button>
    </section>
  `, {nav: false});
}

async function renderFullReport(checkId) {
  await ensureSession();
  const report = await api(`/vin/${checkId}`);
  if (!isCurrentRoute('report', checkId)) return;
  if (!qaMode() && (report.vin_history_origin === 'DEMO' || report.dossier_origin === 'DEMO')) {go('/reports');return;}
  if (report.paid_report) {
    renderPaidReport(report);
    return;
  }
  const vehicle = report.vehicle;
  const historyCounts = ['timeline', 'auctions', 'photos', 'damage_details', 'odometer_records']
    .map((key) => report.history[key]?.length || 0);
  const hasVinHistory = historyCounts.some((count) => count > 0);
  const profileOnly = report.developer_mode && !report.simulate_user_paywall && !hasVinHistory;
  root.innerHTML = layout(`
    <section class="report-cover v2-cover">
      ${report.developer_mode && !report.simulate_user_paywall ? `<span class="pill developer-pill">${esc(t('developerAccess'))}</span>` : ''}
      ${profileOnly ? `<span class="pill">${esc(t('profileOnlyAccess'))}</span>` : `<span class="pill">${esc(t(report.vin_history_origin === 'DEMO' ? 'demoVinHistory' : 'fullHistory'))}</span>`}
      <span class="pill real-pill">${esc(t(report.dossier_origin === 'REAL' ? 'realModelDossier' : 'demoModelDossier'))}</span>
      <p class="eyebrow">${esc(profileOnly ? t('evidenceBasedDossier') : t('historyAndDossier'))}</p>
      <h1>${esc(`${vehicle.year} ${vehicle.make} ${vehicle.model}`)}</h1>
      <p>${esc([vehicle.trim, vehicle.generation !== 'UNRESOLVED' ? vehicle.generation : null, vehicle.market].filter(Boolean).join(' · '))}</p>
      ${report.vin ? `<code>${esc(maskVin(report.vin))}</code>` : ''}
    </section>
    <section class="report-tabs-summary">
      ${profileOnly ? metric(vehicle.source_ids.length, t('sources')) : metric(report.history.timeline.length, t('timeline'))}
      ${profileOnly ? metric(report.dossier.sections.filter((item) => !item.is_empty).length, t('sectionsWithData')) : metric(report.history.photos.length, t('archivePhotos'))}
      ${metric(report.dossier.sections.length, t('dossierSections'))}
    </section>
    ${profileOnly ? `<section class="origin-separation"><strong>${esc(t('noVinHistoryAttached'))}</strong><p>${esc(t('specificVehicleInspectionProfile'))}</p></section>` : historyDetails(report.history)}
    ${!profileOnly && report.vin_history_origin === 'DEMO' ? `<section class="origin-separation"><strong>${esc(t('syntheticNotice'))}</strong><p>${esc(t('specificVehicleInspection'))}</p></section>` : ''}
    <section class="section-heading"><p class="eyebrow">${esc(report.dossier_origin === 'REAL' ? t('evidenceBased') : t('demoData'))}</p><h2>${esc(t('fullDossier'))}</h2></section>
    <section class="dossier-stack">
      ${report.dossier.sections.map(dossierSection).join('')}
    </section>
    <section class="section-heading"><h2>${esc(t('sources'))}</h2></section>
    <section class="source-stack">${report.sources.map(sourceCard).join('')}</section>
    ${report.developer_mode ? reportDeveloperDiagnostics(report) : ''}
    <section class="chat-ready-card">
      <span class="method-icon">AI</span>
      <div><strong>${esc(t('chatReadyTitle'))}</strong><p>${esc(t('chatReadyDescription'))}</p></div>
      <button class="button gold full" data-action="chat-start" data-check="${esc(checkId)}">${esc(t('askAutoExpert'))}</button>
    </section>
  `, {active: 'reports', wide: true});
}

async function renderChat(sessionId) {
  await ensureSession();
  const session = await api(`/chat/sessions/${sessionId}`);
  if (!isCurrentRoute('chat', sessionId)) return;
  const vehicle = session.vehicle;
  const vehicleTitle = `${vehicle.year} ${vehicle.make} ${vehicle.model}`;
  const policyText = session.policy.unlimited
    ? t('chatUnlimited')
    : t('chatQuestionsRemaining', {count: session.policy.questions_remaining});
  root.innerHTML = layout(`
    <section class="chat-vehicle-header">
      <button class="back-button chat-back" data-action="chat-report" data-check="${esc(session.vin_check_id)}" aria-label="${esc(t('back'))}">‹</button>
      <div class="chat-vehicle-copy">
        <span class="eyebrow">AUTO EXPERT</span>
        <h1>${esc(vehicleTitle)}</h1>
        <p>${esc([vehicle.generation !== 'UNRESOLVED' ? vehicle.generation : null, vehicle.market].filter(Boolean).join(' · '))}${session.vin_masked !== '—' ? ` · <code>${esc(session.vin_masked)}</code>` : ''}</p>
      </div>
      <span class="chat-online" title="${esc(t('groundedContext'))}"><i></i>${esc(t('grounded'))}</span>
    </section>
    <section class="demo-alert chat-demo-alert ${session.is_demo ? '' : 'real-context-alert'}"><strong>${esc(session.is_demo ? t('demoShort') : t('evidenceBased'))}</strong><span>${esc(session.is_demo ? t('chatDemoNotice') : t('chatRealNotice'))}</span></section>
    <section class="chat-thread" aria-live="polite">
      ${session.messages.length ? session.messages.map(chatMessage).join('') : chatWelcome(vehicleTitle)}
    </section>
    <section class="chat-suggestions" aria-label="${esc(t('suggestedQuestions'))}">
      ${session.suggested_questions.map((question) => `
        <button data-action="chat-suggestion" data-session="${esc(session.session_id)}" data-question="${esc(question)}">${esc(question)}</button>
      `).join('')}
    </section>
    <form id="chat-form" class="chat-composer" data-session="${esc(session.session_id)}">
      <label class="sr-only" for="chat-question">${esc(t('chatQuestionLabel'))}</label>
      <textarea id="chat-question" name="question" rows="1" maxlength="1000" placeholder="${esc(t('chatPlaceholder'))}" required></textarea>
      <button type="submit" aria-label="${esc(t('sendQuestion'))}">↑</button>
      <small>${esc(policyText)} · ${esc(t('groundedOnly'))}</small>
    </form>
  `, {nav: false, wide: true});
}

function chatWelcome(vehicleTitle) {
  return `
    <article class="chat-message assistant">
      <div class="chat-avatar">AE</div>
      <div class="chat-bubble">
        <strong>Auto Expert</strong>
        <p>${esc(t('chatWelcome', {vehicle: vehicleTitle}))}</p>
      </div>
    </article>`;
}

function chatMessage(message) {
  const assistant = message.role === 'ASSISTANT';
  return `
    <article class="chat-message ${assistant ? 'assistant' : 'user'}">
      ${assistant ? '<div class="chat-avatar">AE</div>' : ''}
      <div class="chat-bubble">
        ${assistant ? '<strong>Auto Expert</strong>' : ''}
        <p>${esc(message.content)}</p>
        ${assistant && message.status ? `<div class="chat-evidence-line">${statusBadge(message.status)}</div>` : ''}
        ${assistant && message.sources.length ? chatSources(message.sources) : ''}
      </div>
    </article>`;
}

function chatSources(sources) {
  return `
    <details class="chat-sources">
      <summary>${esc(t('sources'))} · ${sources.length}</summary>
      <div>${sources.map((source) => `
        <article>
          <strong>${esc(consumerSourceTitle(source))}</strong>
          <span>${esc(consumerSourcePurpose(source.source_type))}</span>
          <small>${esc(t('sourceRetrieved'))}: ${esc(String(source.retrieved_at).slice(0, 10))}</small>
          ${safeHttpUrl(source.url) ? `<a href="${esc(source.url)}" target="_blank" rel="noopener noreferrer">${esc(t('openSource'))}</a>` : ''}
        </article>`).join('')}</div>
    </details>`;
}

async function submitChat(form) {
  const input = form.querySelector('#chat-question');
  const question = input.value.trim();
  if (question.length < 2) return;
  await sendChatQuestion(form.dataset.session, question);
}

async function sendChatQuestion(sessionId, question) {
  const input = document.querySelector('#chat-question');
  const submit = document.querySelector('#chat-form button[type="submit"]');
  const thread = document.querySelector('.chat-thread');
  if (input) input.disabled = true;
  if (submit) submit.disabled = true;
  if (thread) {
    thread.insertAdjacentHTML('beforeend', `
      <article class="chat-message user pending"><div class="chat-bubble"><p>${esc(question)}</p></div></article>
      <article class="chat-message assistant typing-message"><div class="chat-avatar">AE</div><div class="chat-bubble"><strong>Auto Expert</strong><div class="typing-dots" aria-label="${esc(t('loading'))}"><i></i><i></i><i></i></div></div></article>`);
    scrollChatToBottom();
  }
  try {
    await api(`/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({question}),
    });
    await renderChat(sessionId);
    scrollChatToBottom();
  } catch (error) {
    document.querySelectorAll('.pending, .typing-message').forEach((node) => node.remove());
    if (input) input.disabled = false;
    if (submit) submit.disabled = false;
    throw error;
  }
}

function scrollChatToBottom() {
  window.requestAnimationFrame(() => window.scrollTo({top: document.body.scrollHeight, behavior: 'auto'}));
}

function historyDetails(history) {
  return `
    <section class="section-heading"><p class="eyebrow">VIN</p><h2>${esc(t('fullHistory'))}</h2></section>
    <details class="section-card" open>
      <summary><span>${esc(t('timeline'))}</span><span>${history.timeline.length}</span></summary>
      <div class="section-body timeline-list">${history.timeline.map((item) => `
        <article><time>${esc(item.date)}</time><strong>${esc(item.summary)}</strong>${statusBadge(item.status)}</article>`).join('')}</div>
    </details>
    <details class="section-card">
      <summary><span>${esc(t('auctionRecords'))}</span><span>${history.auctions.length}</span></summary>
      <div class="section-body">${history.auctions.map((item) => `
        <article class="data-row"><span>${esc(item.date)} · ${esc(item.damage)} ${statusBadge(item.status)}</span><strong>${formatMoney(item.sale_price, item.currency)}</strong></article>`).join('')}</div>
    </details>
    <details class="section-card">
      <summary><span>${esc(t('odometerHistory'))}</span><span>${history.odometer_records.length}</span></summary>
      <div class="section-body">${history.odometer_records.map((item) => `
        <article class="data-row"><span>${esc(item.date)} ${statusBadge(item.status)}</span><strong>${formatNumber(item.value)} ${esc(item.unit)}</strong></article>`).join('')}</div>
    </details>
    <details class="section-card">
      <summary><span>${esc(t('damageDetails'))}</span><span>${history.damage_details.length}</span></summary>
      <div class="section-body">${history.damage_details.map((item) => `
        <article class="claim-card">${statusBadge(item.status)}<h3>${esc(item.area)}</h3><p>${esc(item.description)}</p></article>`).join('')}</div>
    </details>
    <details class="section-card">
      <summary><span>${esc(t('archivePhotos'))}</span><span>${history.photos.length}</span></summary>
      <div class="section-body demo-photo-grid">${history.photos.map((item) => `
        <div class="demo-photo"><span>DEMO</span><small>${esc(item.label)}</small>${statusBadge(item.status)}</div>`).join('')}</div>
    </details>`;
}

function dossierSection(section, index) {
  const empty = Boolean(section.is_empty);
  return `
    <details class="section-card ${empty ? 'empty-section' : ''}" ${index === 0 && !empty ? 'open' : ''}>
      <summary><span><small>${String(index + 1).padStart(2, '0')}</small>${esc(section.title)}</span><span>⌄</span></summary>
      <div class="section-body">
        <p class="section-summary ${empty ? 'compact-empty-copy' : ''}">${esc(section.summary)}</p>
        ${section.claims.map(dossierClaim).join('')}
        ${section.known_issues.map((issue) => `
          <article class="issue-card severity-${esc(issue.severity.toLowerCase())}">
            <div><span class="severity ${issue.severity.toLowerCase()}">${esc(issue.severity)}</span>${statusBadge(issue.status)}</div>
            <h3>${esc(issue.component)}</h3><p>${esc(issue.description)}</p>
            <strong>${esc(t('inspectionRecommendation'))}</strong><p>${esc(issue.inspection_recommendation)}</p>
          </article>`).join('')}
      </div>
    </details>`;
}

async function renderPaidReport(report) {
  const paid = report.paid_report;
  const photoGallery = groups => groups.some(group => group.photos.length) ? `<div class="vehicle-photo-gallery">${groups.flatMap(set => set.photos).map(photo => `<figure><a href="#" data-action="open-vin-photo" data-photo-id="${esc(photo.id)}" aria-label="${esc(photo.caption)}"><img loading="lazy" data-photo-image="${esc(photo.id)}" alt="${esc(photo.caption)}"></a><figcaption>${esc(photo.caption)}</figcaption></figure>`).join('')}</div>` : '';
  root.innerHTML = layout(`
    <section class="report-cover v2-cover paid-report-cover">
      <p class="eyebrow">AUTO EXPERT · ${esc(paid.subtitle)}</p>
      <h1>${esc(paid.title)}</h1><code>${esc(paid.vin)}</code>
      <p>${esc(String(paid.generated_at).slice(0, 10))}</p>
      <button class="button gold" data-action="download-report-pdf" data-check="${esc(report.check_id)}" data-vin="${esc(paid.vin)}">${esc(t('exportReportPdf'))} ↓</button>
    </section>
    ${paid.notice ? `<p class="report-draft-notice">${esc(paid.notice)}</p>` : ''}
    <section class="paid-report-sections">
      ${paid.sections.map((section, index) => `<details class="section-card paid-report-section" data-section="${esc(section.key)}" ${section.collapsed ? '' : 'open'}>
        <summary><span><small>${String(index + 1).padStart(2, '0')}</small>${esc(section.title)}</span><span>⌄</span></summary>
        <div class="section-body">
          ${section.rows.length ? `<dl class="vehicle-facts">${section.rows.map(row => `<div><dt>${esc(row.label)}</dt><dd>${esc(row.value)}</dd></div>`).join('')}</dl>` : ''}
          ${section.paragraphs.map(item => `<p class="report-paragraph">${esc(item.text)}</p>`).join('')}
          ${!section.rows.length && !section.paragraphs.length ? `<p class="report-empty">${esc(t('reportSectionEmpty'))}</p>` : ''}
          ${(section.events || []).map(event => `<article class="vin-event" data-event="${esc(event.id)}"><h3>${esc(event.title)}</h3><dl class="vehicle-facts">${event.rows.map(row => `<div><dt>${esc(row.label)}</dt><dd>${esc(row.value)}</dd></div>`).join('')}</dl>${photoGallery(paid.photo_sets.filter(set => set.event_id === event.id))}</article>`).join('')}
          ${section.key === 'history' && !(section.events || []).length && paid.photo_sets.length ? photoGallery(paid.photo_sets) : ''}
        </div>
      </details>`).join('')}
    </section>
    <details class="section-card report-sources"><summary>${esc(t('sources'))}</summary><div class="section-body source-stack">${report.sources.map(sourceCard).join('')}</div></details>
    ${report.developer_mode ? reportDeveloperDiagnostics(report) : ''}
    <section class="chat-ready-card"><strong>${esc(t('chatReadyTitle'))}</strong><button class="button gold full" data-action="chat-start" data-check="${esc(report.check_id)}">${esc(t('askAutoExpert'))}</button></section>
  `, {active: 'reports', wide: true});
  for (const img of root.querySelectorAll('[data-photo-image]')) {
    try {
      const url = await vehiclePhotoUrl(report.check_id, img.dataset.photoImage);
      if (img.isConnected) {
        img.onload = () => URL.revokeObjectURL(url); img.src = url;
        img.closest('a').addEventListener('click', async event => {
          event.preventDefault(); event.stopPropagation();
          const fullUrl = await vehiclePhotoUrl(report.check_id, img.dataset.photoImage);
          const dialog = document.createElement('dialog');
          dialog.className = 'vin-photo-dialog';
          const close = document.createElement('button'); close.textContent = '×';
          const picture = document.createElement('img'); picture.src = fullUrl; picture.alt = img.alt;
          const caption = document.createElement('p'); caption.textContent = img.alt;
          dialog.append(close, picture, caption); document.body.append(dialog);
          close.onclick = () => dialog.close();
          dialog.onclose = () => { URL.revokeObjectURL(fullUrl); dialog.remove(); };
          dialog.showModal();
        });
      }
      else URL.revokeObjectURL(url);
    } catch { img.alt = t('reportSectionEmpty'); }
  }
}

function dossierClaim(claim) {
  return `<article class="claim-card consumer-claim">
    <div class="claim-topline">${statusBadge(claim.status)}${claim.original_available ? `<span class="source-available">${esc(t('originalInSources'))}</span>` : ''}</div>
    ${claim.heading ? `<h3>${esc(claim.heading)}</h3>` : ''}
    <p>${esc(claim.text)}</p>
    ${claim.why_it_matters ? `<div class="consumer-detail"><strong>${esc(t('whyItMatters'))}</strong><p>${esc(claim.why_it_matters)}</p></div>` : ''}
    ${claim.applicability ? `<div class="consumer-detail"><strong>${esc(t('applicability'))}</strong><p>${esc(claim.applicability)}</p></div>` : ''}
    ${claim.what_to_check ? `<div class="consumer-detail action"><strong>${esc(t('inspectionRecommendation'))}</strong><p>${esc(claim.what_to_check)}</p></div>` : ''}
  </article>`;
}

function statusBadge(status) {
  const labels = {
    CONFIRMED: t('statusConfirmed'),
    ESTIMATE: t('statusEstimate'),
    NEEDS_INSPECTION: t('statusNeedsInspection'),
    INSUFFICIENT_DATA: t('statusInsufficient'),
  };
  return `<span class="status status-${String(status).toLowerCase()}">${esc(labels[status] || status)}</span>`;
}

function sourceCard(source) {
  const title = consumerSourceTitle(source);
  const confirms = consumerSourcePurpose(source.source_type);
  return `
    <article class="source-card">
      <span class="pill">${esc(source.data_origin === 'REAL' ? t('realSource') : t('demoSource'))}</span>
      <h3>${esc(title)}</h3>
      <p><strong>${esc(t('sourceConfirms'))}:</strong> ${esc(confirms)}</p>
      ${source.applicability_summary ? `<p>${esc(source.applicability_summary)}</p>` : ''}
      <small>${esc(t('sourceRetrieved'))}: ${esc(String(source.retrieved_at).slice(0, 10))}</small>
      ${safeHttpUrl(source.url) ? `<a class="source-link" href="${esc(source.url)}" target="_blank" rel="noopener noreferrer">${esc(t('openSource'))} ↗</a>` : ''}
    </article>`;
}

function consumerSourceTitle(source) {
  if (String(source.publisher).toLowerCase().includes('national highway traffic safety')) {
    return t('nhtsaOfficial');
  }
  return source.publisher || source.title;
}

function consumerSourcePurpose(sourceType) {
  const purposes = {
    GOVERNMENT_VEHICLE_API: t('sourcePurposeIdentity'),
    GOVERNMENT_CONFIGURATION_API: t('sourcePurposeConfiguration'),
    GOVERNMENT_RECALL_API: t('sourcePurposeRecalls'),
    OWNER_SUBMISSIONS_GOVERNMENT_REPOSITORY: t('sourcePurposeComplaints'),
    MANUFACTURER_COMMUNICATION: t('sourcePurposeCommunications'),
  };
  return purposes[sourceType] || t('sourcePurposeTechnical');
}

function reportDeveloperDiagnostics(report) {
  if (!state.meta?.developer?.diagnostics_visible) return '';
  return `<details class="developer-diagnostics report-diagnostics">
    <summary>${esc(t('rawProvenanceDiagnostics'))}</summary>
    ${report.paid_report ? `<button class="button secondary" data-action="load-report-diagnostics" data-check="${esc(report.check_id)}">${esc(t('rawProvenanceDiagnostics'))} JSON</button><pre class="report-diagnostics-json" hidden></pre>` : ''}
    <div>${report.sources.map((source) => `<article>
      <strong>${esc(source.title)}</strong>
      <span>${esc(source.source_type)} · TIER ${esc(source.source_tier)} · ${esc(source.confidence)}</span>
      <small>${esc(source.url)} · ${esc(source.id)}</small>
    </article>`).join('')}</div>
  </details>`;
}

async function renderReports() {
  await ensureSession();
  const [allChecks, historyCards] = await Promise.all([api('/vin/checks'), historyViews.savedCards()]);
  const checks=qaMode()?allChecks:allChecks.filter(item=>!item.is_demo);
  if (!isCurrentRoute('reports') && !isCurrentRoute('legacy-reports')) return;
  root.innerHTML = layout(`
    <section class="section-heading"><p class="eyebrow">AUTO EXPERT 2.0</p><h1>${esc(t('myReports'))}</h1><p>${esc(t('vinReportsDescription'))}</p></section>
    <section class="report-list">
      ${historyCards}${checks.map((item) => {
        const vehicle = item.vehicle;
        const title = vehicle ? `${vehicle.year} ${vehicle.make} ${vehicle.model}` : item.vin;
        return `<article class="report-card">
          <div><span class="pill">${item.is_demo ? 'DEMO DATA' : 'VIN'}</span><span class="status ${item.is_unlocked ? 'status-confirmed' : 'status-insufficient_data'}">${esc(item.is_unlocked ? t('statusUnlocked') : t('statusLocked'))}</span></div>
          <h2>${esc(title)}</h2><code>${esc(maskVin(item.vin))}</code>
          <p>${esc(t('recordsFound', {count: item.records_count}))} · ${esc(t('photosFound', {count: item.photos_count}))}</p>
          <button class="button secondary full" data-action="open-check" data-check="${esc(item.check_id)}" data-unlocked="${item.is_unlocked}">${esc(item.is_unlocked ? t('openFullReport') : t('openTeaser'))}</button>
        </article>`;
      }).join('') || (!historyCards ? `<div class="empty-state"><h2>${esc(t('noVinReports'))}</h2><p>${esc(t('noReportsHintV2'))}</p><button class="button gold" data-action="vin-start">${esc(t('vinMethod'))}</button></div>` : '')}
    </section>
  `, {active: 'reports'});
}

function layout(content, {active = '', wide = false, nav = true} = {}) {
  return `
    <div class="shell ${nav ? '' : 'no-nav'}">
      <header class="app-header">
        <button class="brand ghost-button" data-action="home" aria-label="${esc(t('navHome'))}">
          <span class="brand-car" aria-hidden="true"><svg viewBox="0 0 50 28"><path d="m5 16 6-10h25l8 10 3 2v7H3v-7Z"/><path d="M14 9h19l6 8H9ZM24 9v8"/><circle cx="12" cy="23" r="4"/><circle cx="38" cy="23" r="4"/></svg></span><span><strong><em>AUTO</em> EXPERT</strong><small>Azerbaijan</small></span>
        </button>
        <div class="header-actions"><div class="language-switch">${['en','az','ru'].map(code => `<button data-action="buyer-language" data-language="${code}" class="${state.language === code ? 'selected' : ''}">${code.toUpperCase()}</button>`).join('')}</div><button class="profile-button" data-action="profile" aria-label="${pickText(state.language, 'Профиль', 'Profil')}">●</button></div>
      </header>
      ${state.meta?.developer?.enabled ? `<details class="developer-drawer"><summary>${esc(state.language === 'ru' ? 'Настройки тестирования' : pickText(state.language, 'Test settings', 'Sınaq parametrləri'))}</summary>${developerToolbar()}</details>` : ''}
      <main class="screen ${wide ? 'wide' : ''}">${content}</main>
      ${nav ? bottomNav(active) : ''}
    </div>`;
}

function developerToolbar() {
  if (!state.meta?.developer?.enabled) return '';
  return `<section class="developer-toolbar">
    <div><strong>DeveloperMode</strong><small>${esc(t('developerModeDescription'))}</small></div>
    <button class="developer-switch ${state.simulateUserPaywall ? 'active' : ''}"
      data-action="toggle-paywall" role="switch" aria-checked="${state.simulateUserPaywall}">
      <span aria-hidden="true"></span><b>${esc(t('simulateUserPaywall'))}</b>
    </button>
  </section>`;
}

function bottomNav(active) {
  return `
    <nav class="bottom-nav ${garageViews.enabled() ? 'five' : ''}" aria-label="Primary">
      <button class="${active === 'home' ? 'active' : ''}" data-action="home"><span class="nav-icon">⌂</span><span>${esc(t('navHome'))}</span></button>
      <button class="${active === 'compare' ? 'active' : ''}" data-action="buyer-compare"><span class="nav-icon">⇄</span><span>${esc(state.language === 'ru' ? 'Сравнение' : pickText(state.language, 'Compare', 'Müqayisə'))}</span></button>
      <button class="${active === 'check' ? 'active' : ''}" data-action="buyer-check"><span class="nav-icon">⌕</span><span>${esc(pickText(state.language, 'Проверить', 'Yoxla'))}</span></button>
      <button class="${active === 'reports' ? 'active' : ''}" data-action="reports"><span class="nav-icon">▤</span><span>${esc(t('navReports'))}</span></button>
      ${garageViews.enabled() ? `<button class="${active === 'garage' ? 'active' : ''}" data-action="garage"><span class="nav-icon">⚙</span><span>${esc(garageViews.navLabel())}</span></button>` : ''}
    </nav>`;
}

function backTitle(title, subtitle) {
  return `<section class="page-heading"><button class="back-button" data-action="back">‹</button><div><h1>${esc(title)}</h1><p>${esc(subtitle)}</p></div></section>`;
}

function metric(value, label) {
  return `<div><strong>${esc(value)}</strong><span>${esc(label)}</span></div>`;
}

async function ensureSession() {
  // Without demo sessions (staging / production) a signed-in account is needed: the profile screen
  // signs in or registers; demo sessions exist only in the local QA preview.
  if (!hasSession() && !qaMode()) {
    const error = new Error('LOGIN_REQUIRED');
    error.loginRequired = true;
    throw error;
  }
  await ensureDemoSession(state.language || deviceLanguage());
}

async function handleAction(target) {
  if (await historyViews.action(target)) return;
  if (await garageViews.action(target)) return;
  if (await clubViews.action(target)) return;
  if (await subscriptionViews.action(target)) return;
  const action = target.dataset.action;
  if (action === 'profile') {go('/profile'); return;}
  if (action === 'buyer-check') {go('/check'); return;}
  if (action === 'buyer-compare') {go('/compare'); return;}
  if (action === 'buyer-language') {
    state.language = target.dataset.language;
    localStorage.setItem(LANGUAGE_KEY, state.language);
    await loadLanguage(state.language); await route(); return;
  }
  if (action === 'load-report-diagnostics') {
    const data = await api(`/vin/${target.dataset.check}/diagnostics`);
    const output = target.parentElement.querySelector('.report-diagnostics-json');
    output.textContent = JSON.stringify(data, null, 2);
    output.hidden = false;
    return;
  }
  if (action === 'download-report-pdf') {
    target.disabled = true;
    try { await downloadReportPdf(target.dataset.check, target.dataset.vin); } finally { target.disabled = false; }
    return;
  }
  if (action === 'language-choice') {
    state.pendingLanguage = target.dataset.language;
    document.querySelectorAll('.language-option').forEach((item) => {
      const active = item.dataset.language === state.pendingLanguage;
      item.classList.toggle('active', active);
      item.setAttribute('aria-checked', String(active));
    });
  } else if (action === 'language-continue') {
    state.language = state.pendingLanguage;
    localStorage.setItem(LANGUAGE_KEY, state.language);
    // Language affects new report content; keep the owner session and saved reports.
    await loadLanguage(state.language);
    await ensureSession();
    await trackEvent('language_selected', {language: state.language, client: 'web_preview_v2'});
    go('/home');
  } else if (action === 'change-language') {
    go('/language');
  } else if (action === 'home') {
    go('/home');
  } else if (action === 'back') {
    history.back();
  } else if (action === 'vin-start') {
    go('/vin');
  } else if (action === 'manual-start') {
    go('/manual');
  } else if (action === 'use-demo-vin') {
    if (!qaMode()) return;
    const input = document.querySelector('#vin');
    input.value = state.meta.vin_demo.sample_vin;
    input.dispatchEvent(new Event('input', {bubbles: true}));
  } else if (action === 'research-continue') {
    await continueCompletedResearch(
      target.dataset.job,
      target.dataset.profile,
      target.dataset.vin || '',
    );
  } else if (action === 'research-new') {
    go('/manual');
  } else if (action === 'variant-select') {
    await api(`/research/jobs/${target.dataset.job}/variant-selection`, {
      method: 'POST', body: JSON.stringify({candidate_id: target.dataset.candidate}),
    });
    go(`/research/${target.dataset.job}`);
  } else if (action === 'unlock') {
    go(`/payment/${target.dataset.check}`);
  } else if (action === 'unlock-confirm') {
    const result = await api(`/vin/${target.dataset.check}/payments/mock`, {
      method: 'POST', body: JSON.stringify({simulate_failure: false}),
    });
    if (!result.is_unlocked) throw new Error(t('errorGeneric'));
    showToast(t('reportUnlocked'));
    go(`/report/${target.dataset.check}`);
  } else if (action === 'open-full') {
    go(`/report/${target.dataset.check}`);
  } else if (action === 'chat-start') {
    const session = await api(`/vin/${target.dataset.check}/chat/session`, {method: 'POST'});
    go(`/chat/${session.session_id}`);
  } else if (action === 'chat-report') {
    go(`/report/${target.dataset.check}`);
  } else if (action === 'chat-suggestion') {
    await sendChatQuestion(target.dataset.session, target.dataset.question);
  } else if (action === 'reports') {
    go('/reports');
  } else if (action === 'open-check') {
    go(`/${target.dataset.unlocked === 'true' ? 'report' : 'precheck'}/${target.dataset.check}`);
  } else if (action === 'toggle-paywall') {
    state.simulateUserPaywall = !state.simulateUserPaywall;
    localStorage.setItem(SIMULATE_PAYWALL_KEY, String(state.simulateUserPaywall));
    configureDeveloperAccess({enabled: true, simulatePaywall: state.simulateUserPaywall});
    showToast(state.simulateUserPaywall ? t('paywallSimulationOn') : t('paywallSimulationOff'));
    const lastResearchJob = localStorage.getItem(LAST_RESEARCH_JOB_KEY);
    const lastCheck = localStorage.getItem(LAST_CHECK_KEY);
    const [currentPage] = routeParts();
    if (!['report', 'chat', 'research', 'precheck', 'payment'].includes(currentPage)) await route();
    else if (state.simulateUserPaywall && lastResearchJob) go(`/research/${lastResearchJob}`);
    else if (lastCheck) go(`/precheck/${lastCheck}`);
    else await route();
  } else if (action === 'reconnect') {
    await boot();
  }
}

function renderError(error) {
  const friendly = error?.status === 402 ? {ru:'Включён режим обычного пользователя. Локальный полный доступ доступен владельцу при выключенном Simulate User Paywall; покупка данных не выполнялась.',az:'Adi istifadəçi rejimi aktivdir. Simulate User Paywall söndürüldükdə sahib üçün lokal tam giriş açılır; məlumat alınmayıb.',en:'User paywall simulation is active. The owner has full local access when Simulate User Paywall is off; no data purchase was made.'} : error?.status === 0 ? {ru:'Связь с локальным сервисом потеряна. Введённые данные сохранены.',az:'Lokal xidmətlə əlaqə itdi. Daxil edilən məlumat saxlanıb.',en:'Connection to the local service was lost. Your input is saved.'} : error?.status >= 500 ? {ru:'Не удалось подготовить данные отчёта. Ввод сохранён; попробуйте открыть его повторно.',az:'Hesabat məlumatı hazırlanmadı. Giriş saxlanıb; yenidən açmağa çalışın.',en:'Report data could not be prepared. Input is saved; try opening it again.'} : null;
  const message = friendly ? friendly[state.language || 'ru'] : error instanceof ApiError ? error.message : error?.message || t('errorGeneric');
  root.innerHTML = layout(`
    <section class="error-card"><h2>${esc(t('errorGeneric'))}</h2><p>${esc(message)}</p>
      <button class="button secondary" data-action="back">${esc(t('back'))}</button>
      <button class="button gold" data-action="home">${esc(t('goHome'))}</button>
    </section>`, {nav: false});
}

function handleError(error) {
  if (error?.loginRequired || (error?.status === 401 && !qaMode())) {
    showToast(pickText(state.language, 'Войдите или зарегистрируйтесь', 'Daxil olun və ya qeydiyyatdan keçin', 'Sign in or register'));
    go('/profile');
    return;
  }
  if (subscriptionViews.handle(error)) return;
  renderError(error);
}

function showToast(message) {
  toastNode.textContent = message;
  toastNode.classList.add('show');
  window.setTimeout(() => toastNode.classList.remove('show'), 2200);
}

function safeDataImage(value) {
  return typeof value === 'string' && value.startsWith('data:image/svg+xml;base64,') ? value : '';
}

function safeHttpUrl(value) {
  return typeof value === 'string' && /^https?:\/\//i.test(value) && !value.includes('example.invalid');
}

function maskVin(vin) {
  return `${vin.slice(0, 5)}••••${vin.slice(-4)}`;
}

function formatMoney(value, currency) {
  if (value == null) return '—';
  return `${new Intl.NumberFormat(state.language, {minimumFractionDigits: 2, maximumFractionDigits: 2}).format(Number(value))} ${esc(currency || '')}`;
}

function formatNumber(value) {
  return new Intl.NumberFormat(state.language).format(Number(value));
}

function profileTerm(value, fallback = '—') {
  if (value === 'A25A-FKS') return t('a25aExplanation');
  if (value === '8AT') return t('eightAtExplanation');
  return value || fallback;
}

function esc(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;',
  })[character]);
}
