// hairless probe: is the hair stripped/replaced? per view: hairless vs plain FR diff px, hair URLs mapped, staged responses, errors
const pp=require('/workspace/jt/node_modules/puppeteer-core');(async()=>{const b=await pp.launch({executablePath:'/usr/bin/google-chrome',headless:'new',protocolTimeout:1800000,args:['--no-sandbox','--disable-dev-shm-usage']});const out={};
const PORT=process.env.PORT||8795;
async function grab(v,q){const p=await b.newPage();const e=[],st=[];p.on('pageerror',x=>e.push(x.message));p.on('response',r=>{const u=r.url();if(/staged|hairless/.test(u))st.push(r.status()+' '+u.replace(/^.*?\/\/[^/]+\//,'').replace(/\?v=\d+$/,''))});
 await p.goto(`http://127.0.0.1:${PORT}/rig/index.html?view=${v}${q}`,{waitUntil:'domcontentloaded',timeout:1500000});
 await p.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:1500000,polling:2000});await new Promise(r=>setTimeout(r,1000));
 const r=await p.evaluate(()=>{document.getElementById('auto').checked=false;document.getElementById('rest').click();draw();const d=FR.getContext('2d').getImageData(0,0,W,H).data;let h=0;for(let i=0;i<d.length;i+=4)h=(h*31+d[i]*7+d[i+1]*3+d[i+2]+d[i+3]*11)|0;
  return{on:window.RigHairless?RigHairless.on:null,mapN:window.RigHairless?Object.keys(RigHairless.hairMap||{}).length:null,missing:window.RigHairless?RigHairless.missing:null,hash:h,px:Array.from(d)}});
 r.errors=e;r.staged=[...new Set(st)];await p.close();return r}
for(const v of (process.argv[2]||'apose,tpose,left,right,back').split(',')){const a=await grab(v,'&quality=linear'),h=await grab(v,'&hairless=1&quality=linear');let n=0;for(let i=0;i<a.px.length;i+=4)if(a.px[i]!==h.px[i]||a.px[i+1]!==h.px[i+1]||a.px[i+2]!==h.px[i+2]||a.px[i+3]!==h.px[i+3])n++;
 out[v]={px_hairless_vs_plain:n,hairless_on:h.on,hairMapEntries:h.mapN,missing:h.missing,stagedHairResponses:h.staged.filter(s=>/hair/.test(s)).length,stagedSample:h.staged.slice(0,4),errors:[...a.errors,...h.errors]};console.error(v,JSON.stringify(out[v]))}
console.log(JSON.stringify(out,null,1));await b.close()})().catch(e=>{console.error(e);process.exit(1)});
