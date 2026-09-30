// Patched Clean room page: layer toggles must change the video frame (masking) and the white-flash skip must hold the last frame.
const puppeteer = require('/workspace/jt/node_modules/puppeteer-core');
const fs = require('fs');
const BASE = process.argv[2] || 'http://127.0.0.1:8765';
const OUT = '/workspace/shadowveil/app/qa/driver/';
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const br = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', args: ['--no-sandbox', '--autoplay-policy=no-user-gesture-required'] });
  const pg = await br.newPage(); await pg.setViewport({ width: 1500, height: 1000 });
  const failed = [];
  pg.on('requestfailed', r => { const e = (r.failure() || {}).errorText || ''; if (!e.includes('ERR_ABORTED')) failed.push(r.url() + ' ' + e); });
  pg.on('response', r => { if (r.status() >= 400) failed.push(r.status() + ' ' + r.url()); });
  const errs = []; pg.on('pageerror', e => errs.push(String(e)));
  await pg.goto(BASE + '/app/cleanroom/index.html', { waitUntil: 'networkidle2' });
  await sleep(2500); console.error('loaded', await pg.evaluate(() => ({ id: current.id, rs: video.readyState, hidden: document.getElementById('stage-wrap').hidden })));
  const hash = () => pg.evaluate(() => { const d = ctx.getImageData(0, 0, stage.width, stage.height).data; let h = 0, s = 0; for (let i = 0; i < d.length; i += 97) { h = (h * 31 + d[i]) | 0; s += d[i]; } return { h, s, w: stage.width }; });
  const freeze = async t => { await pg.evaluate(t => new Promise(r => { video.pause(); const to = setTimeout(r, 4000); video.onseeked = () => { clearTimeout(to); r(); }; video.currentTime = t; }), t); console.error('frozen'); await sleep(300); await pg.evaluate(() => keyFrame()); await sleep(100); };
  const res = { clip: await pg.evaluate(() => current.id) };
  await freeze(1.0); const A = await hash();
  const shot = async n => { const d = await pg.evaluate(() => stage.toDataURL('image/png')); fs.writeFileSync(OUT + n, Buffer.from(d.split(',')[1], 'base64')); };
  await shot('cleanroom_all_on.png');
  res.toggles = {};
  for (const name of ['Hair', 'Face', 'Eyes', 'Body', 'Plate']) {
    console.error('toggle', name); await pg.evaluate(n => [...document.querySelectorAll('#layers button')].find(b => b.textContent === n).click(), name);
    await sleep(80); await pg.evaluate(() => keyFrame()); await sleep(80);
    const B = await hash(); res.toggles[name] = { changed: B.h !== A.h, sumRatio: +(B.s / A.s).toFixed(3) };
    if (name === 'Hair') await shot('cleanroom_hair_off.png');
    console.error('toggle', name); await pg.evaluate(n => [...document.querySelectorAll('#layers button')].find(b => b.textContent === n).click(), name);
    await sleep(80); await pg.evaluate(() => keyFrame());
    const C = await hash(); res.toggles[name].restored = C.h === A.h;
  }
  // white flash: feed one all-white frame through keyFrame (test-only patch of drawImage) -> canvas must keep the held frame
  res.flash = await pg.evaluate(() => { const before = ctx.getImageData(0, 0, stage.width, stage.height).data; const orig = ctx.drawImage;
    ctx.drawImage = function () { ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, stage.width, stage.height); };
    keyFrame(); ctx.drawImage = orig;
    const after = ctx.getImageData(0, 0, stage.width, stage.height).data; let diff = 0, white = 0; for (let i = 0; i < after.length; i += 4) { if (after[i] !== before[i]) diff++; if (after[i] > 245 && after[i + 1] > 245 && after[i + 2] > 245) white++; }
    return { changedPx: diff, whitePx: white, total: after.length / 4 }; });
  // talk clips: play each, held-frame lane must say "No held frame" without a request
  res.talk = [];
  await pg.evaluate(() => [...document.querySelectorAll('#tabs button, button[data-kind]')].find(b => b.dataset.kind === 'talk')?.click()); await sleep(800);
  for (const id of await pg.evaluate(() => VIDEOS.filter(v => v.kind === 'talk').map(v => v.id))) {
    await pg.evaluate(id => [...document.querySelectorAll('button[data-id]')].find(b => b.dataset.id === id).click(), id); await sleep(2500);
    res.talk.push(await pg.evaluate(() => ({ id: current.id, rs: video.readyState, t: +video.currentTime.toFixed(2), err: video.error && video.error.code,
      lanes: [...document.querySelectorAll('#layers .lane')].map(l => l.querySelector('button').textContent + ':' + (l.querySelector('.track').textContent || (l.querySelector('img') ? 'img' : ''))).join(' | '),
      brokenImgs: [...document.querySelectorAll('#layers img')].filter(i => i.complete && i.naturalWidth === 0).length })));
  }
  res.failed = failed; res.errors = errs;
  fs.writeFileSync(OUT + 'check_cleanroom_toggles.json', JSON.stringify(res, null, 1));
  console.log(JSON.stringify(res, null, 1));
  await br.close();
})().catch(e => { console.error(e); process.exit(1); });
