import {api} from './api.js?v=0.8.1';

// Shared by the existing dossier and comparison. All arithmetic stays on the backend.
export function mountOwnership(host, members, {language, esc, ensureSession, go}) {
  const az = language === 'az';
  const t = (ru, a) => az ? a : ru;
  const key = 'autoexpert.verified.ownership.v1';
  let stored = {}; try {stored = JSON.parse(localStorage.getItem(key) || '{}');} catch {}
  const common = stored.common || {};
  const cars = stored.cars || {};
  const localDay = new Date(Date.now() - new Date().getTimezoneOffset()*60000).toISOString().slice(0,10);
  const input = (name, ru, a, value, type='number', attrs='min="0" step="any"') => `<label>${esc(t(ru,a))}<input name="${name}" type="${type}" value="${esc(value??'')}" ${attrs}></label>`;
  const select = (name, ru, a, value, opts) => `<label>${esc(t(ru,a))}<select name="${name}">${opts.map(([v,r,z])=>`<option value="${v}" ${String(value)===v?'selected':''}>${esc(t(r,z))}</option>`).join('')}</select></label>`;
  const labels = {
    energy:['Топливо / электричество','Yanacaq / elektrik'],scheduled_service:['Плановое ТО','Planlı xidmət'],
    operating_known_subtotal:['Рассчитанная часть эксплуатации','İstismarın hesablanmış hissəsi'],
    operating_total:['Полная эксплуатация','Tam istismar'],purchase_separate:['Цена покупки отдельно','Alış qiyməti ayrıca'],
    depreciation:['Покупка − перепродажа · сценарий','Alış − təkrar satış · ssenari'],
    repair_reserve_separate:['Резерв отдельно от расходов','Xərclərdən ayrı ehtiyat'],ownership_total:['Полная стоимость владения','Tam istifadə xərci']
  };
  const gapLabels = {
    MAINTENANCE_SCHEDULE_NOT_RESEARCHED:['Применимый регламент ТО ещё не исследован.','Uyğun xidmət cədvəli hələ araşdırılmayıb.'],
    MAINTENANCE_COVERAGE_INCOMPLETE:['Покрытие ТО неполное: итог нельзя считать полной стоимостью.','Xidmət əhatəsi natamamdır: nəticə tam xərc deyil.'],
    FUEL_GRADE_PRICE_OR_CONSUMPTION_REQUIRED:['Не хватает марки топлива, её цены или применимого расхода.','Yanacaq markası, qiyməti və ya uyğun sərfiyyat çatışmır.'],
    POWERTRAIN_COST_MODEL_UNSUPPORTED:['Для этой силовой установки модель расходов пока не поддерживается.','Bu güc qurğusu üçün xərc modeli hələ dəstəklənmir.'],
    PHEV_MODE_SHARE_REQUIRED:['Уточните силовую установку и долю электрического пробега PHEV.','Güc qurğusunu və PHEV-in elektriklə məsafə payını dəqiqləşdirin.'],
    ELECTRIC_MODE_GASOLINE_COMPONENT_REQUIRED:['Неизвестен бензин в электрическом режиме PHEV.','PHEV-in elektrik rejimində benzin sərfiyyatı məlum deyil.'],
    ELECTRICITY_CONSUMPTION_SIDE_OR_LOSS_REQUIRED:['Укажите сторону измерения расхода и потери, если они ещё не учтены.','Sərfiyyatın ölçü tərəfini və daxil edilməmiş itkiləri göstərin.'],
    CHARGING_TARIFF_OR_HOUSEHOLD_BASE_REQUIRED:['Нет тарифа зарядки или бытового потребления без автомобиля.','Şarj tarifi və ya avtomobilsiz məişət sərfiyyatı yoxdur.'],
    HOME_TARIFF_CHANGE_BILLING_ALLOCATION_REQUIRED:['Тариф сменился внутри расчётного месяца; нужен порядок распределения по счётчику.','Tarif hesab ayı daxilində dəyişib; sayğac üzrə bölgü qaydası lazımdır.'],
    RESALE_OR_PURCHASE_ASSUMPTION_REQUIRED:['Нет сценария покупки и перепродажи.','Alış və təkrar satış ssenarisi yoxdur.'],
    OTHER_COST_SCOPE_UNSPECIFIED:['Прочие статьи расходов не заданы.','Digər xərc maddələri göstərilməyib.'],
    HISTORY_REQUIRED:['Нужна история обслуживания.','Xidmət tarixçəsi lazımdır.'],
    NEEDS_INSPECTION:['Решение об операции требует осмотра.','Əməliyyat barədə qərar üçün baxış lazımdır.'],
    EXACT_FITMENT_PRICE_REQUIRED:['Нет цены детали с подтверждённой совместимостью.','Uyğunluğu təsdiqlənmiş hissənin qiyməti yoxdur.'],
    LABOR_QUOTE_REQUIRED:['Нет применимой цены работы.','Uyğun iş qiyməti yoxdur.'],
    CONFLICTING_ENERGY_PRICES:['Конфликт цен: выберите применимого поставщика.','Qiymətlər ziddiyyətlidir: uyğun təchizatçını seçin.'],
    CONFLICTING_MAINTENANCE_SCHEDULE:['Конфликт регламентов: требуется редакционная проверка.','Xidmət cədvəlləri ziddiyyətlidir: redaktor yoxlaması lazımdır.'],
    OVERLAPPING_LABOR_REQUIRES_COMBINED_QUOTE:['Пересекающиеся работы требуют общего предложения СТО.','Üst-üstə düşən işlər üçün servisin birgə təklifi lazımdır.']
  };
  const gap = code => {const [base,detail] = code.split(':'); return t(...(gapLabels[base] || ['Не хватает подтверждённых данных.','Təsdiqlənmiş məlumat çatışmır.'])) + (detail ? ` (${detail})` : '');};
  host.className = 'catalog-card ownership-panel';
  host.innerHTML = `<h2>${esc(t('Стоимость владения · источники AZ','İstifadə xərcləri · AZ mənbələri'))}</h2>
    <p>${esc(t('Расчёт использует опубликованные цены. Неизвестная сумма остаётся неизвестной. Укажите свои условия; марку топлива сверьте с руководством.','Hesab dərc edilmiş qiymətlərdən istifadə edir. Naməlum məbləğ naməlum qalır. Şəraitinizi göstərin; yanacaq markasını təlimatla tutuşdurun.'))}</p>
    <form class="verified-ownership-form"><div class="form-pair">
      ${input('start_date','Начало расчёта','Hesabın başlanğıcı',common.start_date||localDay,'date','required')}
      ${input('months','Месяцев','Ay sayı',common.months||24,'number','min="1" max="120" step="1" required')}
      ${input('monthly_km','Пробег в месяц, км','Aylıq məsafə, km',common.monthly_km??1000,'number','min="0" max="30000" required')}
      ${input('region','Регион цен','Qiymət regionu',common.region||'Baku','text','required maxlength="100"')}
    </div>
    ${members.map((v,i)=>{const c=cars[v.id]||{};return `<fieldset class="filter-group"><legend>${esc(v.make+' '+v.model+' · '+v.year+' · '+v.market)}</legend>
      <div class="form-pair">${input(`odo_${i}`,'Текущий пробег, км','Hazırkı yürüş, km',c.current_odometer_km,'number','min="0" max="5000000" step="1" required')}
      ${select(`fuel_${i}`,'Марка топлива · по руководству','Yanacaq markası · təlimata əsasən',c.fuel_energy||'', [['','Не указана','Göstərilməyib'],['AI92','АИ-92','Aİ-92'],['AI95','АИ-95','Aİ-95'],['AI98','АИ-98','Aİ-98'],['DIESEL','Дизель','Dizel']])}${input(`reg_${i}`,'Первая регистрация · если известна','İlk qeydiyyat · məlumdursa',c.first_registration,'date','')}</div><div data-service-inputs="${i}"></div></fieldset>`;}).join('')}
    <details><summary>${esc(t('Условия обслуживания','Xidmət şəraiti'))}</summary><div class="form-pair">${select('schedule','Режим обслуживания','Xidmət rejimi',common.schedule||'NORMAL',[['NORMAL','Обычный','Normal'],['SEVERE','Тяжёлые условия по руководству','Təlimata görə ağır şərait']])}${input('severe_conditions','Коды условий из регламента · через запятую','Cədvəldəki şərait kodları · vergüllə',(common.severe_conditions||[]).join(','),'text','')}</div><label class="check-label"><input type="checkbox" name="initial_service_assumption" ${common.initial_service_assumption?'checked':''}>${esc(t('Сценарий первоначального ТО при неизвестной истории','Tarixçə naməlum olduqda ilkin xidmət ssenarisi'))}</label></details>
    <details><summary>${esc(t('EV / PHEV и домашняя зарядка','EV / PHEV və evdə şarj'))}</summary><div class="form-pair">
      ${input('electric_distance_share','Доля электрического пробега PHEV, 0–1','PHEV elektrik məsafəsi payı, 0–1',common.electric_distance_share,'number','min="0" max="1" step="0.05"')}
      ${input('home_share','Доля домашней зарядки, 0–1','Evdə şarj payı, 0–1',common.home_share??1,'number','min="0" max="1" step="0.05" required')}
      ${input('household_monthly_kwh','Дом без автомобиля, кВт·ч/месяц','Avtomobilsiz ev, kVt·s/ay',common.household_monthly_kwh)}
      ${select('consumption_side','Сторона измерения расхода','Sərfiyyatın ölçü tərəfi',common.consumption_side||'UNKNOWN', [['UNKNOWN','Не уточнена','Dəqiqləşdirilməyib'],['GRID','От сети · потери включены','Şəbəkədən · itkilər daxildir'],['BATTERY','На батарее · потери отдельно','Batareyada · itkilər ayrıca']])}
      ${input('charging_loss_fraction','Потери, 0–0,99 · только для батареи','İtkilər, 0–0,99 · yalnız batareya üçün',common.charging_loss_fraction,'number','min="0" max="0.99" step="0.01"')}
      ${select('public_channel','Общественная зарядка','İctimai şarj',common.public_channel||'PUBLIC_DC',[['PUBLIC_DC','DC','DC'],['PUBLIC_AC','AC','AC']])}
    </div><label class="check-label"><input type="checkbox" name="new_dedicated_meter" ${common.new_dedicated_meter?'checked':''}>${esc(t('Новый отдельный счётчик для автомобиля','Avtomobil üçün yeni ayrıca sayğac'))}</label></details>
    ${members.length===1?`<details><summary>${esc(t('Покупка и другие предположения','Alış və digər fərziyyələr'))}</summary><div class="form-pair">${input('purchase','Цена покупки, AZN','Alış qiyməti, AZN',common.purchase)}${input('resale','Предполагаемая перепродажа, AZN','Təkrar satış fərziyyəsi, AZN',common.resale)}${input('repair_reserve','Резерв отдельно, AZN','Ehtiyat ayrıca, AZN',common.repair_reserve)}${input('other','Другие учтённые расходы, AZN','Digər nəzərə alınmış xərclər, AZN',common.other)}</div></details>`:''}
    <p class="catalog-note">${esc(t('Будущий пробег распределён равномерно; последняя известная цена сохраняется как предположение. Отсутствующие ТО, детали и работа не равны нулю.','Gələcək məsafə bərabər paylanır; son məlum qiymət fərziyyə kimi saxlanır. Çatışmayan xidmət, hissə və iş qiymətləri sıfır deyil.'))}</p>
    <button class="button primary full" type="submit">${esc(t('Рассчитать по источникам','Mənbələr üzrə hesabla'))}</button></form>
    <div class="ownership-output" aria-live="polite"></div>`;
  const form=host.querySelector('form'), output=host.querySelector('.ownership-output');
  let last = null, lastScenario = null;
  const evidenceByMember = [];
  members.forEach(async(v,i)=>{try {
    const rows=await api('/knowledge/ownership/evidence?variant_id='+encodeURIComponent(v.id));
    if(!host.isConnected)return;evidenceByMember[i]=rows;
    const target=host.querySelector(`[data-service-inputs="${i}"]`);
    const ops=[...new Map(rows.filter(r=>r.kind==='MAINTENANCE').map(r=>[r.data.operation,r])).values()];
    const hist=cars[v.id]?.history||[];
    target.innerHTML=`<details><summary>${esc(t('История ТО и предложения','Xidmət tarixçəsi və təkliflər'))}</summary>`+(ops.length?ops.map((r,j)=>{const h=hist.find(h=>h.operation===r.data.operation)||{};return `<fieldset><legend>${esc(r.data.labels[az?'az':'ru'])}</legend><div class="form-pair">${input(`last_date_${i}_${j}`,'Дата последней операции','Son əməliyyat tarixi',h.last_date,'date','')}${input(`last_odo_${i}_${j}`,'Одометр при операции, км','Əməliyyatda yürüş, km',h.last_odometer_km)}</div><label class="check-label"><input name="never_${i}_${j}" type="checkbox" ${h.never_serviced?'checked':''}>${esc(t('Подтверждаю: ещё не выполнялась','Təsdiqləyirəm: hələ edilməyib'))}</label></fieldset>`;}).join(''):`<p>${esc(t('Применимый регламент ещё не опубликован. История не считается нулевой.','Uyğun cədvəl hələ dərc edilməyib. Tarixçə sıfır sayılmır.'))}</p>`)+rows.filter(r=>['PART_PRICE','LABOR'].includes(r.kind)).map(r=>`<label class="check-label"><input name="quote_${i}" type="checkbox" value="${esc(r.id)}">${esc([r.data.seller_id,r.data.part_number||r.data.operation,r.data.region,r.observed_at.slice(0,10)].join(' · '))}</label>`).join('')+`</details>`;
  }catch{const target=host.querySelector(`[data-service-inputs="${i}"]`);if(target)target.textContent=t('Сведения о ТО временно недоступны.','Xidmət məlumatı müvəqqəti əlçatan deyil.');}});

  const sums = r => `<dl>${Object.entries(labels).map(([k,[ru,a]])=>`<div><dt>${esc(t(ru,a))}</dt><dd>${r[k]===null?'—':esc(r[k])+' AZN'}</dd></div>`).join('')}</dl>`;
  function result(r,v) {return `<section class="catalog-card"><h3>${esc(v.make+' '+v.model)}</h3><p class="catalog-notice">${esc(r.status==='COMPLETE'?t('Расчёт по заданным предположениям','Göstərilən fərziyyələr üzrə hesab'):t('Частичный расчёт · полной суммы пока нет','Qismən hesab · tam məbləğ hələ yoxdur'))}</p>${sums(r)}
    <details open><summary>${esc(t('Что ещё не учтено','Nələr nəzərə alınmayıb'))}</summary><ul>${r.missing.map(x=>`<li>${esc(gap(x))}</li>`).join('')}</ul></details>
    <details><summary>${esc(t('По месяцам','Aylar üzrə'))}</summary><dl>${r.monthly.map(m=>`<div><dt>${esc(m.date||String(m.month))}</dt><dd>${m.energy_known==null?'—':esc(m.energy_known)+' AZN'}</dd></div>`).join('')}</dl></details>
    <details><summary>${esc(t('Количество и тариф','Miqdar və tarif'))}</summary><ul>${(r.energy_breakdown||[]).map(x=>`<li>${esc(x.from+' · '+x.energy+' · '+Number(x.quantity).toFixed(2)+' '+x.unit+' × '+(x.unit_price??t('ступени','pillələr'))+' = '+x.amount+' AZN')}</li>`).join('')}</ul></details>
    <details><summary>${esc(t('Календарь ТО','Xidmət təqvimi'))}</summary>${r.operations.length?`<ul>${r.operations.map(o=>`<li>${esc(o.date+' · '+(o.labels[az?'az':'ru']||o.operation))}: ${o.known_subtotal??'—'} AZN</li>`).join('')}</ul>`:`<p>${esc(t('Подтверждённого календаря пока нет.','Təsdiqlənmiş təqvim hələ yoxdur.'))}</p>`}</details>
    <details><summary>${esc(t('Источники сумм','Məbləğlərin mənbələri'))} (${r.evidence.length})</summary>${r.evidence.map(s=>`<p><a href="${esc(s.source_url)}" target="_blank" rel="noopener noreferrer">${esc(s.source_id)} ↗</a> · ${esc(s.effective_from)}</p><p>${esc(s.limitations[az?'az':'ru']||'')}</p><p class="catalog-note">${esc(s.locator)}</p>`).join('')}</details></section>`;}
  form.addEventListener('submit',async e=>{e.preventDefault();const button=form.querySelector('[type=submit]');button.disabled=true;output.textContent=t('Расчёт…','Hesablanır…');try {
    const fields=new FormData(form),d=Object.fromEntries(fields);
    const scenario={start_date:d.start_date,months:Number(d.months),monthly_km:d.monthly_km,region:d.region,current_odometer_km:0,
      schedule:d.schedule,severe_conditions:d.severe_conditions.split(',').map(x=>x.trim()).filter(Boolean),initial_service_assumption:!!d.initial_service_assumption,
      home_share:d.home_share,consumption_side:d.consumption_side,public_channel:d.public_channel,new_dedicated_meter:!!d.new_dedicated_meter};
    for(const k of ['electric_distance_share','household_monthly_kwh','charging_loss_fraction','purchase','resale','repair_reserve','other']) if(d[k]!=='') scenario[k]=d[k]??null;
    const selected=members.map((v,i)=>({variant_id:v.id,current_odometer_km:Number(d[`odo_${i}`]),fuel_energy:d[`fuel_${i}`]||null}));
    scenario.selected_part_prices=[];scenario.selected_labor_quotes=[];
    selected.forEach((c,i)=>{c.first_registration=d[`reg_${i}`]||null;c.history=[];
      const rows=evidenceByMember[i]||[];
      const ops=[...new Map(rows.filter(r=>r.kind==='MAINTENANCE').map(r=>[r.data.operation,r])).values()];
      ops.forEach((r,j)=>{const last_date=d[`last_date_${i}_${j}`]||null,last_odometer_km=d[`last_odo_${i}_${j}`]||null,never_serviced=!!d[`never_${i}_${j}`];if(last_date||last_odometer_km!==null||never_serviced)c.history.push({operation:r.data.operation,last_date,last_odometer_km,never_serviced});});
      for(const id of fields.getAll(`quote_${i}`)){const row=rows.find(r=>r.id===id);if(row)scenario[row.kind==='PART_PRICE'?'selected_part_prices':'selected_labor_quotes'].push(id);}
      cars[c.variant_id]={current_odometer_km:c.current_odometer_km,fuel_energy:c.fuel_energy,first_registration:c.first_registration,history:c.history};
    });
    scenario.selected_part_prices=[...new Set(scenario.selected_part_prices)];scenario.selected_labor_quotes=[...new Set(scenario.selected_labor_quotes)];
    localStorage.setItem(key,JSON.stringify({common:scenario,cars}));
    if(members.length===1){lastScenario={...scenario,...selected[0]};delete lastScenario.variant_id;last=[await api(`/knowledge/vehicles/${members[0].id}/ownership`,{method:'POST',body:JSON.stringify(lastScenario)})];}
    else {const r=await api('/knowledge/ownership/compare',{method:'POST',body:JSON.stringify({scenario,members:selected})});last=r.members.map(x=>x.calculation);lastScenario=scenario;}
    if(!host.isConnected)return;
    output.innerHTML=(members.length>1?`<p class="catalog-notice">${esc(t('Условия пробега и срока одинаковые. При неполном покрытии расходов победитель не определяется. EPA и NRCan — разные испытательные наборы.','Məsafə və müddət şərtləri eynidir. Xərc əhatəsi natamam olduqda qalib müəyyən edilmir. EPA və NRCan fərqli sınaq məlumatlarıdır.'))}</p>`:'')+last.map((r,i)=>result(r,members[i])).join('')+
      `<button type="button" class="button secondary full" data-snapshot>${esc(t('Скачать расчёт и источники · JSON','Hesabı və mənbələri endir · JSON'))}</button>`+
      (members.length===1?`<button type="button" class="button primary full" data-save-ownership>${esc(t('Сохранить в мои отчёты','Hesabatlarımda saxla'))}</button>`:'');
    output.querySelector('[data-snapshot]').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(last,null,2)],{type:'application/json'}));a.download='autoexpert-ownership-snapshot.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
    const saver=output.querySelector('[data-save-ownership]');if(saver)saver.onclick=async()=>{saver.disabled=true;try{await ensureSession();const r=await api(`/knowledge/vehicles/${members[0].id}/ownership/save`,{method:'POST',body:JSON.stringify({language:az?'az':'ru',scenario:lastScenario,expected_scenario_id:last[0].scenario_id})});go('/buyer-report/'+r.id);}catch(error){if(error.status===409){output.insertAdjacentHTML('beforeend',`<p>${esc(t('Источники изменились. Выполните расчёт снова.','Mənbələr dəyişib. Yenidən hesablayın.'))}</p>`);saver.disabled=false;return;}output.insertAdjacentHTML('beforeend',`<p>${esc(t('Войдите в профиль, чтобы сохранить отчёт.','Hesabatı saxlamaq üçün profilə daxil olun.'))}</p>`);saver.disabled=false;}};
  }catch{output.textContent=t('Проверьте введённые значения и доступность локального сервера.','Daxil edilmiş dəyərləri və lokal serverin əlçatanlığını yoxlayın.');}finally{button.disabled=false;}});
}
