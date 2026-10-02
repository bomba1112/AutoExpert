import assert from 'node:assert/strict';
import test from 'node:test';
import {localizeConfiguration, localizeProfile, localizeTechnicalValue} from '../catalog-display.js';

const source = {
  engine_description: '1.6L turbo Gamma-II GDI inline-4',
  engine_displacement: '1.6 L',
  cylinders: '4',
  fuel: 'Gasoline',
  powertrain: 'ICE',
  transmission_description: '8-speed torque-converter automatic',
  transmission_family: 'AT',
  gears: '8',
  drivetrain: 'Front',
};

test('published English source fields render as localized technical facts without losing codes', () => {
  for(const language of ['ru','az']) {
    const facts=Object.fromEntries(Object.entries(source).map(([key,value])=>[key,{value}]));
    const line=localizeConfiguration(facts,language);
    assert.doesNotMatch(line,/gasoline|inline-4|torque-converter|\bFront\b/i);
    assert.match(line,/Gamma-II/);
    assert.match(line,/GDI/);
    assert.match(line,language==='ru'?/классический автомат|передний привод/i:/klassik avtomat|Ön ötürücü/i);
  }
});

test('profile hides unknown optional source descriptions and keeps source codes', () => {
  const profile=localizeProfile({
    summary:[{key:'drivetrain',value:'Front'}],
    technical:[
      {key:'engine',rows:[{key:'engine_description',value:source.engine_description},{key:'engine_code',value:'G4FJ'}]},
      {key:'transmission',rows:[{key:'transmission_description',value:'Undocumented marketing phrase'},{key:'transmission_code',value:'8F24'}]},
      {key:'fluids',rows:[]},
    ],
  },'ru');
  assert.equal(profile.summary[0].value,'Передний привод');
  assert.equal(profile.technical[0].rows.find(row=>row.key==='engine_code').value,'G4FJ');
  assert.equal(profile.technical[1].rows.find(row=>row.key==='transmission_description'),undefined);
  assert.equal(profile.technical[1].rows.find(row=>row.key==='transmission_code').value,'8F24');
  assert.equal(profile.technical[2].rows.length,0);
  assert.equal(localizeTechnicalValue('fuel','Gasoline','az'),'Benzin');
});

test('confirmed AT family resolves source wording and D-4S code remains visible', () => {
  for(const [language,family,known] of [
    ['ru','Обычный автомат AT','классический автомат'],
    ['az','Klassik avtomat AT','klassik avtomat'],
  ]) {
    const profile=localizeProfile({
      summary:[],
      technical:[
        {key:'engine',rows:[{key:'engine_description',value:'3.5 L V6 D-4S'}]},
        {key:'transmission',rows:[
          {key:'transmission_description',value:'8-speed automatic'},
          {key:'transmission_family',value:family},
        ]},
      ],
    },language);
    const engine=profile.technical[0].rows[0].value;
    const transmission=profile.technical[1].rows[0].value;
    assert.match(engine,/D-4S/);
    assert.match(transmission,new RegExp(known,'i'));
    assert.doesNotMatch(transmission,/тип не уточнён|növü dəqiqləşdirilməyib|8-speed automatic/i);
  }
});
