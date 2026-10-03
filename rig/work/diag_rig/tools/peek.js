const puppeteer = require('/workspace/jt/node_modules/puppeteer-core');
(async () => { const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--disable-dev-shm-usage'], headless: 'new' });
  const pg = await b.newPage(); const errs = []; pg.on('pageerror', e => errs.push(String(e))); pg.on('console', m => errs.push(m.type() + ': ' + m.text())); pg.on('requestfailed', r => errs.push('REQFAIL ' + r.url()));
  pg.on('response', r => { if (r.status() >= 400) errs.push(r.status() + ' ' + r.url()) });
  await pg.goto(process.argv[2], { waitUntil: 'domcontentloaded' }); await new Promise(r => setTimeout(r, +process.argv[3] || 25000));
  if (process.argv[4]) console.log(await pg.evaluate(async () => { try { await load(); return 'ok' } catch (e) { return e.stack } }));
  console.log(await pg.evaluate(() => JSON.stringify({ st: document.getElementById('status').textContent, view: document.getElementById('view').value, R: typeof R !== 'undefined' && R ? { loading: R.loading } : null })));
  console.log(errs.slice(0, 40).join('\n')); await b.close() })();
