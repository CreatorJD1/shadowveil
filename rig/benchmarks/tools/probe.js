const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');
(async()=>{
const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:'new',args:['--no-sandbox','--disable-dev-shm-usage']});
const p=await b.newPage();p.on('console',m=>{if(m.type()==='error')console.log('CONSOLE',m.text().slice(0,200))});p.on('pageerror',e=>console.log('PAGEERR',e.message.slice(0,200)));
await p.setViewport({width:1600,height:1000});
await p.goto('http://127.0.0.1:8797/rig/?view=apose',{waitUntil:'domcontentloaded',timeout:300000});
await p.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:300000});
const t0=Date.now();console.log('loaded');const info=await p.evaluate(()=>{const o={};o.auto=document.getElementById('auto').checked;o.clip=window.SVClip?.state;o.skin=!!R.skin;o.bodyEnabled=BODY_PARAMS.filter(k=>!inputs[k].disabled);o.groupsShown=Object.keys(groupBox).filter(g=>groupBox[g].style.display!=='none');o.mouth=(R.mouthShapes||[]).map?.(s=>s.name);o.warn=(R.warn||[]).slice(0,20);o.keys=Object.keys(R);o.nP=Object.keys(P).length;
o.disabled=Object.keys(inputs).filter(k=>inputs[k].disabled);return o});
console.log(JSON.stringify(info,null,1));
await b.close()})();
