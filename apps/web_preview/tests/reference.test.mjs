// The UI-by-reference pass: the one check field, the region, the UI flags, the fuel-only cost,
// the curated battles config, the Auto Expert opinion screen and the EN home without AZN / Turbo.az.
import assert from 'node:assert/strict';
import test from 'node:test';
import {readFile} from 'node:fs/promises';

const store = new Map();
globalThis.localStorage = {getItem: k => (store.has(k) ? store.get(k) : null), setItem: (k, v) => store.set(k, String(v)), removeItem: k => store.delete(k)};
globalThis.sessionStorage = {getItem: () => null, setItem() {}, removeItem() {}};
globalThis.document = globalThis.document || {documentElement: {classList: {toggle() {}}}, querySelector: () => null};
globalThis.location = globalThis.location || {hash: '#/home'};

const CYR = /[А-Яа-яЁё]/;

function fakeRoot() {
  return {innerHTML: '', addEventListener() {}, querySelector: () => null, querySelectorAll: () => []};
}

test('the one field recognises a VIN, a link, a plate and make / model / year', async () => {
  const {detectInput} = await import('../ui-config.js');
  assert.equal(detectInput('https://turbo.az/autos/10556520-kia-stinger'), 'LINK');
  assert.equal(detectInput('turbo.az/autos/10556520-kia-stinger'), 'LINK');
  assert.equal(detectInput('1HGCM82633A004352'), 'VIN');
  assert.equal(detectInput('1hgcm 82633a004352'), 'VIN');
  assert.equal(detectInput('10-AB-123'), 'PLATE');
  assert.equal(detectInput('Toyota Camry 2018'), 'TEXT');
  assert.equal(detectInput('hello'), 'UNKNOWN');
  assert.equal(detectInput(''), '');
});

test('the region follows the language until chosen; money follows the region', async () => {
  const {region, setRegion, money, currency, REGION_KEY} = await import('../ui-config.js');
  store.delete(REGION_KEY);
  assert.equal(region({language: 'en'}), 'US');
  assert.equal(region({language: 'ru'}), 'AZ');
  assert.equal(money(20000, {language: 'ru'}).replace(/\s/g, ' '), '20 000 AZN');
  assert.equal(money(20000, {language: 'en'}), '$20,000');
  setRegion('US');
  assert.equal(currency({language: 'ru'}), 'USD');
  store.delete(REGION_KEY);
});

test('older paths are hidden by flags that are off by default', async () => {
  const {flag, FLAG_DEFAULTS, FLAGS_KEY} = await import('../ui-config.js');
  for (const name of Object.keys(FLAG_DEFAULTS)) assert.equal(flag(name), false, name);
  assert.deepEqual(Object.keys(FLAG_DEFAULTS).sort(), ['listingPaste', 'ownershipQuestionnaire', 'randomPairs', 'serviceLabels']);
  store.set(FLAGS_KEY, JSON.stringify({listingPaste: true}));
  assert.equal(flag('listingPaste'), true);
  store.delete(FLAGS_KEY);
});

test('costs are fuel only: EPA L/100 km x km a month x the price; no price, no cost', async () => {
  const {fuelCost} = await import('../ui-config.js');
  const cost = fuelCost({litresPer100: 8, grade: 'AI92', monthlyKm: 1000, months: 24, prices: {AI92: 1}});
  assert.equal(cost.monthly, 80);
  assert.equal(cost.total, 1920);
  assert.equal(fuelCost({litresPer100: 8, grade: 'AI95', monthlyKm: 1000, months: 24, prices: {AI92: 1}}), null);
  assert.equal(fuelCost({litresPer100: null, grade: 'AI92', monthlyKm: 1000, months: 24, prices: {AI92: 1}}), null);
  const config = JSON.parse(await readFile(new URL('../fuel-prices.json', import.meta.url), 'utf8'));
  assert.equal(typeof config.prices, 'object');
  for (const key of Object.keys(config.prices)) assert.ok(['AI92', 'AI95', 'AI98', 'DIESEL'].includes(key), key);
});

