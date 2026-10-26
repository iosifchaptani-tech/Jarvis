// Renders one PNG letter per promoter code.
// node render.js <outDir>
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const outDir = process.argv[2];
const template = fs.readFileSync(path.join(__dirname, 'letter.html'), 'utf8');
const letters = [
  { code: 'TEAM10-FHL3', uses: 'Works for the first 10 orders, once per customer' },
  { code: 'DUO10-QQ3H', uses: 'Works for the first 2 orders, once per customer' },
  { code: 'GIFT10-5LTH', uses: 'Works for 1 order' },
];

(async () => {
  const browser = await chromium.launch();
  for (const l of letters) {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
    const html = template.replace('{{CODE}}', l.code).replace('{{USES}}', l.uses);
    await page.setContent(html, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    const overflow = await page.evaluate(() => {
      const card = document.querySelector('.card');
      return card.scrollHeight - card.clientHeight;
    });
    const file = path.join(outDir, `Pivendo-letter-${l.code}.png`);
    const bulbs = await page.evaluate(() => document.querySelectorAll('#bulbs ellipse').length);
    await page.screenshot({ path: file });
    await page.close();
    console.log(file, 'overflow:', overflow, 'bulbs:', bulbs);
  }
  await browser.close();
})();
