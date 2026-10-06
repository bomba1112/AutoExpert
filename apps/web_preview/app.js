import {ApiError, api, clearSession, ensureDemoSession, hasSession, trackEvent} from './api.js?v=0.12.0';

const root = document.querySelector('#app');
const toastNode = document.querySelector('#toast');
const LANGUAGE_KEY = 'autoexpert.ui.language';
const DRAFT_KEY = 'autoexpert.analysis.draft';
const LAST_PREVIEW_KEY = 'autoexpert.last.preview';

const defaultUsage = {
  monthlyMileage: '',
  cityPercent: 70,
  roadQuality: 'mixed',
  mountainTrips: false,
  regionalTrips: true,
  passengers: 3,
  economyPriority: 4,
  reliabilityPriority: 5,
  comfortPriority: 4,
  performancePriority: 2,
  maintenancePriority: 5,
  resalePriority: 4,
};

const state = {
  language: localStorage.getItem(LANGUAGE_KEY) || null,
  pendingLanguage: localStorage.getItem(LANGUAGE_KEY) || 'ru',
  copy: {},
  catalog: null,
  draft: loadDraft(),
  lastPreview: loadJson(LAST_PREVIEW_KEY),
  routeVersion: 0,
};

root.addEventListener('click', (event) => {
  const target = event.target.closest('[data-action]');
  if (!target || target.disabled) return;
  event.preventDefault();
  void handleAction(target).catch((error) => handleError(error));
});

root.addEventListener('input', (event) => {
  const input = event.target;
  if (!(input instanceof HTMLInputElement) || input.type !== 'range') return;
  const output = document.querySelector(`[data-range-output="${input.id}"]`);
  if (output) output.textContent = input.value;
  if (input.id === 'cityPercent') {
    const highway = document.querySelector('[data-highway-output]');
    if (highway) highway.textContent = String(100 - Number(input.value));
  }
});

root.addEventListener('change', (event) => {
  const field = event.target;
  if (field instanceof HTMLInputElement && ['checkbox', 'radio'].includes(field.type)) {
    if (field.type === 'radio') {
      document.querySelectorAll(`input[name="${field.name}"]`).forEach((input) => {
        input.closest('.choice')?.classList.toggle('selected', input.checked);
      });
    } else {
      field.closest('.choice')?.classList.toggle('selected', field.checked);
    }
  }
  if (!(field instanceof HTMLSelectElement)) return;
  if (field.id === 'country' || field.id === 'make') {
    saveVisibleVehicleSelections();
    const step = Number(routeParts()[1] || 0);
    void renderVehicleWizard(step);
  }
});

window.addEventListener('hashchange', () => void route());
window.addEventListener('DOMContentLoaded', () => void boot());

async function boot() {
  await loadLanguage(state.language || 'ru');
  if (hasSession()) void trackOnce('app_open', 'session');
  if (!location.hash) {
    location.hash = state.language ? '#/home' : '#/language';
    return;
  }
  await route();
}

async function route() {
  const version = ++state.routeVersion;
  const [name, idOrStep, suffix] = routeParts();
  if (!state.language && name !== 'language') {
    go('/language');
    return;
  }
  try {
    if (name === 'language') renderLanguage();
    else if (name === 'home' || !name) renderHome();
    else if (name === 'vehicle') await renderVehicleWizard(Number(idOrStep || 0));
    else if (name === 'usage') renderUsageProfile(Number(idOrStep || 0));
    else if (name === 'analysis') renderAnalysis(Boolean(state.lastPreview), state.lastPreview);
    else if (name === 'preview') await renderPreview(idOrStep);
    else if (name === 'payment') await renderPayment(idOrStep);
    else if (name === 'report' && suffix === 'questions') await renderQuestions(idOrStep);
    else if (name === 'report') await renderFullReport(idOrStep);
    else if (name === 'reports') await renderReports();
    else renderHome();
  } catch (error) {
    if (version === state.routeVersion) renderError(error);
  }
  window.scrollTo({top: 0, behavior: 'auto'});
}

