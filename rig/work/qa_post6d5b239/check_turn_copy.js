// v2 driver check: authored turn frames only, handoffs only at handoff frames, cycle, frame strip, alignment at handoffs.
// usage: node check_turn.js [driverURL] (env AUTH=user:pass)
const puppeteer = require('/workspace/jt/node_modules/puppeteer-core');
const fs = require('fs'), path = require('path');
const OUT = '/workspace/shadowveil/rig/work/qa_post6d5b239/driver_turn';
const URL_ = process.argv[2] || 'http://127.0.0.1:8765/app/driver/index.html';
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--disable-dev-shm-usage', '--autoplay-policy=no-user-gesture-required'], headless: 'new' });
  const pg = await b.newPage(); await pg.setViewport({ width: 1500, height: 1000 });
  if (process.env.AUTH) { const i = process.env.AUTH.indexOf(':'); await pg.authenticate({ username: process.env.AUTH.slice(0, i), password: process.env.AUTH.slice(i + 1) }); }
  const failed = [], errors = [], urls = [];
  pg.on('requestfailed', r => { const e = (r.failure() || {}).errorText || ''; if (!e.includes('ERR_ABORTED')) failed.push(r.url() + ' ' + e); });
  pg.on('response', r => { urls.push(r.url()); if (r.status() >= 400 && !r.url().endsWith('favicon.ico')) failed.push(r.url() + ' HTTP ' + r.status()); });
  pg.on('pageerror', e => errors.push(String(e)));
  await pg.goto(URL_, { waitUntil: 'domcontentloaded', timeout: 120000 });
  await pg.waitForFunction('window.SVDriver && SVDriver.ready', { timeout: 120000 });
  await pg.waitForFunction(() => Object.values(SVDriver.rigReady()).every(Boolean) && Object.keys(SVDriver.rigReady()).length === 4, { timeout: 120000 }).catch(() => {});
  const rigs = await pg.evaluate(() => SVDriver.rigReady());
  await pg.evaluate(() => SVDriver.preload(1, 232));
  const grab = async n => { const d = await pg.evaluate(() => document.getElementById('stage').toDataURL('image/png')); fs.writeFileSync(path.join(OUT, n), Buffer.from(d.split(',')[1], 'base64')); };
  // 1) cycle at speed 2: sample state; live parts (w>0) may only show on handoff frames
  await pg.evaluate(() => { SVDriver.setOpt({ speed: 2 }); SVDriver.setAuto(true); });
  const seen = [], badHandoff = [], wFrames = new Set(); const t0 = Date.now(); let n = 0;
  while (Date.now() - t0 < 60000) { const s = await pg.evaluate(() => SVDriver.state); n++;
    if (seen[seen.length - 1] !== s.phase) seen.push(s.phase);
    if (s.last && s.last.w > 0.001) { wFrames.add(s.last.frame + ':' + s.last.view); if (![1, 62, 109, 160].includes(s.last.frame)) badHandoff.push(s.last); }
    if (seen.join('>').split('idle>turn>hold>drift>idle').length > 3) break; await sleep(40); }
  const hist = await pg.evaluate(() => SVDriver.state.history);
  await pg.evaluate(() => SVDriver.setAuto(false));
  // 2) frame strip: anchors + mids (manual dial, no release -> frame only) and handoff crossfades
  const shots = [1, 17, 33, 47, 62, 75, 87, 98, 109, 120, 132, 146, 160, 175, 191, 212, 232];
  await pg.evaluate(() => SVDriver.setOpt({ sway: false }));
  for (const f of shots) { await pg.evaluate(f => SVDriver.scrubTo(f), f); await sleep(420); await pg.evaluate(() => SVDriver.drawNow()); await sleep(120); await grab(`f${String(f).padStart(3, '0')}.png`); }
  // 3) handoffs: whole scaled frame vs whole live view (rig), 50 % crossfade, pixel difference per view
  const align = {};
  for (const [f, v] of [[1, 'apose'], [62, 'left'], [109, 'back'], [160, 'right']]) {
    await pg.evaluate(f => SVDriver.scrubTo(f), f); await sleep(400);
    for (const [w, tag] of [[0, 'frame'], [0.5, 'mid'], [1, 'live']]) { await pg.evaluate((w, v) => SVDriver.setW(w, v), w, v); await sleep(60); await pg.evaluate(() => SVDriver.drawNow()); await sleep(60); await grab(`handoff_${v}_${tag}.png`); }
    align[v] = await pg.evaluate(async (f, v) => {
      SVDriver.setW(0, v); await SVDriver.drawNow(); const A = document.getElementById('stage').getContext('2d').getImageData(0, 0, 1365, 1739).data.slice();
      const B = document.querySelector(`iframe[src*="view=${v}"]`).contentDocument.getElementById('c').getContext('2d').getImageData(0, 0, 1365, 1739).data;
      let i1 = 0, u = 0, sum = 0, cnt = 0, big = 0; const bb = (m) => m;
      let ay = [1e9, 0], by = [1e9, 0];
      for (let y = 0; y < 1739; y++) for (let x = 0; x < 1365; x++) { const j = (y * 1365 + x) * 4; const a = A[j + 3] > 128, b = B[j + 3] > 128;
        if (a && b) { i1++; const d = (Math.abs(A[j] - B[j]) + Math.abs(A[j + 1] - B[j + 1]) + Math.abs(A[j + 2] - B[j + 2])) / 3; sum += d; cnt++; if (d > 40) big++; }
        if (a || b) u++; if (a) { ay[0] = Math.min(ay[0], y); ay[1] = Math.max(ay[1], y); } if (b) { by[0] = Math.min(by[0], y); by[1] = Math.max(by[1], y); } }
      return { frame: f, iou: +(i1 / u).toFixed(4), mismatch_px: u - i1, meanAbsRGB_overlap: +(sum / cnt).toFixed(2), overlap_px_diff_gt40: big, frame_top_bottom: ay, live_top_bottom: by }; }, f, v);
  }
  await pg.evaluate(() => SVDriver.setW(0));
  // 4) no-hold frames: releasing the dial on f057 / f164 must not rest there
  const nohold = {}; for (const f of [57, 164]) { await pg.evaluate(f => SVDriver.scrubTo(f, true), f); await sleep(100); nohold[f] = await pg.evaluate(() => SVDriver.state.frame); }
  // 5) talk at f001 + white-flash skip
  await pg.evaluate(() => SVDriver.scrubTo(1, true)); await sleep(500); await pg.evaluate(() => SVDriver.startTalk()); await sleep(3000);
  const talk = await pg.evaluate(() => { const st = SVDriver.state; const before = tctx.getImageData(0, 0, 768, 1168).data.slice(); const orig = tctx.drawImage; const n0 = st.flashSkips;
    tctx.drawImage = function () { tctx.fillStyle = '#fff'; tctx.fillRect(0, 0, 768, 1168); }; talkKey(); tctx.drawImage = orig; const a = tctx.getImageData(0, 0, 768, 1168).data; let d = 0; for (let i = 0; i < a.length; i += 4) if (a[i] !== before[i]) d++;
    return { talk: st.talk, t: SVDriver.video.currentTime, rs: SVDriver.video.readyState, flashSkipAdded: SVDriver.state.flashSkips - n0, changedPx: d }; });
  await pg.evaluate(() => SVDriver.scrubTo(62)); await sleep(200); talk.stoppedAwayFromFront = !(await pg.evaluate(() => SVDriver.state.talk));
  await pg.screenshot({ path: path.join(OUT, 'page.png') });
  const broken = await pg.evaluate(() => [...document.images].filter(i => i.complete && i.naturalWidth === 0).map(i => i.src));
  const generated = urls.filter(u => /layers\/rotation\/turn-/.test(u));
  const res = { url: URL_.replace(/\/\/[^/]*@/, '//'), rigs, seen: seen.join('>'), samples: n, liveFrames: [...wFrames], badHandoff, align, nohold, talk, generatedStillRequests: generated, turnFrameRequests: urls.filter(u => /apose_turn\/frames\/f\d+\.png/.test(u)).length, failed, errors, broken, history: hist };
  fs.writeFileSync(path.join(OUT, 'check_turn.json'), JSON.stringify(res, null, 1));
  const { history, ...short } = res; console.log(JSON.stringify(short, null, 1));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
