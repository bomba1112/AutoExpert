/* Reproducible local browser capture for the approved consumer UI.
 * Runs against an isolated QA database and synthetic user-supplied listings.
 * It never opens Turbo.az or calls a paid provider.
 */
'use strict';

const fs = require('node:fs');
const path = require('node:path');

const playwrightRoot = process.env.PLAYWRIGHT_MODULE;
if (!playwrightRoot) throw new Error('Set PLAYWRIGHT_MODULE to the bundled playwright directory');
const { chromium } = require(playwrightRoot);

const base = (process.env.AUTOEXPERT_QA_BASE_URL || 'http://127.0.0.1:8765').replace(/\/$/, '');
const output = path.resolve(process.env.AUTOEXPERT_QA_OUTPUT || 'deliverables/ApprovedUITurboAzListingIntake/qa');
const browserPath = process.env.CHROMIUM_EXECUTABLE;
fs.mkdirSync(output, { recursive: true });

const manifest = [];
const errors = [];
const forbidden = /\bUNKNOWN\b|уточняется|данных нет|данные неполные|информация отсутствует|məlumat natamamdır|məlumat yoxdur|изображение уточняется/i;

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function main() {
  const browser = await chromium.launch({
    executablePath: browserPath || undefined,
    headless: true,
    args: ['--no-sandbox'],
  });
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    locale: 'ru-RU',
    colorScheme: 'light',
  });
  const page = await context.newPage();
  let initialized = false;
  let navigation = 0;
  page.on('pageerror', error => errors.push(`pageerror: ${error.message}`));
  page.on('console', message => { if (message.type() === 'error') errors.push(`console: ${message.text()}`); });

  async function go(route, language = 'ru') {
    if (!initialized) {
      await page.goto(`${base}/preview/#/language`, { waitUntil: 'domcontentloaded' });
      initialized = true;
    }
    await page.evaluate(language => localStorage.setItem('autoexpert.ui.language', language), language);
    await page.goto(`${base}/preview/?qa=${++navigation}#${route}`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => {
      const text = document.querySelector('#app')?.innerText || '';
      return text.length > 25 && !text.includes('Auto Expert service is unavailable');
    }, null, { timeout: 45000 });
    await page.waitForTimeout(300);
  }

  async function capture(number, slug, title, route, options = {}) {
    if (route) await go(route, options.language || 'ru');
    if (options.click) await page.locator(options.click).first().click();
    if (options.selector) {
      const element = page.locator(options.selector).first();
      try { await element.waitFor({ timeout: 120000 }); }
      catch (error) {
        console.error(`Route ${page.url()} did not render ${options.selector}:`, (await page.locator('#app').innerText()).slice(0, 1600));
        await page.screenshot({ path: path.join(output, `debug-${String(number).padStart(2, '0')}.png`) });
        throw error;
      }
      if (options.open && await element.evaluate(node => node instanceof HTMLDetailsElement && !node.open)) {
        await element.locator('summary').click();
      }
      await element.scrollIntoViewIfNeeded();
    }
    await page.waitForTimeout(280);
    const name = `${String(number).padStart(2, '0')}-${slug}.png`;
    const target = path.join(output, name);
    await page.screenshot({ path: target, animations: 'disabled' });
    const state = await page.evaluate(() => ({
      route: location.hash,
      width: innerWidth,
      scrollWidth: document.documentElement.scrollWidth,
      text: document.querySelector('#app')?.innerText || '',
    }));
    assert(state.scrollWidth <= state.width + 1, `Horizontal overflow in ${name}: ${state.scrollWidth} > ${state.width}`);
    const bad = state.text.match(forbidden);
    if (bad) throw new Error(`Forbidden user phrase in ${name}: ${bad[0]}`);
    manifest.push({ number, name, title, route: state.route, width: state.width, height: 844, fixture: options.fixture || null });
    process.stdout.write(`${name}\n`);
  }

  async function post(pathname, payload, token) {
    const response = await context.request.post(`${base}/api/v1${pathname}`, {
      data: payload,
      headers: { Authorization: `Bearer ${token}` },
      timeout: 60000,
    });
    const body = await response.json().catch(() => ({}));
    assert(response.ok(), `${pathname} HTTP ${response.status()}: ${JSON.stringify(body).slice(0, 700)}`);
    return body;
  }

  try {
    await go('/home');
    const auth = await context.request.post(`${base}/api/v1/auth/demo`, {
      data: { preferred_language: 'ru' },
    });
    assert(auth.ok(), `Demo auth HTTP ${auth.status()}`);
    const session = await auth.json();
    const token = session.access_token;
    await page.evaluate(payload => {
      localStorage.setItem('autoexpert.demo.token', payload.access_token);
      localStorage.setItem('autoexpert.demo.user', JSON.stringify(payload.user));
    }, session);

    const exact = await post('/listings/intake', {
      input_type: 'TEXT', source_url: 'https://turbo.az/autos/12345678', language: 'ru',
      text: 'Марка: Toyota\nМодель: Camry\nГод: 2018\nДвигатель: 3.5 л\nТопливо: бензин\nКоробка: автомат\nПривод: передний\nЦена: 25 000 AZN\nПробег: 85 000 км\nГород: Баку\nHansı bazar üçün yığılıb: Amerika',
    }, token);
    const multiple = await post('/listings/intake', {
      input_type: 'TEXT', source_url: 'https://turbo.az/autos/12345679', language: 'ru',
      text: 'Марка: Toyota\nМодель: Camry\nГод: 2018\nКоробка: автомат\nHansı bazar üçün yığılıb: Amerika',
    }, token);
    const conflict = await post('/listings/intake', {
      input_type: 'TEXT', source_url: 'https://turbo.az/autos/12345680', language: 'ru',
      text: 'Марка: Toyota\nМодель: Camry\nГод: 2018\nТопливо: дизель\nКоробка: автомат\nHansı bazar üçün yığılıb: Amerika',
    }, token);
    const withVin = await post('/listings/intake', {
      input_type: 'TEXT', source_url: 'https://turbo.az/autos/12345681', language: 'ru',
      text: 'Марка: Ford\nМодель: Fusion\nГод: 2019\nVIN: 3FA6P0HD0KR114795\nHansı bazar üçün yığılıb: Amerika',
    }, token);
    assert(exact.match.status === 'EXACT_MATCH', `Exact fixture: ${exact.match.status}`);
    assert(multiple.match.status === 'MULTIPLE_CANDIDATES', `Multiple fixture: ${multiple.match.status}`);
    assert(conflict.match.status === 'CLAIM_CONFLICT', `Conflict fixture: ${conflict.match.status}`);
    assert(withVin.match.status === 'OUT_OF_PRODUCT_SCOPE', `VIN fixture: ${withVin.match.status}`);
    assert(exact.match.candidates?.[0]?.variant_id, 'Exact fixture needs a production candidate');

    await capture(1, 'home-ru', 'Главная RU', '/home');
    await capture(2, 'home-az', 'Главная AZ', '/home', { language: 'az' });
    await capture(3, 'check-vehicle', 'Проверить конкретную машину', '/check');
    await capture(4, 'tab-vin', 'VIN tab', '/check/vin', { click: '[name="vin"]' });
    await capture(5, 'tab-turbo', 'Turbo.az tab', '/check/turbo');
    await capture(6, 'manual-input', 'Ручной ввод', '/check/manual');
    await capture(7, 'listing-seller-claims', 'Указано в объявлении', `/listing-result/${exact.id}`, { selector: '.listing-claims' });
    await capture(8, 'listing-exact', 'Однозначное сопоставление', `/listing-result/${exact.id}`, { selector: '.matching-state.exact' });
    await capture(9, 'listing-multiple', 'Несколько версий', `/listing-result/${multiple.id}`, { selector: '.matching-state.multiple' });
    await capture(10, 'listing-conflict', 'Противоречие полей', `/listing-result/${conflict.id}`, { selector: '.matching-state.conflict' });
    await capture(11, 'listing-vin-cta', 'Переход к VIN', `/listing-result/${withVin.id}`, { selector: '.listing-actions' });
    await capture(12, 'filters', 'Подбор и фильтры', '/pick', { selector: '#catalog-wizard' });
    await capture(13, 'top-recommendation', 'Главная рекомендация', '/catalog-results', { selector: '.top-recommendation' });
    await capture(14, 'competitors', 'Другие подходящие варианты', '/catalog-results', { selector: '.list-heading' });
    const variantId = exact.match.candidates[0].variant_id;
    await capture(15, 'vehicle-profile', 'Профиль автомобиля', `/catalog-car/${variantId}`, { selector: '.vehicle-profile-summary' });
    await capture(16, 'four-categories', 'Четыре категории', `/catalog-car/${variantId}`, { selector: '.profile-categories' });
    await capture(17, 'technical-section', 'Техническая часть', `/catalog-car/${variantId}`, { selector: '#panel-technical' });
    assert(await page.locator('.fluids-group').count() === 0, 'Production profile must hide fluids without COMMERCIAL_OK facts');

    // Oil and fluid rendering is verified with an isolated browser response fixture.
    // The current 644 commercial-safe configurations contain no oil/fluid facts;
    // this fixture never touches a DB and must not be described as live vehicle data.
    await page.route(`**/api/v1/knowledge/vehicles/${variantId}?*`, async route => {
      const response = await route.fetch();
      const data = await response.json();
      const language = new URL(route.request().url()).searchParams.get('language');
      const groups = data.profile?.technical;
      if (Array.isArray(groups)) {
        const fluids = groups.find(group => group.key === 'fluids');
        const fixture = { key: 'fluids', title: language === 'az' ? 'Yağlar və mayelər' : 'Масла и жидкости', rows: [
          { key: 'engine_oil_viscosity', label: language === 'az' ? 'Özlülük' : 'Вязкость', value: 'QA fixture · SAE 0W-20' },
          { key: 'engine_oil_specification', label: language === 'az' ? 'Spesifikasiya' : 'Допуск / спецификация', value: 'QA fixture · API SP' },
          { key: 'transmission_fluid', label: language === 'az' ? 'Sürətlər qutusu mayesi' : 'Жидкость коробки', value: 'QA fixture · sample specification' },
        ] };
        if (fluids) Object.assign(fluids, fixture);
        else groups.push(fixture);
      }
      await route.fulfill({ response, json: data });
    });
    await capture(18, 'oils-fluids-ru-fixture', 'Масла и жидкости RU · QA fixture', `/catalog-car/${variantId}`, { selector: '.fluids-group', open: true, fixture: 'synthetic response-only oil values; no DB write' });
    await capture(19, 'oils-fluids-az-fixture', 'Yağlar və mayelər AZ · QA fixture', `/catalog-car/${variantId}`, { selector: '.fluids-group', open: true, language: 'az', fixture: 'synthetic response-only oil values; no DB write' });
    await page.unroute(`**/api/v1/knowledge/vehicles/${variantId}?*`);

    const check = await post('/vin/history/checks', { vin: '3FA6P0HD0KR114795', language: 'ru' }, token);
    await capture(20, 'vin-preview', 'VIN preview', `/history-preview/${check.check_id}`);
    await capture(21, 'locked-mock-report', 'Закрытый mock-отчёт', `/history-preview/${check.check_id}`, { selector: '.locked-preview' });
    const unlock = await post(`/vin/history/checks/${check.check_id}/payments/mock`, { simulate_failure: false }, token);
    assert(unlock.is_unlocked, 'Mock report did not unlock');
    await capture(22, 'unlocked-mock-report', 'Открытый mock-отчёт', `/history-report/${check.check_id}`);
    await capture(23, 'my-reports', 'Мои отчёты', '/reports');
    await go('/home');
    await page.locator('#home-publications .battle-card').first().waitFor({ timeout: 45000 });
    await capture(24, 'generation-battles', 'Битва поколений · production-safe comparison cards', null, { selector: '.home-battles' });

    for (const width of [360, 390, 430]) {
      await page.setViewportSize({ width, height: 844 });
      for (const route of ['/home', '/check/turbo', `/listing-result/${exact.id}`, '/pick', `/catalog-car/${variantId}`, `/history-preview/${check.check_id}`]) {
        await go(route);
        const sizes = await page.evaluate(() => ({ body: document.documentElement.scrollWidth, viewport: innerWidth }));
        assert(sizes.body <= sizes.viewport + 1, `Overflow ${route} at ${width}px: ${sizes.body}`);
        if (route.startsWith('/history-preview/')) {
          const clipped = await page.locator('.signal strong').evaluateAll(nodes => nodes.some(node => node.scrollWidth > node.clientWidth + 1));
          assert(!clipped, `VIN preview signal text clipped at ${width}px`);
        }
      }
    }
    await page.setViewportSize({ width: 360, height: 844 });
    for (const route of ['/home', '/check/turbo', `/listing-result/${exact.id}`, '/pick']) {
      await go(route);
      await page.addStyleTag({ content: 'html { font-size: 125% !important; }' });
      const sizes = await page.evaluate(() => ({ body: document.documentElement.scrollWidth, viewport: innerWidth }));
      assert(sizes.body <= sizes.viewport + 1, `Large-text overflow ${route}: ${sizes.body}`);
    }

    fs.writeFileSync(path.join(output, 'capture_manifest.json'), JSON.stringify({ base, captured_at: new Date().toISOString(), screenshots: manifest, responsive: [360, 390, 430], large_text: '125% at 360px', browser_errors: errors }, null, 2));
    assert(manifest.length === 24, `Captured ${manifest.length}/24 screenshots (23 required + generation battles)`);
    assert(errors.length === 0, `Browser errors: ${errors.join(' | ')}`);
    process.stdout.write(`PASS: ${manifest.length} PNGs (23 required + generation battles); 360/390/430 and 125% large text; no browser errors\n`);
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error.stack || String(error)); process.exitCode = 1; });
