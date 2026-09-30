// Headless check of rig/index.html and hair/live/index.html via Chrome DevTools Protocol (read-only, local server).
import { spawn } from 'node:child_process';
const port=9337, prof='/tmp/cdp-hair-prof';
const ch=spawn('google-chrome',['--headless=new','--no-sandbox','--disable-gpu',`--remote-debugging-port=${port}`,`--user-data-dir=${prof}`,'--window-size=1400,1000','about:blank'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
let ws,id=0;const pend={};const logs=[];
async function connect(){for(let i=0;i<50;i++){try{const r=await fetch(`http://127.0.0.1:${port}/json/list`);const l=await r.json();const pg=l.find(x=>x.type==='page');if(pg)return pg.webSocketDebuggerUrl}catch(e){}await sleep(200)}throw new Error('no chrome')}
function send(method,params={}){return new Promise(r=>{const i=++id;pend[i]=r;ws.send(JSON.stringify({id:i,method,params}))})}
async function ev(expr){const r=await send('Runtime.evaluate',{expression:expr,awaitPromise:true,returnByValue:true});return r.result?.result?.value}
const out={};
try{
 ws=new WebSocket(await connect());await new Promise(r=>ws.onopen=r);
 ws.onmessage=m=>{const d=JSON.parse(m.data);if(d.id&&pend[d.id]){pend[d.id](d);delete pend[d.id]}
  if(d.method==='Runtime.consoleAPICalled'&&['error','warning'].includes(d.params.type))logs.push(d.params.type+': '+d.params.args.map(a=>a.value??a.description).join(' '));
  if(d.method==='Runtime.exceptionThrown')logs.push('EXCEPTION: '+(d.params.exceptionDetails.exception?.description||d.params.exceptionDetails.text));
  if(d.method==='Log.entryAdded'&&d.params.entry.level==='error')logs.push('LOG: '+d.params.entry.text+' '+(d.params.entry.url||''))};
 await send('Runtime.enable');await send('Log.enable');await send('Page.enable');
 for(const v of (process.env.VIEWS||'apose,tpose,left,right,back').split(',')){
  logs.length=0;await send('Page.navigate',{url:`http://127.0.0.1:8765/rig/index.html?view=${v}#check`});await sleep(6000);
  const st1=await ev("document.getElementById('status').textContent");
  // sway extremes through the sliders (drawn with the renderer's own chain), then motion quality
  const sw=await ev(`(async()=>{const r=[];for(const [x,y] of [[-1,-1],[-1,1],[1,-1],[1,1],[0.5,0]]){const a=document.querySelector('#sliders input');const ins=[...document.querySelectorAll('#sliders input')];for(const i of ins){const l=i.parentElement.textContent;if(l.startsWith('HairSwayX')){i.value=x;i.oninput()}if(l.startsWith('HairSwayY')){i.value=y;i.oninput()}}r.push([x,y])}return r.length})()`);
  const mqb=await ev("!!document.getElementById('mq')");
  let st2=null;if(mqb){await ev("document.getElementById('mq').click()");for(let i=0;i<60;i++){await sleep(1000);st2=await ev("document.getElementById('status').textContent");if(st2&&/motion|Motion|pass|PASS|FAIL/.test(st2)&&!/running/i.test(st2))break}}
  const shot=await send('Page.captureScreenshot',{format:'png'});
  (await import('node:fs')).writeFileSync(`/workspace/shadowveil/hair/qa/cdp/rig_${v}.png`,Buffer.from(shot.result.data,'base64'));
  out[v]={restCheck:st1,swaySteps:sw,motionQuality:st2,consoleErrors:[...logs]};
 }
 logs.length=0;await send('Page.navigate',{url:'http://127.0.0.1:8765/hair/live/index.html'});await sleep(3000);
 for(const v of ['apose','tpose','left','right','back']){await ev(`(()=>{const s=document.getElementById('view');s.value='${v}';s.onchange({target:s})})()`);await sleep(1500)}
 const shot=await send('Page.captureScreenshot',{format:'png'});(await import('node:fs')).writeFileSync('/workspace/shadowveil/hair/qa/cdp/live.png',Buffer.from(shot.result.data,'base64'));
 out.live={consoleErrors:[...logs]};
}catch(e){out.error=String(e)}
finally{console.log(JSON.stringify(out,null,1));ch.kill('SIGKILL');process.exit(0)}
