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

test('battles are curated: 2-3 cars, close years, three languages', async () => {
  const config = JSON.parse(await readFile(new URL('../battles.json', import.meta.url), 'utf8'));
  assert.ok(config.battles.length >= 5);
  const titles = config.battles.map(b => b.members.map(m => m.model).join(' vs '));
  for (const wanted of ['Camry vs Accord vs Sonata', 'Corolla vs Elantra vs Civic', 'RAV4 vs CR-V vs Tucson', 'Optima vs Sonata', 'E-Class vs 5 Series']) assert.ok(titles.includes(wanted), wanted);
  for (const b of config.battles) {
    assert.ok(b.members.length >= 2 && b.members.length <= 3, b.id);
    for (const m of b.members) assert.ok(m.make && m.model && Number.isInteger(m.year), b.id);
    const years = b.members.map(m => m.year);
    assert.ok(Math.max(...years) - Math.min(...years) <= 2, b.id);
    assert.ok(b.subtitle.ru && b.subtitle.az && b.subtitle.en, b.id);
    assert.doesNotMatch(b.subtitle.en, CYR);
  }
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
