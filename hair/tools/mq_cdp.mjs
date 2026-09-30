// Click the renderer's "Motion quality" button in every view (skins on) and collect the status text.
import { spawn } from 'node:child_process'; import fs from 'node:fs';
const port=9341, prof='/tmp/cdp-mq-prof';
const ch=spawn('google-chrome',['--headless=new','--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader',`--remote-debugging-port=${port}`,`--user-data-dir=${prof}`,'--window-size=1400,1000','about:blank'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));let ws,id=0;const pend={};const logs=[];
async function connect(){for(let i=0;i<60;i++){try{const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();const pg=l.find(x=>x.type==='page');if(pg)return pg.webSocketDebuggerUrl}catch(e){}await sleep(200)}throw new Error('no chrome')}
function send(method,params={}){return new Promise(r=>{const i=++id;pend[i]=r;ws.send(JSON.stringify({id:i,method,params}))})}
async function ev(expr){const r=await send('Runtime.evaluate',{expression:expr,awaitPromise:true,returnByValue:true});return r.result?.result?.value}
const out={};
try{ws=new WebSocket(await connect());await new Promise(r=>ws.onopen=r);
 ws.onmessage=m=>{const d=JSON.parse(m.data);if(d.id&&pend[d.id]){pend[d.id](d);delete pend[d.id]}
  if(d.method==='Runtime.consoleAPICalled'&&['error','warning'].includes(d.params.type))logs.push(d.params.type+': '+d.params.args.map(a=>a.value??a.description).join(' '));
  if(d.method==='Runtime.exceptionThrown')logs.push('EXC: '+(d.params.exceptionDetails.exception?.description||d.params.exceptionDetails.text))};
 await send('Runtime.enable');await send('Page.enable');
 for(const v of ['apose','tpose','left','right','back']){logs.length=0;
  await send('Page.navigate',{url:`http://127.0.0.1:8765/rig/index.html?view=${v}`});
  for(let i=0;i<120;i++){await sleep(500);if(await ev("typeof R!=='undefined'&&!!R&&!!R.im")===true)break}await sleep(1000);
  const skin=await ev("!!R.skin&&useSkin()");
  await ev("document.getElementById('mq').click()");let st=null;
  for(let i=0;i<600;i++){await sleep(1000);st=await ev("document.getElementById('status').textContent");if(st&&!/running/i.test(st)&&/motion|Motion/.test(st))break}
  out[v]={skin,status:st,consoleErrors:[...logs]};console.error(v,st);
 }}catch(e){out.error=String(e)}
finally{fs.writeFileSync(process.env.OUT||'/tmp/mq.json',JSON.stringify(out,null,1));ch.kill('SIGKILL');process.exit(0)}
