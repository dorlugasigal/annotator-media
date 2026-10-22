// Renders the fictional sample-app fixtures at 2x and records target rectangles (points, top-left origin).
import { chromium } from '../../../website/node_modules/playwright-core/index.mjs';
import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const names = ['dashboard', 'design', 'gallery'];
const browser = await chromium.launch();
const out = {};
for (const name of names) {
  const page = await browser.newPage({ viewport: { width: 1580, height: 690 }, deviceScaleFactor: 2 });
  await page.goto(`file://${root}/fixtures/${name}.html`);
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: `${root}/fixtures/${name}@2x.png`, omitBackground: false });
  out[name] = await page.evaluate(() => {
    const t = {};
    for (const el of document.querySelectorAll('[data-target]')) {
      const r = el.getBoundingClientRect();
      t[el.dataset.target] = { x: +r.x.toFixed(2), y: +r.y.toFixed(2), width: +r.width.toFixed(2), height: +r.height.toFixed(2) };
    }
    return { width: innerWidth, height: innerHeight, targets: t };
  });
  await page.close();
}
await browser.close();
writeFileSync(`${root}/fixtures/targets.json`, JSON.stringify(out, null, 2) + '\n');
console.log(JSON.stringify(out, null, 1));
