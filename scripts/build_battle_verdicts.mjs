// Prepare the short verdicts of the curated battles once (owner 2026-10-06): our database for
// power, fuel use, boot, clearance, known problems and recalls (the same compare-verdict.js the
// comparison screen uses), NHTSA 5-Star overall ratings for safety (not in our base; the source is
// named), and the published figures in each member's "specs" (power, EPA mpg, boot, clearance,
// each with its source) where our base has none. Writes verdict / safety into battles.json.
//   node scripts/build_battle_verdicts.mjs [base_url]      (the preview API, e.g. http://127.0.0.1:8020)
import {readFile, writeFile} from 'node:fs/promises';

globalThis.localStorage = {getItem: () => null, setItem() {}, removeItem() {}};
const {metricsOf, specMetrics, verdict} = await import('../apps/web_preview/compare-verdict.js');
const base = process.argv[2] || 'http://127.0.0.1:8020';
const file = new URL('../apps/web_preview/battles.json', import.meta.url);
const config = JSON.parse(await readFile(file, 'utf8'));
const FILTERS = {catalog_scope: 'US_BASE_2000', catalog_ready_only: true, market_preference: 'SELECTED', markets: ['US'], sort: 'recommended', limit: 30};
const NHTSA = 'NHTSA 5-Star Safety Ratings';

async function json(url, options) {
  const r = await fetch(url, options);
  if (!r.ok) throw new Error(`${url} ${r.status}`);
  return r.json();
}

// the same base version the app compares: not a preview, gasoline without hybrid, the smallest engine
async function baseVariant(m) {
  const data = await json(`${base}/api/v1/knowledge/search?language=ru`, {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({...FILTERS, makes: [m.make], models: [m.model], year_min: m.year, year_max: m.year})});
  const disp = v => Number(v.facts?.engine_displacement?.value) || 99;
  const plain = v => (v.facts?.fuel?.value === 'GASOLINE' && v.facts?.powertrain?.value === 'ICE' ? 0 : 1);
  return (data.matches || []).slice().sort((a, b) => (!!a.preview - !!b.preview) || (plain(a) - plain(b)) || (disp(a) - disp(b)))[0] || null;
}

async function safety(m) {
  try {
    const list = await json(`https://api.nhtsa.gov/SafetyRatings/modelyear/${m.year}/make/${encodeURIComponent(m.make)}/model/${encodeURIComponent(m.model)}`);
    const items = list.Results || [];
    const pick = items.find(x => /FWD|4 DR/.test(x.VehicleDescription || '')) || items[0];
    if (!pick) return null;
    const rating = (await json(`https://api.nhtsa.gov/SafetyRatings/VehicleId/${pick.VehicleId}`)).Results?.[0]?.OverallRating;
    const value = Number(rating);
    return value ? {value, text: `${value}/5 NHTSA`, source: `${NHTSA}: ${pick.VehicleDescription}`} : null;
  } catch {
    return null;
  }
}

for (const battle of config.battles) {
  const cars = [];
  for (const m of battle.members) {
    const v = await baseVariant(m);
    const tech = v ? await json(`${base}/api/v1/catalog/variants/${v.id}/us-tech?language=en`).catch(() => null) : null;
    const s = await safety(m);
    if (s) m.safety = s; else delete m.safety;
    cars.push({name: `${m.make} ${m.model}`, metrics: metricsOf(tech, {}, specMetrics(m).metrics), found: !!v});
  }
  const sources = [];
  const lines = {};
  for (const language of ['ru', 'az', 'en']) lines[language] = verdict(cars, language, {sources}).lines;
  battle.verdict = {lines, sources: verdict(cars, 'en', {sources}).sources, prepared: new Date().toISOString().slice(0, 10)};
  console.log(battle.id, cars.map(c => c.found ? '' : `missing ${c.name}`).join(' '), '|', lines.ru.join(' / '));
}
await writeFile(file, JSON.stringify(config, null, 2) + '\n', 'utf8');
