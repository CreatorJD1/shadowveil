// ?handorder=1 check: per view, rest frame with &hairless=1&handorder=1 vs the &hairless=1 control (and vs base), staged palms loaded, z of hands, errors
const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');
(async()=>{const PORT=process.env.PORT||8792;const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new',protocolTimeout:1800000});const out={};
async function grab(v,q){const pg=await b.newPage();const errs=[],st=[];pg.on('pageerror',e=>errs.push(String(e)));pg.on('response',r=>{const u=r.url();if(/staged/.test(u))st.push(r.status()+' '+u.replace(/^.*?\/\/[^/]+\//,'').replace(/\?v=\d+$/,''))});
 await pg.goto(`http://127.0.0.1:${PORT}/${process.env.PAGE||'rig/index.html'}?view=${v}${q}`,{waitUntil:'domcontentloaded',timeout:600000});
 await pg.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:600000});await new Promise(r=>setTimeout(r,1500));
 const r=await pg.evaluate(async()=>{document.getElementById('auto').checked=false;document.getElementById('rest').click();await new Promise(r=>setTimeout(r,300));draw();
  const fr=Array.from(FR.getContext('2d').getImageData(0,0,W,H).data);const rp=Array.from(restPixels());
  const bc=document.createElement('canvas');bc.width=W;bc.height=H;const gb=bc.getContext('2d');gb.drawImage(R.im.base,0,0);const B=Array.from(gb.getImageData(0,0,W,H).data);
  document.getElementById('check').click();const z={};if(R.z)for(const k in R.z)if(/_palm|forearm|thigh/.test(k))z[k]=R.z[k];
  return{fr,rp,B,restCheck:document.getElementById('status').textContent.split('\n')[0],z,scheme:R.scheme&&R.scheme.hairless}});
 r.errors=errs;r.staged=[...new Set(st)];await pg.close();return r}
const cmp=(A,B)=>{let n=0;for(let i=0;i<A.length;i+=4){if(A[i]!==B[i]||A[i+1]!==B[i+1]||A[i+2]!==B[i+2]||A[i+3]!==B[i+3])n++}return n};
for(const v of (process.argv[2]||'apose,tpose,left,right,back').split(',')){const c=await grab(v,'&hairless=1&quality=linear');const t=await grab(v,'&hairless=1&handorder=1&quality=linear');
 out[v]={rest_FR_vs_control:cmp(t.fr,c.fr),restPixels_vs_control:cmp(t.rp,c.rp),restPixels_vs_base:{control:cmp(c.rp,c.B),handorder:cmp(t.rp,t.B)},restCheck:{control:c.restCheck,handorder:t.restCheck},
  z_handorder:t.z,z_control:c.z,scheme:t.scheme,staged_handorder:t.staged.filter(s=>/hands/.test(s)),errors:[...c.errors,...t.errors]};console.error(v,'done')}
console.log(JSON.stringify(out,null,1));await b.close()})().catch(e=>{console.error(e);process.exit(1)});