test('battles are curated pairs of one class with a prepared short verdict and its sources', async () => {
  const config = JSON.parse(await readFile(new URL('../battles.json', import.meta.url), 'utf8'));
  assert.ok(config.battles.length >= 5);
  const titles = config.battles.map(b => b.members.map(m => m.model).join(' vs '));
  for (const wanted of ['Camry vs Accord', 'Corolla vs Civic', 'RAV4 vs CR-V', 'Optima vs Sonata', 'E-Class vs 5 Series']) assert.ok(titles.includes(wanted), wanted);
  for (const b of config.battles) {
    assert.equal(b.members.length, 2, b.id);
    for (const m of b.members) assert.ok(m.make && m.model && Number.isInteger(m.year), b.id);
    const years = b.members.map(m => m.year);
    assert.ok(Math.max(...years) - Math.min(...years) <= 2, b.id);
    assert.ok(b.subtitle.ru && b.subtitle.az && b.subtitle.en, b.id);
    assert.doesNotMatch(b.subtitle.en, CYR);
    assert.ok(b.verdict.lines.ru.length >= 1 && b.verdict.lines.ru.length <= 4, b.id);
    assert.equal(b.verdict.lines.en.length, b.verdict.lines.ru.length, b.id);
    for (const line of b.verdict.lines.en) assert.doesNotMatch(line, CYR, line);
    assert.ok(Array.isArray(b.verdict.sources), b.id);
    for (const m of b.members) for (const spec of Object.values(m.specs || {})) if (spec && spec.value !== null) assert.ok(spec.source, `${b.id}: a figure without its source`);
  }
});

test('the verdict: who is better at what, only parameters someone has, ties not mentioned', async () => {
  const {verdict, numberOf, specMetrics, metricsOf} = await import('../compare-verdict.js');
  assert.equal(numberOf('1 234 л'), 1234);
  assert.equal(numberOf('7,4 л/100 км'), 7.4);
  const {valueIn} = await import('../compare-verdict.js');
  // units: the first number is not always the comparable one
  assert.equal(valueIn('fuel', '27 mpg (8.7 L/100km)'), 8.7);
  assert.equal(valueIn('clearance', '5.7 in (145 mm)'), 145);
  assert.equal(valueIn('cargo', '392 qt (371 L)'), 371);
  assert.equal(valueIn('fuel', '27 mpg'), null);  // another unit only: not compared
  const a = {name: 'Toyota Camry', metrics: {power: {value: 203, text: '203 hp'}, fuel: {value: 7.4, text: '7.4'}, cargo: {value: 428, text: '428 L'}, problems: {value: 1003, serious: 1, count: 3}, recalls: {value: 3, count: 3}}};
  const b = {name: 'Honda Accord', metrics: {power: {value: 192, text: '192 hp'}, fuel: {value: 7.2, text: '7.2'}, cargo: {value: 473, text: '473 L'}, problems: {value: 5009, serious: 5, count: 9}, recalls: {value: 3, count: 3}}};
  const r = verdict([a, b], 'ru');
  assert.deepEqual(r.lines, ['Toyota Camry лучше по: мощность, известные проблемы', 'Honda Accord лучше по: багажник']);  // fuel within 3 %, recalls equal
  assert.deepEqual(r.table.map(x => x.key), ['power', 'fuel', 'cargo', 'problems', 'recalls']);  // no clearance, no safety: not mentioned
  assert.equal(r.table.find(x => x.key === 'power').cells[0].best, true);
  const en = verdict([a, b], 'en');
  assert.equal(en.lines[1], 'Honda Accord is better at: boot space');
  // published figures fill only what our base lacks, with their source
  const fill = specMetrics({specs: {power_hp: {value: 178, source: 'Toyota Pressroom'}, cargo_cuft: {value: 15.1, source: 'Edmunds'}}, safety: {value: 5, text: '5/5 NHTSA'}});
  const m = metricsOf({categories: [{rows: [{key: 'power_hp', values: [{value: '203 hp', source: {publisher: 'EPA'}}]}]}], weak_points: [], campaigns: []}, {}, fill.metrics);
  assert.equal(m.power.value, 203);
  assert.equal(Math.round(m.cargo.value), 428);
  assert.equal(m.safety.value, 5);
  assert.ok(m.sources.includes('Edmunds') && m.sources.includes('NHTSA 5-Star Safety Ratings'));
});

