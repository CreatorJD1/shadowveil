const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');
(async()=>{const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new',protocolTimeout:600000});
const pg=await b.newPage();const errs=[];pg.on('pageerror',e=>errs.push(String(e)));
await pg.goto('http://127.0.0.1:8793/rig/_ps_test.html?view=apose&palsnap=1&quality=linear',{waitUntil:'domcontentloaded',timeout:300000});
await pg.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:300000});
const r=await pg.evaluate(()=>({P:Object.keys(P).join(' '),mouth:R.mouth?Object.keys(R.mouth).slice(0,20):null,ms:typeof mouthState!=='undefined'?Object.keys(mouthState):null,ids:R.mouth&&R.mouth.parts?R.mouth.parts.map(p=>p.id).join(' '):null,fns:Object.keys(window).filter(k=>/^Rig|mouth|Mouth/.test(k)).join(' ')}));
console.log(JSON.stringify(r,null,1),errs);await b.close()})();
