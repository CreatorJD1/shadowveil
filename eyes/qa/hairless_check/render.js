// Eyes on hairless base: renders live vs ?hairless=1 per face view and eye pose (approach reused from rig/work/hairless/hl_render.js)
const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');const fs=require('fs');
const POSES=[['rest',null],['posed_default',{}],['blink0.5',{EyeLOpen:.5,EyeROpen:.5}],['blink0',{EyeLOpen:0,EyeROpen:0}],
['gx+1',{EyeBallX:1}],['gx-1',{EyeBallX:-1}],['gy+1',{EyeBallY:1}],['gy-1',{EyeBallY:-1}],
['gx+1y+1',{EyeBallX:1,EyeBallY:1}],['gx+1y-1',{EyeBallX:1,EyeBallY:-1}],['gx-1y+1',{EyeBallX:-1,EyeBallY:1}],['gx-1y-1',{EyeBallX:-1,EyeBallY:-1}],
['closed_gx+1',{EyeLOpen:0,EyeROpen:0,EyeBallX:1}],['closed_gx-1',{EyeLOpen:0,EyeROpen:0,EyeBallX:-1}]];
(async()=>{const views=(process.argv[2]||'apose,tpose,left,right,back').split(',');
const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new'});const res={};
try{for(const v of views)for(const [tag,q] of [['live',''],['hairless','&hairless=1']]){const pg=await b.newPage();const errs=[],st=[];pg.on('pageerror',e=>errs.push(String(e)));pg.on('response',r=>{const u=r.url();if(/staged|base_body/.test(u))st.push(r.status()+' '+u.replace(/^.*?8765\//,'').replace(/\?v=\d+$/,''))});
 await pg.goto(`http://127.0.0.1:8765/rig/?view=${v}&quality=linear${q}`,{waitUntil:'domcontentloaded',timeout:120000});
 await pg.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:120000});await new Promise(r=>setTimeout(r,1500));
 const ps=v==='back'?POSES.slice(0,2):POSES;
 const r=await pg.evaluate(async POSES=>{document.getElementById('auto').checked=false;if(typeof pauseManual==='function')pauseManual();
  const out={img:{},hasEyes:!!R.eyes};document.getElementById('check').click();out.restCheck=document.getElementById('status').textContent.split('\n')[0];
  for(const [t,ps] of POSES){for(const k in P)v[k]=P[k][2];if(ps)for(const k in ps)v[k]=ps[k];const c=document.createElement('canvas');c.width=W;c.height=H;const g=guard(c.getContext('2d'));render(g,!ps);out.img[t]=c.toDataURL('image/png')}
  for(const k in P)v[k]=P[k][2];out.fallbacks=window.RigHairless?RigHairless.missing:null;return out},ps);
 for(const t in r.img)fs.writeFileSync(`renders/${v}_${tag}_${t}.png`,Buffer.from(r.img[t].split(',')[1],'base64'));delete r.img;
 res[v+'_'+tag]={...r,errs,loaded:[...new Set(st)]};await pg.close();console.error('done',v,tag)}}
finally{await b.close()}
fs.writeFileSync('render_log.json',JSON.stringify(res,null,1))})().catch(e=>{console.error(e);process.exit(1)});
