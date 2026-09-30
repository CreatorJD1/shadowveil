// #preview "Pose driver (Clean room)" tab: driver loads inside the app iframe with 0 failed media requests. usage: node check_preview_tab.js [base] (env AUTH=user:pass)
const puppeteer = require('/workspace/jt/node_modules/puppeteer-core');
const BASE = process.argv[2] || 'http://127.0.0.1:8765';
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const br = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const pg = await br.newPage(); await pg.setViewport({ width: 1600, height: 1000 });
  if (process.env.AUTH) { const i = process.env.AUTH.indexOf(':'); await pg.authenticate({ username: process.env.AUTH.slice(0, i), password: process.env.AUTH.slice(i + 1) }); }
  const failed = [], errs = []; let n = 0;
  pg.on('requestfailed', r => { const e = (r.failure() || {}).errorText || ''; if (!e.includes('ERR_ABORTED')) failed.push(r.url() + ' ' + e); });
  pg.on('response', r => { n++; if (r.status() >= 400 && !r.url().endsWith('favicon.ico')) failed.push(r.status() + ' ' + r.url()); });
  pg.on('pageerror', e => errs.push(String(e)));
  await pg.goto(BASE + '/app/#preview?src=drv', { waitUntil: 'domcontentloaded', timeout: 120000 }); console.error('nav');
  let fr = null; for (let i = 0; i < 120 && !fr; i++) { fr = pg.frames().find(f => f.url().includes('/app/driver/')); if (!fr) await sleep(500); }
  if (!fr) throw new Error('driver iframe not found'); console.error('iframe', fr.url());
  await fr.waitForFunction('window.SVDriver && SVDriver.ready', { timeout: 120000 });
  console.error('ready'); await fr.evaluate(() => { SVDriver.setOpt({ speed: 2 }); SVDriver.setAuto(true); });
  const seen = []; const t0 = Date.now();
  while (Date.now() - t0 < 25000) { const p = await fr.evaluate(() => SVDriver.state.phase); if (seen[seen.length - 1] !== p) seen.push(p); if (seen.join('>').includes('idle>turn>hold>drift>idle')) break; await sleep(80); }
  console.error('seen', seen.join('>'));
  // white-flash skip in the driver's talk panel: one synthetic white frame must be skipped (canvas keeps the held frame)
  await fr.evaluate(() => { SVDriver.setAuto(false); SVDriver.scrubTo(0); SVDriver.startTalk(); }); await sleep(3000);
  const flash = await fr.evaluate(() => { const before = tctx.getImageData(0, 0, 768, 1168).data.slice(); const orig = tctx.drawImage; const n0 = SVDriver.state.flashSkips;
    tctx.drawImage = function () { tctx.fillStyle = '#fff'; tctx.fillRect(0, 0, 768, 1168); }; talkKey(); tctx.drawImage = orig;
    const a = tctx.getImageData(0, 0, 768, 1168).data; let d = 0; for (let i = 0; i < a.length; i += 4) if (a[i] !== before[i]) d++; return { skipsAdded: SVDriver.state.flashSkips - n0, changedPx: d, t: SVDriver.video.currentTime }; });
  const broken = await fr.evaluate(() => [...document.images].filter(i => i.complete && i.naturalWidth === 0).map(i => i.src));
  await pg.screenshot({ path: '/workspace/shadowveil/app/qa/driver/preview_tab' + (process.env.AUTH ? '_tunnel' : '') + '.png' });
  console.log(JSON.stringify({ base: BASE.replace(/\/\/.*@/, '//'), seen: seen.join('>'), flash, broken, failed, errs, responses: n }, null, 1));
  await br.close();
})().catch(e => { console.error(String(e)); process.exit(1); });