function routeParts() {
  return location.hash.replace(/^#\/?/, '').split('/').filter(Boolean);
}

function go(path) {
  const hash = `#${path.startsWith('/') ? path : `/${path}`}`;
  if (location.hash === hash) void route();
  else location.hash = hash;
}

async function loadLanguage(language) {
  const supported = ['az', 'ru', 'en'];
  const safeLanguage = supported.includes(language) ? language : 'ru';
  const response = await fetch(`/preview/locales/${safeLanguage}.json`);
  if (!response.ok) throw new Error('Localization could not be loaded');
  state.copy = await response.json();
  document.documentElement.lang = safeLanguage;
}

function t(key, values = {}) {
  let value = state.copy[key] || key;
  for (const [name, replacement] of Object.entries(values)) {
    value = value.replaceAll(`{${name}}`, String(replacement));
  }
  return value;
}

function renderLanguage() {
  const chosen = state.pendingLanguage || state.language || 'ru';
  root.innerHTML = `
    <main class="language-screen">
      <div class="brand-mark" aria-hidden="true"></div>
      <div style="height: 28px"></div>
      <p class="eyebrow">AUTO EXPERT</p>
      <h1>${esc(t('languageTitle'))}</h1>
      <p class="lead">${esc(t('languageSubtitle'))}</p>
      <div class="language-grid" role="radiogroup" aria-label="Language">
        ${languageChoice('az', 'Azərbaycan dili', chosen)}
        ${languageChoice('ru', 'Русский', chosen)}
        ${languageChoice('en', 'English', chosen)}
      </div>
      <button class="button gold full" data-action="language-continue">${esc(t('continue'))}</button>
    </main>`;
}

function languageChoice(code, label, chosen) {
  return `
    <button class="language-option ${code === chosen ? 'active' : ''}"
      data-action="language-choice" data-language="${code}" role="radio"
      aria-checked="${code === chosen}">
      <span class="radio-dot" aria-hidden="true"></span>
      <strong>${esc(label)}</strong>
      <span>${code.toUpperCase()}</span>
    </button>`;
}

function layout(content, {active = '', wide = false, nav = true} = {}) {
  return `
    <div class="shell ${nav ? '' : 'no-nav'}">
      <header class="app-header">
        <button class="brand ghost-button" data-action="home" aria-label="${esc(t('navHome'))}"
          style="border:0;background:none;color:inherit;padding:0;text-align:left">
          <span class="brand-mark" aria-hidden="true"></span>
          <span>${esc(t('appName'))}</span>
        </button>
        <div class="header-actions">
          <button class="icon-button" data-action="change-language"
            aria-label="${esc(t('changeLanguage'))}" title="${esc(t('changeLanguage'))}">文</button>
        </div>
      </header>
      <div class="demo-ribbon">${esc(t('demoData'))}</div>
      <main class="screen ${wide ? 'wide' : ''}">${content}</main>
      ${nav ? bottomNav(active) : ''}
    </div>`;
}

function bottomNav(active) {
  return `
    <nav class="bottom-nav" aria-label="Primary">
      <button class="${active === 'home' ? 'active' : ''}" data-action="home">
        <span class="nav-icon">⌂</span><span>${esc(t('navHome'))}</span>
      </button>
      <button class="${active === 'reports' ? 'active' : ''}" data-action="reports">
        <span class="nav-icon">▤</span><span>${esc(t('navReports'))}</span>
      </button>
    </nav>`;
}

function renderHome() {
  root.innerHTML = layout(`
    <section class="hero">
      <p class="eyebrow">${esc(t('homeEyebrow'))}</p>
      <h1>${esc(t('homeTitle'))}</h1>
      <p class="lead">${esc(t('homeSubtitle'))}</p>
    </section>
    <section class="action-grid" aria-label="Actions">
      ${actionCard('check', t('checkVehicle'), t('checkVehicleDescription'), 'start-check')}
      ${actionCard('⇄', t('compareVehicles'), `${t('compareVehiclesDescription')} · ${t('comingSoon')}`, 'compare', true)}
      ${actionCard('▤', t('myReports'), t('myReportsDescription'), 'reports')}
    </section>
    <p class="helper center" style="margin-top:18px">${esc(t('refreshSafe'))}</p>
  `, {active: 'home'});
}

function actionCard(icon, title, subtitle, action, disabled = false) {
  return `
    <button class="action-card" data-action="${action}" ${disabled ? 'aria-disabled="true"' : ''}>
      <span class="action-icon">${esc(icon)}</span>
      <span class="action-copy"><strong>${esc(title)}</strong><span>${esc(subtitle)}</span></span>
      ${disabled ? `<span class="pill">${esc(t('comingSoon'))}</span>` : '<span class="chevron">›</span>'}
    </button>`;
}

async function catalog() {
  if (state.catalog) return state.catalog;
  state.catalog = await api('/catalog/options');
  return state.catalog;
}

async function renderVehicleWizard(step) {
  const data = await catalog();
  if (!data.variants.length || !data.countries.length) {
    throw new Error('Demo catalog is empty. Run the demo seed.');
  }
  const safeStep = Math.max(0, Math.min(3, step));
  initializeVehicleDraft(data);
  const headings = [t('location'), t('car'), t('powertrain'), t('listingDetails')];
  const forms = [locationForm(data), carForm(data), powertrainForm(data), listingForm(data)];
  root.innerHTML = layout(`
    <p class="eyebrow">${esc(t('stepOf', {current: safeStep + 1, total: 4}))}</p>
    <h2>${esc(t('vehicleWizard'))}</h2>
    <p class="lead">${esc(t('vehicleWizardSubtitle'))}</p>
    ${stepper(safeStep, 4)}
    <section class="card form-card">
      <h3>${esc(headings[safeStep])}</h3>
      <p class="helper" style="margin-bottom:18px">${esc(t('demoCatalogHint'))}</p>
      <form id="vehicleForm">${forms[safeStep]}</form>
    </section>
    <div class="sticky-actions ${safeStep === 0 ? 'one' : ''}">
      ${safeStep > 0 ? `<button class="button secondary" data-action="vehicle-prev" data-step="${safeStep}">${esc(t('back'))}</button>` : ''}
      <button class="button primary" data-action="vehicle-next" data-step="${safeStep}">${esc(t('next'))}</button>
    </div>
  `, {active: 'home'});
}

function initializeVehicleDraft(data) {
  const country = state.draft.vehicle.country || data.countries[0].code;
  const variants = data.variants.filter((item) => item.country === country);
  const variant = variants.find((item) => item.id === state.draft.vehicle.variantId) || variants[0] || data.variants[0];
  const countryData = data.countries.find((item) => item.code === country) || data.countries[0];
  const savedCity = countryData.cities.includes(state.draft.vehicle.city)
    ? state.draft.vehicle.city
    : countryData.cities[0] || '';
  state.draft.vehicle = {
    ...state.draft.vehicle,
    country: countryData.code,
    city: savedCity,
    make: variant.make,
    model: variant.model,
    variantId: variant.id,
    year: state.draft.vehicle.year || variant.year_to || variant.year_from,
    engine: variant.engine,
    transmission: variant.transmission,
    drivetrain: variant.drivetrain,
    currency: countryData.currency,
  };
  persistDraft();
}

function locationForm(data) {
  const selectedCountry = state.draft.vehicle.country;
  const country = data.countries.find((item) => item.code === selectedCountry) || data.countries[0];
  return `<div class="field-grid two">
    ${selectField('country', t('country'), data.countries.map((item) => ({
      value: item.code,
      label: item.code === 'AZ' ? t('countryAZ') : item.code,
    })), selectedCountry)}
    ${selectField('city', t('city'), country.cities.map((city) => ({value: city, label: city})), state.draft.vehicle.city)}
  </div>`;
}

function carForm(data) {
  const variants = data.variants.filter((item) => item.country === state.draft.vehicle.country);
  const makes = unique(variants.map((item) => item.make));
  const selectedMake = makes.includes(state.draft.vehicle.make) ? state.draft.vehicle.make : makes[0];
  const models = unique(variants.filter((item) => item.make === selectedMake).map((item) => item.model));
  return `<div class="field-grid two">
    ${selectField('make', t('make'), makes.map(option), selectedMake)}
    ${selectField('model', t('model'), models.map(option), state.draft.vehicle.model)}
  </div>`;
}

function powertrainForm(data) {
  const variants = relevantVariants(data);
  const variant = variants.find((item) => item.id === state.draft.vehicle.variantId) || variants[0];
  const years = yearOptions(variant);
  return `<div class="field-grid">
    ${selectField('variantId', t('powertrain'), variants.map((item) => ({
      value: item.id,
      label: `${item.generation_code || item.generation} · ${item.engine || '—'}`,
    })), variant.id)}
    <div class="field-grid two">
      ${selectField('year', t('year'), years.map((year) => ({value: year, label: year})), state.draft.vehicle.year)}
      ${selectField('engine', t('engine'), unique(variants.map((item) => item.engine).filter(Boolean)).map(option), variant.engine)}
      ${selectField('transmission', t('transmission'), unique(variants.map((item) => item.transmission).filter(Boolean)).map(option), variant.transmission)}
      ${selectField('drivetrain', t('drivetrain'), unique(variants.map((item) => item.drivetrain).filter(Boolean)).map(option), variant.drivetrain)}
    </div>
  </div>`;
}

function listingForm(data) {
  const country = data.countries.find((item) => item.code === state.draft.vehicle.country);
  return `<div class="field-grid">
    <div class="field">
      <label for="mileage">${esc(t('mileage'))}</label>
      <input id="mileage" name="mileage" type="number" inputmode="numeric" min="0" max="5000000"
        step="1000" value="${attr(state.draft.vehicle.mileage || '')}" required autocomplete="off">
    </div>
    <div class="field-grid two">
      <div class="field">
        <label for="price">${esc(t('price'))}</label>
        <input id="price" name="price" type="number" inputmode="decimal" min="1" step="0.01"
          value="${attr(state.draft.vehicle.price || '')}" required autocomplete="off">
      </div>
      ${selectField('currency', t('currency'), [{value: country.currency, label: country.currency}], country.currency)}
    </div>
  </div>`;
}

function relevantVariants(data) {
  return data.variants.filter((item) =>
    item.country === state.draft.vehicle.country &&
    item.make === state.draft.vehicle.make &&
    item.model === state.draft.vehicle.model
  );
}

function selectField(id, label, options, selected) {
  return `<div class="field">
    <label for="${attr(id)}">${esc(label)}</label>
    <select id="${attr(id)}" name="${attr(id)}" required>
      ${options.map((item) => `<option value="${attr(item.value)}" ${String(item.value) === String(selected) ? 'selected' : ''}>${esc(item.label)}</option>`).join('')}
    </select>
  </div>`;
}

function option(value) {
  return {value, label: value};
}

function yearOptions(variant) {
  const start = variant.year_from || new Date().getFullYear();
  const end = variant.year_to || start;
  const result = [];
  for (let year = end; year >= start; year -= 1) result.push(year);
  return result;
}

function stepper(active, total) {
  return `<div class="stepper" aria-hidden="true">${Array.from({length: total}, (_, index) =>
    `<span class="${index < active ? 'done' : index === active ? 'active' : ''}"></span>`
  ).join('')}</div>`;
}

function saveVisibleVehicleSelections() {
  for (const name of ['country', 'city', 'make', 'model', 'variantId', 'year', 'engine', 'transmission', 'drivetrain', 'mileage', 'price', 'currency']) {
    const node = document.querySelector(`#${name}`);
    if (node) state.draft.vehicle[name] = node.value;
  }
  persistDraft();
}

function saveVehicleStep(step) {
  const form = document.querySelector('#vehicleForm');
  if (!form.reportValidity()) return false;
  saveVisibleVehicleSelections();
  if (step === 0) {
    state.draft.vehicle.city = document.querySelector('#city').value;
  }
  if (step === 1) {
    const variants = state.catalog.variants.filter((item) =>
      item.country === state.draft.vehicle.country &&
      item.make === state.draft.vehicle.make &&
      item.model === state.draft.vehicle.model
    );
    state.draft.vehicle.variantId = variants[0]?.id;
  }
  if (step === 2) {
    const variant = state.catalog.variants.find((item) => item.id === state.draft.vehicle.variantId);
    state.draft.vehicle.engine = variant.engine;
    state.draft.vehicle.transmission = variant.transmission;
    state.draft.vehicle.drivetrain = variant.drivetrain;
  }
  if (step === 3) {
    state.draft.vehicle.mileage = Number(state.draft.vehicle.mileage);
    state.draft.vehicle.price = Number(state.draft.vehicle.price);
    void trackEvent('vehicle_completed', {
      country: state.draft.vehicle.country,
      variant_id: state.draft.vehicle.variantId,
    });
  }
  persistDraft();
  return true;
}

function renderUsageProfile(step) {
  state.draft.usage = {...defaultUsage, ...state.draft.usage};
  const safeStep = Math.max(0, Math.min(3, step));
  const headings = [t('drivingPattern'), t('roadConditions'), t('familyUse'), t('priorities')];
  const forms = [drivingForm(), roadsForm(), familyForm(), prioritiesForm()];
  root.innerHTML = layout(`
    <p class="eyebrow">${esc(t('stepOf', {current: safeStep + 1, total: 4}))}</p>
    <h2>${esc(t('usageProfile'))}</h2>
    <p class="lead">${esc(t('usageProfileSubtitle'))}</p>
    ${stepper(safeStep, 4)}
    <section class="card form-card">
      <h3>${esc(headings[safeStep])}</h3>
      <form id="usageForm">${forms[safeStep]}</form>
    </section>
    <div class="sticky-actions">
      <button class="button secondary" data-action="usage-prev" data-step="${safeStep}">${esc(t('back'))}</button>
      <button class="button primary" data-action="usage-next" data-step="${safeStep}">${esc(safeStep === 3 ? t('analyze') : t('next'))}</button>
    </div>
  `, {active: 'home'});
}

function drivingForm() {
  const usage = state.draft.usage;
  return `<div class="field-grid">
    <div class="field">
      <label for="monthlyMileage">${esc(t('monthlyMileage'))}</label>
      <input id="monthlyMileage" type="number" inputmode="numeric" min="0" max="100000"
        step="100" value="${attr(usage.monthlyMileage)}" required autocomplete="off">
    </div>
    ${rangeField('cityPercent', `${t('cityDriving')} / ${t('highwayDriving')}`, usage.cityPercent, 0, 100, 5,
      `${t('cityDriving')}: <strong data-range-output="cityPercent">${usage.cityPercent}</strong>% · ${t('highwayDriving')}: <strong data-highway-output>${100 - usage.cityPercent}</strong>%`)}
  </div>`;
}

function roadsForm() {
  const usage = state.draft.usage;
  return `<div class="field-grid">
    <div>
      <span class="field-label">${esc(t('roadQuality'))}</span>
      <div class="choice-grid">
        ${radioChoice('roadQuality', 'good', t('roadGood'), usage.roadQuality)}
        ${radioChoice('roadQuality', 'mixed', t('roadMixed'), usage.roadQuality)}
        ${radioChoice('roadQuality', 'poor', t('roadPoor'), usage.roadQuality)}
      </div>
    </div>
    ${checkChoice('mountainTrips', t('mountainTrips'), usage.mountainTrips)}
    ${checkChoice('regionalTrips', t('regionalTrips'), usage.regionalTrips)}
  </div>`;
}

function familyForm() {
  const usage = state.draft.usage;
  return `<div class="field-grid">
    ${rangeField('passengers', t('passengers'), usage.passengers, 1, 8, 1,
      `<strong data-range-output="passengers">${usage.passengers}</strong>`)}
    <p class="helper">${esc(t('passengersHelper'))}</p>
  </div>`;
}

function prioritiesForm() {
  const usage = state.draft.usage;
  return `<p class="helper">${esc(t('prioritiesSubtitle'))}</p>
    ${rangeField('economyPriority', t('economyPriority'), usage.economyPriority, 1, 5, 1)}
    ${rangeField('reliabilityPriority', t('reliabilityPriority'), usage.reliabilityPriority, 1, 5, 1)}
    ${rangeField('comfortPriority', t('comfortPriority'), usage.comfortPriority, 1, 5, 1)}
    ${rangeField('performancePriority', t('performancePriority'), usage.performancePriority, 1, 5, 1)}
    ${rangeField('maintenancePriority', t('maintenancePriority'), usage.maintenancePriority, 1, 5, 1)}
    ${rangeField('resalePriority', t('resalePriority'), usage.resalePriority, 1, 5, 1)}`;
}

function rangeField(id, label, value, min, max, step, customValue = null) {
  return `<div class="range-row">
    <div class="range-head"><label for="${id}">${esc(label)}</label><span class="range-value">${customValue || `<strong data-range-output="${id}">${value}</strong>`}</span></div>
    <input id="${id}" type="range" min="${min}" max="${max}" step="${step}" value="${attr(value)}">
  </div>`;
}

function radioChoice(name, value, label, selected) {
  return `<label class="choice ${selected === value ? 'selected' : ''}">
    <input type="radio" name="${name}" value="${value}" ${selected === value ? 'checked' : ''}>
    <span>${esc(label)}</span>
  </label>`;
}

function checkChoice(id, label, checked) {
  return `<label class="choice ${checked ? 'selected' : ''}">
    <input id="${id}" type="checkbox" ${checked ? 'checked' : ''}>
    <span>${esc(label)}</span>
  </label>`;
}

function saveUsageStep(step) {
  const form = document.querySelector('#usageForm');
  if (!form.reportValidity()) return false;
  const usage = state.draft.usage;
  if (step === 0) {
    usage.monthlyMileage = Number(document.querySelector('#monthlyMileage').value);
    usage.cityPercent = Number(document.querySelector('#cityPercent').value);
  } else if (step === 1) {
    usage.roadQuality = document.querySelector('input[name="roadQuality"]:checked').value;
    usage.mountainTrips = document.querySelector('#mountainTrips').checked;
    usage.regionalTrips = document.querySelector('#regionalTrips').checked;
  } else if (step === 2) {
    usage.passengers = Number(document.querySelector('#passengers').value);
  } else {
    for (const name of ['economyPriority', 'reliabilityPriority', 'comfortPriority', 'performancePriority', 'maintenancePriority', 'resalePriority']) {
      usage[name] = Number(document.querySelector(`#${name}`).value);
    }
  }
  persistDraft();
  return true;
}

async function runAnalysis() {
  const isSecondAnalysis = Boolean(state.lastPreview);
  state.lastPreview = null;
  localStorage.removeItem(LAST_PREVIEW_KEY);
  location.hash = '#/analysis';
  renderAnalysis(false);
  await ensureDemoSession(state.language);
  void trackEvent('usage_profile_completed', {language: state.language});
  void trackEvent('analysis_started', {language: state.language});
  if (isSecondAnalysis) void trackEvent('second_analysis_started', {language: state.language});
  const vehicle = state.draft.vehicle;
  const usage = state.draft.usage;
  const payload = {
    vehicle_variant_id: vehicle.variantId,
    vehicle: {
      country: vehicle.country,
      city: vehicle.city,
      make: vehicle.make,
      model: vehicle.model,
      generation: state.catalog.variants.find((item) => item.id === vehicle.variantId)?.generation_code,
      year: Number(vehicle.year),
      engine: vehicle.engine,
      transmission: vehicle.transmission,
      drivetrain: vehicle.drivetrain,
      mileage_km: Number(vehicle.mileage),
      price: Number(vehicle.price),
      currency: vehicle.currency,
    },
    usage_profile: {
      monthly_mileage_km: Number(usage.monthlyMileage),
      city_share: Number(usage.cityPercent) / 100,
      poor_roads: usage.roadQuality !== 'good',
      regular_region_trips: Boolean(usage.regionalTrips),
      mountains: Boolean(usage.mountainTrips),
      unpaved_roads: usage.roadQuality === 'poor',
      passengers: Number(usage.passengers),
      cargo_need: 'normal',
      economy_priority: Number(usage.economyPriority),
      reliability_priority: Number(usage.reliabilityPriority),
      comfort_priority: Number(usage.comfortPriority),
      performance_priority: Number(usage.performancePriority),
      maintenance_cost_priority: Number(usage.maintenancePriority),
      resale_priority: Number(usage.resalePriority),
    },
    report_language: state.language,
  };
  const preview = await api('/analyses/preview', {method: 'POST', body: JSON.stringify(payload)});
  state.lastPreview = preview;
  localStorage.setItem(LAST_PREVIEW_KEY, JSON.stringify(preview));
  renderAnalysis(true, preview);
}

function renderAnalysis(completed, preview = null) {
  const stages = preview?.pipeline_stages || [
    'vehicle_resolution', 'technical_evidence', 'market_analysis', 'ownership_calculation',
    'owner_feedback', 'fit_analysis', 'grounding_validation', 'snapshot_saved',
  ];
  root.innerHTML = layout(`
    <section class="card loading-card">
      ${completed ? '<div class="payment-shield">✓</div>' : '<div class="spinner" aria-hidden="true"></div>'}
      <h2>${esc(completed ? t('analysisCompleted') : t('analysisTitle'))}</h2>
      <p class="lead">${esc(completed ? t('refreshSafe') : t('analysisRunning'))}</p>
      <div class="pipeline">
        ${stages.map((stage) => `<div class="pipeline-item ${completed ? 'done' : ''}">
          <span class="pipeline-check">${completed ? '✓' : ''}</span>
          <span>${esc(t(`stage_${stage}`))}</span>
        </div>`).join('')}
      </div>
      ${completed ? `<button class="button primary full" style="margin-top:20px" data-action="open-preview" data-id="${attr(preview.report_id)}">${esc(t('openPreview'))}</button>` : ''}
    </section>
  `, {nav: false});
}

async function renderPreview(reportId) {
  await ensureDemoSession(state.language);
  const preview = await api(`/reports/${encodeURIComponent(reportId)}/preview`);
  void trackOnce('paywall_viewed', reportId, {report_id: reportId});
  state.lastPreview = preview;
  localStorage.setItem(LAST_PREVIEW_KEY, JSON.stringify(preview));
  const vehicle = preview.vehicle;
  const verdict = fitLabel(preview.verdict);
  root.innerHTML = layout(`
    <p class="eyebrow">${esc(t('freePreview'))}</p>
    <section class="card verdict-card">
      <span class="pill demo">${esc(t('demoShort'))}</span>
      <h2 style="margin-top:15px">${esc(verdict)}</h2>
      <p class="lead">${esc(preview.verdict_summary)}</p>
    </section>
    <div class="summary-grid">
      ${metric(t('selectedVehicle'), `${vehicle.make} ${vehicle.model}`)}
      ${metric(t('location'), [countryLabel(preview.country), preview.city].filter(Boolean).join(' · '))}
      ${metric(t('comparables'), preview.comparable_count)}
      ${metric(t('usedComparables'), preview.used_comparable_count)}
    </div>
    <section class="card form-card" style="margin-bottom:13px">
      <h3>${esc(t('highlights'))}</h3>
      <ul class="highlight-list">
        ${preview.highlights.length ? preview.highlights.map((item) => `<li class="highlight">${statusBadge(item.status)}<p>${esc(item.text)}</p></li>`).join('') : `<li>${esc(t('noSectionData'))}</li>`}
      </ul>
    </section>
    <section class="card form-card" style="margin-bottom:13px">
      <h3>${esc(t('localMarket'))}</h3>
      <div class="summary-grid">
        ${metric(t('comparables'), preview.comparable_count)}
        ${metric(t('usedComparables'), preview.used_comparable_count)}
        ${metric(t('evidenceItems'), preview.evidence_count)}
        ${metric(t('sourceCount'), preview.source_count)}
      </div>
      ${statusBadge(preview.local_market_status)}
    </section>
    <section class="card paywall">
      <p class="eyebrow">${esc(t('fullReportIncludes'))}</p>
      <h3>${esc(t('fullReportList'))}</h3>
      ${preview.price === null ? `<p class="notice">${esc(t('priceUnavailable'))}</p>` : `
        <div class="price">${esc(formatMoney(preview.price, preview.currency))}</div>
        <button class="button gold full" data-action="${preview.is_unlocked ? 'open-report' : 'purchase'}" data-id="${attr(reportId)}">
          ${esc(preview.is_unlocked ? t('openReport') : t('purchaseReport', {price: preview.price, currency: preview.currency}))}
        </button>`}
    </section>
  `, {active: 'home'});
}

async function renderPayment(reportId) {
  await ensureDemoSession(state.language);
  const preview = await api(`/reports/${encodeURIComponent(reportId)}/preview`);
  root.innerHTML = layout(`
    <section class="card form-card center">
      <div class="payment-shield">✓</div>
      <span class="pill demo">${esc(t('demoShort'))}</span>
      <h2 style="margin-top:14px">${esc(t('mockPaymentTitle'))}</h2>
      <p class="lead">${esc(t('mockPaymentSubtitle'))}</p>
      <div class="price">${esc(formatMoney(preview.price, preview.currency))}</div>
      <p class="pill confirmed" style="margin-bottom:18px">${esc(t('noRealCharge'))}</p>
      <button class="button gold full" data-action="mock-unlock" data-id="${attr(reportId)}">${esc(t('mockPaymentButton'))}</button>
      <button class="button ghost full" style="margin-top:8px" data-action="open-preview" data-id="${attr(reportId)}">${esc(t('back'))}</button>
    </section>
  `, {nav: false});
}

async function unlockReport(reportId, button) {
  button.disabled = true;
  button.textContent = t('unlocking');
  const result = await api(`/reports/${encodeURIComponent(reportId)}/payments/mock`, {
    method: 'POST',
    body: JSON.stringify({simulate_failure: false}),
  });
  if (!result.is_unlocked) throw new Error(t('errorGeneric'));
  go(`/report/${reportId}`);
}

async function renderFullReport(reportId) {
  await ensureDemoSession(state.language);
  const report = await api(`/reports/${encodeURIComponent(reportId)}`);
  if (!report.is_unlocked) {
    go(`/preview/${reportId}`);
    return;
  }
  const bundle = report.evidence_bundle;
  void trackEvent('report_opened', {report_id: reportId});
  const generated = report.generated_sections;
  const fit = bundle.fit_analysis;
  root.innerHTML = layout(`
    <p class="eyebrow">${esc(t('fullReport'))}</p>
    <section class="card verdict-card">
      <div style="display:flex;gap:8px;flex-wrap:wrap">${statusBadge('ESTIMATE')}<span class="pill demo">${esc(t('demoShort'))}</span></div>
      <div class="verdict-score">
        <div class="score-ring">${esc(fit.score)}/100</div>
        <div><h2>${esc(fitLabel(fit.rating))}</h2><p class="lead">${esc(generated.verdict_summary)}</p></div>
      </div>
    </section>
    <div class="summary-grid">
      ${metric(t('reportId'), shortId(report.id))}
      ${metric(t('reportDate'), formatDate(report.created_at))}
      ${metric(t('selectedVehicle'), `${bundle.vehicle.make} ${bundle.vehicle.model}`)}
      ${metric(t('location'), countryLabel(bundle.vehicle.market))}
    </div>
    <p class="notice">${esc(generated.inspection_notice || t('inspectionNotice'))}</p>
    <p class="helper">${esc(t('reportLanguageFixed'))}</p>
    <section style="margin-top:18px">
      ${generated.sections.map((section, index) => renderReportSection(section, index, bundle)).join('')}
    </section>
    <section class="card form-card" style="margin-top:14px">
      <h3>${esc(t('questionsTitle'))}</h3>
      <p class="helper">${esc(t('questionsRemaining', {count: report.questions_remaining}))}</p>
      <button class="button primary full" data-action="open-questions" data-id="${attr(reportId)}">${esc(t('askQuestion'))}</button>
      <button class="button secondary full" style="margin-top:9px" disabled>${esc(t('pdfStageD'))}</button>
    </section>
  `, {active: 'reports', wide: true});
}

function renderReportSection(section, index, bundle) {
  const status = sectionStatus(section.key, section, bundle);
  return `<details class="card section-card" ${index === 0 ? 'open' : ''}>
    <summary><span class="section-number">${index + 1}</span><span class="section-title">${esc(section.title)}</span>${statusBadge(status)}</summary>
    <div class="section-body">${sectionContent(section, bundle)}</div>
  </details>`;
}

function sectionStatus(key, section, bundle) {
  if (key === 'vehicle') return bundle.vehicle.source_ids?.length ? 'CONFIRMED' : 'INSUFFICIENT_DATA';
  if (key === 'expert_verdict' || key === 'suitability') return 'ESTIMATE';
  if (key === 'local_market') return bundle.market_analysis.status;
  if (key === 'ownership_costs' || key === 'fuel_consumption') return bundle.ownership_calculation.status;
  if (key === 'owner_feedback') return bundle.owner_evidence.length ? 'ESTIMATE' : 'INSUFFICIENT_DATA';
  if (key === 'inspection') return 'NEEDS_INSPECTION';
  if (key === 'sources') return bundle.sources.length ? 'CONFIRMED' : 'INSUFFICIENT_DATA';
  return section.claims?.[0]?.status || 'INSUFFICIENT_DATA';
}

function sectionContent(section, bundle) {
  if (section.key === 'expert_verdict' || section.key === 'suitability') return fitContent(bundle);
  if (section.key === 'vehicle') return vehicleContent(bundle.vehicle);
  if (section.key === 'local_market') return marketContent(bundle.market_analysis);
  if (section.key === 'ownership_costs') return ownershipContent(bundle.ownership_calculation);
  if (section.key === 'owner_feedback') return ownerContent(bundle.owner_feedback);
  if (section.key === 'inspection') return inspectionContent(bundle);
  if (section.key === 'sources') return sourcesContent(bundle.sources);
  if (section.claims?.length) return claimsContent(section.claims);
  return `<p>${esc(section.summary || t('noSectionData'))}</p>${statusBadge('INSUFFICIENT_DATA')}`;
}

function fitContent(bundle) {
  const fit = bundle.fit_analysis;
  const rows = [
    [t('preliminaryVerdict'), fitLabel(fit.rating)],
    [t('score'), `${fit.score}/100`],
    [t('confidence'), fit.confidence],
  ];
  const reasons = fit.reasons.length ? `<ul class="plain-list">${fit.reasons.map((reason) =>
    `<li class="claim">${statusBadge(reason.evidence_status)}<p><strong>${esc(reasonLabel(reason.code))}</strong> · ${reason.impact > 0 ? '+' : ''}${esc(reason.impact)}</p></li>`
  ).join('')}</ul>` : `<p>${esc(t('noSectionData'))}</p>`;
  return `${dataTable(rows)}${reasons}`;
}

function reasonLabel(code) {
  const labels = {
    'priority.economy': t('economyPriority'),
    'priority.reliability': t('reliabilityPriority'),
    'priority.comfort': t('comfortPriority'),
    'priority.performance': t('performancePriority'),
    'priority.maintenance_affordability': t('maintenancePriority'),
    'priority.resale_liquidity': t('resalePriority'),
    'conditions.road_clearance': t('roadQuality'),
    'conditions.mountain_drivetrain': t('mountainTrips'),
    'conditions.passenger_space': t('passengers'),
    'conditions.cargo_space': t('cargo'),
  };
  return labels[code] || code;
}

function vehicleContent(vehicle) {
  return dataTable([
    [t('make'), vehicle.make], [t('model'), vehicle.model], [t('powertrain'), vehicle.variant],
    [t('year'), vehicle.year], [t('engine'), vehicle.engine], [t('transmission'), vehicle.transmission],
    [t('drivetrain'), vehicle.drivetrain], [t('body'), vehicle.body], [t('fuel'), vehicle.fuel],
    [t('displacement'), vehicle.displacement_l ? `${vehicle.displacement_l} L` : null],
    [t('power'), vehicle.power_kw ? `${vehicle.power_kw} kW` : null],
    [t('groundClearance'), vehicle.ground_clearance_mm ? `${vehicle.ground_clearance_mm} mm` : null],
  ].filter((row) => row[1] !== null && row[1] !== undefined));
}

function marketContent(market) {
  if (market.status === 'INSUFFICIENT_DATA') return `<p>${esc(t('noSectionData'))}</p>${statusBadge(market.status)}`;
  return `${dataTable([
    [t('comparables'), market.comparable_count],
    [t('usedComparables'), market.used_count],
    [t('marketMedian'), formatMoney(market.median, market.currency)],
    [t('marketRange'), `${formatMoney(market.market_range_low, market.currency)} — ${formatMoney(market.market_range_high, market.currency)}`],
    [t('selectedPrice'), formatMoney(market.selected_price, market.currency)],
    [t('priceDeviation'), market.percentage_deviation === null ? '—' : `${market.percentage_deviation}%`],
  ])}<h3>${esc(t('assumptions'))}</h3>${plainList(market.assumptions)}`;
}

function ownershipContent(ownership) {
  const rows = [];
  if (ownership.monthly_fuel) rows.push([t('monthlyFuel'), moneyRange(ownership.monthly_fuel)]);
  if (ownership.yearly_fuel) rows.push([t('yearlyFuel'), moneyRange(ownership.yearly_fuel)]);
  if (ownership.first_year_total) rows.push([t('firstYearTotal'), moneyRange(ownership.first_year_total)]);
  return `${rows.length ? dataTable(rows) : `<p>${esc(t('noSectionData'))}</p>`}
    <h3>${esc(t('assumptions'))}</h3>${plainList(ownership.assumptions)}${plainList(ownership.notes)}`;
}

function ownerContent(owner) {
  if (!owner.unique_material_count) return `<p>${esc(t('noSectionData'))}</p>`;
  return `${dataTable([[t('ownerMaterials'), owner.unique_material_count]])}
    <p class="notice">${esc(t('sampleDisclaimer'))}</p>
    <ul class="plain-list">${owner.topics.map((topic) => `<li class="claim">
      ${statusBadge('ESTIMATE')}<p><strong>${esc(topic.topic)}</strong><br>${esc(topic.show_percentage
        ? t('mentionedInSample', {percent: Math.round(topic.mention_share * 100), mentions: topic.material_mentions, sample: topic.sample_size})
        : t('mentionsSmallSample', {mentions: topic.material_mentions}))}</p>
    </li>`).join('')}</ul>`;
}

function inspectionContent(bundle) {
  const issues = bundle.known_issues.map((issue) => `<div class="claim">
    ${statusBadge(issue.status)} <span class="pill">${esc(issue.severity)}</span>
    <p><strong>${esc(issue.component)}</strong><br>${esc(issue.description)}<br>${esc(issue.inspection_recommendation)}</p>
  </div>`).join('');
  return `<p class="notice">${esc(t('inspectionNotice'))}</p>${issues || `<p>${esc(t('noSectionData'))}</p>`}`;
}

function sourcesContent(sources) {
  if (!sources.length) return `<p>${esc(t('noSectionData'))}</p>`;
  return sources.map((source) => {
    const url = safeUrl(source.url);
    return `<div class="claim">
      ${statusBadge('CONFIRMED')} ${source.is_demo ? `<span class="pill demo">${esc(t('demoShort'))}</span>` : ''}
      <p><strong>${esc(source.title)}</strong><br>${esc(source.publisher)} · ${esc(source.source_type)}<br>
      ${esc(t('sourceRetrieved'))}: ${esc(formatDate(source.retrieved_at))}
      ${url ? `<a class="source-link" href="${attr(url)}" target="_blank" rel="noopener noreferrer">${esc(source.url)}</a>` : ''}</p>
    </div>`;
  }).join('');
}

function claimsContent(claims) {
  return claims.map((claim) => `<div class="claim">${statusBadge(claim.status)}<p>${esc(claim.text)}</p></div>`).join('');
}

async function renderQuestions(reportId) {
  await ensureDemoSession(state.language);
  const report = await api(`/reports/${encodeURIComponent(reportId)}`);
  if (!report.is_unlocked) {
    go(`/preview/${reportId}`);
    return;
  }
  const exhausted = report.questions_remaining <= 0;
  root.innerHTML = layout(`
    <p class="eyebrow">${esc(t('questionsTitle'))}</p>
    <h2>${esc(t('questionsTitle'))}</h2>
    <p class="lead">${esc(t('questionsSubtitle'))}</p>
    <section class="card question-card" style="margin-bottom:13px">
      <span class="pill ${exhausted ? 'locked' : 'estimate'}">${esc(t('questionsRemaining', {count: report.questions_remaining}))}</span>
      <div style="height:15px"></div>
      ${report.questions.length ? report.questions.map((item) => `
        <div class="question-bubble">${esc(item.question)}</div>
        <div class="answer-bubble">${esc(item.answer)}</div>`).join('') : `<p class="helper">${esc(t('noQuestions'))}</p>`}
    </section>
    <section class="card form-card">
      ${exhausted ? `<p class="notice">${esc(t('questionLimitReached'))}</p>` : `
        <form id="questionForm">
          <div class="field"><label for="question">${esc(t('askQuestion'))}</label>
            <textarea id="question" minlength="2" maxlength="1000" required placeholder="${attr(t('questionPlaceholder'))}"></textarea>
          </div>
        </form>
        <button class="button primary full" style="margin-top:13px" data-action="send-question" data-id="${attr(reportId)}">${esc(t('sendQuestion'))}</button>`}
      <button class="button ghost full" style="margin-top:8px" data-action="open-report" data-id="${attr(reportId)}">${esc(t('back'))}</button>
    </section>
  `, {active: 'reports'});
}

async function sendQuestion(reportId, button) {
  const form = document.querySelector('#questionForm');
  if (!form.reportValidity()) return;
  const question = document.querySelector('#question').value.trim();
  button.disabled = true;
  const result = await api(`/reports/${encodeURIComponent(reportId)}/questions`, {
    method: 'POST',
    body: JSON.stringify({question}),
  });
  toast(t('questionsRemaining', {count: result.questions_remaining}));
  await renderQuestions(reportId);
}

async function renderReports() {
  await ensureDemoSession(state.language);
  const reports = await api('/reports');
  root.innerHTML = layout(`
    <p class="eyebrow">${esc(t('myReports'))}</p>
    <h2>${esc(t('myReportsTitle'))}</h2>
    <p class="lead">${esc(t('myReportsSubtitle'))}</p>
    <section class="report-list">
      ${reports.length ? reports.map(reportCard).join('') : `<div class="card empty-state">
        <div class="empty-icon">▤</div><h3>${esc(t('noReports'))}</h3><p class="helper">${esc(t('noReportsHint'))}</p>
        <button class="button primary" data-action="start-check">${esc(t('checkVehicle'))}</button>
      </div>`}
    </section>
  `, {active: 'reports'});
}

function reportCard(report) {
  const vehicle = report.vehicle;
  return `<article class="card report-card">
    <div class="report-card-top">
      <div><h3>${esc(`${vehicle.make || ''} ${vehicle.model || ''}`.trim() || shortId(report.id))}</h3>
        <p class="meta-line">${esc([vehicle.year, vehicle.city, formatDate(report.created_at)].filter(Boolean).join(' · '))}</p></div>
      <span class="pill ${report.is_unlocked ? 'unlocked' : 'locked'}">${esc(report.is_unlocked ? t('statusUnlocked') : t('statusLocked'))}</span>
    </div>
    <div style="display:flex;gap:7px;flex-wrap:wrap;margin:13px 0"><span class="pill demo">${esc(t('demoShort'))}</span><span class="pill estimate">${esc(fitLabel(report.verdict))}</span></div>
    <button class="button secondary full" data-action="${report.is_unlocked ? 'open-report' : 'open-preview'}" data-id="${attr(report.id)}">
      ${esc(report.is_unlocked ? t('openReport') : t('openSavedPreview'))}
    </button>
  </article>`;
}

function renderError(error) {
  const message = error instanceof ApiError ? error.message : error?.message || t('errorGeneric');
  root.innerHTML = layout(`
    <section class="card error-card">
      <h2>${esc(t('errorGeneric'))}</h2>
      <p>${esc(message)}</p>
      <button class="button primary" data-action="retry">${esc(t('tryAgain'))}</button>
      <button class="button ghost" data-action="home">${esc(t('goHome'))}</button>
    </section>
  `, {nav: false});
}

async function handleAction(target) {
  const action = target.dataset.action;
  if (action === 'language-choice') {
    state.pendingLanguage = target.dataset.language;
    await loadLanguage(state.pendingLanguage);
    renderLanguage();
  } else if (action === 'language-continue') {
    state.language = state.pendingLanguage || 'ru';
    localStorage.setItem(LANGUAGE_KEY, state.language);
    await loadLanguage(state.language);
    if (!hasSession()) {
      target.disabled = true;
      target.textContent = t('sessionCreating');
      await ensureDemoSession(state.language);
    }
    await trackOnce('app_open', 'session');
    void trackEvent('language_selected', {language: state.language});
    go('/home');
  } else if (action === 'change-language') {
    state.pendingLanguage = state.language;
    go('/language');
  } else if (action === 'home') go('/home');
  else if (action === 'reports') go('/reports');
  else if (action === 'start-check') go('/vehicle/0');
  else if (action === 'compare') toast(t('comingSoon'));
  else if (action === 'vehicle-prev') go(`/vehicle/${Math.max(0, Number(target.dataset.step) - 1)}`);
  else if (action === 'vehicle-next') {
    const step = Number(target.dataset.step);
    if (!saveVehicleStep(step)) return;
    if (step < 3) go(`/vehicle/${step + 1}`);
    else go('/usage/0');
  } else if (action === 'usage-prev') {
    const step = Number(target.dataset.step);
    if (step === 0) go('/vehicle/3');
    else go(`/usage/${step - 1}`);
  } else if (action === 'usage-next') {
    const step = Number(target.dataset.step);
    if (!saveUsageStep(step)) return;
    if (step < 3) go(`/usage/${step + 1}`);
    else await runAnalysis();
  } else if (action === 'open-preview') go(`/preview/${target.dataset.id}`);
  else if (action === 'purchase') go(`/payment/${target.dataset.id}`);
  else if (action === 'mock-unlock') await unlockReport(target.dataset.id, target);
  else if (action === 'open-report') go(`/report/${target.dataset.id}`);
  else if (action === 'open-questions') go(`/report/${target.dataset.id}/questions`);
  else if (action === 'send-question') await sendQuestion(target.dataset.id, target);
  else if (action === 'retry') {
    if (!hasSession() && state.language) await ensureDemoSession(state.language);
    await route();
  }
}

function persistDraft() {
  localStorage.setItem(DRAFT_KEY, JSON.stringify(state.draft));
}

async function trackOnce(eventName, identity, properties = {}) {
  const key = `autoexpert.analytics.${eventName}.${identity}`;
  if (sessionStorage.getItem(key)) return;
  sessionStorage.setItem(key, '1');
  await trackEvent(eventName, properties);
}

function loadDraft() {
  return loadJson(DRAFT_KEY) || {vehicle: {}, usage: {...defaultUsage}};
}

function loadJson(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || 'null');
  } catch {
    return null;
  }
}

