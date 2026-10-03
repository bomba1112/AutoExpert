import {mountOwnership} from './ownership-panel.js?v=0.8.1';
import {editorTools, bindEditorTools} from './editor-tools.js?v=0.8.1';
import {api, sessionUser, clearSession} from './api.js?v=0.8.1';
import {message} from './catalog-copy.js?v=0.9.3';
import {localizeConfiguration, localizeProfile, localizeTechnicalValue} from './catalog-display.js?v=0.9.1';

export function createCatalogViews({root, state, layout, go, esc, ensureSession, showToast, usTech = null}) {
  const KEY = 'autoexpert.catalog.buyer.v1';
  const CONSUMER_CATALOG_SCOPE = 'US_BASE_2000';
  const defaults = () => ({catalog_scope:CONSUMER_CATALOG_SCOPE, catalog_ready_only:true, year_min:2012, market_preference:'SELECTED', markets:['US'], body:[], engine:'ANY', transmission:'ANY', makes:[], models:[], roads:[], priorities:[], monthly_km:1000, ownership_months:24, charging:'UNKNOWN', sort:'recommended', initial_service_included:null});
  let saved = {}; try {saved = JSON.parse(localStorage.getItem(KEY) || '{}');} catch {}
  let filters = {...defaults(), ...(saved.filters || {})};
  filters = {...filters, catalog_scope:CONSUMER_CATALOG_SCOPE, catalog_ready_only:true, market_preference:'SELECTED', markets:['US'], year_min:Math.max(2012,Number(filters.year_min)||2012), year_max:Number(filters.year_max)>=2012?Number(filters.year_max):null};
  let basket = Array.isArray(saved.basket) ? saved.basket.slice(0,3) : [];
  let step = 1, facets = null, result = null, current = null, compareData = null, topic = '', onlyFavorites = false, catalogPairs = null;
  const scenarios = saved.scenarios || {};
  const names = saved.names || {};
  let largeText = !!saved.largeText;
  document.documentElement.classList.toggle('large-text', largeText);
  let viewRequest=0;
  const guardView=()=>{const n=++viewRequest,hash=location.hash,language=state.language;return ()=>n===viewRequest&&hash===location.hash&&language===state.language;};
  const l = key => message(state.language, key);
  const save = () => localStorage.setItem(KEY, JSON.stringify({filters,basket,scenarios,names,largeText}));
  const btn = (key, action, id='', cls='secondary') => `<button class="button ${cls}" data-k="${action}" data-id="${esc(id)}">${esc(l(key))}</button>`;
  const heading = (title, sub='') => `<div class="catalog-heading"><h1>${esc(l(title))}</h1>${sub ? `<p>${esc(l(sub))}</p>`:''}</div>`;
  const show = (html, active='') => {root.innerHTML = layout(`<div class="catalog-view">${html}</div>`, {active});};
  const box = html => `<section class="catalog-card">${html}</section>`;
  const note = key => `<p class="catalog-note">${esc(l(key))}</p>`;
  const emptyImage = () => `<div class="catalog-image-placeholder" aria-hidden="true"><svg viewBox="0 0 120 64"><path d="m15 37 12-19h47l21 20 10 4v11H9V41Z"/><path d="m31 24-7 13h58L71 24Zm24 0v13"/><circle cx="29" cy="53" r="9"/><circle cx="86" cy="53" r="9"/></svg></div>`;
  const attribution = v => (v.attribution?`<details class="catalog-note"><summary>${esc(l('source'))} · NRCan</summary><p>${esc(v.attribution)}</p><a href="https://open.canada.ca/en/open-government-licence-canada" target="_blank" rel="noopener noreferrer">Open Government Licence – Canada</a></details>`:'')+(v.asset?.attribution?`<p class="catalog-note">${esc(v.asset.attribution)}</p>`:'');
  const number = (name,key,value,attrs='') => `<label>${esc(l(key))}<input type="number" inputmode="decimal" name="${name}" value="${esc(value ?? '')}" ${attrs}></label>`;
  const select = (name,key,values,current,attrs='') => `<label>${esc(l(key))}<select name="${name}" ${attrs}>${values.map(([v,k])=>`<option value="${esc(v)}" ${String(current)===String(v)?'selected':''}>${esc(l(k))}</option>`).join('')}</select></label>`;
  const chip = (field,value,key,multi=false) => `<button type="button" class="filter-chip ${(multi ? (filters[field]||[]).includes(value):filters[field]===value)?'selected':''}" data-k="chip" data-field="${field}" data-value="${value}" data-multi="${multi}" aria-pressed="${(multi ? (filters[field]||[]).includes(value):filters[field]===value)}">${esc(l(key))}</button>`;
  const chips = (key,field,values,multi=false) => `<fieldset class="filter-group"><legend>${esc(l(key))}</legend><div class="filter-chips">${values.map(([v,k])=>chip(field,v,k,multi)).join('')}</div></fieldset>`;
  const wait = () => show(`<p class="catalog-loading" role="status">${esc(l('loading'))}</p>`);
  const fail = e => {const key=Object.keys((e?.payload?.detail&&Array.isArray(e.payload.detail))?Object.fromEntries(e.payload.detail.map(d=>[String(d.msg).replace('Value error, ',''),true])):{[e?.message]:true}).find(k=>l(k)!==k);showToast(key?l(key):l('error'));};
  bindEditorTools(root,{refresh:()=>admin(),fail,l});
  const assetUrl = url => url ? (globalThis.AUTOEXPERT_API_ROOT||'/api/v1').replace(/\/api\/v1\/?$/,'')+url : '';
  async function loadFacets() {if (!facets) facets = await api(`/knowledge/facets?catalog_scope=${CONSUMER_CATALOG_SCOPE}`); return facets;}
  function minor(v) {if(v==='' || v===null) return null; const s=String(v).replace(',','.'); if(!/^\d+(\.\d{1,2})?$/.test(s)) throw Error('BUDGET_RANGE'); const [a,b='']=s.split('.'); return Number(a)*100+Number(b.padEnd(2,'0'));}
  function readFilters(form) {
    const d = new FormData(form);
    for(const key of ['year_min','year_max','min_seats','min_clearance_mm','monthly_km','ownership_months']) if(d.has(key)) filters[key] = d.get(key)===''?null:Number(d.get(key));
    for(const key of ['budget_min_minor','budget_max_minor']) if(d.has(key)) filters[key] = minor(d.get(key));
    for(const key of ['city','charging','drivetrain','displacement_max_l','supply_channel']) if(d.has(key)) filters[key] = d.get(key) || (key==='city'?'':null);
    filters.year_min=Math.max(2012,Number(filters.year_min)||2012);
    if(filters.year_max!==null && filters.year_max<2012)filters.year_max=null;
    if(d.has('initial_service_included')) filters.initial_service_included = d.get('initial_service_included')==='UNKNOWN'?null:d.get('initial_service_included')==='YES';
    if(form.querySelector('[name="large_boot"]')) filters.large_boot = d.has('large_boot');
    if(form.querySelector('[name="family_use"]')) filters.family_use = d.has('family_use');
    save();
  }
  async function home() {
    const valid=guardView();
    show(`<section class="home-intro"><p class="home-location">AZƏRBAYCAN</p><h1>${esc(l('slogan'))}</h1><p>${esc(l('sub'))}</p><span class="skyline" aria-hidden="true"></span></section>
      <section class="home-buy"><img class="home-buy-art" src="/preview/assets/buyer-road.svg" alt="" aria-hidden="true"><div><h2>${esc(l('buy'))}</h2><p>${esc(l('buySub'))}</p>${btn('start','wizard','','primary')}<button class="home-existing" data-k="check-listing">${esc(state.language==='az'?'Artıq seçimlərim var':'У меня уже есть варианты')} →</button></div><div class="home-tags">${['budget','engine','transmission','body','market'].map(k=>`<span>${esc(l(k))}</span>`).join('')}</div></section>
      <section class="home-check"><span class="check-illustration" aria-hidden="true">VIN<span>▱ ▱ ▱</span></span><h2>${esc(l('check'))}</h2><p>${esc(state.language==='az'?'VIN, Turbo.az elanı və ya bildiyiniz göstəricilərlə başlayın.':'VIN, объявление Turbo.az или известные вам параметры.')}</p>${btn('checkCta','check','','primary')}<div class="check-foot">VIN · Turbo.az · ${esc(state.language==='az'?'Əllə daxil et':'Ручной ввод')}</div></section>
      <section class="home-battles"><div class="section-title"><h2>${esc(l('battles'))}</h2><button class="text-button" data-k="battles">${esc(l('all'))} →</button></div><p>${esc(l('battlesSub'))}</p><div id="home-publications" class="battle-strip"><p class="catalog-loading" role="status">${esc(l('loading'))}</p></div></section>`, 'home');
    const pairs = await loadCatalogPairs();
    if(!valid())return;
    const node = root.querySelector('#home-publications'); if(node) node.innerHTML = pairs.length?pairs.map(catalogPairCard).join(''):box(`<h3>${esc(l('noEditorial'))}</h3><p>${esc(l('noEditorialSub'))}</p>${btn('personalCompare','compare')}`);
  }
  function mode() {show(heading('chooseMode') + `<div class="mode-grid">${box(`<span class="mode-number">01</span><h2>${esc(l('helpPick'))}</h2><p>${esc(l('buySub'))}</p>${btn('start','wizard','','primary full')}`)}${box(`<span class="mode-number">02</span><h2>${esc(l('ownCars'))}</h2><p>${esc(l('ownSub'))}</p>${btn('catalog','browse','','secondary full')}`)}</div>`);}
  async function wizard() {
    const valid=guardView();await loadFacets();if(!valid())return;
    show(`<div class="page-top"><button class="icon-button" data-k="${step===2?'step-back':'home'}" aria-label="${esc(l('back'))}">←</button><strong>${esc(l('wizard'))}</strong><button class="text-button" data-k="reset">${esc(l('reset'))}</button></div><ol class="wizard-progress">${['basics','conditions','results'].map((k,i)=>`<li class="${step===i+1?'active':step>i+1?'done':''}"><span>${i+1}</span>${esc(l(k))}</li>`).join('')}</ol>${heading(step===1?'wizardTitle':'conditions',step===1?'wizardSub':'priorityHelp')}
      <form id="catalog-wizard">${step===1?basicFields():conditionFields()}<button class="button primary full" type="submit">${esc(l(step===1?'next':'showCars'))} →</button></form>${box(`<div class="help-box"><span aria-hidden="true">☼</span><div><strong>${esc(l('helpTitle'))}</strong><p>${esc(l('helpSub'))}</p></div></div>`)}`);
  }
  function basicFields() {
    const latestYear=Math.max(new Date().getFullYear()+1,...facets.years);
    const years = [['','any'], ...Array.from({length:latestYear-2011},(_,i)=>[String(latestYear-i),String(latestYear-i)])];
    return `<div class="form-pair">${number('budget_min_minor','from',filters.budget_min_minor==null?'':(filters.budget_min_minor/100).toFixed(2),'min="0" step="0.01"')}${number('budget_max_minor','budget',filters.budget_max_minor==null?'':(filters.budget_max_minor/100).toFixed(2),'min="0" step="0.01"')}</div>${select('initial_service_included','initialService',[['UNKNOWN','unknown'],['YES','yes'],['NO','no']],filters.initial_service_included===null?'UNKNOWN':filters.initial_service_included?'YES':'NO')}
      <fieldset class="filter-group"><legend>${esc(l('year'))}</legend><div class="form-pair">${select('year_min','from',years.slice(1),filters.year_min)}${select('year_max','to',years,filters.year_max||'')}</div></fieldset>
      <details class="filter-optional"><summary>${esc(l('make'))} / ${esc(l('model'))} · ${esc(l('optional'))}</summary><label>${esc(l('make'))}<input id="make-query" list="make-list" placeholder="${esc(l('search'))}"><datalist id="make-list">${facets.makes.map(m=>`<option value="${esc(m.name)}">`).join('')}</datalist></label><button type="button" class="text-button" data-k="add-make">＋ ${esc(l('make'))}</button><div class="filter-chips">${filters.makes.map(m=>chip('makes',m,m,true)).join('')}</div><label>${esc(l('model'))}<input id="model-query" list="model-list"><datalist id="model-list">${facets.makes.filter(m=>!filters.makes.length||filters.makes.includes(m.name)).flatMap(m=>m.models).map(m=>`<option value="${esc(m)}">`).join('')}</datalist></label><button type="button" class="text-button" data-k="add-model">＋ ${esc(l('model'))}</button><div class="filter-chips">${filters.models.map(m=>chip('models',m,m,true)).join('')}</div></details>
      <div class="market-scope"><strong>USA</strong><p>${esc(l('usLayer'))}</p></div>
      ${select('supply_channel','supply',[['','any'],['OFFICIAL_AZ','official'],['OTHER','other']],filters.supply_channel||'')}
      ${chips('body','body',['SEDAN','CROSSOVER','SUV','HATCHBACK','WAGON','COUPE','MINIVAN','PICKUP'].map(k=>[k,k]),true)}${chips('engine','engine',[['ANY','any'],['UNKNOWN','unknown'],...['GASOLINE','GASOLINE_NA','GASOLINE_TURBO','DIESEL','HEV','PHEV','BEV'].map(k=>[k,k])])}${chips('transmission','transmission',[['ANY','any'],['UNKNOWN','unknown'],...['AT','CVT','DCT','MANUAL','AUTOMATIC_UNSPECIFIED'].map(k=>[k,k])])}
      <details class="filter-optional"><summary>${esc(l('drive'))}, ${esc(l('seats'))}, ${esc(l('clearance'))}</summary>${select('drivetrain','drive',[['','any'],...['FWD','RWD','AWD','4WD'].map(k=>[k,k])],filters.drivetrain||'')}<div class="form-pair">${number('min_seats','seats',filters.min_seats,'min="1" max="30"')}${number('min_clearance_mm','clearance',filters.min_clearance_mm,'min="0" max="600"')}${number('displacement_max_l','displacement',filters.displacement_max_l,'min="0" max="12" step="0.1"')}</div><label class="check-label"><input type="checkbox" name="large_boot" ${filters.large_boot?'checked':''}>${esc(l('boot'))}</label></details>`;
  }
  function conditionFields() {return `<label>${esc(l('city'))}<input name="city" value="${esc(filters.city||'')}" placeholder="Bakı"></label>${chips('roads','roads',['urban','highway','rough'].map(k=>[k,k]),true)}<div class="form-pair">${number('monthly_km','km',filters.monthly_km,'min="0" max="30000" required')}${number('ownership_months','months',filters.ownership_months,'min="1" max="120" required')}</div>${select('charging','charging',[['UNKNOWN','unknown'],['YES','yes'],['NO','no']],filters.charging)}<label class="check-label"><input type="checkbox" name="family_use" ${filters.family_use?'checked':''}>${esc(l('family'))}</label>${chips('priorities','priorities',['reliability','cost','comfort','performance','repair','parts','space','safety','resale'].map(k=>[k,k]),true)}${note('priorityHelp')}`;}
  async function results() {
    const valid=guardView();wait(); result=await api(`/knowledge/search?language=${state.language==='az'?'az':'ru'}`,{method:'POST',body:JSON.stringify(filters)});if(!valid())return;
    show(heading('suitable') + box(`<div class="profile-summary"><span class="profile-dot">●</span><div><strong>${esc(l('profile'))}</strong><p>${esc([filters.budget_max_minor!=null?`${l('to')} ${(filters.budget_max_minor/100).toLocaleString(state.language)} AZN`:l('any'),[filters.year_min,filters.year_max].filter(Boolean).join('–'), ...filters.makes,...filters.models,...filters.markets.map(l),...filters.body.map(l),l(filters.engine),l(filters.transmission)].filter(Boolean).join(' · '))}</p></div><button class="text-button" data-k="wizard">${esc(l('change'))}</button></div>`)+`<div class="result-tools"><label class="search-label"><span class="sr-only">${esc(l('search'))}</span><input id="catalog-search" value="${esc(filters.query||'')}" placeholder="${esc(l('search'))}" type="search"><button data-k="search" class="icon-button" aria-label="${esc(l('search'))}">⌕</button></label>${select('sort','sort',['recommended','year_desc','make','consumption'].map(k=>[k,k]),filters.sort,'id="catalog-sort"')}</div>
      <p class="result-count"><strong>${result.matched_models} ${esc(l('models'))}</strong> · ${result.matched_versions} ${esc(l('versions'))}</p>${result.recommendation?.top?`${topRecommendation(result.recommendation)}${result.recommendation.competitors.length?`<h2 class="list-heading">${esc(l('alternatives'))}</h2>${result.recommendation.competitors.map(vehicleCard).join('')}`:''}`:box(`<h2>${esc(l('noMatches'))}</h2>${btn('change','wizard')}`)}
      ${(result.recommendation?.competitor_models||0)>(filters.offset||0)+20?btn('more','more','','secondary full'):''}<div class="catalog-sticky">${btn('compare','compare','','primary full')}<span>${basket.length} / 3</span></div>`, 'compare');
  }
  function topRecommendation(r) {return `<section class="top-recommendation"><p class="recommendation-eyebrow">${esc(l('topChoice'))}</p>${vehicleCard(r.top)}<div class="recommendation-reasons"><strong>${esc(l('whyChoice'))}</strong><ul>${r.top.ranking.reasons.map(x=>`<li>${esc(x)}</li>`).join('')}</ul></div></section>`;}
  function vehicleCard(v) {
    names[v.id]=v.make+' '+v.model+' · '+v.year;
    const f = v.facts;
    const keyFacts = ['body','seats','fuel','transmission_family'].filter(k=>f[k]?.status==='CONFIRMED' && ![null,undefined,'','UNKNOWN'].includes(f[k].value));
    const specification=localizeConfiguration(f,state.language);
    return `<article class="vehicle-result"><div class="vehicle-result-top">${v.asset.url?`<img src="${esc(assetUrl(v.asset.url))}" alt="${esc(v.make+' '+v.model)}" loading="lazy">`:emptyImage()}<div><h2>${esc(v.make)} ${esc(v.model)}</h2><p>${v.year} · ${esc(v.market)}</p>${v.preview?`<span class="match-badge preview-badge">${esc(l('previewBadge'))}</span>`:''}${v.us_catalog_ready?`<span class="match-badge">${esc(l('basicVerified'))}</span>`:''}</div></div>${specification?`<p class="catalog-note">${esc(specification)}</p>`:''}<div class="vehicle-facts">${keyFacts.map(k=>`<div><small>${esc(f[k].label)}</small><strong>${esc(localizeTechnicalValue(k,f[k].value,state.language,Object.fromEntries(Object.entries(f).map(([name,fact])=>[name,fact?.value]))))} ${esc(f[k].unit||'')}</strong></div>`).join('')}</div>${v.asking_prices?.length?`<p class="asking-price">${esc(l('askingPrice'))}: ${v.asking_prices.slice(0,3).map(p=>`${(p.price_minor/100).toFixed(2)} AZN · ${esc(p.observed_at.slice(0,10))}`).join('; ')}</p>`:''}${v.tradeoffs?.length?`<p class="catalog-note">${v.tradeoffs.map(k=>esc(l(k))).join(' · ')}</p>`:''}<div class="card-actions">${btn('open','vehicle',v.id,'primary')}${v.preview?'':btn(basket.includes(v.id)?'selected':'addCompare','basket',v.id,basket.includes(v.id)?'selected':'secondary')}</div></article>`;
  }
  function missingLabel(k){return ({body_subtype:l('body'),budget:l('budgetMissing'),initial_service_budget:l('initialService'),transmission_construction:l('transmission'),powertrain:l('engine'),aspiration:l('engine'),ground_clearance:l('clearance'),cargo_l:l('boot'),displacement:l('displacement'),supply_channel:l('supply'),year_min:l('year'),year_max:l('year')})[k]||l(k);}
  function fluidsGroup(rows, rowsHtml) {
    const groups=[
      {title:state.language==='az'?'Mühərrik yağı':'Моторное масло',keys:['engine_oil_viscosity','engine_oil_specification','engine_oil_capacity_l','engine_oil_alternatives'],labels:{engine_oil_viscosity:state.language==='az'?'Özlülük':'Вязкость',engine_oil_specification:state.language==='az'?'Spesifikasiya':'Допуск / спецификация',engine_oil_capacity_l:state.language==='az'?'Filtrlə həcm':'Объём с фильтром',engine_oil_alternatives:state.language==='az'?'İcazə verilən alternativ':'Допустимая альтернатива'}},
      {title:state.language==='az'?'Sürətlər qutusu':'Коробка',keys:['transmission_fluid']},
      {title:state.language==='az'?'Paylayıcı qutu':'Раздатка',keys:['transfer_fluid']},
      {title:state.language==='az'?'Ön diferensial':'Передний дифференциал',keys:['front_differential_fluid']},
      {title:state.language==='az'?'Arxa diferensial':'Задний дифференциал',keys:['rear_differential_fluid']},
      {title:state.language==='az'?'Soyuducu maye':'Охлаждающая жидкость',keys:['coolant','coolant_capacity_note']},
      {title:state.language==='az'?'Əyləc mayesi':'Тормозная жидкость',keys:['brake_fluid']},
    ];
    return `<div class="fluids-grid">${groups.map(group=>{const found=rows.filter(row=>group.keys.includes(row.key));return found.length?`<section class="fluid-card"><h3>${esc(group.title)}</h3>${rowsHtml(found.map(row=>({...row,label:group.labels?.[row.key]||row.label})))}</section>`:'';}).join('')}</div>`;
  }
  function technicalGroup(group, index, rowsHtml) {
    return `<details class="catalog-card technical-group ${group.key==='fluids'?'fluids-group':''}" ${index===0?'open':''}><summary>${esc(group.title)}<small>${group.rows.length}</small></summary>${group.key==='fluids'?fluidsGroup(group.rows,rowsHtml):rowsHtml(group.rows)}${group.key==='fuel'?`<p class="catalog-note">${esc(state.language==='az'?'AKI və RON fərqli şkalalardır. Tələb olunan yanacağı avtomobilin sənədlərindən yoxlayın.':'AKI и RON — разные шкалы. Требуемое топливо проверьте по документам автомобиля.')}</p>`:''}</details>`;
  }
  function categoryEmpty(key) {
    if(key==='weak_points')return state.language==='az'?'Almazdan əvvəl diaqnostika nəticələrini və servis tarixçəsini yoxlayın.':'Перед покупкой проверьте диагностику и сервисную историю.';
    if(key==='campaigns')return state.language==='az'?'Servis kampaniyalarının tətbiqini VIN üzrə yoxlayın.':'Проверьте применимость сервисных кампаний по VIN.';
    return state.language==='az'?'VIN və sənədləri, kuzovu, soyuq işəsalmanı və servis tarixçəsini yoxlayın.':'Проверьте VIN и документы, кузов, холодный запуск и сервисную историю.';
  }
  async function vehicle(id) {
    const valid=guardView();wait(); current=await api(`/knowledge/vehicles/${encodeURIComponent(id)}?language=${state.language==='az'?'az':'ru'}`);
    if(!valid())return;
    const p=current.projection;
    const profile=localizeProfile(current.profile,state.language);
    const rowsHtml=rows=>`<dl>${rows.map(r=>`<div><dt>${esc(r.label)}</dt><dd>${esc(r.value)}${r.source_url?`<a class="fact-source" href="${esc(r.source_url)}" target="_blank" rel="noopener noreferrer" title="${esc(r.locator||l('source'))}" aria-label="${esc(l('source')+' · '+r.label)}"> ↗</a>`:''}</dd></div>`).join('')}</dl>`;
    const summaryOrder=['market','years','model_year','engine_description','transmission_description','drivetrain','body','fuel','seats'];
    const summaryRows=[...profile.summary].filter(r=>r.value && !['UNKNOWN','UNRESOLVED'].includes(String(r.value).toUpperCase())).sort((a,b)=>{
      const ai=summaryOrder.indexOf(a.key),bi=summaryOrder.indexOf(b.key);
      return (ai<0?summaryOrder.length:ai)-(bi<0?summaryOrder.length:bi);
    });
    const specification=localizeConfiguration(current.facts || {},state.language) || [summaryRows.find(r=>r.key==='engine_description')?.value,summaryRows.find(r=>r.key==='transmission_description')?.value,summaryRows.find(r=>r.key==='drivetrain')?.value].filter(Boolean).join(' · ');
    show(`<div class="page-top"><button class="icon-button" data-k="results" aria-label="${esc(l('back'))}">←</button><strong>${esc(current.make+' '+current.model)}</strong>${current.preview?'':btn(basket.includes(id)?'selected':'addCompare','basket',id,'text-button')}</div>${current.preview?`<p class="catalog-notice preview-notice">${esc(l('previewNote'))}</p>`:''}<section class="catalog-card vehicle-profile-summary"><div class="dossier-hero">${current.asset.url?`<img src="${esc(assetUrl(current.asset.url))}" alt="${esc(p.title)}">`:emptyImage()}<h1>${esc(p.title)}</h1>${specification?`<p>${esc(specification)}</p>`:''}</div>${rowsHtml(summaryRows)}</section><nav class="profile-categories" role="tablist" aria-label="${esc(l('vehicleCategories'))}">${profile.categories.map((c,i)=>`<button type="button" role="tab" id="tab-${c.key}" aria-controls="panel-${c.key}" aria-selected="${i===0}" tabindex="${i===0?0:-1}" class="profile-category category-${c.key}" data-profile-tab="${c.key}"><span aria-hidden="true">${['⚙','!','↻','✓'][i]}</span>${esc(c.title)}</button>`).join('')}</nav>${profile.categories.map((c,i)=>`<section id="panel-${c.key}" role="tabpanel" aria-labelledby="tab-${c.key}" ${i?'hidden':''} class="profile-panel">${i===0?profile.technical.filter(g=>g.rows.length).map((g,j)=>technicalGroup(g,j,rowsHtml)).join(''):`<div class="catalog-card">${c.entries.length?c.entries.map(e=>`<p>${esc(e.text)}</p><p>${e.sources.map(s=>`<a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(l('source'))} ↗</a>`).join(' · ')}</p>`).join(''):`<p>${esc(categoryEmpty(c.key))}</p>`}</div>`}</section>`).join('')}${usTech?.enabled()?'<div id="us-tech-mount"></div>':''}<details class="catalog-card"><summary>${esc(l('sources'))}</summary><p><a href="${esc(current.source_url)}" target="_blank" rel="noopener noreferrer">${esc(l('source'))} ↗</a></p><p>${esc(current.published_at?.slice(0,10)||'')}</p></details><div class="catalog-actions">${current.preview?'':btn('save','save',id,'primary full')}${btn('inspect','check',id,'secondary full')}${current.preview?'':btn('compare','compare','','secondary full')}</div>`);
    if(usTech?.enabled())void usTech.mount(root.querySelector('#us-tech-mount'),id,valid);

  }
  async function compare() {
    const valid=guardView();
    if(basket.length<2) {show(heading('compareTitle','emptyBasket')+basket.map(id=>box(`<p>${esc(names[id]||l('selected'))}</p>${btn('remove','remove',id)}`)).join('')+btn('catalog','browse','','primary full')+btn('savedCompare','saved-compare','','secondary full'),'compare');return;}
    wait(); compareData=await api('/knowledge/compare',{method:'POST',body:JSON.stringify({variant_ids:basket,language:state.language==='az'?'az':'ru',scenarios:basket.map(id=>({months:filters.ownership_months||24,monthly_km:filters.monthly_km||0,...scenarios[id]}))})});
    const comparedFact=(v,k)=>{
      const fact=v.facts[k]; if(!fact)return '—';
      const context=Object.fromEntries(Object.entries(v.facts).map(([name,item])=>[name,item?.value]));
      const localized=localizeTechnicalValue(k,fact.value,state.language,context);
      return localized || (['engine_description','transmission_description','drivetrain','fuel','powertrain','body','transmission_family'].includes(k)?'—':fact.display||'—');
    };
    if(!valid())return;show(heading('compareTitle')+box(`<h2>${esc(l('differences'))}</h2><p>${esc(compareData.verdict)}</p>`)+`<div class="comparison-grid">${compareData.members.map(v=>`<article class="catalog-card compare-member">${v.asset.url?`<img class="compare-image" src="${esc(assetUrl(v.asset.url))}" alt="${esc(v.make+' '+v.model)}" loading="lazy">`:emptyImage()}${attribution(v)}<h2>${esc(v.make+' '+v.model)}</h2><p>${v.year} · ${esc(localizeConfiguration(v.facts,state.language))}</p>${btn('remove','remove',v.id,'text-button')}<dl>${compareData.differences.map(k=>`<div><dt>${esc(v.facts[k]?.label||compareData.members.find(m=>m.facts[k])?.facts[k]?.label||missingLabel(k))}</dt><dd>${esc(comparedFact(v,k))} ${esc(v.facts[k]?.unit||'')}</dd></div>`).join('')}</dl><div class="cost-summary"><h3>${esc(l('scenario'))} · ${v.costs.months} ${esc(l('monthUnit'))}</h3><p>${v.costs.total?`<strong>${v.costs.total} AZN</strong>`:esc(l('unknownTotal'))}</p><dl>${Object.entries(v.costs.components).map(([k,val])=>`<div><dt>${esc(l(k==='maintenance'?'maintenanceCost':k==='other'?'otherCost':k))}</dt><dd>${val===null?'—':esc(val)+' AZN'}</dd></div>`).join('')}<div><dt>${esc(l('knownSubtotal'))}</dt><dd>${esc(v.costs.known_subtotal??'—')} AZN</dd></div><div><dt>${esc(l('purchase'))}</dt><dd>${v.costs.purchase_separate||'—'}</dd></div></dl></div><details><summary>${esc(l('scenario'))}</summary>${costForm(v.id)}</details>${btn('open','vehicle',v.id,'secondary full')}</article>`).join('')}</div>${note('costHelp')}${btn('save','save-compare','','primary full')}${btn('catalog','browse','','secondary full')}${btn('savedCompare','saved-compare','','secondary full')}`, 'compare');
    const host=document.createElement('section');root.querySelector('.comparison-grid').before(host);mountOwnership(host,compareData.members,{language:state.language,esc,ensureSession,go});
  }
  function costForm(id) {const s=scenarios[id]||{};return `<form class="cost-form" data-id="${id}">${[['purchase_price','purchase'],['resale_price','resalePrice'],['fuel_price','fuelPrice'],['electricity_price','electricityPrice'],['maintenance','maintenance'],['repair_reserve','repairReserve'],['other_costs','otherCosts']].map(([k,label])=>number(k,label,s[k],'min="0" step="0.01"')).join('')}<label>${esc(l('priceDate'))}<input type="date" name="price_date" value="${esc(s.price_date||'')}"></label><label>${esc(l('priceSource'))}<input name="price_source" maxlength="1000" value="${esc(s.price_source||'')}"></label><button class="button primary full">${esc(l('calculate'))}</button></form>`;}
  function check() {show(heading('check','checkSub')+box(`<span class="mode-number">VIN / URL</span><h2>${esc(l('vinListing'))}</h2>${btn('next','vin','','primary full')}`)+box(`<h2>${esc(l('plate'))}</h2><form id="plate-form">${select('country','country',['AZ','US','CA','DE','KR','JP','CN','OTHER'].map(k=>[k,k==='OTHER'?'other':k]),'AZ')}<label>${esc(l('plate'))}<input name="plate" required maxlength="24" autocomplete="off" placeholder="10-AA-123"></label><button class="button secondary full">${esc(l('checkCta'))}</button></form><p id="plate-result" role="status"></p>`)+btn('manual','manual','','secondary full'), 'check');}
  async function resolver() {show(heading('resolve','resolverHelp')+`<form id="resolver-form" class="catalog-card"><div class="form-pair"><label>${esc(l('make'))}<input name="make" required></label><label>${esc(l('model'))}<input name="model" required></label>${number('year','year','','min="2012" max="2100"')}${number('engine','displacement','','step="0.1"')}</div>${select('market','market',[['US','US']],'US')}<button class="button primary full">${esc(l('resolve'))}</button></form><div id="resolver-result"></div>`);}
  async function loadCatalogPairs() {
    if(catalogPairs !== null)return catalogPairs;
    const data = await api(`/knowledge/search?language=${state.language==='az'?'az':'ru'}`,{method:'POST',body:JSON.stringify({...defaults(),sort:'make',limit:100})});
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
    const label=state.language==='az'?'Kataloqdakı iki versiyanı müqayisə edin':'Сравните две версии из каталога';
    return `<article class="battle-card catalog-pair-card"><div class="battle-visual" aria-hidden="true"><span>↔</span></div><h3>${esc(title(first))}<br><span class="catalog-pair-vs">vs</span> ${esc(title(second))}</h3><p>${esc(label)}</p><button class="text-button" data-k="catalog-pair-compare" data-ids="${esc(first.id+','+second.id)}">${esc(l('personalCompare'))} →</button></article>`;
  }
  async function battles() {const valid=guardView();wait();const pairs=await loadCatalogPairs();if(!valid())return;show(heading('battles','battlesSub')+`<div class="battle-list">${pairs.length?pairs.map(catalogPairCard).join(''):box(`<h2>${esc(l('noEditorial'))}</h2><p>${esc(l('noEditorialSub'))}</p>`)}</div>${btn('personalCompare','compare','','primary full')}`, 'compare');}
  function profile() {const user=sessionUser();show(heading('account','publicBrowse')+btn(largeText?'normalText':'largeText','text-size','','secondary full')+(user?box(`<p>${esc(user.email.startsWith('demo-')?l('localPreview'):user.email)}</p>${btn('reports','reports','','primary full')}${user.is_admin?btn('editor','admin','','secondary full'):''}${btn('logout','logout','','secondary full')}`):`<form id="account-form" class="catalog-card"><label>${esc(l('email'))}<input name="email" type="email" required autocomplete="email"></label><label>${esc(l('password'))}<input name="password" type="password" required minlength="10" autocomplete="current-password"></label><button class="button primary full" name="mode" value="login">${esc(l('login'))}</button><button class="button secondary full" name="mode" value="register">${esc(l('register'))}</button></form>`));}
  async function researchStatus(id){const valid=guardView();wait();const job=await api('/knowledge/research/'+encodeURIComponent(id));if(!valid())return;show(heading('research')+box(`<h2 role="status">${esc(l(job.state))}</h2><p>${esc(l('researchReview'))}</p><p>${esc(l('calls'))}: ${job.calls}</p>${btn('refresh','research-refresh',id)}${['QUEUED','RUNNING'].includes(job.state)?btn('cancel','research-cancel',id):job.state==='FAILED'&&job.attempts<2?btn('retry','research-retry',id):''}`));}
  async function admin() {const valid=guardView();wait();const d=await api('/knowledge/admin');if(!valid())return;show(heading('adminTitle')+box(`<h2>${esc(l('coverage'))}</h2><dl>${Object.entries(d.coverage).filter(([,v])=>typeof v==='number').map(([k,v])=>`<div><dt>${esc(k)}</dt><dd>${v}</dd></div>`).join('')}</dl>${!d.worker_enabled?note('workerOff'):''}`)+box(`<h2>${esc(l('sourceRegistry'))}</h2>${d.sources.map(s=>`<details><summary>${esc(s.title)} · ${esc(s.state)}</summary><p>${esc(s.limitations||'')}</p><p>${esc(l(s.commercial_reuse?'rightsReviewed':'rightsPending'))}</p><button class="button secondary" data-k="source-toggle" data-id="${esc(s.id)}" data-paused="${s.paused}">${esc(l(s.paused?'resume':'pause'))}</button></details>`).join('')}`)+box(`<h2>${esc(l('imports'))}</h2><form id="manifest-form"><label>${esc(l('manifest'))}<textarea name="manifest" rows="8" required spellcheck="false"></textarea></label><button class="button primary full">${esc(l('enqueue'))}</button></form><form id="document-form"><label>${esc(l('sourceId'))}<input name="source_id" required></label><label>${esc(l('document'))}<input name="document" type="file" required accept=".json,.csv,.pdf,.zip,.txt"></label><button class="button secondary full">${esc(l('document'))}</button><output id="document-output"></output></form>${d.jobs.map(j=>`<details class="admin-job"><summary>${esc(j.source_id)} · ${esc(j.state)} · ${j.cursor}</summary><p>${esc(j.id)}</p><pre>${esc(JSON.stringify(j.metrics,null,2))}</pre><label>${esc(l('note'))}<textarea class="review-note" minlength="10" required></textarea></label><div class="filter-chips">${['details',...(j.state==='STAGED'?['approve','reject']:j.state==='APPROVED'?['publish']:j.state==='FAILED'?['retry']:['cancel'])].map(a=>`<button class="button secondary" data-k="job" data-id="${j.id}" data-job-action="${a}">${esc(l(a))}</button>`).join('')}</div><pre class="job-detail"></pre></details>`).join('')}`)+box(`<h2>${esc(l('assets'))}</h2>${d.assets.map(a=>`<p>${esc(a.id)} · ${esc(a.state)}</p>`).join('')||'0'}`)+editorTools(d,l,esc));}

  async function action(target) {
    const a=target.dataset.k, id=target.dataset.id;
    if(a==='text-size'){largeText=!largeText;document.documentElement.classList.toggle('large-text',largeText);save();profile();return;}
    if(a==='research'){await ensureSession();const job=await api('/knowledge/research',{method:'POST',body:JSON.stringify({vehicle:{make:current.make,model:current.model,year:current.year,market:current.market},language:state.language==='az'?'az':'ru'})});go('/catalog-research/'+job.id);return;}
    if(a==='research-refresh'){await researchStatus(id);return;}
    if(a==='research-cancel'||a==='research-retry'){await api('/knowledge/research/'+id+'/control',{method:'POST',body:JSON.stringify({action:a==='research-cancel'?'cancel':'retry',note:'Owner requested action through buyer interface'})});await researchStatus(id);return;}
    if(a==='chip'){const form=root.querySelector('#catalog-wizard');if(form)readFilters(form);const key=target.dataset.field,value=target.dataset.value;if(target.dataset.multi==='true'){const arr=filters[key]||[];if(arr.includes(value))filters[key]=arr.filter(x=>x!==value);else {if(key==='priorities'&&arr.length===3){showToast(l('max3'));return;}filters[key]=[...arr,value];}}else filters[key]=value;save();await wizard();return;}
    if(a==='add-make'||a==='add-model'){const input=root.querySelector(a==='add-make'?'#make-query':'#model-query'),key=a==='add-make'?'makes':'models';if(input.value.trim()){readFilters(root.querySelector('#catalog-wizard'));filters[key]=[...new Set([...filters[key],input.value.trim()])];save();await wizard();}return;}
    if(a==='reset'){filters=defaults();step=1;save();await wizard();return;}
    if(a==='wizard'){step=1;go('/pick');return;} if(a==='step-back'){readFilters(root.querySelector('#catalog-wizard'));step=1;await wizard();return;}
    if(a==='check-listing'){go('/check/turbo');return;}
    if(a==='browse'){filters={...defaults(),market_preference:'ANY'};save();go('/catalog-results');return;}
    if(a==='search'){filters.query=root.querySelector('#catalog-search').value;filters.offset=0;save();await results();return;}
    if(a==='more'){filters.offset=(filters.offset||0)+20;save();await results();window.scrollTo(0,0);return;}
    if(a==='basket'){if(basket.includes(id))basket=basket.filter(x=>x!==id);else {if(basket.length===3){showToast(l('max3'));return;}basket.push(id);}save();target.textContent=l(basket.includes(id)?'selected':'addCompare');target.classList.toggle('selected',basket.includes(id));root.querySelector('.catalog-sticky span')?.replaceChildren(`${basket.length} / 3`);return;}
    if(a==='remove'){basket=basket.filter(x=>x!==id);save();await compare();return;}
    if(a==='save'){if(!sessionUser()&&!state.meta?.developer?.enabled){go('/profile');return;}await ensureSession();const r=await api(`/knowledge/vehicles/${id}/save`,{method:'POST',body:JSON.stringify({language:state.language==='az'?'az':'ru',preferences:filters})});showToast(l('saved'));go('/buyer-report/'+r.id);return;}
    if(a==='save-compare'){if(!sessionUser()&&!state.meta?.developer?.enabled){go('/profile');return;}await ensureSession();const r=await api('/knowledge/compare/save',{method:'POST',body:JSON.stringify({variant_ids:basket,language:state.language==='az'?'az':'ru',scenarios:basket.map(id=>({months:filters.ownership_months||24,monthly_km:filters.monthly_km||0,...scenarios[id]}))})});go('/buyer-report/'+r.id);return;}
    if(a==='favorite'){await ensureSession();await api('/knowledge/favorites/'+id,{method:'PUT'});showToast(l('saved'));return;}
    if(a==='only-favorites'){onlyFavorites=!onlyFavorites;await battles();return;}
    if(a==='topic'){topic=id;await battles();return;}
    if(a==='catalog-pair-compare'){const ids=target.dataset.ids.split(',').filter(Boolean).slice(0,2);if(ids.length!==2)return;basket=ids;save();go('/compare');return;}
    if(a==='logout'){clearSession();profile();return;}
    if(a==='job'){const parent=target.closest('.admin-job');if(target.dataset.jobAction==='details'){const d=await api('/knowledge/admin/imports/'+id);parent.querySelector('.job-detail').textContent=JSON.stringify(d,null,2);return;}const note=parent.querySelector('.review-note').value;if(note.length<10){parent.querySelector('.review-note').reportValidity();return;}await api(`/knowledge/admin/imports/${id}/review`,{method:'POST',body:JSON.stringify({action:target.dataset.jobAction,note})});await admin();return;}
    if(a==='source-toggle'){await api('/knowledge/admin/sources/'+id,{method:'PATCH',body:JSON.stringify({paused:target.dataset.paused!=='true',note:'Operator toggled source acquisition/publication in protected editorial UI'})});await admin();return;}
    const routes={home:'/home',mode:'/choose',results:'/catalog-results',vehicle:'/catalog-car/'+id,compare:'/compare',check:'/check',vin:'/vin',manual:'/manual',battles:'/battles',publication:'/battle/'+id,resolve:'/resolve',reports:'/reports',admin:'/editor','saved-compare':'/saved-compare'};if(routes[a])go(routes[a]);
  }
  root.addEventListener('click',e=>{const target=e.target.closest('[data-k]');if(!target||target.disabled)return;e.preventDefault();target.disabled=true;void action(target).catch(fail).finally(()=>{target.disabled=false;});});
  root.addEventListener('change',e=>{if(e.target.id==='catalog-sort'){filters.sort=e.target.value;filters.offset=0;save();void results().catch(fail);}});
  root.addEventListener('submit',e=>{const form=e.target;if(!['catalog-wizard','plate-form','resolver-form','account-form','manifest-form','document-form'].includes(form.id)&&!form.matches('.cost-form'))return;e.preventDefault();const submit=e.submitter;if(submit)submit.disabled=true;void(async()=>{
    if(form.id==='catalog-wizard'){readFilters(form);if(step===1){step=2;await wizard();window.scrollTo(0,0);}else{filters.offset=0;save();go('/catalog-results');}}
    else if(form.id==='plate-form'){root.querySelector('#plate-result').textContent=l('plateUnavailable');}
    else if(form.matches('.cost-form')){scenarios[form.dataset.id]=Object.fromEntries([...new FormData(form)].map(([k,v])=>[k,v===''?null:v]));save();await compare();}
    else if(form.id==='resolver-form'){const d=Object.fromEntries([...new FormData(form)].filter(([,v])=>v!==''));if(d.year)d.year=Number(d.year);d.catalog_scope=CONSUMER_CATALOG_SCOPE;d.language=state.language==='az'?'az':'ru';const r=await api('/knowledge/resolve',{method:'POST',body:JSON.stringify(d)});root.querySelector('#resolver-result').innerHTML=box(`<h2>${esc(l(r.status))}</h2><p>${esc(l('resolverHelp'))}</p>`)+(r.suggestions?.length?box(`<h3>${esc(l('suggestions'))}</h3>${r.suggestions.map(s=>`<p>${esc(s.make+' '+s.model)}</p>`).join('')}`):'')+r.candidates.map(vehicleCard).join('')+(r.needs_confirmation?.length?box(`<h3>${esc(l('needs'))}</h3>`)+r.needs_confirmation.map(vehicleCard).join(''):'')+btn('manual','manual','','secondary full');}
    else if(form.id==='account-form'){const d=Object.fromEntries(new FormData(form));const mode=submit?.value||'login';if(mode==='register'){d.preferred_language=state.language==='az'?'az':'ru';d.country_code='AZ';}const r=await api('/auth/'+mode,{method:'POST',body:JSON.stringify(d)});localStorage.setItem('autoexpert.demo.token',r.access_token);localStorage.setItem('autoexpert.demo.user',JSON.stringify(r.user));profile();}
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
      if(basket.length>=3)return false;
      basket.push(id);if(title)names[id]=title;save();return true;
    },
    async route(name,id){const routes={home,choose:mode,pick:wizard,'catalog-results':results,'catalog-car':vehicle,'catalog-research':researchStatus,compare,check,resolve:resolver,battles,battle:battles,profile,editor:admin};if(!routes[name])return false;++viewRequest;await routes[name](id);return true;}
  };
}
