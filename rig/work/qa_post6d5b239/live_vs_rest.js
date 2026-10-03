// In-page: live draw() frame buffer (FR) at Reset-to-rest vs the rig's rest render and base.png. No PNG round trip.
const puppeteer = require('/workspace/jt/node_modules/puppeteer-core');
const page = process.argv[2] || 'index.html', views = (process.argv[3] || 'apose').split(',');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'], headless: 'new' });
  const out = {};
  for (const v of views) {
    const pg = await b.newPage(); const errs = [];
    pg.on('pageerror', e => errs.push(String(e))); pg.on('console', m => { if (m.type() === 'error') errs.push(m.text()) });
    await pg.goto(`http://127.0.0.1:8765/rig/${page}?view=${v}${process.argv[4] || ''}`, { waitUntil: 'domcontentloaded', timeout: 120000 });
    await pg.waitForFunction('typeof R!=="undefined" && R && !R.loading', { timeout: 120000 }); await sleep(1500);
    out[v] = await pg.evaluate(async () => {
      document.getElementById('auto').checked = false; document.getElementById('rest').click(); await new Promise(r => setTimeout(r, 400));
      const cmp = (A, B) => { let n = 0; for (let i = 0; i < A.length; i += 4) { if (A[i + 3] === 0 && B[i + 3] === 0) continue; if (A[i] !== B[i] || A[i + 1] !== B[i + 1] || A[i + 2] !== B[i + 2] || A[i + 3] !== B[i + 3]) n++ } return n };
      const bc = document.createElement('canvas'); bc.width = W; bc.height = H; const gb = bc.getContext('2d'); gb.drawImage(R.im.base, 0, 0); const B = gb.getImageData(0, 0, W, H).data;
      const rp = restPixels(); draw();
      const L = FR.getContext('2d').getImageData(0, 0, W, H).data;
      const life = document.getElementById('life')?.value, q = document.getElementById('quality')?.value;
      return { restPixels_vs_base: cmp(rp, B), liveFR_vs_base: cmp(L, B), liveFR_vs_restPixels: cmp(L, rp), life, quality: q, scheme: R.scheme };
    });
    out[v].errors = errs; await pg.close();
  }
  console.log(JSON.stringify(out));
  await b.close();
})().catch(e => { console.error(e); process.exit(1) });
