// The region and the UI flags (UI-by-reference prompt, 2.1 and 2.7).
// Region AZ: budget in AZN, Turbo.az, the "Azerbaijan" label. Region US: $, no Turbo.az, no label.
// Unset, it follows the language (EN -> US, RU / AZ -> AZ); the profile screen changes it.
// Flags hide older paths without deleting their code: all off by default; a tester turns one on
// with localStorage 'autoexpert.ui.flags' = {"listingPaste": true, ...}.

export const REGION_KEY = 'autoexpert.ui.region';
export const FLAGS_KEY = 'autoexpert.ui.flags';
export const FLAG_DEFAULTS = Object.freeze({
  listingPaste: false,            // pasting listing text / HTML as the main check path
  ownershipQuestionnaire: false,  // the ownership-cost questionnaire as a screen of its own
  randomPairs: false,             // comparison pairs picked from the first search results
  serviceLabels: false,           // "preview", "catalog configurations", "источники AZ"...
});

export function region(state) {
  try {
    const value = localStorage.getItem(REGION_KEY);
    if (value === 'AZ' || value === 'US') return value;
  } catch {}
  return state?.language === 'en' ? 'US' : 'AZ';
}

export function setRegion(value) {
  try { localStorage.setItem(REGION_KEY, value === 'US' ? 'US' : 'AZ'); } catch {}
}

export function flag(name) {
  let stored = {};
  try { stored = JSON.parse(localStorage.getItem(FLAGS_KEY) || '{}') || {}; } catch {}
  const runtime = globalThis.AUTOEXPERT_UI_FLAGS || {};
  const value = name in stored ? stored[name] : name in runtime ? runtime[name] : FLAG_DEFAULTS[name];
  return value === true;
}

export function currency(state) {
  return region(state) === 'US' ? 'USD' : 'AZN';
}

export function money(amount, state) {
  if (amount === null || amount === undefined || amount === '') return '';
  const n = Number(amount);
  if (!Number.isFinite(n)) return '';
  const locale = state?.language === 'az' ? 'az-Latn-AZ' : state?.language === 'en' ? 'en-US' : 'ru-RU';
  const text = Math.round(n).toLocaleString(locale);
  return currency(state) === 'USD' ? `$${text}` : `${text} AZN`;
}

// Budget steps of the selection: AZN for AZ, dollars for US.
export function budgetSteps(state) {
  return currency(state) === 'USD' ? [10000, 15000, 20000, 25000, 30000, 40000, 60000] : [10000, 15000, 20000, 30000, 40000, 60000, 90000];
}

let battlesCache = null;
export async function loadBattles() {
  if (battlesCache) return battlesCache;
  try {
    const response = await fetch(new URL('./battles.json', import.meta.url), {cache: 'no-cache'});
    const data = response.ok ? await response.json() : {};
    battlesCache = Array.isArray(data.battles) ? data.battles.filter(b => Array.isArray(b.members) && b.members.length >= 2) : [];
  } catch {
    battlesCache = [];
  }
  return battlesCache;
}

// Fuel prices for the comparison's cost block (owner decision 2026-10-06: fuel only). No price,
// no block.
let fuelCache = null;
export async function loadFuelPrices() {
  if (fuelCache) return fuelCache;
  try {
    const response = await fetch(new URL('./fuel-prices.json', import.meta.url), {cache: 'no-cache'});
    const data = response.ok ? await response.json() : {};
    const prices = Object.fromEntries(Object.entries(data.prices || {}).filter(([, v]) => Number(v) > 0).map(([k, v]) => [k, Number(v)]));
    fuelCache = {currency: data.currency || 'AZN', updated: data.updated || null, prices};
  } catch {
    fuelCache = {currency: 'AZN', updated: null, prices: {}};
  }
  return fuelCache;
}

// Monthly fuel cost of one car: EPA L/100 km x km per month x the price of its grade.
export function fuelCost({litresPer100, grade, monthlyKm, months, prices}) {
  const price = prices?.[grade];
  if (!(litresPer100 > 0) || !(price > 0) || !(monthlyKm > 0)) return null;
  const monthly = litresPer100 / 100 * monthlyKm * price;
  return {monthly, total: monthly * (months || 1), price, grade};
}

// What the user pasted into the one check field: VIN, a listing link, a plate or a make / model / year.
export function detectInput(value) {
  const text = String(value || '').trim();
  if (!text) return '';
  if (/^(https?:\/\/)?(www\.|ru\.|en\.)?turbo\.az\//i.test(text) || /^https?:\/\//i.test(text)) return 'LINK';
  const compact = text.replace(/[\s-]/g, '').toUpperCase();
  if (/^[A-HJ-NPR-Z0-9]{17}$/.test(compact)) return 'VIN';
  if (/^\d{2}\s?-?\s?[A-Z]{2}\s?-?\s?\d{3}$/i.test(text)) return 'PLATE';
  if (/\b(19|20)\d{2}\b/.test(text) && /[A-Za-zА-Яа-яƏəÖöÜüĞğİıŞşÇç]{2,}/.test(text)) return 'TEXT';
  return 'UNKNOWN';
}