test('every new text has three languages and English has no Russian', async () => {
  for (const file of ['../expert-views.js', '../catalog-views.js']) {
    const source = await readFile(new URL(file, import.meta.url), 'utf8');
    const S = String.raw`'((?:[^'\\\n]|\\.)*)'|"((?:[^"\\\n]|\\.)*)"|` + '`((?:[^`\\\\]|\\\\.)*)`';
    const call = new RegExp(String.raw`\b(?:p|T)\(\s*(?:${S})\s*,\s*(?:${S})\s*(?:,\s*(?:${S})\s*)?\)`, 'g');
    const found = [...source.matchAll(call)].map(m => [m[1] ?? m[2] ?? m[3], m[4] ?? m[5] ?? m[6], m[7] ?? m[8] ?? m[9]]);
    assert.ok(found.length > 40, `${file}: ${found.length}`);
    for (const [ru, az, en] of found) {
      if (!CYR.test(ru)) continue;
      assert.ok(en !== undefined, `${file}: no English for ${ru}`);
      assert.doesNotMatch(en, CYR, en);
    }
  }
});

test('the opinion screen: behind the flag, the confirmed car, seller claims apart, and a mismatch shows no car', async () => {
  const {createExpertViews} = await import('../expert-views.js');
  const root = fakeRoot();
  const state = {language: 'ru', meta: {}};
  const replies = [];
  globalThis.fetch = async () => ({ok: true, status: 200, headers: {get: () => 'application/json'}, json: async () => replies.shift(), text: async () => JSON.stringify(replies.shift())});
  const views = createExpertViews({root, state, layout: x => x, go() {}, ensureSession: async () => {}, showToast() {}});
  assert.equal(await views.route('check'), false);  // flag off: the old check path answers
  state.meta = {expert_opinion_v1: {enabled: true}};
  assert.equal(await views.route('check'), true);
  assert.match(root.innerHTML, /Turbo\.az/);
  state.language = 'en';
  localStorage.setItem('autoexpert.ui.region', 'US');
  await views.route('check');
  assert.doesNotMatch(root.innerHTML, /Turbo\.az|AZN/);
  localStorage.removeItem('autoexpert.ui.region');
  state.language = 'ru';
  const ok = views.render({status: 'OK', make: 'Toyota', model: 'Camry', year: 2020, confirmed: true, source: {kind: 'LINK'},
    configuration: {key: 'k', label: '2.5 л', generation: 'XV70'}, summary: ['Конфигурация определена однозначно'],
    claims: {make: 'Toyota', model: 'Camry', mileage_km: 87000, price: 29400, currency: 'AZN', raw: {engine: '2.5 L / 203 a.g. / Benzin'}, vin: '4T1B11HK5KU000000'},
    discrepancies: [{text: 'Объём 3.0 л не встречается'}], notes: [], checklist: [{text: 'Check by VIN.', kind: 'issue'}],
    next_service: [{label: 'Воздушный фильтр', status: 'OK', next_km: 96000, note: 'по регламенту'}], weak_points: [], campaigns: []});
  assert.match(ok, /Toyota Camry 2020/);
  assert.match(ok, /Модификация подтверждена/);
  assert.match(ok, /Указано в объявлении/);
  assert.match(ok, /Расхождения с базой/);
  assert.match(ok, /Что проверить при осмотре/);
  assert.match(ok, /Проверить историю по VIN/);
  const mismatch = views.render({status: 'MODEL_MISMATCH', message: 'Модель не совпадает', claims: {make: 'Kia', model: 'Stinger'}});
  assert.match(mismatch, /ae-error-card/);
  assert.doesNotMatch(mismatch, /K5|Модификация подтверждена|Что проверить/);
  const missing = views.render({status: 'MODEL_NOT_IN_BASE', message: 'Модели Kia Stinger пока нет в нашей базе.', claims: {make: 'Kia', model: 'Stinger', year: 2018, mileage_km: 70000}});
  assert.match(missing, /Stinger/);
  assert.doesNotMatch(missing, /K5/);
  const blocked = views.render({status: 'LISTING_UNAVAILABLE', message: 'x', paste_text: true});
  assert.match(blocked, /expert-paste/);  // the text paste appears only when the site could not be read
  assert.doesNotMatch(views.render(missing ? {status: 'MODEL_NOT_IN_BASE', message: 'x'} : {}), /expert-paste/);
});

