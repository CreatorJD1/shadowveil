// live front rig (apose) baseline renders for --bend-check: each joint param 0/+1/-1 (25 deg; BodyLean 8 deg, the live limit), body-only (LP solo sys:body) and full
const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');const fs=require('fs');
const PORT=process.env.PORT||8793,OUT='/workspace/shadowveil/rig/work/bend_check/live',VIEW=process.env.VIEW||'apose';
const PAR=['BodyLean','HipL','HipR','ShoulderL','ShoulderR','ElbowL','ElbowR','HeadTilt','HeadNod'];
(async()=>{const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new',protocolTimeout:1800000});
const pg=await b.newPage();const errs=[];pg.on('pageerror',e=>errs.push(String(e)));
await pg.goto(`http://127.0.0.1:${PORT}/rig/index.html?view=${VIEW}&quality=nearest`,{waitUntil:'domcontentloaded',timeout:600000});await pg.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:600000});await new Promise(r=>setTimeout(r,1500));
const meta=await pg.evaluate(()=>({bones:R.skin.bones.map(x=>({id:x.id||x.name,param:x.param,pivot:x.pivot,parent:x.parent})),headPivot:R.neck}));fs.writeFileSync(`${OUT}/${VIEW}_meta.json`,JSON.stringify(meta));
for(const p of PAR)for(const x of [0,1,-1]){if(x===0&&p!==PAR[0])continue;for(const solo of ['body','full']){
 const d=await pg.evaluate((p,x,solo)=>{pauseManual();document.getElementById('auto').checked=false;for(const k in P)set(k,P[k][2]);if(p in P)set(p,x);LP.solo=new Set(solo==='body'?['sys:body']:[]);draw();LP.solo=new Set();return FR.toDataURL('image/png')},p,x,solo);
 fs.writeFileSync(`${OUT}/${VIEW}__${x===0?'rest':p+(x>0?'+1':'-1')}__${solo}.png`,Buffer.from(d.split(',')[1],'base64'))}}
console.log(JSON.stringify({errs}));await b.close()})().catch(e=>{console.error(e);process.exit(1)});