function statusBadge(status) {
  const safe = ['CONFIRMED', 'ESTIMATE', 'NEEDS_INSPECTION', 'INSUFFICIENT_DATA'].includes(status)
    ? status : 'INSUFFICIENT_DATA';
  const labels = {
    CONFIRMED: t('statusConfirmed'), ESTIMATE: t('statusEstimate'),
    NEEDS_INSPECTION: t('statusNeedsInspection'), INSUFFICIENT_DATA: t('statusInsufficient'),
  };
  return `<span class="pill ${safe.toLowerCase()}" title="${attr(labels[safe])}">${safe}</span>`;
}

function fitLabel(value) {
  return t(`fit_${value}`);
}

function countryLabel(code) {
  return code === 'AZ' ? t('countryAZ') : code;
}

function metric(label, value) {
  return `<div class="metric"><span>${esc(label)}</span><strong>${esc(value ?? '—')}</strong></div>`;
}

function dataTable(rows) {
  return `<div class="data-table">${rows.map(([label, value]) => `<div class="data-row"><span>${esc(label)}</span><strong>${esc(value ?? '—')}</strong></div>`).join('')}</div>`;
}

function plainList(items = []) {
  if (!items.length) return '';
  return `<ul class="plain-list">${items.map((item) => `<li class="claim"><p>${esc(item)}</p></li>`).join('')}</ul>`;
}

