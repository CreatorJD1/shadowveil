// Mouth render QA harness. Scratch copy of the rig page (served by serve.py on 8781; /rig/ is a COPY). Read-only: never writes into the rig tree.
// usage: node harness.mjs <view> <outdir> [--quality=linear] [--fade=35]
import puppeteer from '/workspace/jt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
import fs from 'node:fs';
const [view,out]=process.argv.slice(2);const opt=Object.fromEntries(process.argv.slice(4).map(a=>{const s=a.replace(/^--/,'');const i=s.indexOf('=');return i<0?[s,'1']:[s.slice(0,i),s.slice(i+1)]}));
const quality=opt.quality||'linear';const port=opt.port||8765;
fs.mkdirSync(out+'/crops',{recursive:true});
const browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--disable-dev-shm-usage','--js-flags=--max-old-space-size=1536','--user-data-dir=/tmp/mouthfix_chrome_'+view]});
const bp=browser.process();fs.appendFileSync('/workspace/shadowveil/rig/work/mouthfix/qa/my_pids.txt','CHROME_PID '+bp.pid+' '+view+'\n');
const logs=[];const page=await browser.newPage();
page.on('console',m=>logs.push(m.type()+': '+m.text()));page.on('pageerror',e=>logs.push('pageerror: '+e.message));page.on('response',r=>{if(r.status()>=400)logs.push('http '+r.status()+' '+r.url())});
await page.setViewport({width:1200,height:900});
await page.goto(`http://127.0.0.1:${port}/rig/index.html?view=${view}&quality=${quality}&mouthfade=${opt.fade||35}${opt.q?'&'+opt.q:''}`,{waitUntil:'networkidle0',timeout:180000});
await page.waitForFunction(()=>typeof R!=='undefined'&&R&&R.z&&R.mouthShapes,{timeout:180000});
const box=JSON.parse(opt.box);// [x0,y0,x1,y1) crop
const info=await page.evaluate((box)=>{mqRunning=true;document.getElementById('auto').checked=false;anim=null;
 window.__cv=document.createElement('canvas');__cv.width=W;__cv.height=H;window.__g=guard(__cv.getContext('2d'));
 window.__cc=document.createElement('canvas');__cc.width=box[2]-box[0];__cc.height=box[3]-box[1];const cg=__cc.getContext('2d');
 window.__crop=()=>{const d=__g.getImageData(box[0],box[1],box[2]-box[0],box[3]-box[1]).data;let s='';for(let i=0;i<d.length;i+=8192)s+=String.fromCharCode.apply(null,d.subarray(i,i+8192));return 'raw,'+btoa(s)};
 window.__reset=()=>{for(const k in P)set(k,P[k][2]);hairDrive=null;mouthTalk=false};
 return{status:document.getElementById('status').textContent,quality:QUAL,fade:MOUTH_FADE_MS,hold:MOUTH_HOLD_MS,shapes:R.mouthShapes.map(s=>[s.name,s.open,s.form])}},box);
const meta={view,quality,info,box,tests:{}};const save=(name,d)=>fs.writeFileSync(`${out}/crops/${name}.rgba`,Buffer.from(d.split(',')[1],'base64'));
// 1. rest: rig rest path and posed path at defaults, full-frame pixel count vs base.png
meta.tests.rest=await page.evaluate(()=>{__reset();const B=document.createElement('canvas');B.width=W;B.height=H;const gb=B.getContext('2d');gb.drawImage(R.im.base,0,0);const b=gb.getImageData(0,0,W,H).data;
 const cnt=()=>{const a=__g.getImageData(0,0,W,H).data;let n=0;for(let i=0;i<a.length;i+=4){if(a[i+3]===0&&b[i+3]===0)continue;if(a[i]!==b[i]||a[i+1]!==b[i+1]||a[i+2]!==b[i+2]||a[i+3]!==b[i+3])n++}return n};
 render(__g,true);const nRest=cnt();const c0=__crop();
 mouthState={cur:'mouth_rest',prev:null,t0:-1e9};simNow=1e6;renderFinal(__g,false);const nPosed=cnt();const c1=__crop();simNow=null;
 return{restPath_px:nRest,posedDefault_px:nPosed,c0,c1}});
