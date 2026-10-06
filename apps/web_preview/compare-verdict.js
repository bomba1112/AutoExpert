// The short comparison verdict (owner 2026-10-06): two cars of one class, "A is better at: …",
// "B is better at: …", the parameters we have, the sources in one line. Made from our database
// at request time; a parameter nobody has is not mentioned. Curated battles carry the same kind
// of verdict prepared once in battles.json (scripts/build_battle_verdicts.py).
import {pickText} from './en-text.js?v=0.13.0';

export const PARAMS = [
  {key: 'power', better: 'high', label: ['мощность', 'güc', 'power'], rows: ['power_hp', 'system_power_hp']},
  {key: 'fuel', better: 'low', label: ['расход', 'sərfiyyat', 'fuel use'], rows: ['fuel_combined']},
  {key: 'cargo', better: 'high', label: ['багажник', 'baqaj', 'boot space'], rows: ['cargo_l']},
  {key: 'clearance', better: 'high', label: ['клиренс', 'klirens', 'ground clearance'], rows: ['ground_clearance']},
  {key: 'safety', better: 'high', label: ['безопасность', 'təhlükəsizlik', 'safety']},
  {key: 'problems', better: 'low', label: ['известные проблемы', 'məlum problemlər', 'known problems']},
  {key: 'recalls', better: 'low', label: ['отзывные кампании', 'geri çağırmalar', 'recalls']},
];
const TOLERANCE = 0.03;  // closer than 3 %: neither is better

// the number with the unit the comparison needs: values may read "27 mpg (8.7 L/100km)", "5.7 in
// (145 mm)", "392 qt (371 L)" — the first number is not always the right one
const NUM = String.raw`(\d+(?:[.,]\d+)?)`;
export const UNITS = {
  power: new RegExp(NUM + String.raw`\s*(?:hp|л\.?\s?с|a\.?\s?g)`, 'i'),
  fuel: new RegExp(NUM + String.raw`\s*(?:l|л)\s*\/\s*100`, 'i'),
  cargo: new RegExp(NUM + String.raw`\s*(?:l|л)(?![a-zа-я\/])`, 'i'),
  clearance: new RegExp(NUM + String.raw`\s*(?:mm|мм)`, 'i'),
};

export function valueIn(key, text) {
  const clean = String(text ?? '').replace(/(\d)[\s ](?=\d{3}\b)/g, '$1');
  const match = UNITS[key] ? clean.match(UNITS[key]) : null;
  if (match) return Number(match[1].replace(',', '.'));
  return UNITS[key] && /[a-zа-я]/i.test(clean.replace(/\d|[.,\s()]/g, '')) ? null : numberOf(clean);  // another unit only: not comparable
}

export function numberOf(text) {
  const match = String(text ?? '').replace(/(\d)[\s ](?=\d{3}\b)/g, '$1').match(/\d+(?:[.,]\d+)?/);
  return match ? Number(match[0].replace(',', '.')) : null;
}

// published figures prepared for a curated battle (battles.json "specs", each with its source):
// they only fill what our database does not have
export function specMetrics(member) {
  const s = member?.specs || {};
  const out = {}, sources = [];
  const put = (key, spec, value, text) => {
    if (!spec || !(Number(spec.value) > 0)) return;
    out[key] = {value, text, source: spec.source};
    if (spec.source) sources.push(spec.source);
  };
  put('power', s.power_hp, Number(s.power_hp?.value), `${s.power_hp?.value} hp`);
  put('fuel', s.mpg_combined, 235.215 / Number(s.mpg_combined?.value), `${(235.215 / Number(s.mpg_combined?.value)).toFixed(1)} L/100 km (${s.mpg_combined?.value} mpg)`);
  put('cargo', s.cargo_cuft, Number(s.cargo_cuft?.value) * 28.3168, `${Math.round(Number(s.cargo_cuft?.value) * 28.3168)} L`);
  put('clearance', s.clearance_in, Number(s.clearance_in?.value) * 25.4, `${Math.round(Number(s.clearance_in?.value) * 25.4)} mm`);
  if (member?.safety) {
    out.safety = {...member.safety, source: 'NHTSA 5-Star Safety Ratings'};
    sources.push('NHTSA 5-Star Safety Ratings');
  }
  return {metrics: out, sources};
}

