import puppeteer from '/workspace/jt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const p=await b.newPage();p.on('pageerror',e=>console.log('ERR',e.message,e.stack&&e.stack.split('\n').slice(0,3).join(' | ')));p.on('console',m=>console.log('C',m.type(),m.text().slice(0,200)));
await p.goto('http://127.0.0.1:8765/rig/'+process.argv[2]+'?view=apose',{waitUntil:'networkidle0'});await new Promise(r=>setTimeout(r,8000));
console.log(await p.evaluate(()=>document.getElementById('status').textContent.slice(0,300)));await b.close();