save('rest_restpath',meta.tests.rest.c0);save('rest_posed',meta.tests.rest.c1);delete meta.tests.rest.c0;delete meta.tests.rest.c1;
// 1b. browser-composited references: base.png alone, and base.png + each authored shape PNG at identity (same canvas roundtrip as the frames)
const refs=await page.evaluate(()=>{const o={};const g=__g;g.setTransform(1,0,0,1,0,0);g.globalAlpha=1;g.clearRect(0,0,W,H);g.imageSmoothingEnabled=false;g.drawImage(R.im.base,0,0);o.base=__crop();
 for(const s of R.mouthShapes){g.clearRect(0,0,W,H);g.drawImage(R.im.base,0,0);const im=R.im['mouth:'+s.id];g.drawImage(im,im.ox||0,im.oy||0);o[s.name]=__crop();
  g.clearRect(0,0,W,H);g.drawImage(im,im.ox||0,im.oy||0);o['only_'+s.name]=__crop()}return o});
for(const k in refs)save('ref_'+k,refs[k]);meta.refs=Object.keys(refs);
// 2. static sweep (each value settled, no fade): MouthOpen 0..1 step .1 x Form -1,0,1
meta.tests.sweep=[];
for(const form of [-1,0,1])for(let k=0;k<=10;k++){const open=k/10;
 const r=await page.evaluate((open,form)=>{__reset();set('MouthOpen',open);set('MouthForm',form);const pick=mouthPick();mouthState={cur:pick,prev:null,t0:-1e9};simNow=1e6;renderFinal(__g,false);simNow=null;return{pick,crop:__crop()}},open,form);
 const name=`sweep_f${form}_o${k}`;save(name,r.crop);meta.tests.sweep.push({name,open,form,pick:r.pick})}
// 3. timed sweep at 30 fps (rig hold + fade active): one step per frame, Form -1,0,1, open 0->1->0
meta.tests.timed=[];
await page.evaluate(()=>{__reset();mouthState={cur:'mouth_rest',prev:null,t0:-1e9}});let t=0;let fi=0;
for(const form of [-1,0,1]){const seq=[...Array(11).keys(),...[9,8,7,6,5,4,3,2,1,0]];for(const k of seq){for(const rep of [0,1]){t+=1000/30;
 const r=await page.evaluate((open,form,t)=>{set('MouthOpen',open);set('MouthForm',form);simNow=t;renderFinal(__g,false);const st=mouthState;const el=t-st.t0,FD=MOUTH_FADE_MS;
  const a=FD>0?Math.min(1,Math.max(0,(el+FD/4)/FD)):1;const aOut=FD>0?(el<FD/2?1:Math.min(1,Math.max(0,1-(el-FD/2)/(FD/2)))):0;const inFade=FD>0&&el<FD&&!!st.prev;simNow=null;
  return{cur:st.cur,prev:st.prev,el,inFade,aIn:inFade?a:1,aOut:inFade?aOut:0,crop:__crop()}},k/10,form,t);
 const name=`timed_${String(fi).padStart(3,'0')}`;fi++;save(name,r.crop);delete r.crop;meta.tests.timed.push({name,t,open:k/10,form,...r})}}}