// the figures of one car from its US technical card (us_tech_facts.build); `fill` completes only
// what the card does not have
export function metricsOf(tech, extra = {}, fill = {}) {
  const out = {};
  if (!tech) return {...fill, ...extra, sources: [...new Set(Object.values(fill).map(m => m?.source).filter(Boolean))]};
  const rows = Object.fromEntries((tech.categories || []).flatMap(c => c.rows).map(r => [r.key, r]));
  const sources = new Set();
  for (const p of PARAMS.filter(x => x.rows)) {
    const row = p.rows.map(k => rows[k]).find(r => r?.values?.length);
    const value = row ? valueIn(p.key, row.values[0].value) : null;
    if (value) {
      out[p.key] = {value, text: row.values[0].value};
      const s = row.values[0].source;
      if (s?.publisher || s?.title) sources.add(String(s.publisher || s.title).split(' (')[0]);
    }
  }
  const weak = tech.weak_points || [];
  const serious = weak.filter(w => ['HIGH', 'CRITICAL'].includes(w.severity_code)).length;
  out.problems = {value: serious * 1000 + weak.length, serious, count: weak.length};
  out.recalls = {value: (tech.campaigns || []).length, count: (tech.campaigns || []).length};
  if (weak.length) sources.add('Auto Expert known issues');
  if ((tech.campaigns || []).length) sources.add('NHTSA recalls');
  for (const [key, value] of Object.entries(fill)) {
    if (!out[key] && value) {
      out[key] = value;
      if (value.source) sources.add(value.source);
    }
  }
  out.sources = [...sources];
  return {...out, ...extra};
}

function cellText(key, m, language) {
  if (!m) return null;
  if (key === 'problems') return pickText(language, `${m.count}, серьёзных ${m.serious}`, `${m.count}, ciddi ${m.serious}`, `${m.count}, ${m.serious} serious`);
  if (key === 'recalls') return String(m.count);
  if (key === 'safety') return m.text || `${m.value}/5`;
  return m.text || String(m.value);
}

// cars: [{name, metrics}] -> {lines, table, sources}
export function verdict(cars, language, {sources = []} = {}) {
  const label = p => pickText(language, ...p.label);
  const wins = cars.map(() => []);
  const table = [];
  for (const p of PARAMS) {
    const values = cars.map(c => c.metrics?.[p.key]);
    if (!values.some(Boolean)) continue;  // nobody has it: not mentioned
    let best = -1;
    if (values.every(Boolean)) {
      const nums = values.map(v => v.value);
      const pick = p.better === 'high' ? Math.max(...nums) : Math.min(...nums);
      const others = nums.filter(n => n !== pick);
      const gap = others.length ? Math.min(...others.map(n => Math.abs(n - pick) / Math.max(Math.abs(pick), Math.abs(n), 1))) : 0;
      if (others.length && gap > TOLERANCE && nums.filter(n => n === pick).length === 1) {
        best = nums.indexOf(pick);
        wins[best].push(label(p));
      }
    }
    table.push({key: p.key, label: label(p)[0].toUpperCase() + label(p).slice(1), cells: values.map((v, i) => (v ? {text: cellText(p.key, v, language), best: i === best} : null))});
  }
  const lines = cars.map((c, i) => (wins[i].length ? pickText(language, `${c.name} лучше по: ${wins[i].join(', ')}`, `${c.name} daha yaxşıdır: ${wins[i].join(', ')}`, `${c.name} is better at: ${wins[i].join(', ')}`) : null)).filter(Boolean);
  if (!lines.length && table.length) lines.push(pickText(language, 'По данным нашей базы заметной разницы нет', 'Bazamızın məlumatlarına görə nəzərəçarpan fərq yoxdur', 'Our data show no clear difference'));
  const all = [...new Set([...cars.flatMap(c => c.metrics?.sources || []), ...sources])];
  return {lines, table, sources: all};
}
