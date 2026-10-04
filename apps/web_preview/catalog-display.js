import {EN, pickText} from './en-text.js?v=0.10.0';
// Consumer wording is derived from the published structured facts. Source
// descriptions remain available to editors; unsupported English prose is not
// presented as a translated technical specification.
const labels = {
  GASOLINE:['Бензин','Benzin'], DIESEL:['Дизель','Dizel'], ELECTRICITY:['Электроэнергия','Elektrik enerjisi'],
  ICE:['ДВС','Daxiliyanma mühərriki'], BEV:['Электромобиль','Elektromobil'], HEV:['Гибрид','Hibrid'], PHEV:['Заряжаемый гибрид','Şarj olunan hibrid'],
  FWD:['Передний привод','Ön ötürücü'], RWD:['Задний привод','Arxa ötürücü'], AWD:['Полный привод','Tam ötürücü'], '4WD':['Полный привод 4WD','Tam ötürücü 4WD'],
  AT:['Классический автомат AT','Klassik avtomat AT'], CVT:['Вариатор CVT','Variator CVT'], ECVT:['Трансмиссия e-CVT','e-CVT transmissiyası'], DCT:['Робот DCT','Robot DCT'],
  MANUAL:['Механика','Mexaniki'], SINGLE_SPEED:['Одноступенчатый редуктор','Birpilləli reduktor'], AUTOMATIC_UNSPECIFIED:['Автомат, тип не уточнён','Avtomat, növü dəqiqləşdirilməyib'],
  VARIABLE_UNSPECIFIED:['Бесступенчатая, тип не уточнён','Pilləsiz, növü dəqiqləşdirilməyib'], AMT_UNSPECIFIED:['Автоматизированная, тип не уточнён','Avtomatlaşdırılmış, növü dəqiqləşdirilməyib'],
  SEDAN:['Седан','Sedan'], SUV:['Внедорожник','Yolsuzluq avtomobili'], CROSSOVER:['Кроссовер','Krossover'], HATCHBACK:['Хетчбэк','Hetçbek'], WAGON:['Универсал','Universal'], COUPE:['Купе','Kupe'], MINIVAN:['Минивэн','Miniven'], PICKUP:['Пикап','Pikap'],
};
const label = (code, language) => (pair => pair ? pickText(language, pair[0], pair[1], pair[2]) : '')(labels[String(code || '').trim().toUpperCase()]);
const lit = (language, ru, az, en) => pickText(language, ru, az, en);
const decimal = (value) => String(value).replace('.', ',');
const contextValue = (context, key) => {
  const value = context?.[key];
  return typeof value === 'object' && value !== null ? value.value : value;
};

function engineDescription(source, language, context) {
  const raw=String(source || '');
  const volume=raw.match(/\b(\d+(?:[.,]\d+)?)\s*(?:l|liters?|litres?)\b/i)?.[1]
    || String(contextValue(context,'engine_displacement') || '').match(/\b\d+(?:[.,]\d+)?\b/)?.[0];
  const parts=[];
  if(volume)parts.push(`${decimal(volume)} ${lit(language,'л','l')}`);
  const inline=raw.match(/\b(?:inline|in-line|i|l)[- ]?([3-8])\b/i);
  const vee=raw.match(/\bV[- ]?([3-9]|10|12)\b/i);
  const boxer=raw.match(/\b(?:flat|boxer)[- ]?([3-8])\b/i);
  if(inline)parts.push(lit(language,`рядный ${inline[1]}-цилиндровый`,`sıralı ${inline[1]} silindrli`,`inline ${inline[1]}-cylinder`));
  else if(vee)parts.push(`V${vee[1]}`);
  else if(boxer)parts.push(lit(language,`оппозитный ${boxer[1]}-цилиндровый`,`oppozit ${boxer[1]} silindrli`,`flat ${boxer[1]}-cylinder`));
  const fuel=label(contextValue(context,'fuel') || (/(?:gasoline|petrol)/i.test(raw)?'GASOLINE':/diesel/i.test(raw)?'DIESEL':''),language);
  if(fuel)parts.push(fuel.toLowerCase());
  if(/\bturbo(?:charged)?\b/i.test(raw))parts.push(lit(language,'турбо','turbo'));
  if(/\bsupercharged\b/i.test(raw))parts.push(lit(language,'механический нагнетатель','mexaniki kompressor'));
  for(const code of raw.match(/\b(?:D-4S|Gamma[- ]?II|T-GDI|GDI|MPI|TSI|TFSI|EcoBoost)\b/gi) || [])
    if(!parts.includes(code))parts.push(code);
  if(!parts.length)return label(contextValue(context,'powertrain'),language);
  return parts.join(' · ');
}

