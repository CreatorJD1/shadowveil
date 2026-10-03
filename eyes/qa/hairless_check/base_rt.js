// export views/<view>/base.png through the same canvas round-trip as renders (premultiplied alpha), using the rig's own R.im.base on the ?hairless=1 page
const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');const fs=require('fs');
(async()=>{const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new'});
try{for(const v of ['apose','tpose','left','right','back']){if(fs.existsSync(`renders/${v}_base_canvas.png`))continue;const pg=await b.newPage();
 await pg.goto(`http://127.0.0.1:8765/rig/?view=${v}&hairless=1&quality=linear`,{waitUntil:'domcontentloaded',timeout:300000});
 await pg.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:300000});
 const d=await pg.evaluate(()=>{document.getElementById('auto').checked=false;const c=document.createElement('canvas');c.width=W;c.height=H;c.getContext('2d').drawImage(R.im.base,0,0);return c.toDataURL('image/png')});
 fs.writeFileSync(`renders/${v}_base_canvas.png`,Buffer.from(d.split(',')[1],'base64'));await pg.close();console.error('base',v)}}finally{await b.close()}})().catch(e=>{console.error(e);process.exit(1)});
