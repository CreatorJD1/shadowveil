// pixel-level determinism: frames rendered forward, then in reverse after a cold cache; also report which rig state differs
const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');const fs=require('fs');
const HASH=`async(cv)=>{const d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;const b=await crypto.subtle.digest('SHA-256',d);return [...new Uint8Array(b)].slice(0,12).map(x=>x.toString(16).padStart(2,'0')).join('')}`;
(async()=>{const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new',protocolTimeout:1500000});
const pg=await b.newPage();await pg.setViewport({width:1600,height:1000});const errs=[];pg.on('console',m=>{if(m.type()==='error')errs.push(m.text())});pg.on('pageerror',e=>errs.push(e.message));
await pg.goto('http://127.0.0.1:8797/rig/poser.html',{waitUntil:'domcontentloaded'});await pg.waitForFunction('window.SVPoser&&SVPoser.ready',{timeout:900000,polling:1000});await new Promise(r=>setTimeout(r,1500));
const r=await pg.evaluate(async H=>{const hash=eval(H);const X=SVPoser,S=X.state;const cw=document.getElementById('rig').contentWindow;const c=cw.document.getElementById('c');
 const d={};for(const k in S.P)d[k]=S.P[k][2];const K=(t,o,mouth='step')=>({t,ease:'inout',mouth,values:{...d,...o}});
 S.hair.on=true;S.hair.sway=1;S.autoBlink=true;S.headLead=true;S.tl.fps=30;S.tl.dur=4;S.tl.seed=1337;
 S.tl.keys=[K(0,{}),K(1,{NeckTwist:1,BodyLean:1,HeadTilt:1,MouthOpen:1,MouthForm:1},'smooth'),K(2,{NeckTwist:-1,BodyLean:-1,HeadTilt:-1,HeadNod:1,MouthOpen:0,MouthForm:-1}),K(3,{MouthOpen:0.5,MouthForm:0})];
 X.invalidate();const wait=()=>new Promise(r=>setTimeout(r,120));
 const PIX=[10,27,45,75,100,120];const ph={},t0=performance.now();for(const f of PIX){X.applyFrame(f);await wait();ph[f]=await hash(c)}
 const ms=(performance.now()-t0)/PIX.length;X.invalidate();const pm=[];for(const f of [...PIX].reverse()){X.applyFrame(f);await wait();if(await hash(c)!==ph[f])pm.push(f)}
 // same frame twice in a row, warm
 const again=[];for(const f of [45,45,27,27]){X.applyFrame(f);await wait();again.push(await hash(c)===ph[f])}
 return {fade:cw.document.getElementById('mouthfade').value,pixelFrames:PIX,pixelMismatchesAfterColdReverse:pm,repeatSame:again,msPerFrame:Math.round(ms)}},HASH);
r.errors=errs;console.log(JSON.stringify(r));fs.writeFileSync(__dirname+'/../pixdet.json',JSON.stringify(r,null,1));await b.close()})().catch(e=>{console.error(e);process.exit(1)});
