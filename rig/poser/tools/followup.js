// follow-up checks: head-lead direction by rendering, Clear refreshes markers, mouth labels inside the pad, rest identity, screenshot
const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');const fs=require('fs');
const PORT=process.env.BM_PORT||8796,BASE=`http://127.0.0.1:${PORT}/rig/`,OUT=__dirname+'/..';const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const HASH=`async(cv)=>{const d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;const b=await crypto.subtle.digest('SHA-256',d);return [...new Uint8Array(b)].slice(0,12).map(x=>x.toString(16).padStart(2,'0')).join('')}`;
(async()=>{const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new',protocolTimeout:1500000});
const errs=[],res={};const pg=await b.newPage();await pg.setViewport({width:1600,height:1000});
pg.on('console',m=>{if(m.type()==='error')errs.push('console: '+m.text())});pg.on('pageerror',e=>errs.push('pageerror: '+e.message));
await pg.goto(BASE+'poser.html',{waitUntil:'domcontentloaded'});await pg.waitForFunction('window.SVPoser&&SVPoser.ready',{timeout:900000,polling:1000});await sleep(1500);
res.lead=await pg.evaluate(async()=>{const X=SVPoser,S=X.state;const cw=document.getElementById('rig').contentWindow;
 // render-based head direction: luminance centroid shift of the head band, rest vs posed, through the rig's render()
 const shot=vals=>{const v=cw.eval('v'),P=cw.eval('P');for(const k in P)v[k]=P[k][2];Object.assign(v,vals);const c=cw.document.createElement('canvas');c.width=cw.eval('W');c.height=cw.eval('H');cw.render(cw.guard(c.getContext('2d')),!Object.keys(vals).length);return c.getContext('2d').getImageData(0,100,c.width,240).data};
 const W=cw.eval('W');const cx=(d)=>{let sx=0,sw=0;for(let i=0;i<d.length;i+=4){const a=d[i+3];if(a>200){const x=(i/4)%W;sx+=x;sw++}}return sx/sw};
 const r0=cx(shot({})),rL=cx(shot({BodyLean:1})),rN=cx(shot({NeckTwist:1}));
 const d={};for(const k in S.P)d[k]=S.P[k][2];const K=(t,o)=>({t,ease:'inout',mouth:'step',values:{...d,...o}});
 S.autoBlink=false;S.headLead=true;S.leadMs=150;S.tl.fps=30;S.tl.dur=3;
 S.tl.keys=[K(0,{}),K(1,{BodyLean:1}),K(2,{BodyLean:-1})];X.invalidate();
 const gx=f=>X.frameState(f).EyeBallX;const lean=[];for(const f of [0,10,15,20,26,30,40,45,50,56,60])lean.push([f,+gx(f).toFixed(3),+X.poseAt(f/30).BodyLean.toFixed(3)]);
 S.tl.keys=[K(0,{}),K(1,{NeckTwist:1})];X.invalidate();const neck=[10,20,30].map(f=>+gx(f).toFixed(3));
 // eye render direction for EyeBallX +1 (iris moves toward screen right = her left)
 return {headCentroidX:{rest:+r0.toFixed(2),bodyLeanPlus1:+rL.toFixed(2),neckTwistPlus1:+rN.toFixed(2)},leanKeys_frame_gazeX_lean:lean,neckOnlyKey_gazeX:neck}});
// clear refreshes markers
res.clear=await pg.evaluate(async()=>{const X=SVPoser,S=X.state;document.getElementById('reset').click();S.tl.frame=30;X.setKey();S.tl.frame=60;X.setKey();const before=document.querySelectorAll('#keymarks i').length;
 document.getElementById('tl-clear').click();await new Promise(r=>setTimeout(r,200));return {markersBefore:before,markersAfter:document.querySelectorAll('#keymarks i').length,keys:S.tl.keys.length,fade:document.getElementById('rig').contentWindow.document.getElementById('mouthfade').value,info:document.getElementById('tlinfo').textContent}});
// mouth labels inside the pad
res.labels=await pg.evaluate(()=>{const p=document.getElementById('mpad').getBoundingClientRect();return [...document.querySelectorAll('#mpad .mk')].map(m=>{const r=m.getBoundingClientRect();return [m.textContent,r.left>=p.left-0.5&&r.right<=p.right+0.5&&r.top>=p.top-0.5&&r.bottom<=p.bottom+0.5]}).filter(x=>!x[1]).map(x=>x[0])});
// rest identity
res.poserRest=await pg.evaluate(async H=>{const hash=eval(H);document.getElementById('reset').click();await new Promise(r=>setTimeout(r,800));return hash(document.getElementById('rig').contentWindow.document.getElementById('c'))},HASH);
// screenshot with an empty timeline
await pg.evaluate(async()=>{const X=SVPoser;const o={ShoulderL:-1,ShoulderR:1,ElbowL:-0.6,ElbowR:0.6,HeadTilt:0.6,EyeBallX:0.6,MouthOpen:1,MouthForm:1,HandRIndex:1,HandRMiddle:1,HandRRing:1,HandRPinky:1,HandRThumb:1,HandLSpread:1,HipL:-0.3,HipR:0.3};
 for(const k in o)X.setV(k,o[k]);X.afterEdit();X.commit();await new Promise(r=>setTimeout(r,1500))});
await sleep(1000);await pg.screenshot({path:OUT+'/shot.png'});await pg.evaluate(()=>document.getElementById('reset').click());await pg.close();
const p2=await b.newPage();p2.on('pageerror',e=>errs.push('index: '+e.message));await p2.goto(BASE+'index.html',{waitUntil:'domcontentloaded'});await p2.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:900000,polling:1000});await sleep(2500);
res.indexDefault=await p2.evaluate(async H=>{const hash=eval(H);return hash(document.getElementById('c'))},HASH);res.restIdentical=res.indexDefault===res.poserRest;
res.errors=errs;console.log(JSON.stringify(res,null,1));fs.writeFileSync(OUT+'/followup.json',JSON.stringify(res,null,1));await b.close()})().catch(e=>{console.error(e);process.exit(1)});
