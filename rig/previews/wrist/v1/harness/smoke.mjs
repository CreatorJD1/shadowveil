import puppeteer from '/workspace/jt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
const [page_,views]=[process.argv[2],process.argv[3].split(',')];
const browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--disable-dev-shm-usage']});
for(const v of views){const p=await browser.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()==='error')errs.push('console:'+m.text())});
 await p.goto('http://127.0.0.1:8765/rig/'+page_+'?view='+v,{waitUntil:'networkidle0',timeout:180000});await p.waitForFunction(()=>typeof R!=='undefined'&&R&&R.z&&R.handAngles!==undefined,{timeout:180000});
 const info=await p.evaluate(()=>({wrist:R.wrist,twist:R.twist&&R.twist.entries,ha:Object.fromEntries(Object.entries(R.handAngles||{}).map(([H,S])=>[H,{E:S.E.map(e=>({deg:e.deg,src:e.src,n:e.parts?e.parts.length:'native',rot:e.rotDeg})),min:S.min,max:S.max}])),hair:document.getElementById('hairpreset').value,status:document.getElementById('status').textContent.split('\n').filter(l=>/WARN/.test(l))}));
 console.log(v,JSON.stringify(info),'ERRS',JSON.stringify(errs));await p.close()}
await browser.close();
