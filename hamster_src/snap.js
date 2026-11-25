// Render selected times (or test scenes) to PNG for review: node snap.js out_dir t1 t2 ... | test:name
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [, , out, ...items] = process.argv;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', m => console.log('console:', m.text()));
  page.on('pageerror', e => console.log('PAGEERROR:', e.message));
  await page.goto('file://' + path.join(__dirname, 'index.html'));
  await page.evaluate(() => window.READY);
  for (const it of items) {
    if (it.startsWith('test:')) await page.evaluate(n => TESTS[n](), it.slice(5));
    else await page.evaluate(t => renderTime(+t), it);
    await page.screenshot({ path: path.join(out, it.replace(':', '_') + '.png') });
  }
  await browser.close();
})();
