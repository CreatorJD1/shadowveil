import puppeteer from '/workspace/jt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
import fs from 'fs';
const [page_,views,out]=[process.argv[2],process.argv[3].split(','),process.argv[4]];
const browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--disable-dev-shm-usage']});
for(const vw of views){const p=await browser.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));
 await p.goto('http://127.0.0.1:8765/rig/'+page_+'?view='+vw,{waitUntil:'networkidle0',timeout:120000});await p.waitForFunction(()=>typeof R!=='undefined'&&R&&R.z,{timeout:120000});
 for(const seal of ['0','1']){const r=await p.evaluate((seal)=>{mqRunning=true;document.getElementById('seal').value=seal;for(const k in P)v[k]=P[k][2];v.BodyLean=0.3;v.ShoulderL=0.3;v.ShoulderR=-0.2;v.ElbowL=0.3;v.HipL=0.1;v.HipR=0.1;v.KneeL=-0.1;v.KneeR=-0.1;v.HeadTilt=0.5;v.HairSwayX=0.4;
  const c=document.createElement('canvas');c.width=W;c.height=H;const g=guard(c.getContext('2d'));const t0=performance.now();renderFinal(g,false);const ms=performance.now()-t0;for(const k in P)v[k]=P[k][2];return{png:c.toDataURL('image/png'),ms}},seal);
  fs.writeFileSync(`${out}/${vw}_seal${seal}.png`,Buffer.from(r.png.split(',')[1],'base64'));console.log(vw,'seal',seal,'ms',r.ms.toFixed(0))}
 console.log(vw,'errs',errs);await p.close()}
await browser.close();
