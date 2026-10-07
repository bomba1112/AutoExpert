// The visual-match pass: colours only from design/tokens.json, the icons exist, no glyph the
// local font lacks, photos only under licences that allow use in the app.
import assert from 'node:assert/strict';
import test from 'node:test';
import {readFile} from 'node:fs/promises';

const read = path => readFile(new URL(path, import.meta.url), 'utf8');

for (const sheet of ['../visual.css', '../styles.css'])
test(`every colour of ${sheet.slice(3)} comes from the tokens`, async () => {
  const css = await read(sheet);
  const lines = css.split(/[;{}]/).filter(d => !/mask/.test(d) && !/@font-face|src:|unicode-range/.test(d));
  const literal = lines.filter(d => /#[0-9a-f]{3,8}\b|\brgba?\(|\bhsla?\(/i.test(d));
  assert.deepEqual(literal, []);
  const used = new Set([...css.matchAll(/var\(--ae-([a-z0-9-]+)\)/g)].map(m => m[1]));
  const tokens = await read('../tokens.css');
  for (const name of used) assert.match(tokens, new RegExp(`--ae-${name}:`), name);
});

test('tokens.css is tokens.json', async () => {
  const doc = JSON.parse(await read('../../../design/tokens.json'));
  const css = await read('../tokens.css');
  for (const [k, v] of Object.entries(doc.color)) assert.match(css, new RegExp(`--ae-${k.replace(/_/g, '-')}: ${v};`), k);
  for (const [k, v] of Object.entries(doc.derived)) assert.match(css, new RegExp(`--ae-${k.replace(/_/g, '-')}: ${v.value};`), k);
});

test('the icons the screens ask for exist', async () => {
  globalThis.localStorage = globalThis.localStorage || {getItem: () => null, setItem() {}, removeItem() {}};
  const {OUTLINE, icon} = await import('../icons.js');
  for (const file of ['../catalog-views.js', '../expert-views.js', '../app-v2.js']) {
    const src = await read(file);
    const names = [...src.matchAll(/icon\('([a-z0-9-]+)'/g)].map(m => m[1]);
    assert.ok(names.length >= 2, file);
    for (const n of names) assert.ok(OUTLINE[n], `${file}: ${n}`);
  }
  for (const value of (await read('../catalog-views.js')).matchAll(/'(engine|manual-gearbox|gas-station|wind|droplet|car|disc|armchair|bolt)'/g)) assert.ok(OUTLINE[value[1]], value[1]);
  assert.match(icon('car'), /^<svg class="ic ic-car"/);
});

test('no arrows, ticks or emoji the font has no glyph for (they would come from a fallback font)', async () => {
  for (const file of ['../catalog-views.js', '../expert-views.js', '../visual.js']) {
    const src = await read(file);
    const bad = [...src].filter(ch => /[←-⇿✓✔＋⌂⌕▤ℹ]|\p{Extended_Pictographic}/u.test(ch));
    assert.deepEqual(bad, [], file);
  }
});

test('car photos are freely licensed and credited', async () => {
  const src = await read('../photos.js');
  const photos = JSON.parse(src.match(/export const PHOTOS = (.*);\r?\n/)[1]);
  for (const p of photos) {
    assert.match(p.license || '', /^(CC0|Public domain|PD|CC BY(-SA)?( \d\.\d)?)/i, p.file);
    assert.doesNotMatch(p.license, /NC|ND/, p.file);
    assert.ok(p.author && p.source_page, p.file);
  }
});
