// The look of the design reference (visual-match prompt): the brand mark, the Baku skyline of the
// AZ home (a neutral city for US), official press photos of the cars and a neutral placeholder
// where a model has none. Colours come from tokens.css (design/tokens.json) through CSS classes.
import {icon} from './icons.js?v=0.14.0';
import {PHOTOS, HERO} from './photos.js?v=0.14.0';

export {icon};

const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const asset = file => new URL(`./photos/${file}`, import.meta.url).href;
const norm = text => String(text || '').toLowerCase().replace(/-class$/, '').replace(/[^a-z0-9]/g, '');

// the press photo of a model whose generation covers the year (photos/provenance*.json)
export function photoOf(make, model, year) {
  const mk = norm(make), md = norm(model), y = Number(year) || null;
  const same = PHOTOS.filter(p => norm(p.make) === mk && norm(p.model) === md);
  if (!same.length) return null;
  const fit = y ? same.find(p => y >= p.years[0] && y <= p.years[1]) : same[same.length - 1];
  return fit || null;
}

export function carPhoto(make, model, year, {alt = '', cls = ''} = {}) {
  const p = photoOf(make, model, year);
  if (p) return `<img class="ae-photo ${cls}" src="${esc(asset(p.file))}" alt="${esc(alt || `${make} ${model}`)}" loading="lazy" decoding="async">`;
  return placeholder(make, cls);
}

// the author and the licence of a photo (CC BY / CC BY-SA need them next to the photo or on a credits page)
export function photoCredit(make, model, year, language = 'ru') {
  const p = photoOf(make, model, year);
  if (!p || !p.author) return '';
  const word = {ru: 'Фото', az: 'Foto', en: 'Photo'}[language] || 'Фото';
  return `<a class="ae-photo-credit" href="${esc(p.source_page || '#/photo-credits')}" target="_blank" rel="noopener noreferrer">${esc(word)}: ${esc(p.author)} · ${esc(p.license || '')}</a>`;
}

export function allCredits() {
  return [...PHOTOS, ...(HERO.credits || [])];
}

// no photo: a quiet card-coloured block with the make, not a drawn car
export function placeholder(make = '', cls = '') {
  return `<div class="ae-photo ae-photo-empty ${cls}" aria-hidden="true">${icon('photo', 'ae-photo-empty-icon')}${make ? `<span>${esc(make)}</span>` : ''}</div>`;
}

export function heroCars() {
  return (HERO.buy || []).map((file, i) => `<img class="ae-hero-car ae-hero-car-${i + 1}" src="${esc(asset(file))}" alt="" aria-hidden="true" decoding="async">`).join('');
}

export function darkCar() {
  return HERO.dark ? `<img class="ae-check-car" src="${esc(asset(HERO.dark))}" alt="" aria-hidden="true" decoding="async">` : '';
}

export function brandMark() {
  return `<svg class="ae-brand-car" viewBox="0 0 64 28" aria-hidden="true"><path class="body" d="M3 19.5c0-2.6 1.5-4.2 4.3-4.9l8.6-2.1 7.5-5.6C25.6 5.3 28 4.5 30.8 4.5h9.6c2.6 0 4.9.9 6.8 2.6l5.6 5.1 5.4 1.2c2.3.5 3.8 2.5 3.8 4.9v2.6c0 1.2-.9 2.1-2.1 2.1h-3.1a6 6 0 0 0-11.7 0H20.4a6 6 0 0 0-11.7 0H5.1c-1.2 0-2.1-.9-2.1-2.1Z"/><path class="glass" d="M21 12.4 26.4 8.4c1.3-.9 2.7-1.4 4.3-1.4h5.8l1.2 5.4Zm18.6 0-1.2-5.4h1.9c1.7 0 3.2.6 4.4 1.7l3.9 3.7Z"/><circle class="wheel" cx="14.5" cy="22" r="4.2"/><circle class="wheel" cx="49.5" cy="22" r="4.2"/></svg>`;
}

