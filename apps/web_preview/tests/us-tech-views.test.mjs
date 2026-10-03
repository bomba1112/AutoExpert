import assert from 'node:assert/strict';
import test from 'node:test';
import {usTechHtml} from '../us-tech-views.js';

const labels = {secondary: 'по данным справочников', approximate: 'ориентировочно', owner_reports: 'владельцы сообщают', sources: 'Источники'};
const value = (v, extra = {}) => ({value: v, qualifier: null, secondary: false, approximate: false, level: 'GENERATION', source: {title: 'Owner manual', locator: 'page 541', quote: 'q'}, ...extra});
const rows = n => Array.from({length: n}, (_, i) => ({key: `k${i}`, label: `Field ${i}`, values: [value(`${i} mm`)]}));
const data = (extra = {}) => ({summary: '2.5 л · ДВС', designations: ['Camry LE/SE'], categories: [], weak_points: [], campaigns: [], maintenance: [], labels, ...extra});

test('nothing to show renders nothing', () => {
  assert.equal(usTechHtml(data(), 'ru'), '');
  assert.equal(usTechHtml(null, 'ru'), '');
});

test('empty tabs are left out and the maintenance tab appears only with records', () => {
  const html = usTechHtml(data({categories: [{key: 'engine', title: 'Двигатель', rows: rows(5)}]}), 'ru');
  assert.match(html, /data-ustech-tab="technical"/);
  assert.doesNotMatch(html, /data-ustech-tab="maintenance"|data-ustech-tab="weak_points"|data-ustech-tab="campaigns"/);
  const withJobs = usTechHtml(data({maintenance: [{job: 'Масло', action: 'замена', interval: '16 000 км или 1 год', severe: false, approximate: true, secondary: false}]}), 'ru');
  assert.match(withJobs, /data-ustech-tab="maintenance"/);
  assert.match(withJobs, /ориентировочно/);
});

test('secondary values are marked and every value keeps its source', () => {
  const html = usTechHtml(data({categories: [{key: 'fluids', title: 'Масла и жидкости', rows: [
    {key: 'engine_oil_viscosity', label: 'Вязкость масла', values: [value('SAE 0W-16', {secondary: true})]},
    {key: 'curb_weight_kg', label: 'Масса', values: [value('1470 кг', {qualifier: 'L'}), value('1495 кг', {qualifier: 'LE'})]},
  ]}]}), 'ru');
  assert.match(html, /SAE 0W-16<\/span><small class="us-tech-badge secondary">по данным справочников/);
  assert.match(html, /<ul class="us-tech-values">/);
  assert.match(html, /Источники · 3/);
});

test('five and forty rows both render as one collapsible group per category', () => {
  for (const n of [5, 40]) {
    const html = usTechHtml(data({categories: [{key: 'body', title: 'Кузов и размеры', rows: rows(n)}, {key: 'engine', title: 'Двигатель', rows: rows(2)}]}), 'az');
    assert.equal((html.match(/<details class="catalog-card technical-group us-tech-group"/g) || []).length, 2);
    assert.equal((html.match(/<dt>/g) || []).length, n + 2);
    assert.match(html, /Texniki məlumatlar/);
  }
});

test('text from the database is escaped', () => {
  const html = usTechHtml(data({weak_points: [{title: '<script>x</script>', severity: 'высокая', symptoms: ['a&b'], owner_reports: true, note: 'владельцы сообщают', years: [2018, 2020]}]}), 'ru');
  assert.doesNotMatch(html, /<script>/);
  assert.match(html, /&lt;script&gt;/);
  assert.match(html, /владельцы сообщают/);
});
