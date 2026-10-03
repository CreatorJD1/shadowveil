const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');
(async()=>{const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox'],headless:'new',protocolTimeout:600000});
for(const v of ['left','right']){const pg=await b.newPage();await pg.goto(`http://127.0.0.1:8793/rig/index.html?view=${v}`,{waitUntil:'domcontentloaded'});await pg.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:600000});
console.log(v,JSON.stringify(await pg.evaluate(()=>R.skin.bones.filter(b=>b.param).map(b=>{const o={};for(const x of [1,-1]){const s=v[b.param];v[b.param]=x;o[x]=bodyAngle(b);v[b.param]=s}return [b.id||b.name,b.param,o]}))));await pg.close()}await b.close()})();
