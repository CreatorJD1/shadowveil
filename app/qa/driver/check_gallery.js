// Load every page of every group in app/cleanroom/gallery.html; count broken images/videos and failed requests.
const puppeteer = require('/workspace/jt/node_modules/puppeteer-core');
const BASE = process.argv[2] || 'http://127.0.0.1:8765';
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const br = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const pg = await br.newPage(); await pg.setViewport({ width: 1400, height: 12000 });
  const failed = [];
  pg.on('requestfailed', r => { const e = (r.failure() || {}).errorText || ''; if (!e.includes('ERR_ABORTED')) failed.push(r.url() + ' ' + e); });
  pg.on('response', r => { if (r.status() >= 400) failed.push(r.status() + ' ' + r.url()); });
  await pg.goto(BASE + '/app/cleanroom/gallery.html', { waitUntil: 'networkidle2' });
  const M = await pg.evaluate(() => fetch('gallery.json').then(r => r.json()));
  let imgs = 0, vids = 0, datas = 0; const broken = [];
  const from = process.argv[3] ? M.groups.findIndex(g => g.id === process.argv[3]) : 0;
  for (const g of M.groups.slice(from)) {
    const pages = Math.ceil(g.items.length / 48);
    for (let p = 0; p < pages; p++) {
      await pg.goto(`${BASE}/app/cleanroom/gallery.html?g=${g.id}&p=${p}`, { waitUntil: 'domcontentloaded', timeout: 180000 });
      await pg.waitForFunction(() => [...document.images].every(i => i.complete), { timeout: 240000 }).catch(() => {});
      await pg.waitForFunction(() => [...document.querySelectorAll('video')].every(v => v.readyState >= 1 || v.error), { timeout: 240000 }).catch(() => {});
      const r = await pg.evaluate(() => ({
        imgs: document.images.length, vids: document.querySelectorAll('video').length, datas: document.querySelectorAll('.it.data').length,
        bad: [...[...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => 'IMG ' + i.src), ...[...document.querySelectorAll('video')].filter(v => v.error || v.readyState < 1).map(v => `VIDEO rs=${v.readyState} ${v.dataset.src}`),
              ...[...document.querySelectorAll('.cap')].filter(c => /failed/.test(c.textContent)).map(c => 'CAP ' + c.textContent)] }));
      imgs += r.imgs; vids += r.vids; datas += r.datas; broken.push(...r.bad);
    }
    console.log(g.id, g.items.length, 'pages', pages, 'broken so far', broken.length, 'failed', failed.length);
  }
  // data files: fetch each once
  const dataBad = await pg.evaluate(async () => { const M = await fetch('gallery.json').then(r => r.json()); const bad = [];
    for (const g of M.groups) for (const it of g.items) if (it.k === 'data') { const r = await fetch(M.base + it.p, { method: 'HEAD' }); if (!r.ok) bad.push(r.status + ' ' + it.p); } return bad; });
  console.log('TOTAL', JSON.stringify({ imgs, vids, datas, broken: broken.length, failed: failed.length, dataBad: dataBad.length, files: M.total }));
  for (const b of [...broken, ...failed, ...dataBad].slice(0, 50)) console.log('  ', b);
  await br.close();
})().catch(e => { console.error(e); process.exit(1); });
