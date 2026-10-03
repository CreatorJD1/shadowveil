const pp=require('/workspace/jt/node_modules/puppeteer-core');const PORT=process.env.PORT;
(async()=>{const b=await pp.launch({executablePath:'/usr/bin/google-chrome',headless:'new',protocolTimeout:900000,args:['--no-sandbox','--disable-dev-shm-usage']});const out={};
for(const [v,q] of [['left','&headgroup=1&hairless=1'],['apose','']]){const p=await b.newPage();const e=[];p.on('pageerror',x=>e.push(x.message));
 await p.goto(`http://127.0.0.1:${PORT}/rig/index.html?view=${v}&quality=linear${q}`,{waitUntil:'domcontentloaded',timeout:300000});
 await p.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:300000});await new Promise(r=>setTimeout(r,1000));
 out[v+q]=await p.evaluate(async vw=>{pauseManual();for(const k in P)set(k,P[k][2]);let h=null;if(RigHeadGroup.on){h=await RigHeadGroup.applyHandoff(vw)}draw();return{h,sub:RigHeadGroup.get().sub,st:(document.getElementById('status').textContent.match(/(PASS|FAIL)[^\n]*/)||[''])[0]}},v);out[v+q].errs=e;await p.close()}
console.log(JSON.stringify(out));await b.close()})();
