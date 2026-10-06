import {EN, pickText} from './en-text.js?v=0.13.0';
import {mountOwnership} from './ownership-panel.js?v=0.13.0';
import {editorTools, bindEditorTools} from './editor-tools.js?v=0.13.0';
import {api, sessionUser, clearSession} from './api.js?v=0.13.0';
import {message} from './catalog-copy.js?v=0.9.4';
import {localizeConfiguration, localizeProfile, localizeTechnicalValue} from './catalog-display.js?v=0.9.1';
import {metricsOf, numberOf, specMetrics, verdict} from './compare-verdict.js?v=0.13.0';
import {budgetSteps, flag, fuelCost, loadBattles, loadFuelPrices, money, region, setRegion} from './ui-config.js?v=0.13.0';

// Screens by the owner's design reference (design/reference, data_work/ui/REFERENCE_MAP.md):
// home, selection in steps, matching cars, the car card with technical categories, the comparison
// with the Auto Expert verdict, the profile. Values come from the database only; empty fields are
// not shown, secondary data is marked.
export function createCatalogViews({root, state, layout, go, esc, ensureSession, showToast, usTech = null, garage = () => null, expert = () => null, club = () => null, subscription = () => null}) {
  const KEY = 'autoexpert.catalog.buyer.v1';
  const CONSUMER_CATALOG_SCOPE = 'US_BASE_2000';
  const LOCAL_ONLY = ['origin', 'budget_usd'];  // kept in the browser, never sent to the search
  const defaults = () => ({catalog_scope:CONSUMER_CATALOG_SCOPE, catalog_ready_only:true, year_min:2012, market_preference:'SELECTED', markets:['US'], body:[], engine:'ANY', transmission:'ANY', makes:[], models:[], roads:[], priorities:[], monthly_km:1000, ownership_months:24, city:'', charging:'UNKNOWN', sort:'recommended', initial_service_included:null, origin:null, budget_usd:null});
  let saved = {}; try {saved = JSON.parse(localStorage.getItem(KEY) || '{}');} catch {}
  let filters = {...defaults(), ...(saved.filters || {})};
  filters = {...filters, catalog_scope:CONSUMER_CATALOG_SCOPE, catalog_ready_only:true, market_preference:'SELECTED', markets:['US'], year_min:Math.max(2012,Number(filters.year_min)||2012), year_max:Number(filters.year_max)>=2012?Number(filters.year_max):null};
  const MAX = 2;  // two cars of one class (owner 2026-10-06)
  let basket = Array.isArray(saved.basket) ? saved.basket.slice(0,MAX) : [];
  let battleId = saved.battleId || null;
  let step = 1, facets = null, result = null, current = null, currentTech = null, compareData = null, topic = '', onlyFavorites = false, catalogPairs = null;
  const scenarios = saved.scenarios || {};
  const names = saved.names || {};
  let conditions = {city: 'Bakı', monthly_km: 1000, months: 24, ...(saved.conditions || {})};
  let largeText = !!saved.largeText;
  document.documentElement.classList.toggle('large-text', largeText);
  let viewRequest=0;
  const guardView=()=>{const n=++viewRequest,hash=location.hash,language=state.language;return ()=>n===viewRequest&&hash===location.hash&&language===state.language;};
  const l = key => message(state.language, key);
  const T = (ru, az, en) => pickText(state.language, ru, az, en);
  const isAZ = () => region(state) === 'AZ';
  const save = () => localStorage.setItem(KEY, JSON.stringify({filters,basket,scenarios,names,largeText,conditions,battleId}));
  const btn = (key, action, id='', cls='secondary') => `<button class="button ${cls}" data-k="${action}" data-id="${esc(id)}">${esc(l(key))}</button>`;
  const tbtn = (text, action, id='', cls='secondary') => `<button class="button ${cls}" data-k="${action}" data-id="${esc(id)}">${esc(text)}</button>`;
  const heading = (title, sub='') => `<div class="catalog-heading"><h1>${esc(l(title))}</h1>${sub ? `<p>${esc(l(sub))}</p>`:''}</div>`;
  const show = (html, active='') => {root.innerHTML = layout(`<div class="catalog-view">${html}</div>`, {active});};
  const box = html => `<section class="catalog-card">${html}</section>`;
  const note = key => `<p class="catalog-note">${esc(l(key))}</p>`;
  const top = (title, back, right='') => `<div class="page-top"><button class="icon-button" data-k="${back}" aria-label="${esc(l('back'))}">←</button><strong>${esc(title)}</strong>${right||'<span></span>'}</div>`;
  const carArt = (cls='') => `<div class="catalog-image-placeholder ${cls}" aria-hidden="true"><svg viewBox="0 0 120 64"><path d="m15 37 12-19h47l21 20 10 4v11H9V41Z"/><path d="m31 24-7 13h58L71 24Zm24 0v13"/><circle cx="29" cy="53" r="9"/><circle cx="86" cy="53" r="9"/></svg></div>`;
  const emptyImage = () => carArt();
  const attribution = v => (v.attribution?`<details class="catalog-note"><summary>${esc(l('source'))} · NRCan</summary><p>${esc(v.attribution)}</p><a href="https://open.canada.ca/en/open-government-licence-canada" target="_blank" rel="noopener noreferrer">Open Government Licence – Canada</a></details>`:'')+(v.asset?.attribution?`<p class="catalog-note">${esc(v.asset.attribution)}</p>`:'');
  const number = (name,key,value,attrs='') => `<label>${esc(l(key))}<input type="number" inputmode="decimal" name="${name}" value="${esc(value ?? '')}" ${attrs}></label>`;
  const select = (name,key,values,current,attrs='') => `<label>${esc(l(key))}<select name="${name}" ${attrs}>${values.map(([v,k])=>`<option value="${esc(v)}" ${String(current)===String(v)?'selected':''}>${esc(l(k))}</option>`).join('')}</select></label>`;
  const isOn = (field,value,multi) => multi ? (filters[field]||[]).includes(value) : filters[field]===value;
  const chip = (field,value,label,multi=false,icon='') => `<button type="button" class="filter-chip ${isOn(field,value,multi)?'selected':''}" data-k="chip" data-field="${field}" data-value="${value}" data-multi="${multi}" aria-pressed="${isOn(field,value,multi)}">${icon?`<span class="chip-icon" aria-hidden="true">${icon}</span>`:''}${esc(label)}</button>`;
  const chips = (title,field,values,multi=false) => `<fieldset class="filter-group"><legend>${esc(title)}</legend><div class="filter-chips">${values.map(([v,label,icon])=>chip(field,v,label,multi,icon)).join('')}</div></fieldset>`;
  const wait = () => show(`<p class="catalog-loading" role="status">${esc(l('loading'))}</p>`);
  const fail = e => {const key=Object.keys((e?.payload?.detail&&Array.isArray(e.payload.detail))?Object.fromEntries(e.payload.detail.map(d=>[String(d.msg).replace('Value error, ',''),true])):{[e?.message]:true}).find(k=>l(k)!==k);if(e?.loginRequired){go('/profile');return;}showToast(key?l(key):l('error'));};
  bindEditorTools(root,{refresh:()=>admin(),fail,l});
  const assetUrl = url => url ? (globalThis.AUTOEXPERT_API_ROOT||'/api/v1').replace(/\/api\/v1\/?$/,'')+url : '';
  const photo = (v, alt) => v?.asset?.url ? `<img src="${esc(assetUrl(v.asset.url))}" alt="${esc(alt)}" loading="lazy">` : carArt();
  async function loadFacets() {if (!facets) facets = await api(`/knowledge/facets?catalog_scope=${CONSUMER_CATALOG_SCOPE}`); return facets;}
  function searchBody(extra={}) {
    const body = {...filters, ...extra};
    for (const key of LOCAL_ONLY) delete body[key];
    if (!isAZ()) {delete body.budget_max_minor; delete body.budget_min_minor;}  // no US prices in the base
    return body;
  }
  function minor(v) {if(v==='' || v===null) return null; const s=String(v).replace(',','.'); if(!/^\d+(\.\d{1,2})?$/.test(s)) throw Error('BUDGET_RANGE'); const [a,b='']=s.split('.'); return Number(a)*100+Number(b.padEnd(2,'0'));}
  function readFilters(form) {
    const d = new FormData(form);
    for(const key of ['year_min','year_max','min_seats','min_clearance_mm','monthly_km','ownership_months']) if(d.has(key)) filters[key] = d.get(key)===''?null:Number(d.get(key));
    for(const key of ['budget_min_minor','budget_max_minor']) if(d.has(key)) filters[key] = minor(d.get(key));
    if(d.has('budget')){const v=d.get('budget');if(isAZ()){filters.budget_max_minor=v?Number(v)*100:null;}else{filters.budget_usd=v?Number(v):null;}}
    for(const key of ['city','charging','drivetrain','displacement_max_l','supply_channel']) if(d.has(key)) filters[key] = d.get(key) || (key==='city'?'':null);
    filters.year_min=Math.max(2012,Number(filters.year_min)||2012);
    if(filters.year_max!==null && filters.year_max<2012)filters.year_max=null;
    if(filters.monthly_km===null)filters.monthly_km=1000;
    if(filters.ownership_months===null)filters.ownership_months=24;
    if(d.has('initial_service_included')) filters.initial_service_included = d.get('initial_service_included')==='UNKNOWN'?null:d.get('initial_service_included')==='YES';
    if(form.querySelector('[name="large_boot"]')) filters.large_boot = d.has('large_boot');
    save();
  }

  // --- home ---------------------------------------------------------------------------------------
  async function home() {
    const valid=guardView();
    const ex = expert();
    const checkBody = ex?.enabled()
      ? `${ex.checkField('home-check-form')}<ul class="check-chips">${[T('Версия','Versiya','Version'),T('Слабые места','Zəif yerlər','Weak points'),T('Отзывы','Geri çağırmalar','Recalls'),T('ТО по пробегу','Yürüşə görə TXQ','Service'),T('Расхождения','Uyğunsuzluqlar','Discrepancies')].map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`
      : `${btn('checkCta','check','','primary')}<div class="check-foot">VIN${isAZ()?' · Turbo.az':''} · ${esc(T('Ручной ввод','Əllə daxil et','Manual input'))}</div>`;
    const clubCard = club()?.enabled?.() ? `<button class="home-club" data-action="club"><span class="home-club-icon" aria-hidden="true">👥</span><span><strong>${esc(club().navLabel())}</strong><small>${esc(T('Владельцы таких же машин делятся опытом','Eyni avtomobillərin sahibləri təcrübə bölüşür','Owners of the same cars share their experience'))}</small></span><span aria-hidden="true">›</span></button>` : '';
    show(`<section class="home-intro"><h1>${esc(l('slogan'))}</h1><p>${esc(l('sub'))}</p><span class="skyline" aria-hidden="true"></span></section>
      <section class="home-buy"><img class="home-buy-art" src="/preview/assets/buyer-road.svg" alt="" aria-hidden="true"><div><h2>${esc(l('buy'))}</h2><p>${esc(l('buySub'))}</p>${btn('start','wizard','','primary')}${flag('listingPaste')?`<button class="home-existing" data-k="check-listing">${esc(T('У меня уже есть варианты','Artıq seçimlərim var','I already have options'))} →</button>`:''}</div><div class="home-tags">${[T('Бюджет','Büdcə','Budget'),l('engine'),l('transmission'),l('body'),T('Рынок','Bazar','Market')].map(k=>`<span>${esc(k)}</span>`).join('')}</div></section>
      <section class="home-check"><span class="check-illustration" aria-hidden="true">VIN<span>▱ ▱ ▱</span></span><h2>${esc(l('check'))}</h2><p>${esc(isAZ()?T('VIN / госномер / объявление Turbo.az','VIN / dövlət nömrəsi / Turbo.az elanı','VIN / plate / Turbo.az listing'):T('VIN / госномер','VIN / dövlət nömrəsi','VIN / plate number'))}</p>${checkBody}</section>
      <section class="home-battles"><div class="section-title"><h2>${esc(l('battles'))}</h2><button class="text-button" data-k="battles">${esc(l('all'))} →</button></div><p>${esc(T('Популярные споры. Честный разбор по данным.','Populyar mübahisələr. Məlumatlara əsaslanan dürüst təhlil.','Popular debates, settled on the data.'))}</p><div id="home-publications" class="battle-strip"><p class="catalog-loading" role="status">${esc(l('loading'))}</p></div></section>${clubCard}`, 'home');
    const items = await loadBattles();
    if(!valid())return;
    const node = root.querySelector('#home-publications');
    if(!node)return;
    if(items.length){node.innerHTML=items.map(battleCard).join('');return;}
    if(flag('randomPairs')){const pairs=await loadCatalogPairs();if(!valid())return;node.innerHTML=pairs.map(catalogPairCard).join('');return;}
    node.innerHTML=box(`<h3>${esc(l('noEditorial'))}</h3>${btn('personalCompare','compare')}`);
  }
  function battleTitle(b) {return b.members.map(m=>m.model).join(' vs ');}
  function battleCard(b) {
    const years=[...new Set(b.members.map(m=>m.year))];
    const subtitle=(b.subtitle||{})[state.language]||(b.subtitle||{}).ru||'';
    return `<article class="battle-card curated"><div class="battle-visual" aria-hidden="true">${carArt('left')}<span class="battle-vs">VS</span>${carArt('right')}</div><h3>${esc(battleTitle(b))}</h3><p class="battle-years">${esc(b.members.map(m=>m.make).filter((x,i,a)=>a.indexOf(x)===i).join(' · '))} · ${esc(years.join('–'))}</p>${subtitle?`<p>${esc(subtitle)}</p>`:''}<button class="text-button" data-k="battle-compare" data-id="${esc(b.id)}">${esc(T('Сравнить','Müqayisə et','Compare'))} →</button></article>`;
  }
  async function resolveBattle(id) {
    const b=(await loadBattles()).find(x=>x.id===id); if(!b)return null;
    const found=[];
    for(const m of b.members){
      const data=await api(`/knowledge/search?language=${state.language}`,{method:'POST',body:JSON.stringify({...defaults(),origin:undefined,budget_usd:undefined,makes:[m.make],models:[m.model],year_min:m.year,year_max:m.year,limit:30,sort:'recommended'})});
      // the base version of the model: not a preview, gasoline without hybrid, the smallest engine
      const disp=v=>Number(v.facts?.engine_displacement?.value)||99;
      const plain=v=>v.facts?.fuel?.value==='GASOLINE'&&v.facts?.powertrain?.value==='ICE'?0:1;
      const hits=(data.matches||[]).slice().sort((a,b)=>(!!a.preview-!!b.preview)||(plain(a)-plain(b))||(disp(a)-disp(b)));
      const hit=hits[0];
      if(!hit)return {battle:b,missing:`${m.make} ${m.model} ${m.year}`};
      found.push(hit);names[hit.id]=`${hit.make} ${hit.model} · ${hit.year}`;
    }
    return {battle:b,ids:found.map(v=>v.id)};
  }

  // --- selection ----------------------------------------------------------------------------------
  function mode() {show(heading('chooseMode') + `<div class="mode-grid">${box(`<span class="mode-number">01</span><h2>${esc(l('helpPick'))}</h2><p>${esc(l('buySub'))}</p>${btn('start','wizard','','primary full')}`)}${box(`<span class="mode-number">02</span><h2>${esc(l('ownCars'))}</h2><p>${esc(l('ownSub'))}</p>${btn('catalog','browse','','secondary full')}`)}</div>`);}
  const hint = () => box(`<div class="help-box"><span aria-hidden="true">💡</span><div><strong>${esc(T('Не знаете точный тип? Это нормально','Dəqiq növü bilmirsiniz? Bu normaldır','Not sure of the exact type? That is fine'))}</strong><p>${esc(T('Auto Expert уточнит только то, что действительно влияет на результат.','Auto Expert yalnız nəticəyə həqiqətən təsir edəni dəqiqləşdirəcək.','Auto Expert will only ask about what really changes the result.'))}</p></div></div>`);
  async function wizard() {
    const valid=guardView();await loadFacets();if(!valid())return;
    show(`<div class="page-top"><button class="icon-button" data-k="${step===2?'step-back':'home'}" aria-label="${esc(l('back'))}">←</button><strong>${esc(l('wizard'))}</strong><button class="text-button" data-k="reset">${esc(l('reset'))}</button></div><ol class="wizard-progress">${['basics','conditions','results'].map((k,i)=>`<li class="${step===i+1?'active':step>i+1?'done':''}"><span>${i+1}</span>${esc(l(k))}</li>`).join('')}</ol>${step===1?heading('wizardTitle'):`<div class="catalog-heading"><h1>${esc(T('Как вы будете ездить?','Necə sürəcəksiniz?','How will you drive?'))}</h1><p>${esc(T('Можно выбрать «Не знаю» — подберём без этого.','«Bilmirəm» seçə bilərsiniz.','You can choose “Don’t know”.'))}</p></div>`}
      <form id="catalog-wizard">${step===1?basicFields():conditionFields()}<button class="button primary full" type="submit">${esc(step===1?T('Далее','Növbəti','Next'):T('Показать подходящие машины','Uyğun avtomobilləri göstər','Show matching cars'))} →</button>${step===1?`<button class="text-button full" type="submit" name="skip" value="1">${esc(T('Пропустить и показать машины','Keç və avtomobilləri göstər','Skip and show cars'))}</button>`:''}</form>${hint()}`);
  }
  function basicFields() {
    const latestYear=Math.max(new Date().getFullYear()+1,...facets.years);
    const years = Array.from({length:latestYear-2011},(_,i)=>String(latestYear-i));
    const budgetValue = isAZ() ? (filters.budget_max_minor!=null?filters.budget_max_minor/100:'') : (filters.budget_usd||'');
    const budgetOptions = [['',T('Любой','İstənilən','Any')],...budgetSteps(state).map(v=>[String(v),`${T('До','-dək','Up to')} ${money(v,state)}`])];
    const sel = (name,label,options,current) => `<label>${esc(label)}<select name="${name}">${options.map(([v,t])=>`<option value="${esc(v)}" ${String(current??'')===String(v)?'selected':''}>${esc(t)}</option>`).join('')}</select></label>`;
    const origins = [['KR',T('Корея','Koreya','Korea')],['US',T('США / Канада','ABŞ / Kanada','USA / Canada')],['EU',T('Европа','Avropa','Europe')],['CN',T('Китай','Çin','China')],['JP',T('Япония','Yaponiya','Japan')],['OFFICIAL',T('Официальный рынок','Rəsmi bazar','Official market')],['UNKNOWN',T('Не знаю','Bilmirəm',"Don't know")]];
    const originNote = isAZ() && filters.origin && !['US','UNKNOWN'].includes(filters.origin) ? `<p class="catalog-note">${esc(T('В нашей базе пока версии для рынка США. Покажем их с пометкой «уточнить рынок».','Bazamızda hələ ABŞ bazarı versiyaları var. Onları «bazarı dəqiqləşdirin» qeydi ilə göstərəcəyik.','Our database holds US-market versions for now; they are shown marked “confirm the market”.'))}</p>` : '';
    return `<div class="form-pair">${sel('budget',T('Бюджет','Büdcə','Budget'),budgetOptions,budgetValue)}<fieldset class="year-pair"><legend>${esc(T('Год выпуска','Buraxılış ili','Model year'))}</legend><div class="form-pair">${sel('year_min',T('от','-dan','from'),years.map(y=>[y,y]),filters.year_min)}${sel('year_max',T('до','-dək','to'),[['',T('любой','istənilən','any')],...years.map(y=>[y,y])],filters.year_max||'')}</div></fieldset></div>
      ${isAZ()?chips(T('Рынок происхождения','Mənşə bazarı','Origin market'),'origin',origins):''}${originNote}
      ${chips(T('Тип кузова','Kuzov növü','Body type'),'body',[['SEDAN',T('Седан','Sedan','Sedan'),'🚘'],['CROSSOVER',T('Кроссовер','Krossover','Crossover'),'🚙'],['HATCHBACK',T('Хэтчбек','Hetçbek','Hatchback')],['WAGON',T('Универсал','Universal','Wagon')],['COUPE',T('Купе','Kupe','Coupe')],['MINIVAN',T('Минивэн','Miniven','Minivan')],['SUV','SUV'],['PICKUP',T('Пикап','Pikap','Pickup')]],true)}
      ${chips(T('Тип двигателя','Mühərrik növü','Engine type'),'engine',[['GASOLINE_NA',T('Бензин (без турбины)','Benzin (turbinsiz)','Gasoline (no turbo)')],['GASOLINE_TURBO',T('Бензин турбо','Benzin turbo','Turbo gasoline')],['DIESEL',T('Дизель','Dizel','Diesel')],['HEV',T('Гибрид','Hibrid','Hybrid')],['PHEV',T('PHEV (плагин-гибрид)','PHEV (plug-in hibrid)','PHEV (plug-in hybrid)')],['BEV',T('Электро','Elektro','Electric')],['UNKNOWN',T('Не знаю','Bilmirəm',"Don't know")],['ANY',T('Не важно','Fərq etmir','Any')]])}
      ${chips(T('Коробка передач','Sürətlər qutusu','Gearbox'),'transmission',[['AT',T('Обычный автомат (AT)','Adi avtomat (AT)','Conventional automatic (AT)')],['CVT',T('Вариатор (CVT)','Variator (CVT)','CVT')],['DCT',T('Робот (DCT / DSG)','Robot (DCT / DSG)','Dual-clutch (DCT)')],['MANUAL',T('Механика','Mexaniki','Manual')],['UNKNOWN',T('Не знаю','Bilmirəm',"Don't know")],['ANY',T('Не важно','Fərq etmir','Any')]])}
      <details class="filter-optional"><summary>${esc(T('Марка, модель, привод и другое','Marka, model, ötürücü və s.','Make, model, drive and more'))}</summary><label>${esc(l('make'))}<input id="make-query" list="make-list" placeholder="${esc(l('search'))}"><datalist id="make-list">${facets.makes.map(m=>`<option value="${esc(m.name)}">`).join('')}</datalist></label><button type="button" class="text-button" data-k="add-make">＋ ${esc(l('make'))}</button><div class="filter-chips">${filters.makes.map(m=>chip('makes',m,m,true)).join('')}</div><label>${esc(l('model'))}<input id="model-query" list="model-list"><datalist id="model-list">${facets.makes.filter(m=>!filters.makes.length||filters.makes.includes(m.name)).flatMap(m=>m.models).map(m=>`<option value="${esc(m)}">`).join('')}</datalist></label><button type="button" class="text-button" data-k="add-model">＋ ${esc(l('model'))}</button><div class="filter-chips">${filters.models.map(m=>chip('models',m,m,true)).join('')}</div>${select('drivetrain','drive',[['','any'],...['FWD','RWD','AWD','4WD'].map(k=>[k,k])],filters.drivetrain||'')}<div class="form-pair">${number('min_seats','seats',filters.min_seats,'min="1" max="30"')}${number('min_clearance_mm','clearance',filters.min_clearance_mm,'min="0" max="600"')}${number('displacement_max_l','displacement',filters.displacement_max_l,'min="0" max="12" step="0.1"')}</div><label class="check-label"><input type="checkbox" name="large_boot" ${filters.large_boot?'checked':''}>${esc(l('boot'))}</label>${flag('serviceLabels')?select('initial_service_included','initialService',[['UNKNOWN','unknown'],['YES','yes'],['NO','no']],filters.initial_service_included===null?'UNKNOWN':filters.initial_service_included?'YES':'NO'):''}</details>`;
  }
  function conditionFields() {
    const purposes=[['urban',T('Город','Şəhər','City'),'🏙'],['highway',T('Трасса','Yol','Highway'),'🛣'],['rough',T('Плохие дороги','Pis yollar','Rough roads'),'⛰']];
    const purposeChips=purposes.map(([v,label,icon])=>chip('roads',v,label,true,icon)).join('')+`<button type="button" class="filter-chip ${filters.family_use?'selected':''}" data-k="family" aria-pressed="${!!filters.family_use}"><span class="chip-icon" aria-hidden="true">👨‍👩‍👧</span>${esc(T('Семья','Ailə','Family'))}</button><button type="button" class="filter-chip ${!filters.roads.length&&!filters.family_use?'selected':''}" data-k="purpose-unknown">${esc(T('Не знаю','Bilmirəm',"Don't know"))}</button>`;
    const priorities=[['reliability',T('Надёжность','Etibarlılıq','Reliability')],['cost',T('Расходы','Xərclər','Running costs')],['comfort',T('Комфорт','Komfort','Comfort')],['space',T('Простор','Genişlik','Space')],['safety',T('Безопасность','Təhlükəsizlik','Safety')],['performance',T('Динамика','Dinamika','Performance')],['resale',T('Перепродажа','Təkrar satış','Resale')]];
    return `<fieldset class="filter-group"><legend>${esc(T('Для чего нужна машина?','Avtomobil nə üçündür?','What is the car for?'))}</legend><div class="filter-chips">${purposeChips}</div></fieldset>
      ${chips(T('Что для вас важнее (до трёх)','Sizin üçün nə vacibdir (üçə qədər)','What matters most (up to three)'),'priorities',priorities,true)}
      <label>${esc(T('Город эксплуатации','İstismar şəhəri','City'))}<input name="city" value="${esc(filters.city||'')}" placeholder="${esc(isAZ()?'Bakı':'')}"></label>
      <details class="filter-optional"><summary>${esc(T('Изменить условия: пробег и срок','Şərtləri dəyiş: yürüş və müddət','Change conditions: mileage and period'))} · ${esc(String(filters.monthly_km||1000))} ${esc(T('км/мес','km/ay','km/mo'))} · ${esc(String(filters.ownership_months||24))} ${esc(T('мес','ay','mo'))}</summary><div class="form-pair">${number('monthly_km','km',filters.monthly_km,'min="0" max="30000"')}${number('ownership_months','months',filters.ownership_months,'min="1" max="120"')}</div>${select('charging','charging',[['UNKNOWN','unknown'],['YES','yes'],['NO','no']],filters.charging)}</details>`;
  }

  // --- matching cars ------------------------------------------------------------------------------
  function profileText() {
    const budget = isAZ() ? (filters.budget_max_minor!=null?`${T('до','-dək','up to')} ${money(filters.budget_max_minor/100,state)}`:'') : (filters.budget_usd?`${T('до','-dək','up to')} ${money(filters.budget_usd,state)}`:'');
    const engines = {GASOLINE_NA:T('бензин (без турбины)','benzin (turbinsiz)','gasoline (no turbo)'),GASOLINE_TURBO:T('бензин турбо','benzin turbo','turbo gasoline'),GASOLINE:T('бензин','benzin','gasoline'),DIESEL:T('дизель','dizel','diesel'),HEV:T('гибрид','hibrid','hybrid'),PHEV:'PHEV',BEV:T('электро','elektro','electric')};
    const boxes = {AT:T('автомат','avtomat','automatic'),CVT:T('вариатор','variator','CVT'),DCT:T('робот','robot','dual-clutch'),MANUAL:T('механика','mexaniki','manual')};
    return [budget, `${filters.year_min}${filters.year_max?(filters.year_max===filters.year_min?'':`–${filters.year_max}`):'+'}`, ...filters.makes, ...filters.models, ...filters.body.map(l).map(x=>String(x).toLowerCase()), engines[filters.engine], boxes[filters.transmission], filters.city].filter(Boolean).join(' · ');
  }
  async function results() {
    const valid=guardView();wait(); result=await api(`/knowledge/search?language=${state.language}`,{method:'POST',body:JSON.stringify(searchBody())});if(!valid())return;
    const list = result.recommendation?.top ? [result.recommendation.top, ...result.recommendation.competitors] : [];
    const usBudget = !isAZ() && filters.budget_usd ? `<p class="catalog-note">${esc(T('Цен рынка США в базе пока нет — бюджет в $ не сужает список.','ABŞ bazarının qiymətləri hələ bazada yoxdur — $ büdcə siyahını daraltmır.','US market prices are not in our database yet — the $ budget does not narrow the list.'))}</p>` : '';
    show(top(T('Подходящие варианты','Uyğun variantlar','Matching cars'),'wizard') + `<section class="catalog-card profile-summary"><span class="profile-dot" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="12" cy="9" r="4"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/></svg></span><div><strong>${esc(T('Ваш профиль','Profiliniz','Your profile'))}</strong><p>${esc(profileText())}</p></div><button class="text-button" data-k="wizard">${esc(l('change'))}</button></section>${usBudget}
      <div class="result-head"><strong>${esc(T(`Мы нашли ${result.matched_models} подходящих моделей`,`${result.matched_models} uyğun model tapdıq`,`We found ${result.matched_models} matching models`))}</strong>${select('sort','sort',['recommended','year_desc','make','consumption'].map(k=>[k,k]),filters.sort,'id="catalog-sort"')}</div>
      ${list.length?list.map(modelCard).join(''):box(`<h2>${esc(l('noMatches'))}</h2>${btn('change','wizard')}`)}
      ${(result.needs_confirmation||[]).length?`<section class="catalog-card ae-warn-card"><h2>${esc(T('Нужно уточнить','Dəqiqləşdirmək lazımdır','Needs confirming'))}</h2><p>${esc(T('Эти версии подходят не по всем условиям — уточните рынок, коробку или двигатель.','Bu versiyalar bütün şərtlərə uyğun deyil — bazarı, qutunu və ya mühərriki dəqiqləşdirin.','These versions do not meet every condition — confirm the market, gearbox or engine.'))}</p><button class="button secondary" data-k="wizard">${esc(T('Уточнить','Dəqiqləşdir','Refine'))}</button></section>${result.needs_confirmation.slice(0,5).map(modelCard).join('')}`:''}
      ${(result.recommendation?.competitor_models||0)>(filters.offset||0)+20?btn('more','more','','secondary full'):''}<div class="catalog-sticky"><button class="button primary full" data-k="compare">📊 ${esc(T('Сравнить выбранные машины','Seçilmiş avtomobilləri müqayisə et','Compare the chosen cars'))} (<span data-basket-count>${basket.length}</span>)</button></div>`, 'compare');
  }
  function factValue(f,k) {return f?.[k]?.status==='CONFIRMED' && ![null,undefined,'','UNKNOWN'].includes(f[k].value) ? f[k].value : null;}
  function factText(f,k) {const v=factValue(f,k);if(v===null)return '';const context=Object.fromEntries(Object.entries(f||{}).map(([n,x])=>[n,x?.value]));return `${localizeTechnicalValue(k,v,state.language,context)||v}${f[k].unit&&k!=='engine_displacement'?' '+f[k].unit:''}`;}
  function specLine(v) {
    const f=v.facts||{};
    const disp=factValue(f,'engine_displacement');
    return [v.year, disp?Number(disp).toFixed(1):null, factText(f,'fuel'), factText(f,'transmission_family')].filter(Boolean).join(' · ');
  }
  function badgeOf(v) {
    const unsure=[];
    if(isAZ()&&filters.origin&&!['US','UNKNOWN'].includes(filters.origin))unsure.push(T('рынок','bazar','market'));
    if((v.missing||[]).some(k=>/transmission/.test(k))||filters.transmission==='UNKNOWN')unsure.push(T('коробку','qutu','gearbox'));
    if((v.missing||[]).some(k=>/powertrain|aspiration|displacement|engine/.test(k))||filters.engine==='UNKNOWN')unsure.push(T('двигатель','mühərrik','engine'));
    if(v.match==='MATCH'&&!unsure.length&&(v.source_confirmed_core||v.us_catalog_ready))return `<span class="ae-badge ok">${esc(T('Модификация подтверждена','Modifikasiya təsdiqlənib','Version confirmed'))}</span>`;
    return `<span class="ae-badge warn">${esc(T('Нужно уточнить','Dəqiqləşdirin','Confirm'))} ${esc(unsure.join(' / ')||T('версию','versiya','the version'))}</span>`;
  }
  function modelCard(v) {
    names[v.id]=v.make+' '+v.model+' · '+v.year;
    const f=v.facts||{};
    const disp=factValue(f,'engine_displacement');
    const icons=[[`🌐`,v.market==='US'?T('США','ABŞ','USA'):v.market],[`◎`,disp?`${Number(disp).toFixed(1)} ${factValue(f,'aspiration')==='TURBOCHARGED'?T('турбо','turbo','turbo'):T('атмосф.','atmosfer','NA')}`:''],[`⇄`,factText(f,'transmission_family')],[`⚙︎`,factText(f,'drivetrain')]].filter(([,t])=>t);
    const reasons=[...(v.ranking?.reasons||[]).slice(0,1),...(v.tradeoffs||[]).map(k=>l(k))].filter(Boolean);
    const inBasket=basket.includes(v.id);
    return `<article class="model-card"><button class="model-card-main" data-k="vehicle" data-id="${esc(v.id)}"><div class="model-photo">${photo(v,v.make+' '+v.model)}</div><div class="model-info"><h2>${esc(v.make)} ${esc(v.model)}</h2><p>${esc(specLine(v))}</p>${badgeOf(v)}${flag('serviceLabels')&&v.preview?`<span class="match-badge preview-badge">${esc(l('previewBadge'))}</span>`:''}</div></button>
      ${icons.length?`<ul class="model-icons">${icons.map(([i,t])=>`<li><span aria-hidden="true">${i}</span>${esc(t)}</li>`).join('')}</ul>`:''}
      <div class="model-foot">${reasons.length?`<p>${esc(reasons.join(' · '))}</p>`:'<p></p>'}<div class="model-actions">${v.preview?'':`<button class="compare-toggle ${inBasket?'selected':''}" data-k="basket" data-id="${esc(v.id)}" aria-pressed="${inBasket}">${esc(inBasket?T('✓ В сравнении','✓ Müqayisədə','✓ In comparison'):T('＋ Сравнить','＋ Müqayisə','＋ Compare'))}</button>`}<button class="model-arrow" data-k="vehicle" data-id="${esc(v.id)}" aria-label="${esc(l('open'))}">›</button></div></div></article>`;
  }
  const vehicleCard = modelCard;
  function missingLabel(k){return ({body_subtype:l('body'),budget:l('budgetMissing'),initial_service_budget:l('initialService'),transmission_construction:l('transmission'),powertrain:l('engine'),aspiration:l('engine'),ground_clearance:l('clearance'),cargo_l:l('boot'),displacement:l('displacement'),supply_channel:l('supply'),year_min:l('year'),year_max:l('year')})[k]||l(k);}

  // --- the car card -------------------------------------------------------------------------------
  const CATEGORY_ICONS={engine:'⚙',transmission:'⇄',fuel:'⛽',induction:'◎',fluids:'💧',body:'🚗',dimensions:'🚗',chassis:'◉',suspension:'◉',brakes:'◉',wheels:'◌',interior:'💺',equipment:'⚡'};
  // one shape for both sources: the US technical base (values with marks) and the catalogue profile
  function techCategories() {
    if(currentTech?.categories?.length)return currentTech.categories.map(c=>({key:c.key,title:c.title,rows:c.rows.map(r=>({key:r.key,label:r.label,values:r.values,kind:r.kind}))}));
    const profile=localizeProfile(current.profile,state.language);
    return profile.technical.filter(g=>g.rows.length).map(g=>({key:g.key,title:g.title,rows:g.rows.map(r=>({key:r.key,label:r.label,kind:r.kind,values:[{value:r.value,reason:r.reason,source:r.source_url?{url:r.source_url}:null}]}))}));
  }
  function valueHtml(v) {
    const labels=currentTech?.labels||{};
    return `${v.qualifier?`<span class="us-tech-qualifier">${esc(v.qualifier)}</span> `:''}<span class="us-tech-value">${esc(v.value)}</span>${v.secondary?`<small class="us-tech-badge secondary">${esc(labels.secondary||T('по данным справочников','məlumat kitabçalarına görə','per reference books'))}</small>`:''}${v.approximate?`<small class="us-tech-badge approximate">${esc(labels.approximate||T('ориентировочно','təxmini','approximate'))}</small>`:''}${v.reason?`<small class="fuel-reason">${esc(v.reason)}</small>`:''}`;
  }
  const rowsHtml = rows => `<dl class="ae-rows">${rows.filter(r=>r.values?.length).map(r=>`<div${r.kind?` class="fuel-line fuel-${esc(r.kind)}"`:''}><dt>${esc(r.label)}</dt><dd>${r.values.length===1?valueHtml(r.values[0]):`<ul class="us-tech-values">${r.values.map(v=>`<li>${valueHtml(v)}</li>`).join('')}</ul>`}</dd></div>`).join('')}</dl>`;
  function maintenanceFor(prefix) {return (currentTech?.maintenance||[]).filter(m=>!m.severe&&m.job_key&&m.job_key.startsWith(prefix));}
  function carTitle() {return `${current.make} ${current.model}`;}
  function carSub() {return [current.year, current.market==='US'?T('США','ABŞ','USA'):current.market].filter(Boolean).join(' • ');}
  async function loadVehicle(id, valid) {
    if(current?.id!==id||current?._language!==state.language){
      const [data,tech]=await Promise.all([api(`/knowledge/vehicles/${encodeURIComponent(id)}?language=${state.language}`),usTech?.enabled()?api(`/catalog/variants/${encodeURIComponent(id)}/us-tech?language=${state.language==='az'?'az':state.language==='en'?'en':'ru'}`).catch(()=>null):Promise.resolve(null)]);
      if(!valid())return false;
      current={...data,_language:state.language};currentTech=tech;
    }
    return true;
  }
  async function vehicle(id, sub) {
    const valid=guardView();wait();
    if(!await loadVehicle(id,valid))return;
    if(sub){techCategory(id,sub);return;}
    const f=current.facts||{};
    const profile=localizeProfile(current.profile,state.language);
    const chipsList=[['body',factText(f,'body')||(currentTech?.categories||[]).flatMap(c=>c.rows).find(r=>r.key==='body')?.values?.[0]?.value],['seats',factValue(f,'seats')?`${factValue(f,'seats')} ${T('мест','yer','seats')}`:''],['fuel',factText(f,'fuel')],['disp',factValue(f,'engine_displacement')?Number(factValue(f,'engine_displacement')).toFixed(1):''],['box',factValue(f,'transmission_family')],['drive',factValue(f,'drivetrain')]].filter(([,t])=>t);
    const fuelRec=profile.summary.find(r=>r.key==='fuel_recommendation');
    const shortRows=[[T('Рынок','Bazar','Market'),current.market==='US'?T('США','ABŞ','USA'):current.market],[T('Поколение','Nəsil','Generation'),currentTech?.generation||current.generation_code||current.generation],[T('Топливо','Yanacaq','Fuel'),fuelRec?.value]].filter(([,v])=>v);
    const cats=techCategories();
    const weak=currentTech?.weak_points||[], recalls=currentTech?.campaigns||[];
    const entries=key=>(profile.categories.find(c=>c.key===key)?.entries||[]);
    const checklist=[...weak.filter(w=>w.how_to_check).map(w=>`${w.title}: ${w.how_to_check}`),...recalls.map(c=>T(`Проверить по VIN, выполнена ли кампания ${c.number}${c.component?` (${c.component})`:''}`,`VIN üzrə ${c.number} kampaniyasının icrasını yoxlayın`,`Check by VIN that recall ${c.number} was done`)),...entries('inspection').map(e=>e.text)];
    const tabs=[
      ['technical',T('Техническая часть','Texniki hissə','Technical'),cats.length?`<ul class="tech-list">${cats.map(c=>`<li><button data-k="tech-cat" data-id="${esc(id)}" data-cat="${esc(c.key)}"><span class="tech-icon" aria-hidden="true">${CATEGORY_ICONS[c.key]||'•'}</span><span><strong>${esc(c.title)}</strong><small>${esc(c.rows.slice(0,3).map(r=>r.label).join(', '))}</small></span><span aria-hidden="true">›</span></button></li>`).join('')}</ul>`:`<p>${esc(categoryEmpty('technical'))}</p>`],
      ['weak_points',T('Слабые места','Zəif yerlər','Weak points'),weak.length?weak.map(w=>`<article class="catalog-card us-tech-issue ${w.owner_reports?'owner-reports':''}"><h3>${esc(w.title)}${w.note?` <small class="us-tech-badge secondary">${esc(w.note)}</small>`:''}</h3><p class="catalog-note">${esc([w.severity,w.probability].filter(Boolean).join(' · '))}</p>${w.symptoms?.length?`<p>${esc(w.symptoms.join('; '))}</p>`:''}${w.how_to_check?`<p class="us-tech-label">${esc(T('Как проверить','Necə yoxlamalı','How to check'))}</p><p>${esc(w.how_to_check)}</p>`:''}</article>`).join(''):(entries('weak_points').map(e=>`<p>${esc(e.text)}</p>`).join('')||`<p>${esc(categoryEmpty('weak_points'))}</p>`)],
      ['campaigns',T('Сервисные кампании','Servis kampaniyaları','Recalls'),recalls.length?recalls.map(c=>`<article class="catalog-card us-tech-campaign"><h3>${esc(c.number)}${c.component?` · ${esc(c.component)}`:''}</h3>${c.summary?`<p>${esc(c.summary)}</p>`:''}<p class="us-tech-note">${esc(c.note||'')}</p></article>`).join(''):(entries('campaigns').map(e=>`<p>${esc(e.text)}</p>`).join('')||`<p>${esc(categoryEmpty('campaigns'))}</p>`)],
      ['inspection',T('Что проверить','Nəyi yoxlamalı','What to check'),`${checklist.length?`<ol class="ae-checklist-list">${checklist.map(x=>`<li>${esc(x)}</li>`).join('')}</ol>`:''}<p class="catalog-note">${esc(categoryEmpty('inspection'))}</p>`],
    ];
    const garageOn=garage()?.enabled?.()&&currentTech?.configuration_key;
    show(`${top(`${carTitle()} ${current.year}`,'results',current.preview?'':`<button class="icon-button ${basket.includes(id)?'selected':''}" data-k="basket" data-id="${esc(id)}" aria-pressed="${basket.includes(id)}" aria-label="${esc(l('addCompare'))}">${basket.includes(id)?'✓':'＋'}</button>`)}${flag('serviceLabels')&&current.preview?`<p class="catalog-notice preview-notice">${esc(l('previewNote'))}</p>`:''}
      <section class="car-hero">${photo(current,carTitle())}<div class="car-hero-text"><h1>${esc(carTitle())}</h1><p>${esc(carSub())}</p></div></section>
      ${chipsList.length?`<ul class="car-chips">${chipsList.map(([,t])=>`<li>${esc(t)}</li>`).join('')}</ul>`:''}
      ${shortRows.length?`<section class="catalog-card car-short"><dl class="ae-rows">${shortRows.map(([k,v])=>`<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl></section>`:''}
      <nav class="profile-categories car-tabs" role="tablist" aria-label="${esc(l('vehicleCategories'))}">${tabs.map(([key,title],i)=>`<button type="button" role="tab" id="tab-${key}" aria-controls="panel-${key}" aria-selected="${i===0}" tabindex="${i===0?0:-1}" class="profile-category category-${key}" data-profile-tab="${key}">${esc(title)}</button>`).join('')}</nav>
      ${tabs.map(([key,,html],i)=>`<section id="panel-${key}" role="tabpanel" aria-labelledby="tab-${key}" ${i?'hidden':''} class="profile-panel">${html}</section>`).join('')}
      <div class="catalog-actions">${garageOn?tbtn(T('Добавить в мой гараж','Qarajıma əlavə et','Add to my garage'),'garage-add',id,'primary full'):''}${current.preview?'':tbtn(basket.includes(id)?T('✓ В сравнении','✓ Müqayisədə','✓ In comparison'):T('Добавить к сравнению','Müqayisəyə əlavə et','Add to comparison'),'basket',id,'secondary full')}${tbtn(T('Проверить конкретную машину','Konkret avtomobili yoxla','Check a specific car'),'check',id,'secondary full')}${current.preview?'':btn('save','save',id,'secondary full')}</div>
      <details class="catalog-card"><summary>${esc(l('sources'))}</summary><p><a href="${esc(current.source_url)}" target="_blank" rel="noopener noreferrer">${esc(l('source'))} ↗</a></p><p>${esc(current.published_at?.slice(0,10)||'')}</p>${attribution(current)}</details>`);
  }
  function techCategory(id, key) {
    const cats=techCategories();
    const cat=cats.find(c=>c.key===key);
    if(!cat){go('/catalog-car/'+id);return;}
    const back=`${carTitle()} ${current.year} • ${current.market==='US'?T('США','ABŞ','USA'):current.market}`;
    const footnote=`<section class="catalog-card ae-info"><span aria-hidden="true">ℹ</span><div><strong>${esc(T('Все данные относятся к выбранной версии автомобиля.','Bütün məlumatlar seçilmiş avtomobil versiyasına aiddir.','All data refer to the chosen version of the car.'))}</strong><p>${esc(T('Могут отличаться в зависимости от рынка, комплектации и года выпуска.','Bazar, komplektasiya və ilə görə fərqlənə bilər.','They may differ by market, trim and model year.'))}</p></div></section>`;
    if(key!=='fluids'){
      show(`<div class="page-top"><button class="icon-button" data-k="vehicle" data-id="${esc(id)}" aria-label="${esc(l('back'))}">←</button><strong>${esc(back)}</strong><span></span></div><h1 class="tech-title">${esc(cat.title)}</h1><section class="catalog-card">${rowsHtml(cat.rows)}</section>${key==='fuel'?`<p class="catalog-note">${esc(T('Октан производителя (AKI, шкала США) пересчитан в АИ по таблице Auto Expert. Рекомендация Auto Expert — не требование производителя.','İstehsalçının oktanı (AKI, ABŞ şkalası) Auto Expert cədvəli ilə AI-yə çevrilib. Auto Expert tövsiyəsi istehsalçının tələbi deyil.','The maker’s octane (AKI, US scale) is converted to RON by the Auto Expert table. The Auto Expert recommendation is not a maker’s requirement.'))}</p>`:''}${footnote}`);
      return;
    }
    // "Двигатель → Масла и жидкости" (reference 02, right screen)
    const all=Object.fromEntries(cats.flatMap(c=>c.rows).map(r=>[r.key,r]));
    const pick=(keys,labels={})=>keys.map(k=>all[k]&&{...all[k],label:labels[k]||all[k].label}).filter(Boolean);
    const interval=(prefix,label)=>{const items=maintenanceFor(prefix);return items.length?[{key:prefix,label,values:items.slice(0,2).map(m=>({value:[m.action,m.interval].filter(Boolean).join(' · '),secondary:m.secondary,approximate:m.approximate}))}]:[];};
    const engineName=factText(current.facts,'engine_description')||null;
    const engineRows=[...(engineName?[{key:'engine_name',label:T('Двигатель','Mühərrik','Engine'),values:[{value:engineName}]}]:[]),...pick(['engine_displacement_l','aspiration']),...pick(['engine_oil_viscosity','engine_oil_specification','engine_oil_capacity_l','engine_oil_alternatives'],{engine_oil_viscosity:T('Моторное масло','Mühərrik yağı','Engine oil'),engine_oil_specification:T('Допуск','Spesifikasiya','Specification'),engine_oil_capacity_l:T('Объём с фильтром','Filtrlə həcm','Capacity with filter'),engine_oil_alternatives:T('Допустимая альтернатива','İcazə verilən alternativ','Allowed alternative')}),...interval('engine_oil',T('Интервал','İnterval','Interval'))];
    const boxRows=[...pick(['transmission_description'],{transmission_description:T('Тип','Növ','Type')}),...pick(['transmission_fluid','transmission_fluid_capacity_l'],{transmission_fluid:T('Жидкость','Maye','Fluid'),transmission_fluid_capacity_l:T('Объём','Həcm','Capacity')}),...interval('transmission_fluid',T('Регламент','Reqlament','Schedule')),...interval('cvt_fluid',T('Регламент','Reqlament','Schedule')),...interval('dct_fluid',T('Регламент','Reqlament','Schedule'))];
    const otherRows=pick(['coolant','coolant_capacity_l','brake_fluid','spark_plug','transfer_fluid','front_differential_fluid','rear_differential_fluid']);
    const block=(icon,title,rows)=>rows.length?`<section class="catalog-card fluid-block"><h2><span aria-hidden="true">${icon}</span>${esc(title)}</h2>${rowsHtml(rows)}</section>`:'';
    show(`<div class="page-top"><button class="icon-button" data-k="vehicle" data-id="${esc(id)}" aria-label="${esc(l('back'))}">←</button><strong>${esc(back)}</strong><span></span></div><h1 class="tech-title">${esc(T('Двигатель','Mühərrik','Engine'))} → ${esc(cat.title)}</h1>${block('⚙',T('Двигатель','Mühərrik','Engine'),engineRows)}${block('⇄',T('Коробка передач','Sürətlər qutusu','Gearbox'),boxRows)}${block('💧',T('Другие жидкости','Digər mayelər','Other fluids'),otherRows)}${footnote}`);
  }
  function categoryEmpty(key) {
    if(key==='weak_points')return T('Подтверждённых слабых мест для этой версии в базе нет. Перед покупкой проверьте диагностику и сервисную историю.','Bu versiya üçün təsdiqlənmiş zəif yer yoxdur. Almazdan əvvəl diaqnostikanı və servis tarixçəsini yoxlayın.','No confirmed weak points for this version. Before buying, check the diagnostics and the service history.');
    if(key==='campaigns')return T('Отзывных кампаний для этой версии в базе нет. Применимость к конкретной машине проверяется по VIN.','Bu versiya üçün geri çağırma kampaniyası yoxdur. Konkret avtomobilə aidiyyəti VIN üzrə yoxlanılır.','No recalls for this version in our database. Whether one applies to a car is checked by VIN.');
    if(key==='technical')return T('Технических данных для этой версии пока нет.','Bu versiya üçün texniki məlumat hələ yoxdur.','No technical data for this version yet.');
    return T('Всегда: VIN и документы, кузов, холодный запуск и сервисная история.','Həmişə: VIN və sənədlər, kuzov, soyuq işəsalma və servis tarixçəsi.','Always: the VIN and papers, the body, a cold start and the service history.');
  }

  // --- the comparison -----------------------------------------------------------------------------
  async function compare() {
    const valid=guardView();
    if(basket.length<2) {show(top(T('Сравнение','Müqayisə','Comparison'),'home')+`<div class="catalog-heading"><h1>${esc(T('Выберите две машины','İki avtomobil seçin','Choose two cars'))}</h1><p>${esc(T('Добавьте машины из подбора или выберите готовое сравнение.','Seçimdən avtomobil əlavə edin və ya hazır müqayisə seçin.','Add cars from the selection or pick a ready comparison.'))}</p></div>`+basket.map(id=>box(`<p>${esc(names[id]||l('selected'))}</p>${btn('remove','remove',id)}`)).join('')+tbtn(T('Подобрать машины','Avtomobil seç','Find cars'),'wizard','','primary full')+tbtn(l('battles'),'battles','','secondary full')+btn('savedCompare','saved-compare','','secondary full'),'compare');return;}
    wait();
    const techLanguage=state.language==='az'?'az':state.language==='en'?'en':'ru';
    const [data,fuel,battleList,...techs]=await Promise.all([api('/knowledge/compare',{method:'POST',body:JSON.stringify({variant_ids:basket,language:state.language,scenarios:basket.map(()=>({months:conditions.months||24,monthly_km:conditions.monthly_km||1000}))})}),loadFuelPrices(),loadBattles(),...basket.map(id=>usTech?.enabled()?api(`/catalog/variants/${encodeURIComponent(id)}/us-tech?language=${techLanguage}`).catch(()=>null):Promise.resolve(null))]);
    if(!valid())return;
    compareData=data;
    const members=data.members, tech=Object.fromEntries(basket.map((id,i)=>[id,techs[i]??null]));
    // a curated battle keeps its prepared verdict and the safety ratings found for it
    const battle=battleId?battleList.find(b=>b.id===battleId):null;
    const prepared=battle?.verdict;
    const cars=members.map((v,i)=>({name:`${v.make} ${v.model}`,metrics:metricsOf(tech[v.id],{},battle?specMetrics(battle.members[i]).metrics:{})}));
    const result=verdict(cars,state.language);
    const lines=prepared?.lines?.[state.language]||prepared?.lines?.ru||result.lines;
    const techRow=(v,key)=>(tech[v.id]?.categories||[]).flatMap(c=>c.rows).find(r=>r.key===key);
    const litres=v=>numberOf(techRow(v,'fuel_combined')?.values?.[0]?.value);
    // the grade: diesel by the fuel, else the Auto Expert recommendation (AI-98 / AI-95 / AI-92)
    const grade=v=>{if(factValue(v.facts,'fuel')==='DIESEL')return 'DIESEL';const rec=techRow(v,'fuel_recommendation')?.values?.[0]?.value||'';return /98/.test(rec)?'AI98':/95/.test(rec)?'AI95':'AI92';};
    const vs=members.map((v,i)=>`${i?'<span class="vs-badge">VS</span>':''}<div class="vs-car">${photo(v,v.make+' '+v.model)}<h2>${esc(v.make+' '+v.model)}</h2><p>${esc(specLine(v))}</p><button class="text-button" data-k="remove" data-id="${esc(v.id)}">${esc(l('remove'))}</button></div>`).join('');
    // costs (owner decision 2026-10-06): fuel only — EPA consumption x km per month x the fuel price
    // from fuel-prices.json; no price there, no block. No service or repair estimates here.
    const months=conditions.months||24, monthlyKm=conditions.monthly_km||1000;
    const fuelRows=members.map(v=>({v,cost:fuelCost({litresPer100:litres(v),grade:grade(v),monthlyKm,months,prices:fuel.prices})}));
    const amount=x=>`${Math.round(x).toLocaleString(state.language==='en'?'en-US':'ru-RU')} ${fuel.currency}`;
    const gradeName={AI92:'АИ-92',AI95:'АИ-95',AI98:'АИ-98',DIESEL:T('дизель','dizel','diesel')};
    const costBlock=Object.keys(fuel.prices).length&&fuelRows.some(r=>r.cost)?`<section class="catalog-card cost-block"><h2>${esc(T(`Топливо за ${months} мес.`,`${months} ay üçün yanacaq`,`Fuel for ${months} months`))}</h2><p class="catalog-note">${esc(T(`Расход EPA × ${monthlyKm.toLocaleString()} км в месяц × цена топлива`,`EPA sərfiyyatı × ayda ${monthlyKm.toLocaleString()} km × yanacaq qiyməti`,`EPA consumption × ${monthlyKm.toLocaleString()} km a month × fuel price`))}${fuel.updated?` · ${esc(fuel.updated)}`:''}</p><div class="cost-grid">${fuelRows.map(({v,cost})=>`<div class="cost-col"><h3>${esc(v.make+' '+v.model+' '+v.year)}</h3>${cost?`<p class="cost-total">${esc(amount(cost.total))}</p><p class="catalog-note">${esc(`${amount(cost.monthly)} ${T('в месяц','ayda','a month')} · ${gradeName[cost.grade]} ${cost.price} ${fuel.currency}/${T('л','l','L')}`)}</p>`:`<p class="catalog-note">${esc(T('Нет расхода EPA или цены этого топлива','EPA sərfiyyatı və ya bu yanacağın qiyməti yoxdur','No EPA consumption or no price for this fuel'))}</p>`}</div>`).join('')}</div>
        <details class="change-conditions"><summary>${esc(T('Изменить условия','Şərtləri dəyiş','Change conditions'))}</summary><form id="conditions-form"><div class="form-pair">${number('monthly_km','km',monthlyKm,'min="0" max="30000"')}${number('months','months',months,'min="1" max="120"')}</div><button class="button secondary full">${esc(l('calculate'))}</button></form></details></section>`:'';
    show(`${top(T('Сравнение','Müqayisə','Comparison'),'results')}
      <section class="vs-head">${vs}</section>
      <section class="ae-verdict"><p class="ae-eyebrow">✓ ${esc(T('Вердикт Auto Expert','Auto Expert hökmü','Auto Expert verdict'))}</p>${lines.length?`<ul>${lines.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`:`<p>${esc(T('Для этих машин в базе пока мало данных для сравнения.','Bu avtomobillər üçün bazada müqayisə üçün məlumat azdır.','Our database has too little on these cars to compare them.'))}</p>`}</section>
      ${result.table.length?`<section class="catalog-card quick-table"><h2>${esc(T('Главное за 30 секунд','30 saniyədə əsas','The main points in 30 seconds'))}</h2><table><thead><tr><th>${esc(T('Параметр','Parametr','Parameter'))}</th>${members.map(v=>`<th>${esc(v.make+' '+v.model)}</th>`).join('')}</tr></thead><tbody>${result.table.map(row=>`<tr><th scope="row">${esc(row.label)}</th>${row.cells.map(c=>`<td>${c?`${c.best?'<span class="dot good" aria-hidden="true"></span>':''}${esc(c.text)}`:'—'}</td>`).join('')}</tr>`).join('')}</tbody></table></section>`:''}
      ${costBlock}
      ${result.sources.length?`<p class="catalog-note compare-sources">${esc(T('Источники','Mənbələr','Sources'))}: ${esc(result.sources.join(' · '))}</p>`:''}
      <div id="ownership-host"></div>
      <section class="ae-cta-dark"><h2>${esc(T('Нашли подходящий вариант?','Uyğun variant tapdınız?','Found the one?'))}</h2><p>${esc(T('Проверьте конкретную машину по VIN или госномеру.','Konkret avtomobili VIN və ya dövlət nömrəsi ilə yoxlayın.','Check a specific car by VIN or plate.'))}</p>${tbtn(T('Проверить VIN / госномер','VIN / dövlət nömrəsini yoxla','Check VIN / plate'),'check','','primary full')}</section>
      ${btn('save','save-compare','','secondary full')}${btn('savedCompare','saved-compare','','secondary full')}`, 'compare');
    if(flag('ownershipQuestionnaire')){const host=root.querySelector('#ownership-host');if(host)mountOwnership(host,members,{language:state.language,esc,ensureSession,go});}
  }
  function costForm(id) {const s=scenarios[id]||{};return `<form class="cost-form" data-id="${id}">${[['purchase_price','purchase'],['resale_price','resalePrice'],['fuel_price','fuelPrice'],['electricity_price','electricityPrice'],['maintenance','maintenance'],['repair_reserve','repairReserve'],['other_costs','otherCosts']].map(([k,label])=>number(k,label,s[k],'min="0" step="0.01"')).join('')}<label>${esc(l('priceDate'))}<input type="date" name="price_date" value="${esc(s.price_date||'')}"></label><label>${esc(l('priceSource'))}<input name="price_source" maxlength="1000" value="${esc(s.price_source||'')}"></label><button class="button primary full">${esc(l('calculate'))}</button></form>`;}

  // --- other screens ------------------------------------------------------------------------------
  function check() {show(heading('check','checkSub')+box(`<span class="mode-number">VIN / URL</span><h2>${esc(l('vinListing'))}</h2>${btn('next','vin','','primary full')}`)+box(`<h2>${esc(l('plate'))}</h2><form id="plate-form">${select('country','country',['AZ','US','CA','DE','KR','JP','CN','OTHER'].map(k=>[k,k==='OTHER'?'other':k]),'AZ')}<label>${esc(l('plate'))}<input name="plate" required maxlength="24" autocomplete="off" placeholder="10-AA-123"></label><button class="button secondary full">${esc(l('checkCta'))}</button></form><p id="plate-result" role="status"></p>`)+btn('manual','manual','','secondary full'), 'check');}
  async function resolver() {show(heading('resolve','resolverHelp')+`<form id="resolver-form" class="catalog-card"><div class="form-pair"><label>${esc(l('make'))}<input name="make" required></label><label>${esc(l('model'))}<input name="model" required></label>${number('year','year','','min="2012" max="2100"')}${number('engine','displacement','','step="0.1"')}</div>${select('market','market',[['US','US']],'US')}<button class="button primary full">${esc(l('resolve'))}</button></form><div id="resolver-result"></div>`);}
  // random pairs from the first search results: behind the randomPairs flag (curated battles replace them)
  async function loadCatalogPairs() {
    if(catalogPairs !== null)return catalogPairs;
    const data = await api(`/knowledge/search?language=${state.language}`,{method:'POST',body:JSON.stringify({...searchBody(defaults()),sort:'make',limit:100})});
    const matches = (data.matches||[]).filter(v=>v.id&&v.make&&v.model&&Number.isInteger(v.year));
    const byModel = new Map();
    for(const vehicle of matches){const key=`${vehicle.make.toLowerCase()}|${vehicle.model.toLowerCase()}`;if(!byModel.has(key))byModel.set(key,vehicle);}
    const remaining=[...byModel.values()], pairs=[];
    while(remaining.length>=2&&pairs.length<3){
      const first=remaining.shift();
      const differentMake=remaining.findIndex(v=>v.make.toLowerCase()!==first.make.toLowerCase());
      const second=remaining.splice(differentMake>=0?differentMake:0,1)[0];
      pairs.push([first,second]);
    }
    catalogPairs=pairs;
    return catalogPairs;
  }
  function catalogPairCard([first,second]) {
    const title=v=>`${v.make} ${v.model} · ${v.year}`;
    return `<article class="battle-card catalog-pair-card"><div class="battle-visual" aria-hidden="true"><span>↔</span></div><h3>${esc(title(first))}<br><span class="catalog-pair-vs">vs</span> ${esc(title(second))}</h3><button class="text-button" data-k="catalog-pair-compare" data-ids="${esc(first.id+','+second.id)}">${esc(l('personalCompare'))} →</button></article>`;
  }
  async function battles() {const valid=guardView();wait();const items=await loadBattles();if(!valid())return;show(top(l('battles'),'home')+`<div class="catalog-heading"><h1>${esc(l('battles'))}</h1><p>${esc(T('Машины одного класса и близких лет. Сравнение — по данным нашей базы.','Eyni sinif və yaxın illərin avtomobilləri. Müqayisə bazamızın məlumatlarına görədir.','Cars of one class and close years, compared on our data.'))}</p></div><div class="battle-list">${items.length?items.map(battleCard).join(''):box(`<h2>${esc(l('noEditorial'))}</h2>`)}</div>${tbtn(T('Своё сравнение','Öz müqayisəniz','Your own comparison'),'compare','','primary full')}`, 'compare');}
  function profile() {
    const user=sessionUser();
    const sub=subscription()?.enabled?.();
    const languages=[['ru','Русский'],['az','Azərbaycan'],['en','English']];
    show(top(T('Профиль','Profil','Profile'),'home')+(user?box(`<div class="profile-head"><span class="profile-dot" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="12" cy="9" r="4"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/></svg></span><div><strong>${esc(user.email.startsWith('demo-')?l('localPreview'):user.email)}</strong></div></div>${btn('reports','reports','','secondary full')}${sub?`<button class="button primary full" data-action="subscription">${esc(T('Подписка','Abunə','Subscription'))}</button>`:''}${garage()?.enabled?.()?`<button class="button secondary full" data-action="garage">${esc(garage().navLabel())}</button>`:''}${club()?.enabled?.()?`<button class="button secondary full" data-action="club">${esc(club().navLabel())}</button>`:''}${user.is_admin?btn('editor','admin','','secondary full'):''}${btn('logout','logout','','secondary full')}`):`<form id="account-form" class="catalog-card"><h2>${esc(T('Вход','Giriş','Sign in'))}</h2><label>${esc(l('email'))}<input name="email" type="email" required autocomplete="email"></label><label>${esc(l('password'))}<input name="password" type="password" required minlength="10" autocomplete="current-password"></label><button class="button primary full" name="mode" value="login">${esc(l('login'))}</button><button class="button secondary full" name="mode" value="register">${esc(l('register'))}</button></form>`)
      +box(`<h2>${esc(T('Язык','Dil','Language'))}</h2><div class="filter-chips">${languages.map(([c,name])=>`<button class="filter-chip ${state.language===c?'selected':''}" data-action="buyer-language" data-language="${c}" aria-pressed="${state.language===c}">${esc(name)}</button>`).join('')}</div><h2>${esc(T('Регион','Region','Region'))}</h2><div class="filter-chips">${[['AZ',T('Азербайджан · AZN, Turbo.az','Azərbaycan · AZN, Turbo.az','Azerbaijan · AZN, Turbo.az')],['US',T('США · $','ABŞ · $','USA · $')]].map(([c,name])=>`<button class="filter-chip ${region(state)===c?'selected':''}" data-k="region" data-id="${c}" aria-pressed="${region(state)===c}">${esc(name)}</button>`).join('')}</div>`)
      +btn(largeText?'normalText':'largeText','text-size','','secondary full'));
  }
  async function researchStatus(id){const valid=guardView();wait();const job=await api('/knowledge/research/'+encodeURIComponent(id));if(!valid())return;show(heading('research')+box(`<h2 role="status">${esc(l(job.state))}</h2><p>${esc(l('researchReview'))}</p><p>${esc(l('calls'))}: ${job.calls}</p>${btn('refresh','research-refresh',id)}${['QUEUED','RUNNING'].includes(job.state)?btn('cancel','research-cancel',id):job.state==='FAILED'&&job.attempts<2?btn('retry','research-retry',id):''}`));}
  async function admin() {const valid=guardView();wait();const d=await api('/knowledge/admin');if(!valid())return;show(heading('adminTitle')+box(`<h2>${esc(l('coverage'))}</h2><dl>${Object.entries(d.coverage).filter(([,v])=>typeof v==='number').map(([k,v])=>`<div><dt>${esc(k)}</dt><dd>${v}</dd></div>`).join('')}</dl>${!d.worker_enabled?note('workerOff'):''}`)+box(`<h2>${esc(l('sourceRegistry'))}</h2>${d.sources.map(s=>`<details><summary>${esc(s.title)} · ${esc(s.state)}</summary><p>${esc(s.limitations||'')}</p><p>${esc(l(s.commercial_reuse?'rightsReviewed':'rightsPending'))}</p><button class="button secondary" data-k="source-toggle" data-id="${esc(s.id)}" data-paused="${s.paused}">${esc(l(s.paused?'resume':'pause'))}</button></details>`).join('')}`)+box(`<h2>${esc(l('imports'))}</h2><form id="manifest-form"><label>${esc(l('manifest'))}<textarea name="manifest" rows="8" required spellcheck="false"></textarea></label><button class="button primary full">${esc(l('enqueue'))}</button></form><form id="document-form"><label>${esc(l('sourceId'))}<input name="source_id" required></label><label>${esc(l('document'))}<input name="document" type="file" required accept=".json,.csv,.pdf,.zip,.txt"></label><button class="button secondary full">${esc(l('document'))}</button><output id="document-output"></output></form>${d.jobs.map(j=>`<details class="admin-job"><summary>${esc(j.source_id)} · ${esc(j.state)} · ${j.cursor}</summary><p>${esc(j.id)}</p><pre>${esc(JSON.stringify(j.metrics,null,2))}</pre><label>${esc(l('note'))}<textarea class="review-note" minlength="10" required></textarea></label><div class="filter-chips">${['details',...(j.state==='STAGED'?['approve','reject']:j.state==='APPROVED'?['publish']:j.state==='FAILED'?['retry']:['cancel'])].map(a=>`<button class="button secondary" data-k="job" data-id="${j.id}" data-job-action="${a}">${esc(l(a))}</button>`).join('')}</div><pre class="job-detail"></pre></details>`).join('')}`)+box(`<h2>${esc(l('assets'))}</h2>${d.assets.map(a=>`<p>${esc(a.id)} · ${esc(a.state)}</p>`).join('')||'0'}`)+editorTools(d,l,esc));}

  async function action(target) {
    const a=target.dataset.k, id=target.dataset.id;
    if(a==='text-size'){largeText=!largeText;document.documentElement.classList.toggle('large-text',largeText);save();profile();return;}
    if(a==='region'){setRegion(id);profile();return;}
    if(a==='research'){await ensureSession();const job=await api('/knowledge/research',{method:'POST',body:JSON.stringify({vehicle:{make:current.make,model:current.model,year:current.year,market:current.market},language:state.language})});go('/catalog-research/'+job.id);return;}
    if(a==='research-refresh'){await researchStatus(id);return;}
    if(a==='research-cancel'||a==='research-retry'){await api('/knowledge/research/'+id+'/control',{method:'POST',body:JSON.stringify({action:a==='research-cancel'?'cancel':'retry',note:'Owner requested action through buyer interface'})});await researchStatus(id);return;}
    if(a==='chip'){const form=root.querySelector('#catalog-wizard');if(form)readFilters(form);const key=target.dataset.field,value=target.dataset.value;if(target.dataset.multi==='true'){const arr=filters[key]||[];if(arr.includes(value))filters[key]=arr.filter(x=>x!==value);else {if(key==='priorities'&&arr.length===3){showToast(l('max3'));return;}filters[key]=[...arr,value];}}else filters[key]=filters[key]===value&&key==='origin'?null:value;save();await wizard();return;}
    if(a==='family'){const form=root.querySelector('#catalog-wizard');if(form)readFilters(form);filters.family_use=!filters.family_use;save();await wizard();return;}
    if(a==='purpose-unknown'){const form=root.querySelector('#catalog-wizard');if(form)readFilters(form);filters.roads=[];filters.family_use=false;save();await wizard();return;}
    if(a==='add-make'||a==='add-model'){const input=root.querySelector(a==='add-make'?'#make-query':'#model-query'),key=a==='add-make'?'makes':'models';if(input.value.trim()){readFilters(root.querySelector('#catalog-wizard'));filters[key]=[...new Set([...filters[key],input.value.trim()])];save();await wizard();}return;}
    if(a==='reset'){filters=defaults();step=1;save();await wizard();return;}
    if(a==='wizard'){step=1;go('/pick');return;} if(a==='step-back'){readFilters(root.querySelector('#catalog-wizard'));step=1;await wizard();return;}
    if(a==='check-listing'){go('/check-legacy/turbo');return;}
    if(a==='browse'){filters={...defaults(),market_preference:'ANY'};save();go('/catalog-results');return;}
    if(a==='search'){filters.query=root.querySelector('#catalog-search')?.value||'';filters.offset=0;save();await results();return;}
    if(a==='more'){filters.offset=(filters.offset||0)+20;save();await results();window.scrollTo(0,0);return;}
    if(a==='basket'){battleId=null;if(basket.includes(id))basket=basket.filter(x=>x!==id);else {if(basket.length>=MAX){showToast(T('В сравнении две машины — уберите одну','Müqayisədə iki avtomobil var — birini çıxarın','Two cars are compared — remove one first'));return;}basket.push(id);}save();const on=basket.includes(id);root.querySelectorAll(`[data-k="basket"][data-id="${CSS.escape(id)}"]`).forEach(b=>{b.classList.toggle('selected',on);b.setAttribute('aria-pressed',String(on));b.textContent=b.classList.contains('icon-button')?(on?'✓':'＋'):b.classList.contains('compare-toggle')?(on?T('✓ В сравнении','✓ Müqayisədə','✓ In comparison'):T('＋ Сравнить','＋ Müqayisə','＋ Compare')):(on?T('✓ В сравнении','✓ Müqayisədə','✓ In comparison'):T('Добавить к сравнению','Müqayisəyə əlavə et','Add to comparison'));});root.querySelectorAll('[data-basket-count]').forEach(n=>{n.textContent=String(basket.length);});return;}
    if(a==='remove'){battleId=null;basket=basket.filter(x=>x!==id);save();await compare();return;}
    if(a==='tech-cat'){go(`/catalog-car/${id}/${target.dataset.cat}`);return;}
    if(a==='garage-add'){garage()?.prefill({make:current.make,model:current.model,year:current.year,configuration_key:currentTech?.configuration_key,label:currentTech?.summary});return;}
    if(a==='save'){if(!sessionUser()&&!state.meta?.developer?.enabled){go('/profile');return;}await ensureSession();const r=await api(`/knowledge/vehicles/${id}/save`,{method:'POST',body:JSON.stringify({language:state.language,preferences:searchBody()})});showToast(l('saved'));go('/buyer-report/'+r.id);return;}
    if(a==='save-compare'){if(!sessionUser()&&!state.meta?.developer?.enabled){go('/profile');return;}await ensureSession();const r=await api('/knowledge/compare/save',{method:'POST',body:JSON.stringify({variant_ids:basket,language:state.language,scenarios:basket.map(()=>({months:conditions.months||24,monthly_km:conditions.monthly_km||1000}))})});go('/buyer-report/'+r.id);return;}
    if(a==='favorite'){await ensureSession();await api('/knowledge/favorites/'+id,{method:'PUT'});showToast(l('saved'));return;}
    if(a==='only-favorites'){onlyFavorites=!onlyFavorites;await battles();return;}
    if(a==='topic'){topic=id;await battles();return;}
    if(a==='battle-compare'){const r=await resolveBattle(id);if(!r)return;if(r.missing){showToast(T(`В каталоге пока нет ${r.missing}`,`Kataloqda hələ ${r.missing} yoxdur`,`${r.missing} is not in the catalogue yet`));return;}basket=r.ids.slice(0,MAX);battleId=r.battle.id;save();go('/compare');return;}
    if(a==='catalog-pair-compare'){const ids=target.dataset.ids.split(',').filter(Boolean).slice(0,2);if(ids.length!==2)return;basket=ids;battleId=null;save();go('/compare');return;}
    if(a==='logout'){clearSession();profile();return;}
    if(a==='job'){const parent=target.closest('.admin-job');if(target.dataset.jobAction==='details'){const d=await api('/knowledge/admin/imports/'+id);parent.querySelector('.job-detail').textContent=JSON.stringify(d,null,2);return;}const note=parent.querySelector('.review-note').value;if(note.length<10){parent.querySelector('.review-note').reportValidity();return;}await api(`/knowledge/admin/imports/${id}/review`,{method:'POST',body:JSON.stringify({action:target.dataset.jobAction,note})});await admin();return;}
    if(a==='source-toggle'){await api('/knowledge/admin/sources/'+id,{method:'PATCH',body:JSON.stringify({paused:target.dataset.paused!=='true',note:'Operator toggled source acquisition/publication in protected editorial UI'})});await admin();return;}
    const routes={home:'/home',mode:'/choose',results:'/catalog-results',vehicle:'/catalog-car/'+id,compare:'/compare',check:'/check',vin:'/vin',manual:'/manual',battles:'/battles',publication:'/battle/'+id,resolve:'/resolve',reports:'/reports',admin:'/editor','saved-compare':'/saved-compare'};if(routes[a])go(routes[a]);
  }
  root.addEventListener('click',e=>{const target=e.target.closest('[data-k]');if(!target||target.disabled)return;e.preventDefault();target.disabled=true;void action(target).catch(fail).finally(()=>{target.disabled=false;});});
  root.addEventListener('change',e=>{if(e.target.id==='catalog-sort'){filters.sort=e.target.value;filters.offset=0;save();void results().catch(fail);}});
  root.addEventListener('submit',e=>{const form=e.target;if(!['catalog-wizard','plate-form','resolver-form','account-form','manifest-form','document-form','conditions-form'].includes(form.id)&&!form.matches('.cost-form'))return;e.preventDefault();const submit=e.submitter;if(submit)submit.disabled=true;void(async()=>{
    if(form.id==='catalog-wizard'){readFilters(form);if(step===1&&submit?.name!=='skip'){step=2;await wizard();window.scrollTo(0,0);}else{step=1;filters.offset=0;save();go('/catalog-results');}}
    else if(form.id==='plate-form'){root.querySelector('#plate-result').textContent=l('plateUnavailable');}
    else if(form.id==='conditions-form'){const d=new FormData(form);conditions={...conditions,monthly_km:Number(d.get('monthly_km'))||1000,months:Number(d.get('months'))||24};save();await compare();}
    else if(form.matches('.cost-form')){scenarios[form.dataset.id]=Object.fromEntries([...new FormData(form)].map(([k,v])=>[k,v===''?null:v]));save();await compare();}
    else if(form.id==='resolver-form'){const d=Object.fromEntries([...new FormData(form)].filter(([,v])=>v!==''));if(d.year)d.year=Number(d.year);d.catalog_scope=CONSUMER_CATALOG_SCOPE;d.language=state.language;const r=await api('/knowledge/resolve',{method:'POST',body:JSON.stringify(d)});root.querySelector('#resolver-result').innerHTML=box(`<h2>${esc(l(r.status))}</h2><p>${esc(l('resolverHelp'))}</p>`)+(r.suggestions?.length?box(`<h3>${esc(l('suggestions'))}</h3>${r.suggestions.map(s=>`<p>${esc(s.make+' '+s.model)}</p>`).join('')}`):'')+r.candidates.map(vehicleCard).join('')+(r.needs_confirmation?.length?box(`<h3>${esc(l('needs'))}</h3>`)+r.needs_confirmation.map(vehicleCard).join(''):'')+btn('manual','manual','','secondary full');}
    else if(form.id==='account-form'){const d=Object.fromEntries(new FormData(form));const mode=submit?.value||'login';if(mode==='register'){d.preferred_language=state.language;d.country_code=isAZ()?'AZ':'US';}const r=await api('/auth/'+mode,{method:'POST',body:JSON.stringify(d)});localStorage.setItem('autoexpert.demo.token',r.access_token);localStorage.setItem('autoexpert.demo.user',JSON.stringify(r.user));profile();}
    else if(form.id==='manifest-form'){await api('/knowledge/admin/imports',{method:'POST',body:JSON.stringify(JSON.parse(new FormData(form).get('manifest')))});await admin();}
    else if(form.id==='document-form'){const d=new FormData(form),file=d.get('document');const r=await api('/knowledge/admin/documents/'+encodeURIComponent(d.get('source_id')),{method:'POST',headers:{'Content-Type':file.type||'application/octet-stream'},body:file});root.querySelector('#document-output').textContent=l('documentId')+': '+r.id;}
  })().catch(fail).finally(()=>{if(submit)submit.disabled=false;});});
  function selectProfileTab(tab,focus=false){
    root.querySelectorAll('[data-profile-tab]').forEach(b=>{const selected=b===tab;b.setAttribute('aria-selected',String(selected));b.tabIndex=selected?0:-1;});
    root.querySelectorAll('.profile-panel').forEach(p=>{p.hidden=p.id!=='panel-'+tab.dataset.profileTab;});
    if(focus)tab.focus();
  }
  root.addEventListener('click',e=>{const tab=e.target.closest('[data-profile-tab]');if(tab)selectProfileTab(tab);});
  root.addEventListener('keydown',e=>{const tab=e.target.closest('[data-profile-tab]');if(!tab||!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const tabs=[...root.querySelectorAll('[data-profile-tab]')],i=tabs.indexOf(tab);selectProfileTab(tabs[e.key==='Home'?0:e.key==='End'?tabs.length-1:(i+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length],true);});
  return {
    addVariantToBasket(id,title=''){
      if(!id)return false;
      if(basket.includes(id)){if(title&&!names[id]){names[id]=title;save();}return true;}
      if(basket.length>=MAX)return false;
      battleId=null;basket.push(id);if(title)names[id]=title;save();return true;
    },
    async route(name,id,sub){const routes={home,choose:mode,pick:wizard,'catalog-results':results,'catalog-car':vehicle,'catalog-research':researchStatus,compare,check,resolve:resolver,battles,battle:battles,profile,editor:admin};if(!routes[name])return false;++viewRequest;await routes[name](id,sub);return true;}
  };
}
