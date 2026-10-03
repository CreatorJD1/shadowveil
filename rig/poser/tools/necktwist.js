// renders apose rest, NeckTwist +1 and EyeBallX +1 through the rig's own render() to check the head-turn direction
const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');const fs=require('fs');
(async()=>{const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new',protocolTimeout:900000});
const pg=await b.newPage();await pg.goto('http://127.0.0.1:8796/rig/index.html?view=apose&quality=linear',{waitUntil:'domcontentloaded'});
await pg.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:900000,polling:1000});await new Promise(r=>setTimeout(r,1500));
const out=await pg.evaluate(()=>{document.getElementById('auto').checked=false;pauseManual();const o={};
 for(const [t,vals] of [['rest',{}],['neck_p1',{NeckTwist:1}],['eyex_p1',{EyeBallX:1}]]){for(const k in P)v[k]=P[k][2];Object.assign(v,vals);const c=document.createElement('canvas');c.width=W;c.height=H;render(guard(c.getContext('2d')),t==='rest');o[t]=c.toDataURL('image/png')}
 for(const k in P)v[k]=P[k][2];draw();return o});
for(const t in out)fs.writeFileSync('/tmp/nt_'+t+'.png',Buffer.from(out[t].split(',')[1],'base64'));await b.close()})();
