// apose: rest check + sway renders, live body vs ?hairless=1 (Body live_patch_staged base_body/base_body_skin), quality=linear
const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');const fs=require('fs');
const POSES=[['rest',null],['sx+1',{HairSwayX:1}],['sx-1',{HairSwayX:-1}],['sx+1sy+1',{HairSwayX:1,HairSwayY:1}],['sx-1sy+1',{HairSwayX:-1,HairSwayY:1}],['sx+1sy-1',{HairSwayX:1,HairSwayY:-1}],['sx-1sy-1',{HairSwayX:-1,HairSwayY:-1}],['sy+1',{HairSwayY:1}],['sy-1',{HairSwayY:-1}]];
(async()=>{const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new'});const res={};
for(const [tag,q] of [['live',''],['hairless','&hairless=1']]){const pg=await b.newPage();const errs=[],urls=[];pg.on('pageerror',e=>errs.push(String(e)));pg.on('response',r=>{if(/base_body/.test(r.url()))urls.push(r.status()+' '+r.url().replace(/^.*?8765/,''))});
 await pg.goto('http://127.0.0.1:8765/rig/index.html?view=apose&quality=linear'+q,{waitUntil:'domcontentloaded',timeout:120000});
 await pg.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:120000});await new Promise(r=>setTimeout(r,1500));
 const r=await pg.evaluate(async POSES=>{document.getElementById('auto').checked=false;pauseManual();
  const cmp=(A,B)=>{let n=0;for(let i=0;i<A.length;i+=4){if(A[i+3]===0&&B[i+3]===0)continue;if(A[i]!==B[i]||A[i+1]!==B[i+1]||A[i+2]!==B[i+2]||A[i+3]!==B[i+3])n++}return n};
  const bc=document.createElement('canvas');bc.width=W;bc.height=H;const gb=bc.getContext('2d');gb.drawImage(R.im.base,0,0);const B=gb.getImageData(0,0,W,H).data;
  document.getElementById('rest').click();await new Promise(z=>setTimeout(z,200));const rp=cmp(restPixels(),B);draw();const fr=cmp(FR.getContext('2d').getImageData(0,0,W,H).data,B);
  document.getElementById('check').click();const rc=document.getElementById('status').textContent.split('\n')[0];
  const out={restPixels_vs_base:rp,liveFR_vs_base:fr,restCheck:rc,img:{}};
  for(const [t,ps] of POSES){for(const k in P)v[k]=P[k][2];if(ps)for(const k in ps)v[k]=ps[k];const c=document.createElement('canvas');c.width=W;c.height=H;const g=guard(c.getContext('2d'));render(g,!ps);out.img[t]=c.toDataURL('image/png')}
  for(const k in P)v[k]=P[k][2];draw();return out},POSES);
 for(const t in r.img)fs.writeFileSync(`${tag}_${t}.png`,Buffer.from(r.img[t].split(',')[1],'base64'));delete r.img;res[tag]={...r,errs,bodyUrls:[...new Set(urls)]};await pg.close()}
console.log(JSON.stringify(res,null,1));await b.close()})().catch(e=>{console.error(e);process.exit(1)});
