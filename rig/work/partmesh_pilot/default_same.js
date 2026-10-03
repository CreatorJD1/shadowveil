// Live default unchanged: FR pixels of the patched rig (no flags) vs the pre-edit backup copy, same poses, per view.
const puppeteer = require('/workspace/jt/node_modules/puppeteer-core');
const crypto = require('crypto'); const sleep = ms => new Promise(r => setTimeout(r, ms));
const POSES = [{}, { HairSwayX: 1 }, { HairSwayX: -1, HairSwayY: 0.5 }, { HandRMiddle: 0.87, HandLMiddle: 0.5, HandRIndex: 1 }, { WristTwistL: 0.25, WristTwistR: -0.25 }, { ElbowL: 0.6, KneeR: 0.4, HeadTilt: 0.5 }];
(async () => {
  const views = (process.argv[2] || 'apose,tpose,left,right,back').split(','), q = process.argv[3] || '';
  const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--disable-dev-shm-usage'], headless: 'new' });
  const out = {};
  for (const v of views) for (const page of ['index.html', 'index_qa_backup.html']) {
    const pg = await b.newPage(); const errs = []; pg.on('pageerror', e => errs.push(String(e)));
    await pg.goto(`http://127.0.0.1:${process.env.PORT||8765}/rig/${page}?view=${v}${q}`, { waitUntil: 'domcontentloaded', timeout: 300000 });
    await pg.waitForFunction('typeof R!=="undefined" && R && !R.loading', { timeout: 300000 }); await sleep(1200);
    const hs = await pg.evaluate(async (POSES) => {
      document.getElementById('auto').checked = false; document.getElementById('autohands').checked = false; const r = [];
      for (const ps of POSES) { document.getElementById('rest').click(); for (const k in ps) if (P[k] && !inputs[k].disabled) set(k, ps[k]); draw(); await new Promise(z => setTimeout(z, 50)); draw();
        const d = FR.getContext('2d').getImageData(0, 0, W, H).data; let h = 0; for (let i = 0; i < d.length; i++) h = (h * 31 + d[i]) | 0; r.push(h) }
      return r }, POSES);
    (out[v] = out[v] || {})[page] = { hashes: hs, errs }; await pg.close();
  }
  for (const v in out) { const a = out[v]['index.html'].hashes, c = out[v]['index_qa_backup.html'].hashes; out[v].identical = a.map((x, i) => x === c[i]); }
  console.log(JSON.stringify(out)); await b.close();
})().catch(e => { console.error(e); process.exit(1) });
