// smoke + pose renders for ?diag=1 slots. node smoke.js <port> <page> <views> [extraQuery]
const puppeteer = require('/workspace/jt/node_modules/puppeteer-core'); const fs = require('fs');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const [port, page, views, xq] = [process.argv[2], process.argv[3], process.argv[4].split(','), process.argv[5] || ''];
const OUT = '/workspace/shadowveil/rig/work/diag_rig/renders/' + (process.argv[6] || 'default');
const BODY = ['BodyLean', 'ShoulderL', 'ShoulderR', 'ElbowL', 'ElbowR', 'HipL', 'HipR', 'KneeL', 'KneeR', 'AnkleL', 'AnkleR'];
const POSES = { rest: {} };
for (const k of BODY) { POSES[k + '+1'] = { [k]: 1 }; POSES[k + '-1'] = { [k]: -1 } }
POSES['all+1'] = Object.fromEntries(BODY.map(k => [k, 1])); POSES['all-1'] = Object.fromEntries(BODY.map(k => [k, -1]));
Object.assign(POSES, { 'gaze_X+1': { EyeBallX: 1 }, 'gaze_X-1': { EyeBallX: -1 }, 'gaze_Y-1': { EyeBallY: -1 }, 'gaze_Y+1': { EyeBallY: 1 }, 'gaze_X+1Y+1': { EyeBallX: 1, EyeBallY: 1 },
  'blink': { EyeLOpen: 0, EyeROpen: 0 }, 'fist': Object.fromEntries(['L', 'R'].flatMap(s => ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky'].map(f => ['Hand' + s + f, 1]))),
  'head': { HeadTilt: 1, HeadNod: 0.5 }, 'wrist_try': { WristL: 1, WristR: -1 }, 'hair': { HairSwayX: 1 }, 'mouth_try': { MouthOpen: 1 } });
(async () => {
  const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--disable-dev-shm-usage'], headless: 'new', protocolTimeout: 1800000 });
  const res = {};
  for (const v of views) {
    const pg = await b.newPage(); const errs = []; pg.on('pageerror', e => errs.push(String(e))); pg.on('console', m => { if (m.type() === 'error') errs.push('console: ' + m.text()) });
    await pg.goto(`http://127.0.0.1:${port}/rig/${page}?diag=1&view=${v}${xq}`, { waitUntil: 'domcontentloaded', timeout: 300000 });
    await pg.waitForFunction('typeof R!=="undefined" && R && !R.loading', { timeout: 150000 }); await sleep(1500);
    const r = await pg.evaluate(async (POSES) => {
      document.getElementById('auto').checked = false; document.getElementById('autohands').checked = false;
      const out = { status: document.getElementById('status').textContent, warn: R.warn.slice(), skin: !!R.skin, eyes: !!R.eyes, mouth: !!R.mouth, hands: R.hands ? R.hands.parts.length : 0, hair: (R.hair || []).length, locks: R.diag && R.diag.locks, shots: {}, applied: {} };
      document.getElementById('check').click(); await new Promise(z => setTimeout(z, 300)); out.rest = document.getElementById('status').textContent.split('\n')[0];
      const cv = document.createElement('canvas'); const cr = R.diag.crop; cv.width = cr[2]; cv.height = cr[3]; const g = cv.getContext('2d');
      for (const n in POSES) { document.getElementById('rest').click(); const ps = POSES[n]; const ap = {};
        for (const k in ps) if (P[k]) { set(k, ps[k]); ap[k] = inputs[k].disabled ? 'disabled' : ps[k] }
        draw(); await new Promise(z => setTimeout(z, 80)); draw(); out.applied[n] = Object.assign(ap, { _v: Object.fromEntries(Object.keys(ps).map(k => [k, v[k]])) });
        g.clearRect(0, 0, cv.width, cv.height); g.drawImage(FR, cr[0], cr[1], cr[2], cr[3], 0, 0, cr[2], cr[3]); out.shots[n] = cv.toDataURL('image/png') }
      document.getElementById('rest').click(); draw(); return out }, POSES);
    fs.mkdirSync(`${OUT}/${v}`, { recursive: true });
    for (const n in r.shots) fs.writeFileSync(`${OUT}/${v}/${n}.png`, Buffer.from(r.shots[n].split(',')[1], 'base64'));
    delete r.shots; r.errs = errs; res[v] = r; await pg.close();
  }
  fs.writeFileSync(`${OUT}/smoke.json`, JSON.stringify(res, null, 1)); console.log(JSON.stringify(Object.fromEntries(Object.entries(res).map(([k, x]) => [k, { rest: x.rest, errs: x.errs, warn: x.warn, skin: x.skin, eyes: x.eyes, mouth: x.mouth, hands: x.hands, hair: x.hair, locks: x.locks }])), null, 1));
  await b.close();
})().catch(e => { console.error(e); process.exit(1) });