test('regression: a new check never shows the car of the previous one', async () => {
  const {createExpertViews} = await import('../expert-views.js');
  const session = new Map();
  globalThis.sessionStorage = {getItem: k => session.get(k) ?? null, setItem: (k, v) => session.set(k, String(v)), removeItem: k => session.delete(k)};
  const sent = [];
  const reply = query => (query.includes('stinger')
    ? {status: 'MODEL_NOT_IN_BASE', message: 'Модели Kia Stinger пока нет в нашей базе.', claims: {make: 'Kia', model: 'Stinger'}}
    : {status: 'OK', make: 'Toyota', model: 'Camry', year: 2019, confirmed: true, source: {kind: 'LINK'}, configuration: {key: 'k', label: '2.5 л'},
      summary: [], claims: {make: 'Toyota', model: 'Camry'}, discrepancies: [], notes: [], checklist: [], next_service: [], weak_points: [], campaigns: []});
  globalThis.fetch = async (url, options) => {
    const body = JSON.parse(options.body);
    sent.push(body.query);
    return {ok: true, status: 200, headers: {get: () => 'application/json'}, json: async () => reply(body.query)};
  };
  const root = fakeRoot();
  const state = {language: 'ru', meta: {expert_opinion_v1: {enabled: true}}};
  const views = createExpertViews({root, state, layout: x => x, go() {}, ensureSession: async () => {}, showToast() {}});
  session.set('autoexpert.expert.request', JSON.stringify({query: 'https://turbo.az/autos/10556520-kia-stinger'}));
  await views.route('opinion');
  assert.match(root.innerHTML, /Stinger/);
  session.set('autoexpert.expert.request', JSON.stringify({query: 'https://turbo.az/autos/10690262-toyota-camry'}));
  await views.route('opinion');
  assert.match(root.innerHTML, /Toyota Camry 2019/);
  assert.doesNotMatch(root.innerHTML, /Stinger/);
  await views.route('opinion');  // the same request again: the kept result, no second fetch
  assert.equal(sent.length, 2);
  globalThis.sessionStorage = {getItem: () => null, setItem() {}, removeItem() {}};
});

test('the EN home has no AZN, no Turbo.az and no Azerbaijan label', async () => {
  const {createCatalogViews} = await import('../catalog-views.js');
  const {createExpertViews} = await import('../expert-views.js');
  const root = fakeRoot();
  const state = {language: 'en', meta: {expert_opinion_v1: {enabled: true}}};
  const expert = createExpertViews({root, state, layout: x => x, go() {}, ensureSession: async () => {}, showToast() {}});
  const views = createCatalogViews({root, state, layout: x => x, go() {}, esc: s => String(s ?? ''), ensureSession: async () => {}, showToast() {}, expert: () => expert});
  await views.route('home');
  assert.ok(root.innerHTML.length > 500);
  assert.doesNotMatch(root.innerHTML, /AZN|Turbo\.az|Azerbaijan|AZƏRBAYCAN/);
  state.language = 'ru';
  await views.route('home');
  assert.match(root.innerHTML, /Turbo\.az/);
});
