const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');const fs=require('fs');
(async()=>{const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new'});const res={};
for(const [tag,q] of [['live',''],['hairless','&hairless=1']]){const pg=await b.newPage();
 await pg.goto('http://127.0.0.1:8765/rig/index.html?view=apose&quality=linear'+q,{waitUntil:'domcontentloaded',timeout:120000});
 await pg.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:120000});await new Promise(r=>setTimeout(r,1500));
 const r=await pg.evaluate(()=>{document.getElementById('auto').checked=false;pauseManual();const o={has:{WristL:!!P.WristL,WristR:!!P.WristR}};
  for(const [t,ps] of [['L+1',{WristL:1}],['L-1',{WristL:-1}],['R+1',{WristR:1}],['R-1',{WristR:-1}]]){for(const k in P)v[k]=P[k][2];for(const k in ps)if(P[k])v[k]=ps[k];const c=document.createElement('canvas');c.width=W;c.height=H;const g=guard(c.getContext('2d'));render(g,false);o[t]=c.toDataURL('image/png')}
  for(const k in P)v[k]=P[k][2];return o});
 for(const t of['L+1','L-1','R+1','R-1'])fs.writeFileSync(`wrist_${tag}_${t}.png`,Buffer.from(r[t].split(',')[1],'base64'));res[tag]=r.has;await pg.close()}
console.log(JSON.stringify(res));await b.close()})();
