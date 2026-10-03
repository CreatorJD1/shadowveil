// Headless idle render harness for the Shadowveil rig. Loads http://127.0.0.1:8795/rig/index.html?view=<view> UNCHANGED
// and drives the rig's own auto/idle functions (makeAnim/animStep/mouthUpdate/renderFinal) with fixed dt.
// It never draws anything itself: frames are the rig's own guarded canvas output (authored PNGs + transforms), read back as PNG.
// usage: node render_idle.mjs <view> <outdir> [--seconds=8] [--fps=30] [--sub=2] [--seed=20260929] [--hair=fr,zr,fc,zc,lp]
import puppeteer from '/workspace/jt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
import fs from 'node:fs';
import crypto from 'node:crypto';{const h=x=>crypto.createHash('md5').update(x).digest('hex');const srv=h(Buffer.from(await (await fetch('http://127.0.0.1:8795/rig/index.html')).arrayBuffer()));const loc=h(fs.readFileSync('/workspace/shadowveil/rig/index.html'));if(srv!==loc){console.error('INDEX MISMATCH served',srv,'file',loc);process.exit(3)}console.error('index md5 ok',srv)}
const [view,out]=process.argv.slice(2);const opt=Object.fromEntries(process.argv.slice(4).map(a=>{const s=a.replace(/^--/,'');const i=s.indexOf('=');return i<0?[s,'1']:[s.slice(0,i),s.slice(i+1)]}));
const seconds=+(opt.seconds||8),fps=+(opt.fps||30),sub=+(opt.sub||2),seed=+(opt.seed||20260929);const hair=opt.hair?opt.hair.split(',').map(Number):null;
// --keys=<clip>: drive body/hand/mouth params from body_tools/idle/idle_clips.json (linear interpolation, viewKeys override); eyes+hair stay on the rig's auto
let KEYS=null;if(opt.keys){const J=JSON.parse(fs.readFileSync(opt.clipsfile||'/workspace/shadowveil/body_tools/idle/idle_clips.json','utf8'));const c=J.clips[opt.keys];if(!c){console.error('no clip '+opt.keys);process.exit(4)}KEYS={clip:opt.keys,fps:c.fps,duration:c.duration,loop:c.loop,stressTest:c.stressTest===true,keys:Object.assign({},c.keys,(c.viewKeys||{})[view]||{})}}
fs.mkdirSync(out+'/frames',{recursive:true});
const browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--disable-dev-shm-usage','--js-flags=--max-old-space-size=1536']});
const page=await browser.newPage();const logs=[];
page.on('console',m=>logs.push(m.type()+': '+m.text()));page.on('pageerror',e=>logs.push('pageerror: '+e.message));
page.on('response',r=>{if(r.status()>=400)logs.push('http '+r.status()+' '+r.url())});page.on('requestfailed',r=>logs.push('reqfail '+r.url()));
await page.setViewport({width:1200,height:900});
const PAGE=opt.page||'index.html';const QS=opt.q?('&'+opt.q):'';await page.goto('http://127.0.0.1:8795/rig/'+PAGE+'?view='+view+QS,{waitUntil:'networkidle0',timeout:120000});
await page.waitForFunction(()=>typeof R!=='undefined'&&R&&R.z&&R.mouthShapes,{timeout:120000});
const info=await page.evaluate(()=>({title:document.title,status:document.getElementById('status').textContent,skin:!!(R.skin),underlay:!!(R.skin&&R.skin.underlay&&R.skin.underlay.ok),
 bones:R.skin?R.skin.bones.map(b=>({id:b.id,parent:b.parent,pivot:[b.pivotX,b.pivotY],param:b.param})):null,missing:R.missing,feet:R.feet?{line:R.feet.line,L:R.feet.L?R.feet.L.pts.length:0,R:R.feet.R?R.feet.R.pts.length:0}:null,eyeW:R.eyeW,title2:document.title,warn:R.warn,mouthShapes:R.mouthShapes.map(s=>s.name),eyes:R.eyes?R.eyes.eyes:null,
 bodymode:document.getElementById('bodymode').value,quality:document.getElementById('quality').value,autoChecked:document.getElementById('auto').checked}));
let hairInfo=null;
if(hair){hairInfo=await page.evaluate(h=>{const src=stepHair.toString();const a='f=1.1;z=0.3',b='f=1.0;z=0.3',c='dt/0.09';
  if(!src.includes(a)||!src.includes(b)||!src.includes(c))return{error:'stepHair constants not found (rig changed?)'};
  const s2=src.replace(a,'f='+h[0]+';z='+h[1]).replace(b,'f='+h[2]+';z='+h[3]).replace(c,'dt/'+h[4]);stepHair=(0,eval)('('+s2+')');return{ok:true,override:{rootF:h[0],rootZ:h[1],childF:h[2],childZ:h[3],childLowPassS:h[4]}}},hair);
  if(hairInfo.error){console.error(hairInfo.error);process.exit(3)}}
