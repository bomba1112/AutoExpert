import assert from 'node:assert/strict';
import test from 'node:test';
import {EN, pickText, deviceLanguage} from '../en-text.js';
import {message} from '../catalog-copy.js';
import {copyOf, usTechHtml} from '../us-tech-views.js';

const CYR = /[А-Яа-яЁё]/;

test('the English table has no Russian left', () => {
  const bad = Object.entries(EN).filter(([, en]) => CYR.test(en));
  assert.deepEqual(bad, []);
});

test('pickText chooses the language and falls back to the table', () => {
  assert.equal(pickText('ru', 'Двигатель', 'Mühərrik'), 'Двигатель');
  assert.equal(pickText('az', 'Двигатель', 'Mühərrik'), 'Mühərrik');
  assert.equal(pickText('en', 'Двигатель', 'Mühərrik', 'Engine'), 'Engine');
});

test('the device language: en, ru, az, else English', () => {
  assert.equal(deviceLanguage(['ru-RU', 'en-US']), 'ru');
  assert.equal(deviceLanguage(['az-Latn-AZ']), 'az');
  assert.equal(deviceLanguage(['en-CA']), 'en');
  assert.equal(deviceLanguage(['de-DE', 'fr-FR']), 'en');
  assert.equal(deviceLanguage([]), 'en');
});

test('catalog and US tech copy are fully English in English', () => {
  for (const key of ['previewBadge', 'previewNote', 'open', 'addCompare', 'compare', 'remove']) {
    assert.doesNotMatch(message('en', key), CYR, key);
  }
  const copy = copyOf('en');
  for (const [key, value] of Object.entries(copy)) assert.doesNotMatch(value, CYR, key);
  const html = usTechHtml({summary: '2.5 L', designations: [], categories: [{key: 'engine', title: 'Engine', rows: [{key: 'k', label: 'Power', values: [{value: '203 hp', qualifier: null, source: {title: 'manual'}}]}]}], weak_points: [], campaigns: [], maintenance: [], labels: {secondary: 'per reference sources', approximate: 'approx.', owner_reports: 'owners report', sources: 'Sources'}}, 'en');
  assert.doesNotMatch(html, CYR);
});

test('every [ru, az] pair of the modules has English', async () => {
  const {readFile, readdir} = await import('node:fs/promises');
  const dir = new URL('../', import.meta.url);
  const S = "'((?:[^'\\\\\\n]|\\\\.)*)'";
  const pair = new RegExp(`\\[\\s*${S}\\s*,\\s*${S}\\s*(?:,\\s*${S}\\s*)?\\]`, 'g');
  const missing = [];
  for (const name of (await readdir(dir)).filter(n => n.endsWith('.js') && n !== 'en-text.js')) {
    const source = await readFile(new URL(name, dir), 'utf8');
    for (const m of source.matchAll(pair)) {
      if (CYR.test(m[1]) && m[3] === undefined && !(m[1] in EN)) missing.push(`${name}: ${m[1]}`);
    }
  }
  assert.deepEqual(missing, []);
});

test('every locale has the same keys and English has no Russian', async () => {
  const {readFile} = await import('node:fs/promises');
  const load = async l => JSON.parse(await readFile(new URL(`../locales/${l}.json`, import.meta.url), 'utf8'));
  const [ru, az, en] = await Promise.all(['ru', 'az', 'en'].map(load));
  assert.deepEqual(Object.keys(en).sort(), Object.keys(ru).sort());
  assert.deepEqual(Object.keys(az).sort(), Object.keys(ru).sort());
  assert.deepEqual(Object.entries(en).filter(([, v]) => CYR.test(v)), []);
});
