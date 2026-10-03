// shared headless renderer for the benchmark tools: loads the LIVE rig read-only on the scratch server and renders
// poses through the rig's own render(g,rest) into an offscreen canvas (same code path as the screen; nothing written to rig/).
const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');
const PORT=process.env.BM_PORT||8797;
async function openRig(view='apose',extra=''){
  const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new',protocolTimeout:900000});
  const pg=await b.newPage();const errs=[];pg.on('pageerror',e=>errs.push(String(e)));
  await pg.setViewport({width:1600,height:1000});
  await pg.goto(`http://127.0.0.1:${PORT}/rig/index.html?view=${view}&quality=linear${extra}`,{waitUntil:'domcontentloaded',timeout:120000});
  await pg.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:900000,polling:2000});
  await new Promise(r=>setTimeout(r,1500));
  await pg.evaluate(()=>{document.getElementById('auto').checked=false;pauseManual()});
  return {b,pg,errs};
}
// values: {param:value}; unspecified params go to their P default. Returns PNG dataURL (transparent where nothing drawn).
async function renderPose(pg,values){
  return pg.evaluate(vals=>{for(const k in P)v[k]=P[k][2];const unknown=[];
    for(const k in vals){if(!(k in P)){unknown.push(k);continue}v[k]=Math.min(P[k][1],Math.max(P[k][0],+vals[k]))}
    const rest=Object.keys(vals).every(k=>!(k in P)||v[k]===P[k][2]);
    const c=document.createElement('canvas');c.width=W;c.height=H;const g=guard(c.getContext('2d'));render(g,rest);
    const url=c.toDataURL('image/png');for(const k in P)v[k]=P[k][2];return {url,unknown,rest}},values);
}
module.exports={openRig,renderPose};