let keyInfo=null;if(KEYS){keyInfo=await page.evaluate(K=>{const unknown=Object.keys(K.keys).filter(k=>!(k in P));
  window.__K=K;if(typeof stressEnable==='function')stressEnable(K);window.__keyAt=(t)=>{const o={};for(const k in K.keys){if(!(k in P))continue;const ks=K.keys[k];let tt=t;if(K.loop)tt=((t%K.duration)+K.duration)%K.duration;
    if(tt<=ks[0][0]){o[k]=ks[0][1];continue}if(tt>=ks[ks.length-1][0]){o[k]=ks[ks.length-1][1];continue}
    let i=1;while(ks[i][0]<tt)i++;const [t0,v0]=ks[i-1],[t1,v1]=ks[i];o[k]=t1>t0?v0+(v1-v0)*(tt-t0)/(t1-t0):v1}return o};
  window.__applyKeys=(t)=>{const o=__keyAt(t);for(const k in o)set(k,o[k])};return{clip:K.clip,params:Object.keys(K.keys),unknownParams:unknown}},KEYS)}
// rest frame (rig's own render(g,true)) as QA baseline
const setup=await page.evaluate((seed)=>{mqRunning=true; // block the page's own rAF auto loop (same as the Motion quality test)
 window.__cv=document.createElement('canvas');__cv.width=W;__cv.height=H;window.__g=guard(__cv.getContext('2d'));
 render(__g,true);const rest=__cv.toDataURL('image/png');
 for(const k in P)v[k]=P[k][2];hairDrive=null;mouthState={cur:'mouth_rest',prev:null,t0:-1e9};holdLog=[];renderIssues=new Set();if(typeof hairClampLog!=='undefined')hairClampLog=[];window.__A=makeAnim(seed);if(window.__K)__A.t=-1/(__K.fps);window.__errs=[];
 return{rest,bodyNext:__A.body.next,blinkNext:__A.blink.next}},seed);
fs.writeFileSync(out+'/rest.png',Buffer.from(setup.rest.split(',')[1],'base64'));
const N=Math.round(seconds*fps);const meta=[];
for(let f=0;f<N;f++){
 const fpath=`${out}/frames/f${String(f).padStart(4,'0')}.png`;const skip=!!opt.resume&&fs.existsSync(fpath)&&fs.statSync(fpath).size>0;
 const r=await page.evaluate((sub,fps,keyed,skip)=>{const A=__A,dt=1/(fps*sub);for(let i=0;i<sub;i++){if(keyed){__applyKeys(A.t+dt);const plant=typeof footPlantApply==='function'&&!('RootX' in __K.keys)&&!('RootY' in __K.keys);if(plant)footPlantApply();animStep(A,dt,{face:true,hair:true,body:false,rootKeyed:!plant});__applyKeys(A.t)}else animStep(A,dt,{face:true,hair:true,body:true});simNow=A.t*1000;if(R.mouth)mouthUpdate(simNow)}
  let err=null;try{renderFinal(__g,false)}catch(e){err=e.message;__errs.push(A.t.toFixed(3)+'s '+e.message)}
  const BM=R._BM||{};const bones={};if(R.skin)for(const b of R.skin.bones){const M=BM[b.id]||I;bones[b.id]=[M[0]*b.pivotX+M[2]*b.pivotY+M[4],M[1]*b.pivotX+M[3]*b.pivotY+M[5],Math.atan2(M[1],M[0])*180/Math.PI]}
  const pv={};for(const k in v)pv[k]=+(+v[k]).toFixed(5);const hd={};for(const k in (hairDrive||{}))hd[k]=[+hairDrive[k].x.toFixed(4),+hairDrive[k].y.toFixed(4)];
  const extra={blinkT0:A.blink.t0,hairClamps:(typeof hairClampLog!=='undefined'&&hairClampLog)?hairClampLog.splice(0).length:null,preset:typeof HAIR_PRESET!=='undefined'?HAIR_PRESET:null,footplant:(document.getElementById('footplant')||{}).value||null,autostyle:(document.getElementById('autostyle')||{}).value||null,mouthTalk:typeof mouthTalk!=='undefined'?mouthTalk:null,stress:typeof STRESS!=='undefined'?STRESS:null,life:typeof lifeAmt==='function'?lifeAmt():null,lifeLog:(__A.life&&__A.life.log)||null};
  return{extra,t:+A.t.toFixed(5),png:skip?null:__cv.toDataURL('image/png'),err,mouth:mouthState.cur,mouthPrev:mouthState.prev,mouthT0:mouthState.t0,params:pv,hair:hd,bones,issues:[...renderIssues]}},sub,fps,!!KEYS,skip);
 if(!skip)fs.writeFileSync(fpath,Buffer.from(r.png.split(',')[1],'base64'));delete r.png;r.frame=f;meta.push(r);
 if(f%30===0)process.stdout.write(view+' f'+f+' ');
}
const fin=await page.evaluate(()=>{const o={holds:holdLog.slice(),errs:__errs.slice(),issues:[...renderIssues]};simNow=null;holdLog=null;mqRunning=false;return o});
// the rig's own Motion quality test on this view (fixed seed, 60 Hz) for cross-check
let mq=null;if(!hair&&!KEYS&&!opt.nomq){mq=await page.evaluate(async()=>await motionTest())}
fs.writeFileSync(out+'/meta.json',JSON.stringify({view,seconds,fps,sub,dt:1/(fps*sub),seed,info,hairOverride:hairInfo,keys:keyInfo,bodyNext:setup.bodyNext,blinkNext:setup.blinkNext,holds:fin.holds,errs:fin.errs,issues:fin.issues,motionQuality:mq,logs,frames:meta}));
console.log('\n'+view+' done; guard errs',fin.errs.length,'issues',fin.issues.length,'holds',fin.holds.length,fin.holds.length?Math.min(...fin.holds).toFixed(1):'-');
if(mq)console.log(mq);
await browser.close();