// 4. crossfade step-through: pairs, el = 0..45 ms step 2.5 ms
const pairs=opt.pairs?JSON.parse(opt.pairs):[['rest','AA_half'],['AA_half','AA'],['M','OH_half'],['OH_half','OH'],['rest','smile'],['smile','rest'],['rest','M'],['M','rest'],['AA','rest'],['EE_half','rest'],['rest','anger'],['anger','rest'],['anger','M'],['M','anger']];
meta.tests.fade=[];
for(const [p,c] of pairs){const ok=await page.evaluate((p,c)=>R.mouthShapes.some(s=>s.name===p)&&R.mouthShapes.some(s=>s.name===c),p,c);if(!ok)continue;
 for(let el=-5;el<=45;el+=2.5){const r=await page.evaluate((p,c,el)=>{__reset();const S=R.mouthShapes;const sc=S.find(s=>s.name===c);set('MouthOpen',sc.open);set('MouthForm',sc.form);
   const want=mouthPick();const T0=100000;mouthState={cur:'mouth_'+c,prev:'mouth_'+p,t0:T0};if(el<0)mouthState={cur:'mouth_'+p,prev:null,t0:-1e9};
   if(el<0){const sp=S.find(s=>s.name===p);set('MouthOpen',sp.open);set('MouthForm',sp.form)}
   simNow=T0+Math.max(el,0);renderFinal(__g,false);const st=mouthState;simNow=null;return{want,cur:st.cur,prev:st.prev,crop:__crop()}},p,c,el);
  const name=`fade_${p}_${c}_${String(Math.round(el*10)).padStart(4,'0')}`;save(name,r.crop);delete r.crop;meta.tests.fade.push({name,from:p,to:c,el,...r})}}
// 5. auto talk run (rig's own talk driver + body life), 30 fps, sub 2, 8 s
meta.tests.talk=[];const tsec=+(opt.talk||8);
await page.evaluate(()=>{__reset();document.getElementById('autostyle').value='talk';mouthState={cur:'mouth_rest',prev:null,t0:-1e9};holdLog=[];window.__A=makeAnim(20261002)});
for(let f=0;f<tsec*30;f++){const r=await page.evaluate(()=>{const A=__A,dt=1/60;for(let i=0;i<2;i++){animStep(A,dt,{face:true,hair:true,body:true});simNow=A.t*1000;if(R.mouth)mouthUpdate(simNow)}
  renderFinal(__g,false);const st=mouthState;const el=simNow-st.t0,FD=MOUTH_FADE_MS;const inFade=FD>0&&el<FD&&!!st.prev;const BM=R._BM||{};const Mh=BM.head||null;
  return{t:A.t,cur:st.cur,prev:st.prev,el,inFade,talk:mouthTalk,open:v.MouthOpen,form:v.MouthForm,head:Mh?Array.from(Mh).map(x=>+x.toFixed(4)):null,crop:__crop()}});
 const name=`talk_${String(f).padStart(3,'0')}`;save(name,r.crop);delete r.crop;meta.tests.talk.push({name,...r})}
// 6. talk with body frozen (face only): isolates mouth crossfades from head motion
meta.tests.talkface=[];
await page.evaluate(()=>{__reset();mouthState={cur:'mouth_rest',prev:null,t0:-1e9};window.__A=makeAnim(20261002)});
for(let f=0;f<tsec*30;f++){const r=await page.evaluate(()=>{const A=__A,dt=1/60;for(let i=0;i<2;i++){animStep(A,dt,{face:true,hair:false,body:false});simNow=A.t*1000;if(R.mouth)mouthUpdate(simNow)}
  for(const k of ['HairSwayX','HairSwayY'])if(k in P)set(k,P[k][2]);hairDrive=null;
  renderFinal(__g,false);const st=mouthState;const el=simNow-st.t0,FD=MOUTH_FADE_MS;const inFade=FD>0&&el<FD&&!!st.prev;const a=FD>0?Math.min(1,Math.max(0,(el+FD/4)/FD)):1;const aOut=FD>0?(el<FD/2?1:Math.min(1,Math.max(0,1-(el-FD/2)/(FD/2)))):0;
  return{t:A.t,cur:st.cur,prev:st.prev,el,inFade,aIn:inFade?a:1,aOut:inFade?aOut:0,talk:mouthTalk,open:v.MouthOpen,form:v.MouthForm,crop:__crop()}});
 const name=`tface_${String(f).padStart(3,'0')}`;save(name,r.crop);delete r.crop;meta.tests.talkface.push({name,...r})}
meta.holds=await page.evaluate(()=>holdLog?holdLog.slice():null);meta.logs=logs;
fs.writeFileSync(out+'/meta.json',JSON.stringify(meta,null,1));console.log(view,'done',JSON.stringify(meta.tests.rest),'logs',logs.length);
await browser.close();
