const puppeteer = require('/workspace/jt/node_modules/puppeteer-core');
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'], headless: 'new' });
  const pg = await b.newPage(); pg.on('pageerror', e => console.log('ERR', String(e))); pg.on('console', m => console.log('CON', m.text().slice(0,200)));
  pg.on('response', r => { if (r.status() >= 400) console.log('HTTP', r.status(), r.url()); });
  await pg.goto('http://127.0.0.1:8765/app/driver/index.html', { waitUntil: 'domcontentloaded' });
  for (let i = 0; i < 20; i++) { await sleep(2000); console.log(i, await pg.evaluate(() => JSON.stringify({ ready: window.SVDriver && SVDriver.ready, rigs: window.SVDriver && SVDriver.rigReady(), ph: window.SVDriver && SVDriver.state.phase, fr: window.SVDriver && SVDriver.state.frame }))); }
  const t = Date.now(); await pg.evaluate(() => SVDriver.preload(1, 232)); console.log('preload ms', Date.now() - t);
  await b.close();
})();
