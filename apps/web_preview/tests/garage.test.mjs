import assert from 'node:assert/strict';
import test from 'node:test';
import {readFile} from 'node:fs/promises';

const CYR = /[А-Яа-яЁё]/;
// a JS string literal in single or double quotes
const S = String.raw`'((?:[^'\\\n]|\\.)*)'|"((?:[^"\\\n]|\\.)*)"`;
const TRIPLE = new RegExp(String.raw`\[\s*(?:${S})\s*,\s*(?:${S})\s*,\s*(?:${S})\s*\]`, 'g');
const PAIR = new RegExp(String.raw`\[\s*(?:${S})\s*,\s*(?:${S})\s*\]`, 'g');

test('every Garage text has Russian, Azerbaijani and English, and English has no Russian', async () => {
  const source = await readFile(new URL('../garage-views.js', import.meta.url), 'utf8');
  const found = [...source.matchAll(TRIPLE)].map(m => [m[1] ?? m[2], m[3] ?? m[4], m[5] ?? m[6]]);
  assert.ok(found.length > 60, String(found.length));
  for (const [ru, az, en] of found) {
    if (!CYR.test(ru)) continue;
    assert.ok(az && en, ru);
    assert.doesNotMatch(en, CYR, en);
    assert.doesNotMatch(az, CYR, az);
  }
  // no Russian text is left with only two languages
  assert.deepEqual([...source.matchAll(PAIR)].map(m => m[0]).filter(x => CYR.test(x)), []);
});

test('the Garage is behind the garage_v1 flag', async () => {
  globalThis.localStorage = {getItem: () => null, setItem() {}, removeItem() {}};
  const {createGarageViews, garageCopy} = await import('../garage-views.js');
  const state = {language: 'en', meta: {}};
  const views = createGarageViews({root: {}, state, layout: x => x, go() {}, ensureSession: async () => {}, showToast() {}});
  assert.equal(views.enabled(), false);
  assert.equal(await views.route('garage'), false);
  assert.equal(views.homeCard(), '');
  state.meta = {garage_v1: {enabled: true}};
  assert.equal(views.enabled(), true);
  assert.match(views.homeCard(), /Garage/);
  assert.equal(garageCopy('ru', 'statuses.OVERDUE'), 'Просрочено');
  assert.equal(garageCopy('az', 'garage'), 'Qaraj');
});