function transmissionDescription(source, language, context) {
  const raw=String(source || '');
  const code=label(raw,language);
  if(code)return code;
  const speed=raw.match(/\b(\d{1,2})[- ]?(?:speed|spd)\b/i)?.[1]
    || String(contextValue(context,'gears') || '').match(/^\d{1,2}$/)?.[0];
  const count=speed?lit(language,`${speed} передач`,`${speed} pillə`):'';
  const family=String(contextValue(context,'transmission_family') || '').toUpperCase();
  const familyCode=family.match(/\b(?:ECVT|CVT|DCT|AT|MANUAL|SINGLE_SPEED|AUTOMATIC_UNSPECIFIED)\b/)?.[0] || '';
  let construction='';
  if(/\be[- ]?cvt\b/i.test(raw) || familyCode==='ECVT')construction=lit(language,'трансмиссия e-CVT','e-CVT transmissiyası');
  else if(/continuously variable|\b(?:CVT|IVT)\b/i.test(raw) || familyCode==='CVT')construction=lit(language,'бесступенчатая трансмиссия','pilləsiz transmissiya');
  else if(/dual[- ]clutch|\b(?:DCT|DSG)\b/i.test(raw) || familyCode==='DCT')construction=lit(language,'робот с двойным сцеплением','iki muftalı robot');
  else if(/single[- ]speed|one[- ]speed|1[- ]speed|fixed gear|reduction gear/i.test(raw) || familyCode==='SINGLE_SPEED')construction=lit(language,'одноступенчатый редуктор','birpilləli reduktor');
  else if(/torque[- ]converter/i.test(raw) || familyCode==='AT')construction=lit(language,'классический автомат','klassik avtomat');
  else if(/\bmanual\b/i.test(raw) || familyCode==='MANUAL')construction=lit(language,'механическая коробка','mexaniki sürətlər qutusu');
  else if(/\bautomatic\b/i.test(raw) || familyCode==='AUTOMATIC_UNSPECIFIED')construction=lit(language,'автомат, тип не уточнён','avtomat, növü dəqiqləşdirilməyib');
  else if(family)construction=label(family,language);
  if(!construction)return '';
  // A source gearbox code such as S6 is retained verbatim, without guessing
  // that it proves an exact construction or a gear count.
  const sourceCode=raw.match(/\(([A-Z0-9-]{2,12})\)/)?.[1];
  return [count,construction,sourceCode?`(${sourceCode})`:''].filter(Boolean).join(' ');
}

