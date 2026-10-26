// Renders one PNG letter per promoter code.
// node render.js <outDir>
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const outDir = process.argv[2];
const en = fs.readFileSync(path.join(__dirname, 'letter.html'), 'utf8');
const de = fs.readFileSync(path.join(__dirname, 'letter-de.html'), 'utf8');
// To add a new promoter code: add one English and one German line here.
const letters = [
  { template: en, name: 'Pivendo-letter', code: 'TEAM10-FHL3', uses: 'Works for the first 10 orders, once per customer' },
  { template: en, name: 'Pivendo-letter', code: 'DUO10-QQ3H', uses: 'Works for the first 2 orders, once per customer' },
  { template: en, name: 'Pivendo-letter', code: 'GIFT10-5LTH', uses: 'Works for 1 order' },
  { template: de, name: 'Pivendo-Brief-DE', code: 'TEAM10-FHL3', uses: 'Gilt für die ersten 10 Bestellungen, einmal pro Kunde' },
  { template: de, name: 'Pivendo-Brief-DE', code: 'DUO10-QQ3H', uses: 'Gilt für die ersten 2 Bestellungen, einmal pro Kunde' },
  { template: de, name: 'Pivendo-Brief-DE', code: 'GIFT10-5LTH', uses: 'Gilt für 1 Bestellung' },
];

(async () => {
  const browser = await chromium.launch();
  for (const l of letters) {
    const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
    const html = l.template.replace('{{CODE}}', l.code).replace('{{USES}}', l.uses);
    await page.setContent(html, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    const overflow = await page.evaluate(() => {
      const card = document.querySelector('.card');
      return card.scrollHeight - card.clientHeight;
    });
    const file = path.join(outDir, `${l.name}-${l.code}.png`);
    const bulbs = await page.evaluate(() => document.querySelectorAll('#bulbs ellipse').length);
    await page.screenshot({ path: file });
    await page.close();
    console.log(file, 'overflow:', overflow, 'bulbs:', bulbs);
  }
  await browser.close();
})();
