// anger / anger_stress clip load + mouth pick + talk exclusion + rest check after clip, per view.
const puppeteer = require('/workspace/jt/node_modules/puppeteer-core');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'], headless: 'new' });
  const out = {};
  for (const v of (process.argv[2] || 'apose,tpose,left,right,back').split(',')) {
    const pg = await b.newPage(); const errs = [];
    pg.on('pageerror', e => errs.push(String(e))); pg.on('console', m => { if (m.type() === 'error') errs.push(m.text()) });
    pg.on('response', r => { if (r.status() >= 400 && !r.url().endsWith('favicon.ico')) errs.push('HTTP ' + r.status() + ' ' + r.url()) });
    await pg.goto(`http://127.0.0.1:8765/rig/index.html?view=${v}&clip=anger`, { waitUntil: 'domcontentloaded', timeout: 120000 });
    await pg.waitForFunction('typeof R!=="undefined" && R && !R.loading && window.SVClip && (SVClip.state.ready || SVClip.state.error)', { timeout: 120000 }); await sleep(1000);
    out[v] = await pg.evaluate(async () => {
      const r = { clipState: SVClip.state, shapes: (R.mouthShapes || []).map(s => s.name) };
      const probe = async (clip) => { activeClip = clip; document.getElementById('auto').checked = false; const picks = {}; for (const t of [0, 0.2, 0.3, 1, 2, 3]) { clipTime = t - 0.0001; for (const k in P) set(k, P[k][2]); playClip(0.0001); picks[t] = { pick: mouthPick(), MouthForm: +v.MouthForm.toFixed(3), MouthOpen: +v.MouthOpen.toFixed(3) } } return picks };
      r.anger = await probe(activeClip);
      const js = await (await fetch('previews/actions/v1/clips/anger_stress.json')).json(); r.stressFlag = js.clips.anger.stressTest;
      r.anger_stress = await probe(js.clips.anger);
      activeClip = null; document.getElementById('auto').checked = false; document.getElementById('rest').click();
      // talk exclusion: sweep the whole (MouthOpen, MouthForm) grid with mouthTalk on
      mouthTalk = true; const talkPicks = new Set(); for (let o = 0; o <= 1.0001; o += 0.05) for (let f = -1; f <= 1.0001; f += 0.05) { v.MouthOpen = o; v.MouthForm = f; talkPicks.add(mouthPick()) } mouthTalk = false;
      r.talkPicks = [...talkPicks]; r.talkPicksAnger = talkPicks.has('anger');
      document.getElementById('rest').click(); document.getElementById('check').click(); r.restCheck = document.getElementById('status').textContent.split('\n')[0];
      return r;
    });
    out[v].errors = errs; await pg.close();
  }
  console.log(JSON.stringify(out, null, 1)); await b.close();
})().catch(e => { console.error(e); process.exit(1) });
