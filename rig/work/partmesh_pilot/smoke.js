const puppeteer = require('/workspace/jt/node_modules/puppeteer-core');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const [page, views, q] = [process.argv[2] || 'index.html', (process.argv[3] || 'tpose').split(','), process.argv[4] || ''];
  const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--disable-dev-shm-usage'], headless: 'new' });
  const out = {};
  for (const v of views) {
    const pg = await b.newPage(); const errs = [];
    pg.on('pageerror', e => errs.push(String(e))); pg.on('console', m => { if (m.type() === 'error') errs.push(m.text()) });
    pg.on('response', r => { if (r.status() >= 400 && !r.url().endsWith('favicon.ico')) errs.push('HTTP ' + r.status() + ' ' + r.url()) });
    await pg.goto(`http://127.0.0.1:8765/rig/${page}?view=${v}${q}`, { waitUntil: 'domcontentloaded', timeout: 120000 });
    await pg.waitForFunction('typeof R!=="undefined" && R && !R.loading', { timeout: 120000 }); await sleep(1200);
    out[v] = await pg.evaluate(async () => {
      document.getElementById('auto').checked = false; document.getElementById('rest').click(); await new Promise(r => setTimeout(r, 300));
      const cmp = (A, B) => { let n = 0; for (let i = 0; i < A.length; i += 4) { if (A[i + 3] === 0 && B[i + 3] === 0) continue; if (A[i] !== B[i] || A[i + 1] !== B[i + 1] || A[i + 2] !== B[i + 2] || A[i + 3] !== B[i + 3]) n++ } return n };
      const bc = document.createElement('canvas'); bc.width = W; bc.height = H; const gb = bc.getContext('2d'); gb.drawImage(R.im.base, 0, 0); const B = gb.getImageData(0, 0, W, H).data;
      const rp = restPixels(); draw(); const L = FR.getContext('2d').getImageData(0, 0, W, H).data;
      document.getElementById('check').click();
      return { restCheck: document.getElementById('status').textContent.split('\n')[0], restPixels_vs_base: cmp(rp, B), liveFR_vs_base: cmp(L, B), quality: QUAL, pm: window.RigPartMesh ? RigPartMesh.parts : null, pmWarn: R.warn.filter(w => /partmesh/.test(w)), handAngles: Object.fromEntries(Object.entries(R.handAngles || {}).map(([s, x]) => [s, x.E.map(e => e.src)])) };
    });
    out[v].errors = errs; await pg.close();
  }
  console.log(JSON.stringify(out)); await b.close();
})().catch(e => { console.error(e); process.exit(1) });
