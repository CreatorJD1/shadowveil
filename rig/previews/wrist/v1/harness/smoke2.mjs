import puppeteer from '/workspace/jt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
import fs from 'fs';
const browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--disable-dev-shm-usage']});
const p=await browser.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('http://127.0.0.1:8765/rig/index.v19-next.html?view=tpose',{waitUntil:'networkidle0',timeout:240000});await p.waitForFunction(()=>typeof R!=='undefined'&&R&&R.z&&R.claw,{timeout:240000});
const r=await p.evaluate(()=>{document.getElementById('auto').checked=false;const out={claw:R.claw,lbl:document.getElementById('rotlbl').textContent};mqRunning=true;
 const shots={};for(const [n,ps] of Object.entries({open:{},claw:{HandLClaw:1,HandRClaw:1},fist:{HandLIndex:1,HandLMiddle:1,HandLRing:1,HandLPinky:1}})){for(const k in P)v[k]=P[k][2];for(const k in ps)v[k]=ps[k];const c=document.createElement('canvas');c.width=W;c.height=H;renderFinal(guard(c.getContext('2d')),false);shots[n]=c.toDataURL('image/png')}
 for(const k in P)v[k]=P[k][2];mqRunning=false;return{out,shots}});
for(const n in r.shots)fs.writeFileSync('/tmp/wr/claw_'+n+'.png',Buffer.from(r.shots[n].split(',')[1],'base64'));
await p.click('#rotR');await new Promise(q=>setTimeout(q,1500));const v1=await p.evaluate(()=>document.getElementById('view').value+' '+document.getElementById('rotlbl').textContent);
await p.click('#rotR');await new Promise(q=>setTimeout(q,1500));const v2=await p.evaluate(()=>document.getElementById('view').value);
await p.click('#rotR');await p.click('#rotR');await new Promise(q=>setTimeout(q,1500));const v3=await p.evaluate(()=>document.getElementById('view').value);
console.log(JSON.stringify(r.out),'rot:',v1,'|',v2,'|',v3,'errs',JSON.stringify(errs));await browser.close();
