import {EN, pickText} from './en-text.js?v=0.13.0';
// US technical facts of a configuration (next-stage prompt, stage C). Shown only while the API
// advertises the show_us_tech_facts flag (client-config "us_tech_facts"); production without
// the flag never loads or renders anything from here.
import {api} from './api.js?v=0.13.0';

const COPY = {
  ru: {
    title: 'Технические данные · США', technical: 'Техника', weak_points: 'Слабые места', campaigns: 'Сервисные кампании',
    maintenance: 'ТО', sources: 'Источники', component: 'Узел', severity: 'Серьёзность', probability: 'Вероятность',
    symptoms: 'Симптомы', check: 'Как проверить', years: 'Годы', normal: 'Обычные условия', severe: 'Тяжёлые условия',
    limit: 'не позже', page: 'стр.', pickTitle: 'Конфигурации технической базы США', pickNote: 'Предпросмотр за флагом: конфигурации исследовательского слоя не публикуются.',
    make: 'Марка', model: 'Модель', year: 'Модельный год', choose: 'Выберите', none: 'Конфигураций нет', back: 'Назад', loading: 'Загрузка…',
    unavailable: 'Технические данные для этой конфигурации не найдены.',
  },
  az: {
    title: 'Texniki məlumatlar · ABŞ', technical: 'Texnika', weak_points: 'Zəif yerlər', campaigns: 'Servis kampaniyaları',
    maintenance: 'TXQ', sources: 'Mənbələr', component: 'Qovşaq', severity: 'Ciddilik', probability: 'Ehtimal',
    symptoms: 'Əlamətlər', check: 'Necə yoxlamalı', years: 'İllər', normal: 'Adi şərait', severe: 'Ağır şərait',
    limit: 'gec olmayaraq', page: 'səh.', pickTitle: 'ABŞ texniki bazasının konfiqurasiyaları', pickNote: 'Bayraq arxasında ön baxış: tədqiqat qatının konfiqurasiyaları dərc olunmur.',
    make: 'Marka', model: 'Model', year: 'Model ili', choose: 'Seçin', none: 'Konfiqurasiya yoxdur', back: 'Geri', loading: 'Yüklənir…',
    unavailable: 'Bu konfiqurasiya üçün texniki məlumat tapılmadı.',
  },
};
const ICONS = {technical: '⚙', weak_points: '!', campaigns: '↻', maintenance: '✓'};

const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));

export function copyOf(language) {
  if (language === 'en') return Object.fromEntries(Object.entries(COPY.ru).map(([k, v]) => [k, EN[v] ?? v]));
  return COPY[language === 'az' ? 'az' : 'ru'];
}

function badge(text, cls) {
  return `<small class="us-tech-badge ${cls}">${escape(text)}</small>`;
}

function valueHtml(v, data) {
  const marks = (v.secondary ? badge(data.labels.secondary, 'secondary') : '') + (v.approximate ? badge(data.labels.approximate, 'approximate') : '');
  return `${v.qualifier ? `<span class="us-tech-qualifier">${escape(v.qualifier)}</span> ` : ''}<span class="us-tech-value">${escape(v.value)}</span>${marks}`;
}

function rowHtml(row, data) {
  const values = row.values.length === 1
    ? valueHtml(row.values[0], data)
    : `<ul class="us-tech-values">${row.values.map(v => `<li>${valueHtml(v, data)}</li>`).join('')}</ul>`;
  // fuel (owner rule 2026-10-04): the Auto Expert recommendation is a rule of the app, not a sourced fact
  const reason = row.kind === 'recommendation' && row.values[0]?.reason ? `<small class="fuel-reason">${escape(row.values[0].reason)}</small>` : '';
  return `<div${row.kind ? ` class="fuel-line fuel-${escape(row.kind)}" data-fuel-kind="${escape(row.kind)}"` : ''}><dt>${escape(row.label)}</dt><dd>${values}${reason}</dd></div>`;
}

