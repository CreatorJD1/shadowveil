// Headless check of app/driver: media failures, state-machine cycle, frame strip every 45° + mid-blends.
const puppeteer = require('/workspace/jt/node_modules/puppeteer-core');
const fs = require('fs'), path = require('path');
const OUT = '/workspace/shadowveil/app/qa/driver';
const BASE = process.argv[2] || 'http://127.0.0.1:8765/app/driver/index.html';
(async () => {
  const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'], headless: 'new' });
  const pg = await b.newPage(); await pg.setViewport({ width: 1500, height: 1000 });
  const failed = [], errors = [], resp = [];
  pg.on('requestfailed', r => failed.push(r.url() + ' ' + (r.failure() || {}).errorText));
  pg.on('response', r => { if (r.status() >= 400) failed.push(r.url() + ' HTTP ' + r.status()); resp.push(r.url()); });
  pg.on('pageerror', e => errors.push(String(e))); pg.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  await pg.goto(BASE, { waitUntil: 'networkidle0' });
  await pg.waitForFunction('window.SVDriver && SVDriver.ready', { timeout: 60000 });
  const grab = async (name) => { const d = await pg.evaluate(() => document.getElementById('stage').toDataURL('image/png')); fs.writeFileSync(path.join(OUT, name), Buffer.from(d.split(',')[1], 'base64')); };
  // 1) state machine cycle (auto, speed 2)
  await pg.evaluate(() => { SVDriver.setOpt({ speed: 2 }); SVDriver.setAuto(true); });
  const seen = []; const t0 = Date.now(); let k = 0;
  while (Date.now() - t0 < 30000) { const s = await pg.evaluate(() => SVDriver.state); if (!seen.length || seen[seen.length - 1] !== s.phase) seen.push(s.phase);
    if (s.phase === 'turn' && k < 3) { await grab(`cycle_turn_${k}.png`); k++; }
    if (seen.join('>').includes('idle>turn>hold>drift>idle>turn>hold>drift>idle')) break; await new Promise(r => setTimeout(r, 60)); }
  const hist = await pg.evaluate(() => SVDriver.state.history);
  // 2) frame strip every 45° (skip policy) + mid blends
  await pg.evaluate(() => SVDriver.setAuto(false));
  const frames = {};
  for (const pol of ['skip', 'hold']) {
    await pg.evaluate(p => SVDriver.setOpt({ policy: p, sway: false }), pol);
    for (const a of [0, 45, 90, 135, 180, 225, 270, 315, 22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]) {
      await pg.evaluate(a => SVDriver.scrubTo(a), a); await new Promise(r => setTimeout(r, 250)); await pg.evaluate(() => SVDriver.drawNow()); await new Promise(r => setTimeout(r, 150));
      const s = await pg.evaluate(() => SVDriver.state); frames[pol + '@' + a] = s.blend;
      const nm = `${pol}_${String(a).replace('.', '_').padStart(5, '0')}.png`; await grab(nm);
    }
  }
  // 3) toggles: hair hide + eyes/hands off at 0°
  await pg.evaluate(() => { SVDriver.setOpt({ policy: 'skip', hair: false }); SVDriver.scrubTo(0); }); await new Promise(r => setTimeout(r, 2500)); await pg.evaluate(() => SVDriver.drawNow()); await new Promise(r => setTimeout(r, 300)); await grab('hair_hidden_000.png');
  await pg.evaluate(() => { SVDriver.setOpt({ hair: false }); SVDriver.scrubTo(270); }); await new Promise(r => setTimeout(r, 2500)); await pg.evaluate(() => SVDriver.drawNow()); await new Promise(r => setTimeout(r, 300)); await grab('hair_hidden_270.png');
  await pg.evaluate(() => { SVDriver.setOpt({ hair: true, eyes: false, hands: false }); SVDriver.scrubTo(0); }); await new Promise(r => setTimeout(r, 1500)); await pg.evaluate(() => SVDriver.drawNow()); await new Promise(r => setTimeout(r, 300)); await grab('overlays_off_000.png');
  await pg.evaluate(() => { SVDriver.setOpt({ eyes: true, hands: true }); }); 
  // overlay-on vs off pixel difference at 0°
  // 4) talk at the front
  await pg.evaluate(() => { SVDriver.scrubTo(0); SVDriver.startTalk(); }); await new Promise(r => setTimeout(r, 4000));
  const talk = await pg.evaluate(() => ({ talk: SVDriver.state.talk, t: SVDriver.video.currentTime, rs: SVDriver.video.readyState, err: SVDriver.video.error && SVDriver.video.error.code, skips: SVDriver.state.flashSkips }));
  const tdu = await pg.evaluate(() => document.getElementById('talkcv').toDataURL('image/png')); fs.writeFileSync(path.join(OUT, 'talk_frame.png'), Buffer.from(tdu.split(',')[1], 'base64'));
  await pg.evaluate(() => SVDriver.scrubTo(90)); await new Promise(r => setTimeout(r, 300));
  const talkAt90 = await pg.evaluate(() => SVDriver.state.talk);
  await pg.screenshot({ path: path.join(OUT, 'page.png') });
  const broken = await pg.evaluate(() => [...document.images].filter(i => i.complete && i.naturalWidth === 0).map(i => i.src));
  const res = { seen: seen.join('>'), history: hist, frames, talk, talkStoppedAt90: !talkAt90, failed, errors, broken, requests: resp.length };
  fs.writeFileSync(path.join(OUT, 'check_driver.json'), JSON.stringify(res, null, 1));
  console.log(JSON.stringify({ seen: res.seen, talk, talkStoppedAt90: res.talkStoppedAt90, failed, errors, broken, requests: resp.length }, null, 1));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
