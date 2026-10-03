// per view: render live (posed path at rest values, as the frozen rig at a handoff) without and with the head group offset; dump PNGs + member check
const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');const fs=require('fs');
(async()=>{const views=(process.argv[2]||'apose,left,back,right').split(','),out=process.argv[3]||'.';
const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new'});const res={};
for(const v of views){const pg=await b.newPage();const errs=[];pg.on('pageerror',e=>errs.push(String(e)));
 await pg.goto(`http://127.0.0.1:${process.env.PORT||8765}/rig/index.html?view=${v}&quality=linear&headgroup=1`,{waitUntil:'domcontentloaded',timeout:120000});
 await pg.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:120000});await new Promise(r=>setTimeout(r,1500));
 const r=await pg.evaluate(async vw=>{document.getElementById('auto').checked=false;pauseManual();for(const k in P)v[k]=P[k][2];
  const grab=rest=>{const c=document.createElement('canvas');c.width=W;c.height=H;const g=c.getContext('2d');g.__S=1;render(g,rest);return c.toDataURL('image/png')};
  RigHeadGroup.reset();const a0=grab(false),r0=grab(true);const h=await RigHeadGroup.applyHandoff(vw);const a1=grab(false),r1=grab(true);const hg=RigHeadGroup.get();RigHeadGroup.reset();const a2=grab(false);
  return{h,hg,a0,r0,a1,r1,back0:a2===a0}},v);
 for(const k of['a0','r0','a1','r1'])fs.writeFileSync(`${out}/${v}_${k}.png`,Buffer.from(r[k].split(',')[1],'base64'));
 res[v]={handoff:r.h,applied:r.hg,resetRestoresExactly:r.back0,errs};await pg.close()}
console.log(JSON.stringify(res));await b.close()})().catch(e=>{console.error(e);process.exit(1)});
