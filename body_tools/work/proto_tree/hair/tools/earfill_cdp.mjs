// Headless sweep of rig/index.html (the real v1.3 renderer): for each view render rest, then the HairSwayX/Y grid
// (shared slider) and N random independent per-part drives (hairDrive, extremes-biased), and report every pixel in
// the head box that is opaque at rest but at some pose shows background (alpha<255), white (all>240) or chroma blue.
import { spawn } from 'node:child_process'; import fs from 'node:fs';
const port=9338, prof='/tmp/cdp-earfill-prof';
const ch=spawn('google-chrome',['--headless=new','--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader',`--remote-debugging-port=${port}`,`--user-data-dir=${prof}`,'--window-size=1400,1000','about:blank'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));let ws,id=0;const pend={};
async function connect(){for(let i=0;i<60;i++){try{const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();const pg=l.find(x=>x.type==='page');if(pg)return pg.webSocketDebuggerUrl}catch(e){}await sleep(200)}throw new Error('no chrome')}
function send(method,params={}){return new Promise(r=>{const i=++id;pend[i]=r;ws.send(JSON.stringify({id:i,method,params}))})}
async function ev(expr){const r=await send('Runtime.evaluate',{expression:expr,awaitPromise:true,returnByValue:true});if(r.result?.exceptionDetails)return {err:r.result.exceptionDetails.exception?.description};return r.result?.result?.value}
const BOX={apose:[530,20,820,370],tpose:[530,20,830,360],left:[540,20,845,330],right:[515,20,830,330],back:[545,20,820,345]};
const NRAND=+(process.env.NRAND||300);const out={};
try{ws=new WebSocket(await connect());await new Promise(r=>ws.onopen=r);ws.onmessage=m=>{const d=JSON.parse(m.data);if(d.id&&pend[d.id]){pend[d.id](d);delete pend[d.id]}};
 await send('Runtime.enable');await send('Page.enable');
 for(const vw of (process.env.VIEWS||'apose,tpose,left,right,back').split(',')){
  await send('Page.navigate',{url:`http://127.0.0.1:8765/rig/index.html?view=${vw}`});
  for(let i=0;i<60;i++){await sleep(500);const ok=await ev("typeof R!=='undefined'&&!!R&&!!R.im&&document.getElementById('status').textContent.length>0");if(ok===true)break}
  await sleep(800);const info=await ev("({skin:!!R.skin,useSkin:useSkin(),underlay:!!(R.skin&&R.skin.underlay&&R.skin.underlay.ok),warn:R.warn})");console.error(vw,JSON.stringify(info));
  const [x0,y0,x1,y1]=BOX[vw];
  const res=await ev(`(()=>{const bw=${x1-x0},bh=${y1-y0};const cv=document.createElement('canvas');cv.width=W;cv.height=H;const g=guard(cv.getContext('2d'));g.__S=1;
   const grab=()=>g.getImageData(${x0},${y0},bw,bh).data;render(g,true);const rest=grab();
   const bad=d=>{const m=new Uint8Array(bw*bh);for(let i=0,j=0;i<d.length;i+=4,j++){const r=d[i],gg=d[i+1],b=d[i+2],a=d[i+3];m[j]=(a<255)||(r>240&&gg>240&&b>240)||(b>r+40&&b>gg+40)?1:0}return m};
   const rb=bad(rest);const acc=new Uint8Array(bw*bh);let poses=0;const bump=()=>{const m=bad(grab());for(let j=0;j<m.length;j++)if(m[j]&&!rb[j])acc[j]=1;poses++};
   const s0={x:v.HairSwayX,y:v.HairSwayY};
   for(let ix=0;ix<=40;ix++)for(const sy of [-1,-0.5,-1/3,0,1/3,0.5,1]){v.HairSwayX=-1+ix/20;v.HairSwayY=sy;hairDrive=null;render(g,false);bump()}
   let seed=12345;const rnd=()=>{seed=(seed*1103515245+12345)&0x7fffffff;return seed/0x7fffffff};
   const pick=()=>{const u=rnd();return u<0.35?-1:u<0.7?1:rnd()*2-1};
   for(let k=0;k<${NRAND};k++){const d={};for(const p of R.hair)d[p.id]={x:pick(),y:pick()};hairDrive=d;render(g,false);bump()}
   hairDrive=null;v.HairSwayX=s0.x;v.HairSwayY=s0.y;
   const idx=[];for(let j=0;j<acc.length;j++)if(acc[j])idx.push(j);return {poses,box:[${x0},${y0},${x1},${y1}],revealed:idx}})()`);
  out[vw]=Object.assign(res||{},{info});console.error(vw,res&&res.revealed?res.revealed.length:JSON.stringify(res));
 }}catch(e){out.error=String(e)}
finally{fs.writeFileSync(process.env.OUT||'/tmp/earfill_cdp.json',JSON.stringify(out));ch.kill('SIGKILL');process.exit(0)}
