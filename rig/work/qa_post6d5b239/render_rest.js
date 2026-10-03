// Post-6d5b239 regression: rest in 5 views (rig's own Rest check + live canvas grab) and a turned-hand pose.
const puppeteer = require('/workspace/jt/node_modules/puppeteer-core');
const fs = require('fs'), path = require('path'); const OUT = __dirname;
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'], headless: 'new' });
  const res = {};
  for (const v of (process.argv[2]||'apose,tpose,left,right,back').split(',')) {
    const pg = await b.newPage(); await pg.setViewport({ width: 1600, height: 1100 });
    const logs = [];
    pg.on('console', m => { if (['error', 'warn', 'warning'].includes(m.type())) logs.push(m.type() + ': ' + m.text()); });
    pg.on('pageerror', e => logs.push('pageerror: ' + e));
    pg.on('response', r => { if (r.status() >= 400 && !r.url().endsWith('favicon.ico')) logs.push('HTTP ' + r.status() + ' ' + r.url()); });
    pg.on('requestfailed', r => logs.push('failed ' + r.url() + ' ' + (r.failure() || {}).errorText));
    await pg.goto(`http://127.0.0.1:8765/rig/index.html?view=${v}`, { waitUntil: 'domcontentloaded', timeout: 120000 });
    await pg.waitForFunction('typeof R!=="undefined" && R && !R.loading', { timeout: 120000 });
    await sleep(1500);
    await pg.evaluate(() => { document.getElementById('auto').checked = false; document.getElementById('rest').click(); });
    await sleep(500);
    await pg.evaluate(() => { document.getElementById('check').click(); });
    await sleep(500);
    const st = await pg.evaluate(() => document.getElementById('status').textContent);
    const grab = async n => { const d = await pg.evaluate(() => { draw(); return document.getElementById('c').toDataURL('image/png') }); fs.writeFileSync(path.join(OUT, n), Buffer.from(d.split(',')[1], 'base64')); };
    await grab(`rest_${v}.png`);
    const r = { restCheck: st, handAngles: await pg.evaluate(() => Object.fromEntries(Object.entries(R.handAngles || {}).map(([s, x]) => [s, (x.E || []).map(e => e.deg + ':' + (e.src || '') + (e.generated ? ':generated' : ''))]))) };
    // turned-hand pose
    const turned = {};
    for (const deg of [45, 90, 135, -45]) {
      await pg.evaluate((deg) => { document.getElementById('autohands').checked = false; set('WristTwistL', deg / 180); set('WristTwistR', deg / 180); draw(); }, deg);
      await sleep(400);
      turned[deg] = await pg.evaluate(() => { const f = s => { const t = window.RigTwist.handState(s); return t ? Object.fromEntries(Object.entries(t).filter(([k, x]) => x == null || typeof x !== 'object' || Array.isArray(x))) : null }; return { L: f('L'), R: f('R') } });
      await grab(`turned_${v}_${deg}.png`);
    }
    await pg.evaluate(() => document.getElementById('rest').click()); await sleep(300);
    await grab(`rest_after_turn_${v}.png`);
    r.turned = turned;
    r.console = logs; res[v] = r; await pg.close();
  }
  fs.writeFileSync(path.join(OUT, 'render_rest_'+(process.argv[2]||'all')+'.json'), JSON.stringify(res, null, 1));
  await b.close();
})().catch(e => { console.error(e); process.exit(1) });
