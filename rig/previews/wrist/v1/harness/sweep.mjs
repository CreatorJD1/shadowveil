// wrist/twist QA sweep: renders each pose (full ss2 composite + green block probe) and records posed joint positions
import puppeteer from '/workspace/jt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
import fs from 'fs';
const [page_,view,out]=process.argv.slice(2);fs.mkdirSync(out+'/full',{recursive:true});fs.mkdirSync(out+'/probe',{recursive:true});
const F=[];const push=(name,ps)=>F.push({i:F.length,name,ps});
push('zero',{WristL:1e-6,WristR:1e-6}); // posed-path baseline (GL mesh path, like every posed frame)
for(const tw of [-1,0,1])for(let d=-90;d<=90;d+=15)push(`rot${d}_tw${tw}`,{WristL:d/25,WristR:d/25,WristTwistL:tw,WristTwistR:tw});
for(let k=-8;k<=8;k++)if(k)push(`tw${(k/8).toFixed(3)}`,{WristTwistL:k/8,WristTwistR:k/8});
for(const ts of[-1,1])for(const te of[-1,1])for(const wr of[0,1]){const ps={TwistShoulderL:ts,TwistShoulderR:ts,TwistElbowL:te,TwistElbowR:te,ElbowL:0.6,ElbowR:0.6,ShoulderL:0.4,ShoulderR:0.4};if(wr)Object.assign(ps,{WristL:45/25,WristR:45/25,WristTwistL:0.5,WristTwistR:0.5});push(`sh${ts}_el${te}_bend${wr?'_wr45_tw.5':''}`,ps)}
for(const x of[-1,1])push(`legneck${x}`,{TwistHipL:x,TwistHipR:x,TwistKneeL:x,TwistKneeR:x,TwistAnkleL:x,TwistAnkleR:x,TwistNeck:x});
if(process.env.FR){const keep=new Set(process.env.FR.split(',').map(Number));for(let k=F.length-1;k>=0;k--)if(k&&!keep.has(k))F.splice(k,1)}
const browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--disable-dev-shm-usage']});
const p=await browser.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('http://127.0.0.1:8765/rig/'+page_+'?view='+view,{waitUntil:'networkidle0',timeout:240000});await p.waitForFunction(()=>typeof R!=='undefined'&&R&&R.z&&R.handAngles!==undefined,{timeout:240000});
await p.evaluate(async(v)=>{window.__probe=await img('previews/wrist/v1/probe/'+v+'_probe.png');window.__ptex=glTex(SKGL.gl,window.__probe);document.getElementById('auto').checked=false},view);
const meta=[];
for(const f of F){const r=await p.evaluate((ps)=>{mqRunning=true;STRESS=true;for(const k in P)v[k]=P[k][2];hairDrive=null;
  const mk=()=>{const c=document.createElement('canvas');c.width=W;c.height=H;return c};
  for(const k in ps)v[k]=ps[k];const c=mk();renderFinal(guard(c.getContext('2d')),false);const full=c.toDataURL('image/png');
  const BM=R._BM;const J={};const ap=(M,x,y)=>[M[0]*x+M[2]*y+M[4],M[1]*x+M[3]*y+M[5]];
  if(R.skin)for(const b of R.skin.bones){if(b.virtual)continue;J[b.id]=ap(BM[b.id]||I,b.pivotX,b.pivotY);const wp=pt(b.wristPivot);if(wp)J['wrist_'+b.id.slice(-1)]=ap(BM[b.id]||I,wp[0],wp[1])}
  const tw={L:twistState('L',false),R:twistState('R',false)};const twi=Object.fromEntries(Object.entries(tw).filter(([k,x])=>x).map(([k,x])=>[k,{tau:x.tau,want:x.want,clamped:x.clamped,show:x.L.map(q=>q.e.src+'@'+q.alpha.toFixed(2)+'/s'+q.s.toFixed(3))}]));
  const tex=R.skin.tex;const sel=document.getElementById('seal');const s0=sel.value;sel.value='0';R.skin.tex=window.__ptex;let probe;try{const c2=mk();renderFinal(guard(c2.getContext('2d')),false);probe=c2.toDataURL('image/png')}finally{R.skin.tex=tex;sel.value=s0}
  for(const k in P)v[k]=P[k][2];STRESS=false;mqRunning=false;return{full,probe,J,twi,issues:[...renderIssues]}},f.ps);
 fs.writeFileSync(`${out}/full/${String(f.i).padStart(3,'0')}.png`,Buffer.from(r.full.split(',')[1],'base64'));fs.writeFileSync(`${out}/probe/${String(f.i).padStart(3,'0')}.png`,Buffer.from(r.probe.split(',')[1],'base64'));
 meta.push({i:f.i,name:f.name,ps:f.ps,J:r.J,twist:r.twi,issues:r.issues});process.stdout.write(f.i+' ')}
// rest reference (exact rest path)
const rest=await p.evaluate(()=>{const c=document.createElement('canvas');c.width=W;c.height=H;render(guard(c.getContext('2d')),true);const J={};if(R.skin)for(const b of R.skin.bones){if(b.virtual)continue;J[b.id]=[b.pivotX,b.pivotY];const wp=pt(b.wristPivot);if(wp)J['wrist_'+b.id.slice(-1)]=wp}
 const hp={};for(const p of R.hands.parts)if(/_(palm|Index1|Middle1|Ring1|Pinky1|Index2|Middle2|Ring2|Pinky2)$/.test(p.id)&&p.file&&!p.hidden)hp[p.id]=[p.pivotX,p.pivotY];return{url:c.toDataURL('image/png'),J,hp}});
fs.writeFileSync(`${out}/rest.png`,Buffer.from(rest.url.split(',')[1],'base64'));
fs.writeFileSync(`${out}/meta.json`,JSON.stringify({view,page:page_,frames:meta,restJ:rest.J,handPivots:rest.hp,errs}));console.log('\nDONE',view,F.length,'errs',errs.length);await browser.close();
