// Physical Android WebView acceptance only. Never launches a browser or emulator.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdir, writeFile} from 'node:fs/promises';
import path from 'node:path';
const require = createRequire(import.meta.url);
const {chromium} = require('playwright');
const endpoint = process.env.AUTOEXPERT_DEVICE_CDP || 'http://127.0.0.1:9223';
const out = path.resolve(process.env.AUTOEXPERT_ARTIFACT_DIR || 'deliverables/Stage6_2_PaidReport/device');
await mkdir(out,{recursive:true});
const version = await (await fetch(`${endpoint}/json/version`)).json();
assert.equal(version['Android-Package'],'com.autoexpert.demo');
const targets = await (await fetch(`${endpoint}/json/list`)).json();
const visible = targets.find(t=>JSON.parse(t.description || '{}').visible);
assert.ok(visible);
const browser = await chromium.connectOverCDP(endpoint);
let page;
for (const candidate of browser.contexts().flatMap(c=>c.pages())) {
  const session=await candidate.context().newCDPSession(candidate);
  const {targetInfo}=await session.send('Target.getTargetInfo');
  await session.detach();
  if(targetInfo.targetId===visible.id) page=candidate;
}
assert.ok(page);
page.setDefaultTimeout(25000);
const results={}, errors=[];
page.on('pageerror',e=>errors.push(e.message));
async function click(selector) {await page.locator(selector).first().evaluate(e=>e.click());}
async function capture(name) {
  await page.screenshot({path:path.join(out,`${name}.png`)});
  await writeFile(path.join(out,`${name}.txt`),await page.locator('body').innerText());
}
async function language(code) {
  await click('[data-action=change-language]');
  await click(`[data-language=${code}]`);
  await click('[data-action=language-continue]');
  await page.waitForURL('**/#/home');
}
async function research(code) {
  await click('[data-action=vin-start]');
  await page.locator('#vin').fill('3FA6P0HD0KR114795');
  const executed=page.waitForResponse(r=>r.url().endsWith('/execute'),{timeout:180000});
  await page.locator('#vin-form').evaluate(f=>f.requestSubmit());
  let job=await (await executed).json();
  if(job.resolution?.needs_user_selection && !job.profile) {
    const selected=page.waitForResponse(r=>r.url().endsWith('/variant-selection'));
    await click('[data-action=variant-select]'); job=await (await selected).json();
  }
  await page.locator('[data-action=research-continue]').waitFor();
  const loaded=page.waitForResponse(r=>/\/vin\/[^/]+$/.test(new URL(r.url()).pathname));
  await click('[data-action=research-continue]');
  const report=await (await loaded).json();
  await page.locator('.paid-report-sections').waitFor();
  assert.equal(report.is_demo,false);
  assert.equal(report.entitlement_type,'DEVELOPER_BYPASS');
  assert.equal(report.paid_report.readiness.state,'READY');
  const sections=report.paid_report.sections;
  assert.equal(sections[0].key,'vehicle'); assert.equal(sections.at(-1).key,'expert_verdict');
  assert.equal(sections.length,11);
  assert.ok(sections.find(s=>s.key==='engine').rows.length>=8);
  assert.ok(sections.find(s=>s.key==='transmission').rows.length>=3);
  assert.ok(sections.find(s=>s.key==='chassis').rows.length>=3);
  assert.ok(sections.find(s=>s.key==='weak_points').rows.length>=5);
  const text=await page.locator('.paid-report-sections').innerText();
  assert.doesNotMatch(text,/CONFIRMED|ESTIMATE|INSUFFICIENT_DATA|NEEDS_INSPECTION|150 из 100|Какую версию брать|Опыт владельцев|23V440000/);
  assert.match(text,/25V442000/); assert.match(text,/19B37/);
  assert.equal(await page.locator('.vehicle-photo-gallery').count(),0);
  const size=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
  assert.ok(size.scroll<=size.width+1);
  await capture(`report-${code}`);
  if(code==='ru') {
    for(const key of ['vehicle','engine','transmission','chassis','fuel','weak_points','expert_verdict']) {
      await page.locator(`[data-section=${key}]`).evaluate(e=>e.scrollIntoView({block:'start'}));
      await capture(`section-${key}`);
    }
  }
  await writeFile(path.join(out,`report-${code}.json`),JSON.stringify(report,null,2));
  results[`REPORT_${code}`]={checkId:report.check_id,sections:sections.length,sourceCount:report.sources.length};
  console.log(`REPORT_${code}: PASS`);
  return report;
}
async function ask(question) {
  await page.locator('#chat-question').fill(question);
  const sent=page.waitForResponse(r=>r.url().endsWith('/messages')&&r.request().method()==='POST');
  await page.locator('#chat-form').evaluate(f=>f.requestSubmit());
  const response=await sent; assert.equal(response.status(),201);
  await page.waitForFunction(()=>!document.querySelector('.typing-message')&&!document.querySelector('#chat-question')?.disabled);
  return response.json();
}
try {
  if(await page.locator('[data-action=reconnect]').count()) await click('[data-action=reconnect]');
  if(await page.locator('[data-action=language-continue]').count()) {
    await click('[data-language=ru]'); await click('[data-action=language-continue]');
  } else await language('ru');
  if(await page.locator('[data-action=toggle-paywall]').getAttribute('aria-checked')==='true') {
    await click('[data-action=toggle-paywall]');
    await page.waitForFunction(()=>document.querySelector('[data-action=toggle-paywall]')?.getAttribute('aria-checked')==='false');
  }
  let report=await research('ru');
  await page.locator('.report-sources').evaluate(e=>e.open=true);
  assert.equal(await page.locator('.source-card').count(),report.sources.length);
  await page.locator('.report-sources').scrollIntoViewIfNeeded(); await capture('sources');
  await page.locator('.report-diagnostics').evaluate(e=>e.open=true);
  await click('[data-action=load-report-diagnostics]');
  await page.locator('.report-diagnostics-json:not([hidden])').waitFor();
  const diagnostics=JSON.parse(await page.locator('.report-diagnostics-json').innerText());
  assert.ok(Object.keys(diagnostics.knowledge.provenance).length>=34);
  assert.equal(diagnostics.knowledge.issue_aggregation.known_issues.length,1);
  await writeFile(path.join(out,'source-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  results.SOURCES_AND_DIAGNOSTICS=true;
  await click('[data-action=chat-start]'); await page.locator('#chat-question').waitFor();
  for(let i=0;i<12;i++) {
    const answer=await ask(i===0?'Какие слабые места?':'Что известно о коробке?');
    assert.equal(answer.policy.unlimited,true); assert.equal(answer.policy.question_limit,null);
    assert.ok(answer.message.sources.length>0);
    assert.match(answer.message.content,i===0?/антифриз/:/Автоматическая/);
  }
  await capture('chat'); results.CHAT_UNLIMITED_12=true;
  await click('[data-action=chat-report]'); await page.locator('.paid-report-sections').waitFor();
  await click('[data-action=toggle-paywall]'); await page.waitForURL('**/#/research/**');
  await click('[data-action=research-continue]'); await page.waitForURL('**/#/precheck/**');
  await page.locator('[data-action=unlock]').waitFor(); await capture('simulate-paywall');
  await click('[data-action=unlock]'); await click('[data-action=unlock-confirm]');
  await page.locator('.dossier-stack').waitFor();
  await click('[data-action=chat-start]'); await page.locator('#chat-question').waitFor();
  const limited=await ask('Что проверить перед покупкой?');
  assert.equal(limited.policy.question_limit,10); assert.equal(limited.policy.unlimited,false);
  results.SIMULATE_USER_PAYWALL=true;
  await click('[data-action=chat-report]'); await page.locator('.dossier-stack').waitFor();
  await click('[data-action=toggle-paywall]');
  await page.waitForFunction(()=>document.querySelector('[data-action=toggle-paywall]')?.getAttribute('aria-checked')==='false');
  for(const code of ['az','en']) {await language(code); await research(code);}
  await language('ru'); report=await research('ru');
  // Android WebView CDP sometimes reports an empty binary response body while
  // fetch receives the complete PDF. Inspect bytes inside the actual WebView.
  const pdfBytes=await page.evaluate(async id=>{
    const response=await fetch(window.AUTOEXPERT_API_ROOT+'/vin/'+id+'/report.pdf',
      {headers:{Authorization:'Bearer '+localStorage.getItem('autoexpert.demo.token')}});
    if(!response.ok) throw new Error('PDF HTTP '+response.status);
    return Array.from(new Uint8Array(await response.arrayBuffer()));
  },report.check_id);
  const bytes=Buffer.from(pdfBytes); assert.equal(bytes.subarray(0,4).toString(),'%PDF');
  await writeFile(path.join(out,'downloaded-on-HONOR.pdf'),bytes);
  const pdfResponse=page.waitForResponse(r=>r.url().endsWith('/report.pdf')&&r.request().method()==='GET');
  await click('[data-action=download-report-pdf]');
  const pdf=await pdfResponse; assert.equal(pdf.status(),200);
  await pdf.finished();
  await page.waitForFunction(()=>!document.querySelector('[data-action=download-report-pdf]').disabled);
  results.PDF_HTTP=true;
  assert.deepEqual(errors,[]);
  results.BROWSER_ERRORS=[];
  await writeFile(path.join(out,'results.json'),JSON.stringify(results,null,2));
  console.log(JSON.stringify(results,null,2));
} catch(error) {
  await capture('failure'); throw error;
} finally {await browser.close();}
