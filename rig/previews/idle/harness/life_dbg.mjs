import puppeteer from '/workspace/jt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
const [page_,view,q]=[process.argv[2],process.argv[3],process.argv[4]||''];
const browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--disable-dev-shm-usage']});
const p=await browser.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});p.on('error',e=>errs.push('crash '+e.message));
await p.goto('http://127.0.0.1:8765/rig/'+page_+'?view='+view+q,{waitUntil:'networkidle0',timeout:120000});await p.waitForFunction(()=>typeof R!=='undefined'&&R&&R.z,{timeout:120000});
const r=await p.evaluate(()=>{mqRunning=true;const A=makeAnim(1);const out=[];const t0=performance.now();for(let i=0;i<60*8;i++){animStep(A,1/60,{face:true,hair:true,body:true});if(i%30==0)out.push({t:+A.t.toFixed(2),lean:+v.BodyLean.toFixed(3),hip:+v.HipL.toFixed(3),tilt:+v.HeadTilt.toFixed(3),nod:+v.HeadNod.toFixed(3),sh:+v.ShoulderL.toFixed(3),el:+v.ElbowL.toFixed(3),wr:+v.WristL.toFixed(3),rx:v.RootX,ry:v.RootY,ex:+v.EyeBallX.toFixed(2),mf:v.MouthForm})}
 const c=document.createElement('canvas');c.width=W;c.height=H;const g=guard(c.getContext('2d'));const t1=performance.now();renderFinal(g,false);return{out,ms:performance.now()-t1,sim:t1-t0,qual:QUAL,life:lifeAmt()}});
console.log(JSON.stringify(r));console.log('errs',errs);await browser.close();
