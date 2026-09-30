// Headless check of the #reference section: failed image/media requests and broken <img>/<video> in all frames.
// usage: node check_reference.js [baseURL] [screenshot.png] [tabs,comma]  (env AUTH=user:pass for the gate)
const puppeteer = require('/workspace/jt/node_modules/puppeteer-core');
const BASE = process.argv[2] || 'http://127.0.0.1:8765';
const SHOT = process.argv[3] || '';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const isMedia = u => /\.(png|jpe?g|webp|gif|svg|mp4|webm|mov)(\?|#|$)/i.test(u);
(async () => {
  const br = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new',
    args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required', '--window-size=1600,1000'] });
  const pg = await br.newPage();
  await pg.setViewport({ width: 1600, height: 1000 });
  if (process.env.AUTH) { const [username, password] = process.env.AUTH.split(':'); await pg.authenticate({ username, password }); }
  await pg.goto(BASE + '/app/#reference', { waitUntil: 'networkidle2' });
  const R = await pg.evaluate(() => fetch('registry.json').then(r => r.json()));
  const sec = R.sections.find(s => s.id === 'reference');
  const pages = sec.pages.filter(p => p.exists !== false);
  let tabs = pages.map((p, i) => ({ k: 'p' + i, label: p.label, heavy: !!p.heavy, path: p.path })).concat([{ k: 'media', label: 'Media' }]);
  if (process.argv[4]) tabs = tabs.filter(t => process.argv[4].split(',').includes(t.k));
  const total = { failed: 0, brokenImg: 0, brokenVid: 0, imgs: 0, vids: 0 };
  for (const t of tabs) {
    const failed = [], okUrls = new Set();
    const onFail = r => { if (isMedia(r.url()) || r.resourceType() === 'image' || r.resourceType() === 'media') failed.push('FAILED ' + r.url() + ' ' + (r.failure()?.errorText || '')); };
    const onResp = r => { const u = r.url(); if (r.status() < 400) okUrls.add(u); if ((isMedia(u) || /\.json(\?|$)/.test(u)) && r.status() >= 400) failed.push(r.status() + ' ' + u); };
    pg.on('requestfailed', onFail); pg.on('response', onResp);
    await pg.evaluate((k, path) => { localStorage.setItem('sv.bot.reference', JSON.stringify(k)); if (path) localStorage.setItem('sv.ok.' + path, 'true'); }, t.k, t.path || '');
    await pg.reload({ waitUntil: 'networkidle2', timeout: 120000 }).catch(e => failed.push('NAV ' + e.message));
    await sleep(t.heavy ? 8000 : 4000);
    // inside iframes: click every tab-like button to trigger lazy loads, and scroll
    for (const f of pg.frames()) {
      if (f === pg.mainFrame()) continue;
      try { await f.evaluate(async () => { const s = ms => new Promise(r => setTimeout(r, ms));
        for (const b of [...document.querySelectorAll('button[data-tab],button[data-id],button[data-kind]')].slice(0, 80)) { try { b.click(); await s(150) } catch {} }
        window.scrollTo(0, document.body.scrollHeight); await s(500); window.scrollTo(0, 0); }); } catch {}
    }
    // media tab: scroll gallery so lazy videos attach
    await pg.evaluate(async () => { const sc = document.querySelector('#botbody .scroll'); if (sc) { for (let y = 0; y < sc.scrollHeight; y += 400) { sc.scrollTop = y; await new Promise(r => setTimeout(r, 300)) } sc.scrollTop = 0 } });
    await sleep(5000);
    let imgs = 0, vids = 0; const broken = [];
    // clean-room page keeps its <video> off-DOM (drawn into a canvas): probe every clip in its VIDEOS list
    for (const f of pg.frames()) {
      try {
        const r = await f.evaluate(async () => {
          if (typeof VIDEOS === 'undefined') return null;
          const probe = src => new Promise(res => { const v = document.createElement('video'); v.muted = true; v.preload = 'auto';
            const t = setTimeout(() => res(`VIDEO timeout rs=${v.readyState} ${v.src}`), 30000);
            v.onloadeddata = () => { clearTimeout(t); res(v.readyState >= 2 ? null : `VIDEO rs=${v.readyState} ${v.src}`) };
            v.onerror = () => { clearTimeout(t); res(`VIDEO err=${v.error && v.error.code} ${v.src}`) }; v.src = src; });
          const out = []; for (let i = 0; i < VIDEOS.length; i += 6) out.push(...await Promise.all(VIDEOS.slice(i, i + 6).map(x => probe(x.src))));
          return { n: VIDEOS.length, bad: out.filter(Boolean) };
        });
        if (r) { vids += r.n; broken.push(...r.bad.map(b => '[iframe VIDEOS] ' + b)); }
      } catch (e) {}
    }
    for (const f of pg.frames()) {
      try {
        const r = await f.evaluate(() => {
          const out = { imgs: 0, vids: 0, broken: [] };
          for (const i of document.querySelectorAll('img[src]')) { out.imgs++; if (i.complete && i.naturalWidth === 0) out.broken.push('IMG ' + i.currentSrc || i.src); }
          for (const v of document.querySelectorAll('video')) { const s = v.currentSrc || v.getAttribute('src') || v.dataset.src; if (!v.getAttribute('src') && !v.querySelector('source')) continue; out.vids++;
            if (v.error || v.readyState < 2) out.broken.push(`VIDEO rs=${v.readyState} err=${v.error ? v.error.code : ''} ${s}`); }
          return out;
        });
        imgs += r.imgs; vids += r.vids; broken.push(...r.broken.map(b => '[' + (f === pg.mainFrame() ? 'app' : 'iframe') + '] ' + b));
      } catch (e) { broken.push('frame eval error ' + e.message); }
    }
    pg.off('requestfailed', onFail); pg.off('response', onResp);
    const uniqFailed = [...new Set(failed)].filter(x => !(x.startsWith('FAILED ') && x.includes('ERR_ABORTED') && okUrls.has(x.split(' ')[1])));  // aborts from the page swapping video.src after a 200/206 are not failures
    const bi = broken.filter(b => b.includes('IMG')).length, bv = broken.filter(b => b.includes('VIDEO')).length;
    total.failed += uniqFailed.length; total.brokenImg += bi; total.brokenVid += bv; total.imgs += imgs; total.vids += vids;
    console.log(`== tab ${t.k} (${t.label}): imgs=${imgs} vids=${vids} brokenImg=${bi} brokenVid=${bv} failedReq=${uniqFailed.length}`);
    for (const x of uniqFailed.slice(0, 400)) console.log('   ' + x);
    for (const x of broken.slice(0, 400)) console.log('   ' + x);
    if (SHOT && t.k === 'p0') await pg.screenshot({ path: SHOT });
  }
  console.log('TOTAL', JSON.stringify(total));
  await br.close();
})().catch(e => { console.error(e); process.exit(1) });