function sourcesHtml(category, data, t) {
  const items = [];
  for (const row of category.rows) {
    for (const v of row.values) {
      if (!v.source) continue;  // a derived line (the fuel recommendation) has no source
      const s = v.source;
      const where = [s.title, s.publisher, s.locator].filter(Boolean).join(' · ');
      items.push(`<li><strong>${escape(row.label)}${v.qualifier ? ` · ${escape(v.qualifier)}` : ''}</strong>: ${escape(where)}${s.quote ? ` — «${escape(s.quote)}»` : ''}${s.url ? ` <a href="${escape(s.url)}" target="_blank" rel="noopener noreferrer">↗</a>` : ''}</li>`);
    }
  }
  return `<details class="us-tech-sources"><summary>${escape(t.sources)} · ${items.length}</summary><ol>${items.join('')}</ol></details>`;
}

function technicalHtml(data, t) {
  return data.categories.map((c, i) => `<details class="catalog-card technical-group us-tech-group" ${i === 0 ? 'open' : ''}><summary>${escape(c.title)}<small>${c.rows.length}</small></summary><dl>${c.rows.map(r => rowHtml(r, data)).join('')}</dl>${sourcesHtml(c, data, t)}</details>`).join('');
}

function weakPointsHtml(data, t) {
  return data.weak_points.map(w => `<article class="catalog-card us-tech-issue ${w.owner_reports ? 'owner-reports' : ''}">
    <h3>${escape(w.title)}</h3>${w.note ? `<p class="us-tech-note">${escape(w.note)}</p>` : ''}
    <dl>${w.component ? `<div><dt>${escape(t.component)}</dt><dd>${escape(w.component)}</dd></div>` : ''}${w.severity ? `<div><dt>${escape(t.severity)}</dt><dd>${escape(w.severity)}</dd></div>` : ''}${w.probability ? `<div><dt>${escape(t.probability)}</dt><dd>${escape(w.probability)}</dd></div>` : ''}${w.years?.length ? `<div><dt>${escape(t.years)}</dt><dd>${escape(w.years[0] === w.years[1] ? w.years[0] : w.years.join('–'))}</dd></div>` : ''}</dl>
    ${w.symptoms?.length ? `<p class="us-tech-label">${escape(t.symptoms)}</p><ul>${w.symptoms.map(s => `<li>${escape(s)}</li>`).join('')}</ul>` : ''}
    ${w.how_to_check ? `<p class="us-tech-label">${escape(t.check)}</p><p>${escape(w.how_to_check)}</p>` : ''}</article>`).join('');
}

function campaignsHtml(data, t) {
  return data.campaigns.map(c => `<article class="catalog-card us-tech-campaign"><h3>${escape(c.number)}</h3>
    ${c.component ? `<p class="us-tech-label">${escape(c.component)}</p>` : ''}${c.summary ? `<p>${escape(c.summary)}</p>` : ''}
    <p class="us-tech-note">${escape(t.years)}: ${escape(c.years?.[0] === c.years?.[1] ? c.years?.[0] : (c.years || []).join('–'))} · ${escape(c.note)}</p></article>`).join('');
}

function maintenanceHtml(data, t) {
  const groups = [[false, t.normal], [true, t.severe]].map(([severe, title]) => [title, data.maintenance.filter(m => m.severe === severe)]).filter(([, items]) => items.length);
  return groups.map(([title, items]) => `<section class="catalog-card us-tech-maintenance"><h3>${escape(title)}</h3><ul>${items.map(m => {
    const head = [m.job, m.action].filter(Boolean).join(' · ');
    const detail = [m.interval, m.occurrence, m.max_interval ? `${t.limit} ${m.max_interval}` : '', m.system].filter(Boolean).join(' · ');
    const tags = [m.service, m.qualifier, m.condition_detail].filter(Boolean).join(' · ');
    const marks = (m.approximate ? badge(data.labels.approximate, 'approximate') : '') + (m.secondary ? badge(data.labels.secondary, 'secondary') : '');
    return `<li><strong>${escape(head)}</strong>${detail ? `<span>${escape(detail)}</span>` : ''}${tags ? `<small>${escape(tags)}</small>` : ''}${marks}</li>`;
  }).join('')}</ul></section>`).join('');
}

