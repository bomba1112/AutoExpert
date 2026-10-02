/* One-listing UI flow smoke on a local QA database. No Turbo.az HTTP fetch. */
'use strict';

const { chromium } = require(process.env.PLAYWRIGHT_MODULE);
const base = (process.env.AUTOEXPERT_QA_BASE_URL || 'http://127.0.0.1:8773').replace(/\/$/, '');
let externalRequests = 0;

async function run() {
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_EXECUTABLE || undefined,
    headless: true,
    args: ['--no-sandbox'],
  });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await page.route(/^https?:\/\/(?:[^/]+\.)?turbo\.az\//i, route => {
    externalRequests++;
    return route.abort();
  });
  const issues = [];
  page.on('pageerror', error => issues.push(error.message));
  let serial = 0;
  async function go(route) {
    if (!serial) {
      await page.goto(`${base}/preview/#/language`);
      await page.evaluate(() => localStorage.setItem('autoexpert.ui.language', 'ru'));
    }
    await page.goto(`${base}/preview/?listing_smoke=${++serial}#${route}`);
    await page.locator(route === '/check/manual' ? '#listing-manual-form' : '#listing-import-form')
      .waitFor({ timeout: 45000 });
  }
  async function submitAndRead(form) {
    await page.locator(`${form} button[type="submit"]`).click();
    await page.waitForURL(/#\/listing-result\//, { timeout: 60000 });
    await page.locator('.listing-hero').waitFor({ timeout: 60000 });
    return page.locator('#app').innerText();
  }
  try {
    await go('/check/turbo');
    await page.locator('#listing-import-form [name="source_url"]').fill('https://turbo.az/autos/12345990?utm_source=qa');
    let text = await submitAndRead('#listing-import-form');
    if (!text.includes('Ссылка сохранена') || !text.includes('вставьте текст объявления')) {
      throw new Error('URL reference incorrectly parsed or fallback missing');
    }

    await go('/check/turbo');
    await page.locator('#listing-import-form [name="source_url"]').fill('https://turbo.az/autos/12345991');
    await page.locator('#listing-import-form [name="text"]').fill(
      'Марка: Toyota\nМодель: Camry\nГод: 2018\nДвигатель: 3.5 л\nТопливо: бензин\nКоробка: автомат\nПривод: передний\nHansı bazar üçün yığılıb: Amerika'
    );
    text = await submitAndRead('#listing-import-form');
    if (!text.includes('Указано в объявлении') || !text.includes('Найдена соответствующая версия')) {
      throw new Error('Pasted text not matched or seller claims missing');
    }

    await go('/check/turbo');
    await page.locator('#listing-import-form [name="html_file"]').setInputFiles({
      name: 'qa-listing.html', mimeType: 'text/html',
      buffer: Buffer.from('<html><script>window.QA_XSS=true</script><h1>Toyota Camry, 2018 il</h1><dl><dt>Marka</dt><dd>Toyota</dd><dt>Model</dt><dd>Camry</dd><dt>Buraxılış ili</dt><dd>2018</dd><dt>Mühərrik</dt><dd>3.5 L</dd></dl></html>'),
    });
    text = await submitAndRead('#listing-import-form');
    if (!text.includes('Toyota Camry') || text.includes('QA_XSS')) {
      throw new Error('HTML snapshot did not render sanitized claims');
    }
    const xss = await page.evaluate(() => Boolean(window.QA_XSS));
    if (xss) throw new Error('HTML snapshot script executed');

    await go('/check/manual');
    for (const [name, value] of Object.entries({
      make: 'Toyota', model: 'Camry', year: '2018', engine: '3.5 L',
      fuel: 'бензин', transmission: 'автомат', drivetrain: 'передний', market: 'Amerika',
    })) await page.locator(`#listing-manual-form [name="${name}"]`).fill(value);
    text = await submitAndRead('#listing-manual-form');
    if (!text.includes('Найдена соответствующая версия')) {
      throw new Error('Manual entry did not match production catalog');
    }

    await go('/check/turbo');
    await page.locator('#listing-import-form [name="text"]').fill(
      'Марка: Ford\nМодель: Fusion\nГод: 2019\nVIN: 3FA6P0HD0KR114795'
    );
    await submitAndRead('#listing-import-form');
    await page.locator('[data-listing-action="vin"]').click();
    await page.locator('#vin').waitFor({ timeout: 30000 });
    const vin = await page.locator('#vin').inputValue();
    if (vin !== '3FA6P0HD0KR114795') throw new Error(`VIN CTA did not prefill validated VIN: ${vin}`);

    if (externalRequests) throw new Error(`${externalRequests} Turbo.az network requests occurred`);
    if (issues.length) throw new Error(`Browser errors: ${issues.join(' | ')}`);
    console.log('PASS: URL reference, pasted text, local HTML, manual input, validated VIN CTA; Turbo.az fetches=0');
  } finally {
    await browser.close();
  }
}

run().catch(error => { console.error(error.stack || String(error)); process.exitCode = 1; });
