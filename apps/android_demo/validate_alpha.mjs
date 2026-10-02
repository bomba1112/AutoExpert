import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdir} from 'node:fs/promises';
import path from 'node:path';

const require = createRequire(import.meta.url);
const {chromium} = require('playwright');

const baseUrl = process.env.AUTOEXPERT_PREVIEW_URL || 'http://127.0.0.1:8000/preview/';
const chromePath = process.env.CHROME_BIN;
const artifactDir = path.resolve(process.env.AUTOEXPERT_ARTIFACT_DIR || 'artifacts');

if (!chromePath) throw new Error('CHROME_BIN is required');
await mkdir(artifactDir, {recursive: true});

const browser = await chromium.launch({
  executablePath: chromePath,
  headless: true,
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});

const context = await browser.newContext({
  viewport: {width: 369, height: 816},
  deviceScaleFactor: 3.25,
  isMobile: true,
  hasTouch: true,
  locale: 'ru-RU',
});
const page = await context.newPage();
page.setDefaultTimeout(30_000);

const results = {};

function record(name) {
  results[name] = 'PASS';
  process.stdout.write(`${name}=PASS\n`);
}

async function expectHash(fragment) {
  await page.waitForFunction((value) => location.hash.startsWith(value), fragment);
}

async function expectNoOverflow() {
  const dimensions = await page.evaluate(() => ({
    width: window.innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  assert.ok(
    dimensions.scrollWidth <= dimensions.width,
    `horizontal overflow: ${dimensions.scrollWidth} > ${dimensions.width}`,
  );
}

async function selectLanguage(code, homeTitle) {
  await page.locator(`[data-action="language-choice"][data-language="${code}"]`).click();
  await page.locator('[data-action="language-continue"]').click();
  await expectHash('#/home');
  await page.getByRole('heading', {name: homeTitle}).waitFor();
  await expectNoOverflow();
}

try {
  await page.goto(baseUrl, {waitUntil: 'domcontentloaded'});
  await page.getByRole('heading', {name: 'Выберите язык'}).waitFor();
  await selectLanguage('ru', 'Узнайте всё важное об автомобиле до покупки');
  record('RU_HOME');

  await page.locator('[data-action="vin-start"]').first().click();
  await expectHash('#/vin');
  await page.locator('#vin').fill('3FA6P0HD0KR114795');
  await page.locator('#vin-form').evaluate((form) => form.requestSubmit());
  await expectHash('#/report/');
  await page.locator('.report-cover h1').filter({hasText: 'Ford Fusion'}).waitFor();
  await page.getByText('DEVELOPER ACCESS', {exact: true}).waitFor();
  assert.equal(await page.locator('[data-action="unlock"]').count(), 0);
  assert.equal(await page.getByText('4T1', {exact: false}).count(), 0);
  assert.match(await page.locator('body').innerText(), /Полное досье автомобиля/);
  assert.match(await page.locator('body').innerText(), /Источники/);
  assert.doesNotMatch(await page.locator('body').innerText(), /evidence items/i);
  await expectNoOverflow();
  await page.screenshot({path: path.join(artifactDir, 'android-alpha-report.png')});
  record('FORD_VIN_DEVELOPER_ACCESS');
  record('DOSSIER_AND_SOURCES');

  await page.locator('[data-action="chat-start"]').click();
  await expectHash('#/chat/');
  await page.getByText('В DEMO вопросы без лимита', {exact: false}).waitFor();
  await page.locator('#chat-question').fill('Что проверить перед покупкой?');
  await page.locator('#chat-form').evaluate((form) => form.requestSubmit());
  await page.waitForFunction(() => document.querySelectorAll('.chat-message.assistant').length >= 2);
  assert.match(await page.locator('.chat-thread').innerText(), /Auto Expert/);
  record('GROUNDED_CHAT_UNLIMITED');

  await page.locator('[data-action="chat-report"]').click();
  await expectHash('#/report/');
  await page.locator('[data-action="toggle-paywall"]').click();
  await expectHash('#/precheck/');
  const teaserText = await page.locator('body').innerText();
  assert.match(teaserText, /Разблокировать историю/);
  assert.match(teaserText, /5[,.]?00?\s*AZN|5\s*AZN/);
  assert.match(teaserText, /Деньги не списываются/);
  await page.locator('[data-action="unlock"]').click();
  await expectHash('#/payment/');
  await page.getByText('Тестовая разблокировка', {exact: true}).waitFor();
  await page.locator('[data-action="unlock-confirm"]').click();
  await expectHash('#/report/');
  await page.locator('.report-cover h1').filter({hasText: 'Ford Fusion'}).waitFor();
  record('SIMULATE_USER_PAYWALL');

  await page.locator('[data-action="reports"]').last().click();
  await expectHash('#/reports');
  await page.getByRole('heading', {name: /Ford Fusion/}).waitFor();
  await page.reload({waitUntil: 'domcontentloaded'});
  await expectHash('#/reports');
  await page.getByRole('heading', {name: /Ford Fusion/}).waitFor();
  record('MY_REPORTS_REFRESH_PERSISTENCE');

  await page.locator('[data-action="change-language"]').click();
  await expectHash('#/language');
  await selectLanguage('az', 'Avtomobil haqqında vacib məlumatları almadan əvvəl öyrənin');
  record('AZ_HOME');
  await page.locator('[data-action="change-language"]').click();
  await expectHash('#/language');
  await selectLanguage('en', 'Know what matters before you buy the car');
  record('EN_HOME');
  await page.locator('[data-action="change-language"]').click();
  await expectHash('#/language');
  await selectLanguage('ru', 'Узнайте всё важное об автомобиле до покупки');

  await page.locator('[data-action="vin-start"]').first().click();
  await page.locator('#identifier-market').selectOption('KOREA');
  await page.locator('#vin').fill('KLABA76BDJB723118');
  await page.locator('#vin-form').evaluate((form) => form.requestSubmit());
  await expectHash('#/research/');
  await page.getByText('Исследование завершено частично', {exact: true}).waitFor();
  assert.doesNotMatch(await page.locator('body').innerText(), /контрольн.*символ|checksum/i);
  record('KOREAN_VIN_ACCEPTED');

  const reconnectPage = await context.newPage();
  await reconnectPage.addInitScript(() => {
    window.AUTOEXPERT_API_ROOT = 'http://127.0.0.1:65534/api/v1';
  });
  await reconnectPage.goto(baseUrl, {waitUntil: 'domcontentloaded'});
  await reconnectPage.getByRole('heading', {name: 'Сервис временно недоступен'}).waitFor();
  await reconnectPage.evaluate(() => {
    window.AUTOEXPERT_API_ROOT = 'http://127.0.0.1:8000/api/v1';
  });
  await reconnectPage.locator('[data-action="reconnect"]').click();
  await reconnectPage.getByRole('heading', {name: 'Узнайте всё важное об автомобиле до покупки'}).waitFor();
  await reconnectPage.close();
  record('BACKEND_UNAVAILABLE_RECONNECT');

  await page.screenshot({path: path.join(artifactDir, 'android-alpha-korean-vin.png')});
  process.stdout.write(`ALPHA_FLOW_RESULTS=${JSON.stringify(results)}\n`);
} finally {
  await context.close();
  await browser.close();
}
