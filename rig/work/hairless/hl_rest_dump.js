const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');const fs=require('fs');
(async()=>{const q=process.argv[2]||'',tag=process.argv[3]||'x';const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new'});
const pg=await b.newPage();const urls=[];pg.on('response',r=>{if(/staged/.test(r.url()))urls.push(r.status()+' '+r.url().replace(/^.*?8765/,'').replace(/\?v=\d+/,''))});
await pg.goto('http://127.0.0.1:8765/rig/index.html?view=apose&quality=linear'+q,{waitUntil:'domcontentloaded',timeout:120000});
await pg.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:120000});await new Promise(r=>setTimeout(r,1500));
const r=await pg.evaluate(()=>{document.getElementById('auto').checked=false;const A=restPixels();const c=document.createElement('canvas');c.width=W;c.height=H;const g=c.getContext('2d');const id=g.createImageData(W,H);id.data.set(A);g.putImageData(id,0,0);
 const hz=Object.entries(R.z).filter(([k])=>/palm|forearm/.test(k));return{png:c.toDataURL('image/png'),scheme:R.scheme,hz,skinLayers:R.skin?R.skin.groups.map(g=>g.layer):null}});
fs.writeFileSync(`rest_${tag}.png`,Buffer.from(r.png.split(',')[1],'base64'));delete r.png;console.log(JSON.stringify({...r,urls:[...new Set(urls)]}));await b.close()})();
