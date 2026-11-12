const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/usr/bin/chromium' });
  const p = await b.newPage({ viewport: { width: 1080, height: 1440 } });
  for (const v of ['A', 'B']) {
    await p.goto('file://' + __dirname + '/cover.html?v=' + v);
    await p.waitForTimeout(600);
    await p.screenshot({ path: __dirname + '/cover_' + v + '.png' });
  }
  await b.close();
})();