// the right side of the home intro: Flame Towers, the handwritten line and the AZ flag (region AZ);
// a neutral city outline for US
export function skyline(region, language) {
  if (region !== 'AZ') {
    return `<svg class="ae-skyline ae-skyline-us" viewBox="0 0 200 150" aria-hidden="true">
      <rect class="t2" x="18" y="70" width="22" height="80" rx="2"/><rect class="t1" x="44" y="40" width="28" height="110" rx="2"/>
      <rect class="t2" x="76" y="62" width="20" height="88" rx="2"/><rect class="t1" x="100" y="22" width="30" height="128" rx="2"/>
      <rect class="t2" x="134" y="54" width="24" height="96" rx="2"/><rect class="t1" x="162" y="80" width="26" height="70" rx="2"/>
      <path class="lines" d="M48 52h20M48 64h20M48 76h20M104 36h22M104 50h22M104 64h22M104 78h22M138 66h16M138 80h16"/></svg>`;
  }
  const line = {ru: ['Лучшие', 'машины', 'для твоих дорог'], az: ['Yolların üçün', 'ən yaxşı', 'maşınlar'], en: ['The best cars', 'for your', 'roads']}[language] || ['Лучшие', 'машины', 'для твоих дорог'];
  return `<div class="ae-skyline-az" aria-hidden="true">
    <svg class="ae-skyline" viewBox="0 0 200 160">
      <defs>
        <linearGradient id="ae-tower-g" x1="0" x2="1" y1="0" y2="0"><stop offset="0" class="stop-b"/><stop offset=".45" class="stop-a"/><stop offset="1" class="stop-a"/></linearGradient>
        <pattern id="ae-floors" width="6" height="4.5" patternUnits="userSpaceOnUse"><path d="M0 4h6" class="floor"/></pattern>
      </defs>
      <path class="far" d="M0 160v-30h8v-10h9v14h7v-22h10v48Zm60 0v-26h7v-8h8v34Zm110 0v-34h10v-12h8v18h12v28Z"/>
      <path class="tower" d="M24 160V96c0-23 8-41 22-54 6-6 12-12 17-20-2 19-4 40-4 60v78Z"/>
      <path class="tower" d="M80 160V62c0-27 14-48 36-60-3 25-5 50-5 74v84Z"/>
      <path class="tower" d="M132 160V84c0-22 9-38 24-50 4-4 9-9 12-14-2 19-3 38-3 58v82Z"/>
      <path class="floors" d="M24 160V96c0-23 8-41 22-54 6-6 12-12 17-20-2 19-4 40-4 60v78ZM80 160V62c0-27 14-48 36-60-3 25-5 50-5 74v84ZM132 160V84c0-22 9-38 24-50 4-4 9-9 12-14-2 19-3 38-3 58v82Z"/>
      <path class="glint" d="M28 120c0-26 6-46 22-62M84 100c0-34 8-60 26-82M136 116c0-28 7-48 22-64"/>
      <path class="near" d="M0 160v-12h14v-8h12v20Zm44 0v-16h10v6h12v10Zm72 0v-14h14v-6h10v20Zm46 0v-18h12v8h10v-12h10v22Z"/>
      <path class="birds" d="M120 22l3 2.5 3-2.5M132 14l2.5 2 2.5-2M112 32l2.5 2 2.5-2M144 26l2 1.6 2-1.6"/>
    </svg>
    <p class="ae-script">${line.map(esc).join('<br>')}</p>
    <svg class="ae-flag" viewBox="0 0 30 18"><rect class="b" width="30" height="6"/><rect class="r" y="6" width="30" height="6"/><rect class="g" y="12" width="30" height="6"/><circle class="w" cx="14" cy="9" r="2.3"/><circle class="r2" cx="14.8" cy="9" r="1.9"/><path class="w" d="m17.6 7.8.3.9h.9l-.7.6.3.9-.8-.5-.8.5.3-.9-.7-.6h.9Z"/></svg>
  </div>`;
}