export function localizeTechnicalValue(key, value, language, context={}) {
  const raw=String(value ?? '').trim();
  if(!raw)return '';
  const coded=label(raw,language);
  if(coded)return coded;
  if(key==='engine_description')return engineDescription(raw,language,context);
  if(key==='transmission_description')return transmissionDescription(raw,language,context);
  if(key==='drivetrain') {
    if(/^(?:front|front[- ]wheel drive|передний(?: привод)?|ön(?: ötürücü)?)$/i.test(raw))return label('FWD',language);
    if(/^(?:rear|rear[- ]wheel drive|задний(?: привод)?|arxa(?: ötürücü)?)$/i.test(raw))return label('RWD',language);
    if(/^(?:all[- ]wheel drive|four[- ]wheel drive|полный(?: привод)?|tam(?: ötürücü)?)$/i.test(raw))return label('AWD',language);
    return '';
  }
  if(key==='fuel' || key==='fuel_grade') {
    if(/^(?:бензин|benzin|дизель|dizel|электроэнергия|elektrik enerjisi)$/i.test(raw))return raw;
    if(/gasoline|petrol/i.test(raw))return [label('GASOLINE',language),/premium/i.test(raw)?'Premium':/regular/i.test(raw)?'Regular':''].filter(Boolean).join(' · ');
    if(/diesel/i.test(raw))return label('DIESEL',language);
    if(/electric/i.test(raw))return label('ELECTRICITY',language);
  }
  if(key==='motor_description')return /electric|электр|elektr/i.test(raw)?lit(language,'Электропривод','Elektrik ötürücüsü'):'';
  if(key==='engine_family') {
    const inline=raw.match(/\b(?:inline|in-line)[- ]?([3-8])\b/i);
    return inline?lit(language,`Рядный ${inline[1]}-цилиндровый`,`Sıralı ${inline[1]} silindrli`,`Inline ${inline[1]}-cylinder`):raw;
  }
  if(key==='aspiration') {
    if(/[А-Яа-яƏəİıÖöÜüÇçŞşĞğ]/u.test(raw))return raw;
    if(/turbo/i.test(raw))return lit(language,'Турбо','Turbo');
    if(/naturally aspirated/i.test(raw))return lit(language,'Без наддува','Turbosuz');
    if(/supercharged/i.test(raw))return lit(language,'Механический нагнетатель','Mexaniki kompressor');
    return '';
  }
  if(key==='powertrain' || key==='transmission_family' || key==='body') {
    if(/[А-Яа-яƏəİıÖöÜüÇçŞşĞğ]/u.test(raw) || (key==='transmission_family' && /\b(?:AT|CVT|DCT|DSG|e-CVT)\b/i.test(raw)))return raw;
    return '';
  }
  if(key==='cylinders') {
    const inline=raw.match(/\b(?:inline|in-line)[- ]?([3-8])\b/i);
    return inline?lit(language,`Рядный ${inline[1]}-цилиндровый`,`Sıralı ${inline[1]} silindrli`,`Inline ${inline[1]}-cylinder`):raw;
  }
  if(key==='engine_displacement') {
    const match=raw.match(/^(\d+(?:[.,]\d+)?)\s*(?:L|л|l)?$/i);
    return match?`${decimal(match[1])} ${lit(language,'л','l')}`:raw;
  }
  return raw;
}

export function localizeProfile(profile, language) {
  const context=Object.fromEntries((profile.technical || []).flatMap(group => group.rows || []).map(row=>[row.key,row.value]));
  const localize=row=>({...row,value:localizeTechnicalValue(row.key,row.value,language,context)});
  return {...profile,
    summary:(profile.summary || []).map(localize).filter(row=>row.value),
    technical:(profile.technical || []).map(group=>({...group,rows:(group.rows || []).map(localize).filter(row=>row.value)})),
  };
}

export function localizeConfiguration(facts, language) {
  const context=Object.fromEntries(Object.entries(facts || {}).map(([key,fact])=>[key,fact?.value]));
  const engine=localizeTechnicalValue('engine_description',context.engine_description || context.motor_description,language,context)
    || localizeTechnicalValue('engine_displacement',context.engine_displacement,language,context)
    || localizeTechnicalValue('powertrain',context.powertrain,language,context);
  const transmission=localizeTechnicalValue('transmission_description',context.transmission_description,language,context)
    || localizeTechnicalValue('transmission_family',context.transmission_family,language,context);
  const drive=localizeTechnicalValue('drivetrain',context.drivetrain,language,context);
  return [engine,transmission,drive].filter(Boolean).join(' · ');
}
