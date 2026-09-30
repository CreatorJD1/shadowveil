// renders head-param poses per view to PNGs (rest + HeadTilt/HeadNod extremes, alone and with BodyLean) for the neck seam gap check
import puppeteer from '/workspace/jt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
import fs from 'fs';
const [page_,views,out]=[process.argv[2],process.argv[3].split(','),process.argv[4]];
const browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--disable-dev-shm-usage']});
const poses={rest:null,tiltP:{HeadTilt:1},tiltM:{HeadTilt:-1},nodP:{HeadNod:1},nodM:{HeadNod:-1},tiltP_leanM:{HeadTilt:1,BodyLean:-1},nodP_leanP:{HeadNod:1,BodyLean:1},zero:{}};
for(const v of views){const p=await browser.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));
 await p.goto('http://127.0.0.1:8765/rig/'+page_+'?view='+v,{waitUntil:'networkidle0',timeout:120000});await p.waitForFunction(()=>typeof R!=='undefined'&&R&&R.z,{timeout:120000});
 const neck=await p.evaluate(()=>R.neck);
 for(const [n,ps] of Object.entries(poses)){
  const url=await p.evaluate((ps)=>{mqRunning=true;for(const k in P)v[k]=P[k][2];hairDrive=null;const c=document.createElement('canvas');c.width=W;c.height=H;const g=guard(c.getContext('2d'));
   if(ps===null)renderFinal(g,true);else{for(const k in ps)v[k]=ps[k];renderFinal(g,false)}for(const k in P)v[k]=P[k][2];mqRunning=false;return c.toDataURL('image/png')},ps);
  fs.writeFileSync(`${out}/${v}_${n}.png`,Buffer.from(url.split(',')[1],'base64'))}
 console.log(JSON.stringify({view:v,neck,errs}));await p.close()}
await browser.close();
