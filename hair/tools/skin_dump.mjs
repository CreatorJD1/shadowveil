import { spawn } from 'node:child_process'; import fs from 'node:fs';
const port=9340, prof='/tmp/cdp-skindump-prof';
const ch=spawn('google-chrome',['--headless=new','--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader',`--remote-debugging-port=${port}`,`--user-data-dir=${prof}`,'about:blank'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));let ws,id=0;const pend={};
async function connect(){for(let i=0;i<60;i++){try{const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();const pg=l.find(x=>x.type==='page');if(pg)return pg.webSocketDebuggerUrl}catch(e){}await sleep(200)}throw new Error('no chrome')}
function send(method,params={}){return new Promise(r=>{const i=++id;pend[i]=r;ws.send(JSON.stringify({id:i,method,params}))})}
async function ev(expr){const r=await send('Runtime.evaluate',{expression:expr,awaitPromise:true,returnByValue:true});if(r.result?.exceptionDetails)return {err:r.result.exceptionDetails.exception?.description};return r.result?.result?.value}
try{ws=new WebSocket(await connect());await new Promise(r=>ws.onopen=r);ws.onmessage=m=>{const d=JSON.parse(m.data);if(d.id&&pend[d.id]){pend[d.id](d);delete pend[d.id]}};
 await send('Runtime.enable');await send('Page.navigate',{url:'http://127.0.0.1:8765/rig/index.html?view=apose'});
 for(let i=0;i<120;i++){await sleep(500);if(await ev("typeof R!=='undefined'&&!!R&&!!R.im&&!!R.skin")===true)break}await sleep(800);
 const poses=JSON.parse(process.env.POSES||'[{"BodyLean":-1}]');
 for(const [n,p] of poses.entries()){
  const res=await ev(`(()=>{const cv=document.createElement('canvas');cv.width=W;cv.height=H;const g=guard(cv.getContext('2d'));g.__S=1;
   for(const k in P)v[k]=P[k][2];hairDrive=null;Object.assign(v,${JSON.stringify(p)});const outs={};
   const keys=Object.keys(R.im).filter(k=>k.startsWith('hair:'));const sv={};for(const k of keys)sv[k]=R.im[k];
   for(const [tag,drop] of [['full',[]],['nohb',['hair:hair_back']],['nohair',keys]]){for(const k of drop)R.im[k]={empty:true};render(g,false);outs[tag]=cv.toDataURL('image/png');for(const k of keys)R.im[k]=sv[k]}
   for(const k in P)v[k]=P[k][2];return outs})()`);
  for(const t in res)fs.writeFileSync(`/tmp/skd_${n}_${t}.png`,Buffer.from(res[t].split(',')[1],'base64'));
 }}catch(e){console.log(String(e))}finally{ch.kill('SIGKILL');process.exit(0)}
