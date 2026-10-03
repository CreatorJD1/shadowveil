// ?palsnap=1 test: for each case render the FULL frame and per-part SOLO layers with palsnap / nearest / linear; dump PNGs + palettes.
const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');const fs=require('fs');
const PORT=process.env.PORT||8793,PAGE=process.env.PAGE||'rig/_ps_test.html',OUT=process.env.OUT||'rig/work/palsnap/out';
const CASES=JSON.parse(fs.readFileSync(process.argv[2]));
(async()=>{const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new',protocolTimeout:3600000});const meta={};
for(const view of Object.keys(CASES)){for(const mode of ['palsnap','nearest','linear']){
 const pg=await b.newPage();const errs=[];pg.on('pageerror',e=>errs.push(String(e)));
 await pg.goto(`http://127.0.0.1:${PORT}/${PAGE}?view=${view}&quality=${mode==='nearest'?'nearest':'linear'}${mode==='palsnap'?'&palsnap=1':''}`,{waitUntil:'domcontentloaded',timeout:600000});
 await pg.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:600000});await new Promise(r=>setTimeout(r,1000));
 if(!meta[view]){meta[view]=await pg.evaluate(()=>{const pal={};const add=(k,im)=>{if(!im||im.empty)return;const w=im.naturalWidth||im.width,h=im.naturalHeight||im.height;if(!w)return;const c=document.createElement('canvas');c.width=w;c.height=h;const q=c.getContext('2d');q.drawImage(im,0,0);const d=q.getImageData(0,0,w,h).data;const s=pal[k]||(pal[k]=new Set());for(let i=0;i<d.length;i+=4)if(d[i+3]>0)s.add((d[i]<<16)|(d[i+1]<<8)|d[i+2])};
  for(const k in R.im){const m=k.match(/^(\w+):(.*)$/);if(!m)continue;let g=m[1];if(g==='eyes'){const e=m[2].match(/^(EyeR|EyeL)/);g='eyes:'+(e?e[1]:'other')}add(g,R.im[k])}
  for(const id in (R.frames||{}))for(const f of R.frames[id])add('hands',f.img);if(R.skin)add('body',R.skin.img);add('base',R.im.base);
  const o={};for(const k in pal)o[k]=[...pal[k]];return{pal:o,P:Object.fromEntries(Object.entries(P).filter(([k])=>/Twist|Head|Elbow/.test(k))),strands:(R.hair||[]).filter(p=>p.file).map(p=>p.id),mouths:(R.mouth&&R.mouth.parts||[]).map(p=>p.id)}});
  fs.writeFileSync(`${OUT}/${view}_meta.json`,JSON.stringify(meta[view]))}
 for(const cs of CASES[view]){for(const solo of cs.solo){
  const r=await pg.evaluate(async(cs,solo)=>{pauseManual();document.getElementById('auto').checked=false;for(const k in P)set(k,P[k][2]);for(const k in cs.p)set(k,cs.p[k]);
   if(cs.mouth&&typeof mouthState!=='undefined'){window.mouthUpdate=()=>false;mouthState.cur=cs.mouth;mouthState.prev=cs.mouth;mouthState.t0=-1e9}
   LP.solo=new Set(solo==='full'?[]:[solo]);if(window.RigPalSnap)RigPalSnap.reset();const t0=performance.now();draw();const ms=performance.now()-t0;LP.solo=new Set();
   return{png:FR.toDataURL('image/png'),ms,stats:window.RigPalSnap?RigPalSnap.stats():null}},cs,solo);
  const fn=`${view}__${cs.name}__${solo.replace(/[:]/g,'-')}__${mode}.png`;fs.writeFileSync(`${OUT}/${fn}`,Buffer.from(r.png.split(',')[1],'base64'));
  (meta[view].runs=meta[view].runs||[]).push({case:cs.name,solo,mode,fn,ms:r.ms,stats:r.stats})}}
 meta[view].errors=(meta[view].errors||[]).concat(errs);await pg.close();console.error(view,mode,'done')}
 fs.writeFileSync(`${OUT}/${view}_meta.json`,JSON.stringify(meta[view]))}
await b.close()})().catch(e=>{console.error(e);process.exit(1)});