// The panel for one configuration. A tab with no records is left out; with nothing at all the
// panel is empty (the caller shows nothing).
export function usTechHtml(data, language) {
  const t = copyOf(language);
  if (!data) return '';
  const tabs = [
    ['technical', data.categories?.length ? technicalHtml(data, t) : ''],
    ['weak_points', data.weak_points?.length ? weakPointsHtml(data, t) : ''],
    ['campaigns', data.campaigns?.length ? campaignsHtml(data, t) : ''],
    ['maintenance', data.maintenance?.length ? maintenanceHtml(data, t) : ''],
  ].filter(([, html]) => html);
  if (!tabs.length) return '';
  return `<section class="us-tech" aria-label="${escape(t.title)}">
    <div class="us-tech-heading"><h2>${escape(t.title)}</h2>${data.summary ? `<p>${escape(data.summary)}</p>` : ''}${data.designations?.length ? `<p class="us-tech-note">${escape(data.designations.join(' · '))}</p>` : ''}</div>
    <nav class="profile-categories us-tech-tabs" role="tablist" aria-label="${escape(t.title)}">${tabs.map(([key], i) => `<button type="button" role="tab" id="ustech-tab-${key}" aria-controls="ustech-panel-${key}" aria-selected="${i === 0}" tabindex="${i === 0 ? 0 : -1}" class="profile-category category-${key}" data-ustech-tab="${key}"><span aria-hidden="true">${ICONS[key]}</span>${escape(t[key])}</button>`).join('')}</nav>
    ${tabs.map(([key, html], i) => `<section id="ustech-panel-${key}" role="tabpanel" aria-labelledby="ustech-tab-${key}" class="us-tech-panel" ${i ? 'hidden' : ''}>${html}</section>`).join('')}
  </section>`;
}

