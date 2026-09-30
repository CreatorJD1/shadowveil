// loads a rig page for each view: page Rest check, Motion quality, optional jointTest; prints status text
import puppeteer from '/workspace/jt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
const [page_,views,jt]=[process.argv[2],process.argv[3].split(','),process.argv[4]==='jt'];
const browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--disable-dev-shm-usage']});
for(const v of views){const p=await browser.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
 await p.goto('http://127.0.0.1:8765/rig/'+page_+'?view='+v,{waitUntil:'networkidle0',timeout:120000});await p.waitForFunction(()=>typeof R!=='undefined'&&R&&R.z,{timeout:120000});
 const load=await p.evaluate(()=>document.getElementById('status').textContent);
 const rc=await p.evaluate(()=>{document.getElementById('check').click();return document.getElementById('status').textContent.split('\n')[0]});
 const mq=await p.evaluate(async()=>await motionTest());
 let jtr=null;if(jt){jtr=await p.evaluate(async()=>{const s=await jointTest();return {s,summary:window.JT&&window.JT.summary}})}
 const extra=await p.evaluate(()=>({feet:R.feet&&{line:R.feet.line,L:R.feet.L&&R.feet.L.pts.length,R:R.feet.R&&R.feet.R.pts.length},eyeW:R.eyeW,dir:typeof headDirX==='function'?headDirX():null,title:document.title}));
 console.log(JSON.stringify({view:v,warn:load.split('\n').filter(l=>/WARN|REJECT|Not delivered/.test(l)),rest:rc,mq,jt:jtr,extra,errs}));await p.close()}
await browser.close();
