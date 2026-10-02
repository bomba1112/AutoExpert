// Runs only against an already connected physical Android WebView. No browser is launched.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdir, writeFile} from 'node:fs/promises';
import path from 'node:path';

const require = createRequire(import.meta.url);
const {chromium} = require('playwright');
const endpoint = process.env.AUTOEXPERT_DEVICE_CDP || 'http://127.0.0.1:9223';
const artifacts = path.resolve(process.env.AUTOEXPERT_ARTIFACT_DIR || '.runtime/device-acceptance');
await mkdir(artifacts, {recursive: true});
const version = await (await fetch(`${endpoint}/json/version`)).json();
assert.equal(version['Android-Package'], 'com.autoexpert.demo');
const targets = await (await fetch(`${endpoint}/json/list`)).json();
const visible = targets.find(target => JSON.parse(target.description || '{}').visible);
assert.ok(visible, 'The physical app must be visible');
const browser = await chromium.connectOverCDP(endpoint);
let page;
for (const candidate of browser.contexts().flatMap(context => context.pages())) {
  const session = await candidate.context().newCDPSession(candidate);
  const {targetInfo} = await session.send('Target.getTargetInfo');
  await session.detach();
  if (targetInfo.targetId === visible.id) page = candidate;
}
assert.ok(page);
page.setDefaultTimeout(20000);
const results = {};
const requests = [];
const failures = [];
page.on('request', request => {
  if (request.url().includes('/api/v1/')) requests.push({
    method: request.method(), path: new URL(request.url()).pathname,
  });
});
page.on('pageerror', error => failures.push(error.message));
const record = (name, detail = true) => {
  results[name] = detail;
  console.log(`${name}: PASS`);
};
async function click(selector) {
  await page.locator(selector).first().waitFor();
  // WebView's native IME can change CDP pointer offsets; invoke the actual control handler.
  await page.locator(selector).first().evaluate(button => button.click());
}
async function capture(name) {
  await page.screenshot({path: path.join(artifacts, `${name}.png`)});
  await writeFile(path.join(artifacts, `${name}.txt`), await page.locator('body').innerText());
}
async function noOverflow() {
  const size = await page.evaluate(() => ({width: innerWidth, scroll:document.documentElement.scrollWidth}));
  assert.ok(size.scroll <= size.width + 1, `Horizontal overflow: ${JSON.stringify(size)}`);
}
async function chooseLanguage(code) {
  const owner = await page.evaluate(() => localStorage.getItem('autoexpert.demo.user'));
  await click('[data-action=change-language]');
  await click(`[data-language=${code}]`);
  await click('[data-action=language-continue]');
  await page.waitForURL('**/#/home');
  assert.equal(await page.evaluate(() => localStorage.getItem('autoexpert.demo.user')), owner,
    'Changing language must preserve the owner and saved reports');
}
async function researchVin(language) {
  await click('[data-action=vin-start]');
  await page.locator('#vin').fill('3FA6P0HD0KR114795');
  const executed = page.waitForResponse(response => response.url().endsWith('/execute'), {timeout:180000});
  await page.locator('#vin-form').evaluate(form => form.requestSubmit());
  await page.waitForURL('**/#/research/**');
  const response = await executed;
  assert.equal(response.status(), 200);
  let job = await response.json();
  if (job.resolution?.needs_user_selection && !job.profile) {
    const selected = page.waitForResponse(response => response.url().endsWith('/variant-selection'));
    await click('[data-action=variant-select]');
    job = await (await selected).json();
  }
  await page.locator('[data-action=research-continue]').waitFor({timeout:180000});
  assert.equal(job.profile.make, 'Ford');
  assert.equal(job.profile.model, 'Fusion');
  assert.equal(job.profile.year, 2019);
  assert.equal(job.is_demo, false);
  assert.ok(job.profile.source_ids.length > 0);
  record(`RESEARCH_${language.toUpperCase()}`, {jobId:job.id,status:job.status,
    sources:job.profile.source_ids.length,cacheHit:job.cache_hit});
  const reportResponse = page.waitForResponse(response => /\/vin\/[^/]+$/.test(new URL(response.url()).pathname));
  await click('[data-action=research-continue]');
  const report = await (await reportResponse).json();
  await page.locator('.dossier-stack').waitFor();
  assert.equal(report.entitlement_type, 'DEVELOPER_BYPASS');
  assert.equal(report.dossier_origin, 'REAL');
  assert.equal(report.history.timeline.length, 0);
  assert.equal(report.dossier.sections.length, 16);
  assert.equal(await page.locator('[data-action=unlock]').count(), 0);
  assert.equal(await page.locator('.empty-section[open]').count(), 0);
  assert.equal(await page.locator('.source-card').count(), report.sources.length);
  await noOverflow();
  await capture(`dossier-${language}`);
  await page.locator('.dossier-stack details').evaluateAll(nodes => nodes.forEach(node => node.open = true));
  const consumer = await page.locator('.dossier-stack').innerText();
  assert.doesNotMatch(consumer, /component not specified|summary not provided|engine_code|Tier [AC]|Vehicle Knowledge Profile/);
  if (language !== 'en') assert.doesNotMatch(consumer, /power train|electrical system|manufacturer communication/i);
  const claims = report.dossier.sections.find(section => section.key === 'owner_experience').claims;
  assert.equal(new Set(claims.map(claim=>claim.text)).size, claims.length);
  assert.ok(report.dossier.sections.find(section => section.key === 'recalls_tsb').claims.length > 0);
  await writeFile(path.join(artifacts, `dossier-${language}.json`), JSON.stringify(report,null,2));
  record(`DOSSIER_${language.toUpperCase()}`);
  return report;
}
async function ask(question) {
  await page.locator('#chat-question').fill(question);
  const answerResponse = page.waitForResponse(response => /\/messages$/.test(response.url()) && response.request().method() === 'POST');
  await page.locator('#chat-form').evaluate(form => form.requestSubmit());
  const response = await answerResponse;
  assert.equal(response.status(), 201);
  const answer = await response.json();
  await page.waitForFunction(()=>!document.querySelector('.typing-message') && !document.querySelector('#chat-question')?.disabled);
  return answer;
}
try {
  if (await page.locator('[data-action=reconnect]').count()) await click('[data-action=reconnect]');
  if (await page.locator('[data-action=language-continue]').count()) {
    await click('[data-language=ru]'); await click('[data-action=language-continue]');
  } else {
    await chooseLanguage('ru');
  }
  if (await page.locator('[data-action=toggle-paywall]').getAttribute('aria-checked') === 'true') {
    await click('[data-action=toggle-paywall]');
    await page.waitForFunction(() => document.querySelector('[data-action=toggle-paywall]')?.getAttribute('aria-checked') === 'false');
  }
  const start = requests.length;
  await researchVin('ru');
  assert.ok(!requests.slice(start).some(request => /precheck|payments|unlock/.test(request.path)));
  record('DEVELOPER_MODE_NO_PAYWALL');
  const sourceText = await page.locator('.source-stack').innerText();
  assert.match(sourceText, /NHTSA/);
  assert.match(sourceText, /Получено/);
  assert.doesNotMatch(sourceText, /https?:\/\/|source_tier|confidence|TIER/);
  assert.ok((await page.locator('.source-card a').count()) >= 4);
  await page.locator('.source-stack').scrollIntoViewIfNeeded();
  await capture('sources');
  record('SOURCES');
  await click('[data-action=chat-start]');
  await page.locator('#chat-question').waitFor();
  let answer;
  for (let index=0; index<12; index++) {
    answer = await ask(index === 1 ? 'Какие отзывные кампании найдены?' : 'Что проверить перед покупкой?');
    assert.equal(answer.policy.unlimited, true);
    assert.equal(answer.policy.question_limit, null);
    if (index !== 1) assert.match(answer.message.content, /антиблокировочной/);
    if (index === 1) {
      assert.ok(answer.message.sources.length > 0);
      assert.match(answer.message.content, /VIN/);
    }
  }
  await capture('chat-unlimited');
  record('CHAT_12_QUESTIONS', {used:answer.policy.questions_used});
  await click('[data-action=chat-report]');
  await page.locator('.dossier-stack').waitFor();
  await click('[data-action=toggle-paywall]');
  await page.waitForURL('**/#/research/**');
  await click('[data-action=research-continue]');
  await page.waitForURL('**/#/precheck/**');
  await page.locator('[data-action=unlock]').waitFor();
  assert.equal(await page.locator('.dossier-stack').count(), 0);
  const locked = await page.locator('body').innerText();
  assert.match(locked, /5(?:[,.]0+)?\s*AZN/);
  assert.match(locked, /Деньги не списываются/);
  await capture('paywall-locked');
  await click('[data-action=unlock]');
  await click('[data-action=unlock-confirm]');
  await page.locator('.dossier-stack').waitFor();
  await click('[data-action=chat-start]');
  await page.locator('#chat-question').waitFor();
  const limited = await ask('Что проверить перед покупкой?');
  assert.equal(limited.policy.unlimited, false);
  assert.equal(limited.policy.question_limit, 10);
  assert.equal(limited.policy.questions_remaining, 9);
  record('SIMULATE_USER_PAYWALL');
  await click('[data-action=chat-report]');
  await page.locator('.dossier-stack').waitFor();
  await click('[data-action=toggle-paywall]');
  await page.waitForFunction(() => document.querySelector('[data-action=toggle-paywall]')?.getAttribute('aria-checked') === 'false');
  await page.waitForURL('**/#/report/**');
  for (const language of ['az','en']) {
    await chooseLanguage(language);
    await researchVin(language);
    await click('[data-action=chat-start]');
    await page.locator('#chat-question').waitFor();
    const localized = await ask(language === 'az' ? 'Almazdan əvvəl nəyi yoxlamaq?' : 'What to check before purchase?');
    assert.match(localized.message.content, language === 'az' ? /bloklanmasının/ : /anti-lock/);
    record(`CHAT_${language.toUpperCase()}`);
    await click('[data-action=chat-report]');
    await page.locator('.dossier-stack').waitFor();
  }
  await chooseLanguage('ru');
  await researchVin('ru');
  assert.equal(failures.length, 0, failures.join('\n'));
  record('WEBVIEW_NO_JS_ERRORS');
} catch(error) {
  results.failure = error.stack;
  await capture('failure').catch(()=>{});
  throw error;
} finally {
  await writeFile(path.join(artifacts,'results.json'), JSON.stringify({version,results,requests,failures},null,2));
  await browser.close();
}
