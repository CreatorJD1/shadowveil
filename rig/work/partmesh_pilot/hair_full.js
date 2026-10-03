const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');const fs=require('fs');
(async()=>{const [ss,out,q]=[process.argv[2].split(',').map(Number),process.argv[3],process.argv[4]||''];fs.mkdirSync(out,{recursive:true});
const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new'});
const pg=await b.newPage();const errs=[];pg.on('pageerror',e=>errs.push(String(e)));
await pg.goto('http://127.0.0.1:8765/rig/index.html?view=apose&quality=linear'+q,{waitUntil:'domcontentloaded',timeout:120000});
await pg.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:120000});await new Promise(r=>setTimeout(r,1500));
for(const s of ss){const url=await pg.evaluate(s=>{document.getElementById('auto').checked=false;pauseManual();for(const k in P)v[k]=P[k][2];v.HairSwayX=s;LP.active=false;
 const c=document.createElement('canvas');c.width=W;c.height=H;const g=c.getContext('2d');g.__S=1;render(g,false);return c.toDataURL('image/png')},s);fs.writeFileSync(`${out}/full_${s}.png`,Buffer.from(url.split(',')[1],'base64'))}
console.log(JSON.stringify({errs}));await b.close()})().catch(e=>{console.error(e);process.exit(1)});