export function bindUsTech(container) {
  if (!container || container.dataset.usTechBound) return;
  container.dataset.usTechBound = '1';
  const select = (tab, focus = false) => {
    container.querySelectorAll('[data-ustech-tab]').forEach(b => {const on = b === tab; b.setAttribute('aria-selected', String(on)); b.tabIndex = on ? 0 : -1;});
    container.querySelectorAll('.us-tech-panel').forEach(p => {p.hidden = p.id !== `ustech-panel-${tab.dataset.ustechTab}`;});
    if (focus) tab.focus();
  };
  container.addEventListener('click', e => {const tab = e.target.closest('[data-ustech-tab]'); if (tab) select(tab);});
  container.addEventListener('keydown', e => {
    const tab = e.target.closest('[data-ustech-tab]');
    if (!tab || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
    e.preventDefault();
    const tabs = [...container.querySelectorAll('[data-ustech-tab]')], i = tabs.indexOf(tab);
    select(tabs[e.key === 'Home' ? 0 : e.key === 'End' ? tabs.length - 1 : (i + (e.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length], true);
  });
}

export function createUsTechViews({root, state, layout}) {
  const enabled = () => state.meta?.us_tech_facts?.enabled === true;
  const language = () => (['az', 'en'].includes(state.language) ? state.language : 'ru');
  const t = () => copyOf(language());
  let facets = null;

  // the panel inside the existing vehicle card (a catalogue variant linked to a configuration)
  async function mount(container, variantId, valid = () => true) {
    if (!container || !enabled()) return;
    try {
      const data = await api(`/catalog/variants/${encodeURIComponent(variantId)}/us-tech?language=${language()}`);
      if (!valid()) return;
      container.innerHTML = usTechHtml(data, language());
      bindUsTech(container);
    } catch {
      container.innerHTML = '';  // no configuration behind this variant: nothing is shown
    }
  }

  function page(html) {
    root.innerHTML = layout(`<div class="catalog-view us-tech-view">${html}</div>`, {active: 'catalog'});
  }

  async function configuration(key) {
    page(`<p class="catalog-loading" role="status">${escape(t().loading)}</p>`);
    let data = null;
    try {data = await api(`/catalog/us-tech/configurations/${encodeURIComponent(key)}?language=${language()}`);} catch {data = null;}
    const body = data ? usTechHtml(data, language()) : '';
    page(`<div class="page-top"><a class="icon-button" href="#/us-tech" aria-label="${escape(t().back)}">←</a><strong>${escape(data?.title || t().title)}</strong></div>
      ${data ? `<section class="catalog-card vehicle-profile-summary"><h1>${escape(data.title)}</h1>${data.generation ? `<p>${escape(data.generation)}</p>` : ''}</section>` : ''}
      <div id="us-tech-page">${body || `<section class="catalog-card"><p>${escape(t().unavailable)}</p></section>`}</div>`);
    bindUsTech(root.querySelector('#us-tech-page'));
  }

  async function picker() {
    page(`<p class="catalog-loading" role="status">${escape(t().loading)}</p>`);
    facets = facets || await api('/catalog/us-tech/facets');
    const params = new URLSearchParams(location.hash.split('?')[1] || '');
    const make = params.get('make') || '', model = params.get('model') || '', year = params.get('year') || '';
    const makes = [...new Set(facets.map(f => f.make))];
    const models = facets.filter(f => f.make === make);
    const years = models.find(f => f.model === model)?.years || [];
    const options = (values, current) => `<option value="">${escape(t().choose)}</option>${values.map(v => `<option value="${escape(v)}" ${String(v) === String(current) ? 'selected' : ''}>${escape(v)}</option>`).join('')}`;
    let list = '';
    if (make && model && year) {
      const configs = await api(`/catalog/us-tech/configurations?make=${encodeURIComponent(make)}&model=${encodeURIComponent(model)}&year=${encodeURIComponent(year)}&language=${language()}`);
      list = configs.length
        ? configs.map(c => `<a class="catalog-card us-tech-config" href="#/us-tech/${encodeURIComponent(c.configuration_key)}"><strong>${escape(`${c.make} ${c.model} ${c.year}`)}</strong><span>${escape(c.label)}</span></a>`).join('')
        : `<p>${escape(t().none)}</p>`;
    }
    page(`<div class="catalog-heading"><h1>${escape(t().pickTitle)}</h1><p class="catalog-note">${escape(t().pickNote)}</p></div>
      <form class="catalog-card us-tech-picker">
        <label>${escape(t().make)}<select name="make">${options(makes, make)}</select></label>
        <label>${escape(t().model)}<select name="model" ${make ? '' : 'disabled'}>${options(models.map(f => f.model), model)}</select></label>
        <label>${escape(t().year)}<select name="year" ${model ? '' : 'disabled'}>${options(years, year)}</select></label>
      </form>${list}`);
    root.querySelector('.us-tech-picker').addEventListener('change', e => {
      const d = new FormData(e.currentTarget);
      const next = new URLSearchParams();
      if (d.get('make')) next.set('make', d.get('make'));
      if (d.get('make') === make && d.get('model')) next.set('model', d.get('model'));
      if (d.get('make') === make && d.get('model') === model && d.get('year')) next.set('year', d.get('year'));
      location.hash = `#/us-tech?${next}`;
    });
  }

  return {
    enabled,
    mount,
    async route(name, id) {
      if (!String(name || '').startsWith('us-tech') || !enabled()) return false;
      if (id) await configuration(id.split('?')[0]);
      else await picker();
      return true;
    },
  };
}
