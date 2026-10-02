/* Delta-only visual QA against isolated SQLite copies. No Turbo.az or paid calls. */
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE);

const qaBase = (process.env.AUTOEXPERT_DELTA_QA_URL || 'http://127.0.0.1:8776').replace(/\/$/, '');
const productionBase = (process.env.AUTOEXPERT_DELTA_PRODUCTION_URL || 'http://127.0.0.1:8777').replace(/\/$/, '');
const output = path.resolve(process.env.AUTOEXPERT_DELTA_QA_OUTPUT || 'deliverables/DeltaScope2012/qa');
fs.mkdirSync(output, { recursive: true });

function assert(value, message) { if (!value) throw new Error(message); }

async function main() {
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_EXECUTABLE || undefined,
    headless: true,
    args: ['--no-sandbox'],
  });
  const dimensions = { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, locale: 'ru-RU' };
  const qaContext = await browser.newContext(dimensions);
  const productionContext = await browser.newContext(dimensions);
  const qaPage = await qaContext.newPage();
  const productionPage = await productionContext.newPage();
  const errors = [];
  for (const page of [qaPage, productionPage]) {
    page.on('pageerror', error => errors.push(error.message));
  }
  let serial = 0;
  async function go(page, base, route, language = 'ru') {
    await page.goto(`${base}/preview/?delta=${++serial}#/language`, { waitUntil: 'domcontentloaded' });
    await page.evaluate(language => localStorage.setItem('autoexpert.ui.language', language), language);
    await page.goto(`${base}/preview/?delta=${++serial}#${route}`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => (document.querySelector('#app')?.innerText || '').length > 25, null, { timeout: 45000 });
  }
  async function capture(page, name, selector, { element = false, scroll = true } = {}) {
    const item = page.locator(selector).first();
    await item.waitFor({ timeout: 45000 });
    if (scroll) await item.scrollIntoViewIfNeeded();
    await page.waitForTimeout(280);
    const destination = path.join(output, name);
    if (element) await item.screenshot({ path: destination, animations: 'disabled' });
    else await page.screenshot({ path: destination, animations: 'disabled' });
    const size = await page.evaluate(() => ({ screen: innerWidth, content: document.documentElement.scrollWidth }));
    assert(size.content <= size.screen + 1, `${name}: horizontal overflow ${size.content} > ${size.screen}`);
    process.stdout.write(`${name}\n`);
  }
  async function post(context, pathname, data, token) {
    const response = await context.request.post(`${qaBase}/api/v1${pathname}`, {
      data, headers: token ? { Authorization: `Bearer ${token}` } : {}, timeout: 60000,
    });
    const result = await response.json();
    assert(response.ok(), `${pathname}: HTTP ${response.status()} ${JSON.stringify(result).slice(0, 500)}`);
    return result;
  }
  try {
    const qaMetaResponse = await qaContext.request.get(`${qaBase}/api/v1/meta/client-config`);
    const productionMetaResponse = await productionContext.request.get(`${productionBase}/api/v1/meta/client-config`);
    assert(qaMetaResponse.ok() && productionMetaResponse.ok(), 'Both modes must expose client configuration');
    const qaMeta = await qaMetaResponse.json();
    const productionMeta = await productionMetaResponse.json();
    assert(qaMeta.qa_mode === true, 'QA server must explicitly declare QA mode');
    assert(productionMeta.qa_mode === false, 'Production server must explicitly disable QA mode');
    assert(productionMeta.vin_demo == null, 'Production API must not expose sample VIN');
    for (const base of [qaBase, productionBase]) {
      const facetsResponse = await qaContext.request.get(`${base}/api/v1/knowledge/facets`, { timeout: 60000 });
      assert(facetsResponse.ok(), `${base}: consumer default facets HTTP ${facetsResponse.status()}`);
      const facets = await facetsResponse.json();
      const facetYears = (facets.years || []).map(Number).filter(Number.isFinite);
      assert(facetYears.length > 0 && Math.min(...facetYears) >= 2012,
        `${base}: consumer facets expose pre-2012 years`);
      const response = await qaContext.request.post(`${base}/api/v1/knowledge/search?language=ru`, { data: {}, timeout: 60000 });
      assert(response.ok(), `${base}: consumer default search HTTP ${response.status()}`);
      const result = await response.json();
      assert(result.matched_models === 75 && result.matched_versions === 644,
        `${base}: expected 75/644, got ${result.matched_models}/${result.matched_versions}`);
    }

    await go(qaPage, qaBase, '/pick');
    const years = await qaPage.locator('select[name="year_min"] option').evaluateAll(nodes => nodes.map(n => Number(n.value)).filter(Number.isFinite).filter(n => n > 0));
    assert(years.length > 0 && Math.min(...years) === 2012, `Year choices start at ${Math.min(...years)}`);
    assert(await qaPage.locator('select[name="year_min"]').inputValue() === '2012', 'Default minimum year must be MY2012');
    assert(/USA|ABŞ/.test(await qaPage.locator('.market-scope').innerText()), 'USA market badge absent');
    await qaPage.evaluate(() => window.scrollTo(0, 270));
    await capture(qaPage, '01-filter-usa-my2012.png', '.market-scope', { scroll: false });

    const auth = await post(qaContext, '/auth/demo', { preferred_language: 'ru' });
    const token = auth.access_token;
    await qaPage.evaluate(payload => {
      localStorage.setItem('autoexpert.demo.token', payload.access_token);
      localStorage.setItem('autoexpert.demo.user', JSON.stringify(payload.user));
    }, auth);
    const out = await post(qaContext, '/listings/intake', {
      input_type: 'TEXT', source_url: 'https://turbo.az/autos/98765431', language: 'ru',
      text: 'Марка: Ford\nМодель: Fusion\nГод: 2019\nVIN: 3FA6P0HD0KR114795\nHansı bazar üçün yığılıb: Amerika',
    }, token);
    assert(out.match.status === 'OUT_OF_PRODUCT_SCOPE', `Out-of-scope result: ${out.match.status}`);
    await go(qaPage, qaBase, `/listing-result/${out.id}`);
    await qaPage.locator('.listing-actions').waitFor({ timeout: 45000 });
    const listingText = await qaPage.locator('#app').innerText();
    assert(!listingText.includes('Технический каталог пока не охватывает эту модель'), 'Internal coverage gap leaked');
    assert(listingText.includes('Проверить автомобиль по VIN'), 'Neutral VIN CTA missing');
    await capture(qaPage, '02-out-of-scope-vin-cta.png', '.listing-actions');

    const exact = await post(qaContext, '/listings/intake', {
      input_type: 'TEXT', source_url: 'https://turbo.az/autos/98765432', language: 'ru',
      text: 'Марка: Toyota\nМодель: Camry\nГод: 2018\nДвигатель: 3.5 л\nТопливо: бензин\nКоробка: автомат\nПривод: передний\nHansı bazar üçün yığılıb: Amerika',
    }, token);
    assert(exact.match.status === 'EXACT_MATCH', `Camry fixture: ${exact.match.status}`);
    const variantId = exact.match.candidates[0].variant_id;
    const forbiddenTechnical = /\bgasoline\b|\binline[- ]?4\b|8-speed torque-converter automatic|\bFront\b/i;
    for (const [language, filename] of [['ru', '03-technical-ru.png'], ['az', '04-technical-az.png']]) {
      await go(qaPage, qaBase, `/catalog-car/${variantId}`, language);
      await qaPage.locator('#panel-technical').waitFor({ timeout: 45000 });
      await qaPage.locator('#panel-technical .technical-group').evaluateAll(nodes => nodes.forEach(node => { node.open = true; }));
      const visible = await qaPage.locator('#app').innerText();
      assert(!forbiddenTechnical.test(visible), `${language} technical card contains raw English: ${visible.match(forbiddenTechnical)?.[0]}`);
      assert(await qaPage.locator('.fluids-group').count() === 0, `${language} unsupported oils/fluid group is visible`);
      await qaPage.evaluate(() => {
        const panel = document.querySelector('#panel-technical');
        window.scrollTo(0, panel.getBoundingClientRect().top + window.scrollY - 12);
      });
      await capture(qaPage, filename, '#panel-technical', { scroll: false });
    }

    const check = await post(qaContext, '/vin/history/checks', { vin: '3FA6P0HD0KR114795', language: 'ru' }, token);
    await go(qaPage, qaBase, `/history-preview/${check.check_id}`, 'ru');
    await qaPage.locator('.teaser-hero').waitFor({ timeout: 45000 });
    const qaText = await qaPage.locator('#app').innerText();
    assert(/ТЕСТОВЫЙ ПРОВАЙДЕР|MOCK \/ SANDBOX/.test(qaText), 'QA mock label absent');
    await capture(qaPage, '05-qa-mock-screen.png', '.teaser-hero');

    await go(productionPage, productionBase, `/catalog-car/${variantId}`, 'ru');
    await productionPage.locator('.vehicle-profile-summary').waitFor({ timeout: 45000 });
    assert(await productionPage.locator('.fluids-group').count() === 0, 'Unsupported oil/fluid group leaked into production UI');
    await go(productionPage, productionBase, '/check/vin', 'ru');
    await productionPage.locator('#vin-form').waitFor({ timeout: 45000 });
    const productionText = await productionPage.locator('#app').innerText();
    assert(!/QA fixture|MOCK \/ SANDBOX|ТЕСТОВЫЙ ПРОВАЙДЕР|Тестовый провайдер/i.test(productionText), 'QA/mock label leaked into production UI');
    assert(!productionText.includes('3FA6P0HD0KR114795'), 'Sample VIN text leaked into production UI');
    assert(!await productionPage.locator('[data-action="use-demo-vin"]').count(), 'Sample VIN button leaked into production UI');
    assert(!String(await productionPage.locator('#vin').getAttribute('placeholder')).includes('3FA6P0HD0KR114795'), 'Sample VIN placeholder leaked into production UI');
    await capture(productionPage, '06-production-mode-clean.png', '#vin-form');

    assert(errors.length === 0, `Browser errors: ${errors.join(' | ')}`);
    fs.writeFileSync(path.join(output, 'capture_manifest.json'), JSON.stringify({
      captured_at: new Date().toISOString(), screenshots: [
        '01-filter-usa-my2012.png', '02-out-of-scope-vin-cta.png',
        '03-technical-ru.png', '04-technical-az.png', '05-qa-mock-screen.png',
        '06-production-mode-clean.png',
      ], qa_mode: qaMeta.qa_mode, production_qa_mode: productionMeta.qa_mode,
      production_vin_demo: productionMeta.vin_demo, consumer_catalog: 'USA MY2012+ · 75 models / 644 configs', browser_errors: errors,
    }, null, 2));
    process.stdout.write('PASS: six delta PNGs; QA/production mode separation; no browser errors\n');
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error.stack || String(error)); process.exitCode = 1; });
