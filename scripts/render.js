const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const F = JSON.parse(fs.readFileSync(path.join(__dirname, 'film_data.json'), 'utf8'));
fs.writeFileSync(path.join(ROOT, 'film_data.js'), 'window.FILM=' + JSON.stringify(F) + ';\n');
const FPS = 30, SCALE = 1080 / 393;
const mode = process.argv[2] || 'qa';

async function newPage(browser) {
  const page = await browser.newPage({ viewport: { width: 393, height: 699 }, deviceScaleFactor: SCALE });
  page.on('pageerror', e => console.error('Page error:', e.message));
  page.on('console', m => { if (m.type() === 'error') console.error('Console:', m.text()); });
  await page.goto('file://' + path.join(__dirname, 'film.html'));
  await page.evaluate(() => document.fonts.ready);
  return page;
}
async function frame(page, t) {
  const html = await page.evaluate(t => { window.setTime(t); return document.getElementById('screen').innerHTML; }, t);
  await page.evaluate(() => Promise.all([...document.images].map(i => i.decode().catch(() => {}))));
  return html;
}
(async () => {
  const exe = process.env.CHROMIUM_PATH || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
  const browser = await chromium.launch({ executablePath: exe, headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  if (mode === 'qa') {
    const times = (process.argv[3] || '0.2,1.1,1.6,3.5,6.2,6.7,8.0,9.5,10.3,11.4,12.5,22.6,50.6,52.6,55,60,66.5,70,100.3,100.9,101.6,103,106.6,109,113,125').split(',').map(Number);
    fs.mkdirSync(path.join(ROOT, 'qa'), { recursive: true });
    const page = await newPage(browser);
    for (const t of times) {
      await frame(page, t);
      await page.screenshot({ path: path.join(ROOT, 'qa', `t_${t.toFixed(2)}.png`) });
    }
    console.log('QA frames rendered:', times.length);
  } else {
    const total = Math.round(F.duration * FPS);
    const workers = Number(process.env.WORKERS || 4);
    const dir = path.join(ROOT, 'frames');
    // FROM=<seconds>: keep every frame before it from the last full render (frames.ffconcat), re-render only the rest
    const from = process.env.FROM ? Math.round(Number(process.env.FROM) * FPS) : 0;
    const results = new Array(total);
    if (from) {
      const L = fs.readFileSync(path.join(ROOT, 'frames.ffconcat'), 'utf8').split('\n');
      let k = 0;
      for (let q = 0; q < L.length && k < from; q++) {
        const m = L[q].match(/^file '(.*)'$/); if (!m) continue;
        const d = L[q + 1] && L[q + 1].match(/^duration (.*)$/); if (!d) break;
        const n = Math.round(Number(d[1]) * FPS);
        for (let r = 0; r < n && k < from; r++) results[k++] = m[1];
      }
      if (k < from) throw new Error(`frames.ffconcat only covers ${k} frames, need ${from}`);
      console.log(`Keeping frames 0-${from - 1}, re-rendering ${from}-${total - 1}`);
    } else {
      fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
    }
    const per = Math.ceil((total - from) / workers);
    await Promise.all([...Array(workers).keys()].map(async w => {
      const page = await newPage(browser);
      let prevHtml = null, prevFile = null;
      for (let i = from + w * per; i < Math.min(total, from + (w + 1) * per); i++) {
        const t = i / FPS;
        const html = await frame(page, t);
        if (html === prevHtml) { results[i] = prevFile; continue; }
        const file = path.join(dir, `f${String(i).padStart(5, '0')}.png`);
        await page.screenshot({ path: file });
        results[i] = file; prevHtml = html; prevFile = file;
        if (i % 300 === 0) console.log(`Worker ${w}: frame ${i}/${total}`);
      }
    }));
    let list = '';
    let i = 0;
    while (i < total) { let j = i; while (j + 1 < total && results[j + 1] === results[i]) j++; list += `file '${results[i]}'\nduration ${((j - i + 1) / FPS).toFixed(6)}\n`; i = j + 1; }
    list += `file '${results[total - 1]}'\n`;
    fs.writeFileSync(path.join(ROOT, 'frames.ffconcat'), list);
    console.log('Unique frames:', new Set(results).size, 'of', total);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