function moneyRange(range) {
  return `${formatMoney(range.low, range.currency)} — ${formatMoney(range.high, range.currency)}`;
}

function formatMoney(value, currency) {
  if (value === null || value === undefined || !currency) return '—';
  const locale = state.language === 'az' ? 'az-AZ' : state.language === 'ru' ? 'ru-RU' : 'en-US';
  try {
    return new Intl.NumberFormat(locale, {style: 'currency', currency, maximumFractionDigits: 2}).format(Number(value));
  } catch {
    return `${value} ${currency}`;
  }
}

function formatDate(value) {
  if (!value) return '—';
  const locale = state.language === 'az' ? 'az-AZ' : state.language === 'ru' ? 'ru-RU' : 'en-US';
  return new Intl.DateTimeFormat(locale, {dateStyle: 'medium'}).format(new Date(value));
}

function shortId(value) {
  return String(value || '').split('-')[0].toUpperCase();
}

function unique(values) {
  return [...new Set(values)];
}

function safeUrl(value) {
  try {
    const url = new URL(value);
    return ['http:', 'https:'].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}

function esc(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function attr(value) {
  return esc(value).replaceAll('`', '&#096;');
}

function toast(message) {
  toastNode.textContent = message;
  toastNode.classList.add('show');
  window.setTimeout(() => toastNode.classList.remove('show'), 2600);
}

function handleError(error) {
  console.error(error);
  if (error instanceof ApiError && error.status === 401) clearSession();
  renderError(error);
}
