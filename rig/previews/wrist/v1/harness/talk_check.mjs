import puppeteer from '/workspace/jt/node_modules/puppeteer-core/lib/esm/puppeteer/puppeteer-core.js';
const [page_,views]=[process.argv[2],process.argv[3].split(',')];
const browser=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--disable-dev-shm-usage']});
for(const vw of views){const p=await browser.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));
 await p.goto('http://127.0.0.1:8765/rig/'+page_+'?view='+vw,{waitUntil:'networkidle0',timeout:240000});await p.waitForFunction(()=>typeof R!=='undefined'&&R&&R.z,{timeout:240000});
 const r=await p.evaluate(()=>{document.getElementById('auto').checked=false;const names=(R.mouthShapes||[]).map(s=>s.name);const grid=new Set(),talk={};
  mouthTalk=true;for(let o=0;o<=1.0001;o+=0.05)for(let f=-1;f<=1.0001;f+=0.05){v.MouthOpen=o;v.MouthForm=f;const k=mouthPick();grid.add(k)}
  // simulated auto-talk: 120 s at 30 fps through the real talk stepper
  const A=makeAnim(20260938);for(let i=0;i<3600;i++){stepTalk(A,1/30);const k=mouthPick();talk[k]=(talk[k]||0)+1}
  mouthTalk=false;v.MouthOpen=0.25;v.MouthForm=-1;const manual=mouthPick();for(const k in P)v[k]=P[k][2];
  return{names,talkGrid:[...grid],talkSim:talk,manualAt025m1:manual}});
 console.log(vw,JSON.stringify(r),'errs',errs.length);await p.close()}
await browser.close();
