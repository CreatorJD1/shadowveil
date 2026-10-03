// Headless verification of rig/poser.html against the live rig (read-only; scratch server on BM_PORT, default 8797).
// 1) console errors, 2) rest identity: poser Reset frame == index.html default frame (canvas #c pixels),
// 3) determinism: sequential playback == random-order scrub (canvas hash, hair drive, mouth shape, lids), 4) screenshot.
const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');const fs=require('fs');
const PORT=process.env.BM_PORT||8797,BASE=`http://127.0.0.1:${PORT}/rig/`;const OUT=__dirname+'/..';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const HASH=`async(cv)=>{const d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;const b=await crypto.subtle.digest('SHA-256',d);return [...new Uint8Array(b)].slice(0,12).map(x=>x.toString(16).padStart(2,'0')).join('')}`;
(async()=>{const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new',protocolTimeout:900000});
const res={};const errs=[];
const pg=await b.newPage();await pg.setViewport({width:1600,height:1000});
pg.on('console',m=>{if(m.type()==='error')errs.push('console: '+m.text())});pg.on('pageerror',e=>errs.push('pageerror: '+e.message));
await pg.goto(BASE+'poser.html',{waitUntil:'domcontentloaded',timeout:120000});
await pg.waitForFunction('window.SVPoser&&SVPoser.ready',{timeout:900000,polling:1000});await sleep(1500);
// rest identity
const poserRest=await pg.evaluate(async H=>{const hash=eval(H);document.getElementById('reset').click();await new Promise(r=>setTimeout(r,800));const cw=document.getElementById('rig').contentWindow;
 const restPx=cw.restPixels();const c=cw.document.getElementById('c');const live=await hash(c);
 const base=cw.document.createElement('canvas');base.width=c.width;base.height=c.height;base.getContext('2d').drawImage(cw.eval('R.im.base'),0,0);
 const B=base.getContext('2d').getImageData(0,0,c.width,c.height).data,L=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let diff=0;for(let i=0;i<L.length;i+=4){if(L[i+3]===0&&B[i+3]===0)continue;if(L[i]!==B[i]||L[i+1]!==B[i+1]||L[i+2]!==B[i+2]||L[i+3]!==B[i+3])diff++}
 return {hash:live,url:cw.location.search,vsBasePng:diff}},HASH);
res.poserRest=poserRest;
// determinism (state-level for every frame; pixel-level on a subset because one posed ss2 draw costs ~0.3-3 s here)
res.det=await pg.evaluate(async H=>{const hash=eval(H);const X=SVPoser,S=X.state;const cw=document.getElementById('rig').contentWindow;const c=cw.document.getElementById('c');
 const d={};for(const k in S.P)d[k]=S.P[k][2];
 const K=(t,o,mouth='step')=>({t,ease:'inout',mouth,values:{...d,...o}});
 S.hair.on=true;S.hair.sway=1;S.autoBlink=true;S.headLead=true;S.tl.fps=30;S.tl.dur=4;S.tl.seed=1337;
 S.tl.keys=[K(0,{},'smooth'),K(1,{NeckTwist:1,BodyLean:1,HeadTilt:1,MouthOpen:1,MouthForm:1},'smooth'),K(2,{NeckTwist:-1,BodyLean:-1,HeadTilt:-1,HeadNod:1,MouthOpen:0,MouthForm:-1}),K(3,{MouthOpen:0.5,MouthForm:0})];
 X.invalidate();document.getElementById('tl-dur').value=4;
 const pick=(o,f)=>{const v=cw.eval('v');const a=v.MouthOpen,b=v.MouthForm;v.MouthOpen=o;v.MouthForm=f;const r=cw.mouthPick();v.MouthOpen=a;v.MouthForm=b;return r};
 const st=f=>{const drive=X.bakeHairTo(f);const o=X.frameState(f);return JSON.stringify({o,drive,m:pick(o.MouthOpen,o.MouthForm)})};
 const N=120,seq=[];for(let f=0;f<=N;f++)seq.push(st(f));
 const order=[];let s=7;for(let i=0;i<80;i++){s=(s*1103515245+12345)%2147483648;order.push(s%(N+1))}order.push(N,0,64,31,90);
 const mism=[];for(const f of order){X.invalidate();if(st(f)!==seq[f])mism.push(f)}
 for(let f=N;f>=0;f--){if(st(f)!==seq[f])mism.push('warm'+f)}
 const P=seq.map(x=>JSON.parse(x));
 const shapes=[...new Set(P.slice(0,31).map(r=>r.m))];
 const rawShapes=[...new Set(Array.from({length:31},(_,f)=>{const u=f/30,e=u<.5?4*u*u*u:1-Math.pow(-2*u+2,3)/2;return pick(e,e)}))];
 const maxSway=Math.max(...P.map(r=>Math.max(0,...Object.values(r.drive||{}).map(q=>Math.abs(q.x)))));
 const shutFrames=P.filter(r=>r.o.EyeLOpen===0&&r.o.EyeROpen===0).map((r,i)=>i);
 // pixel level: frames rendered in order, then in reverse after a cold cache
 const W=()=>new Promise(r=>setTimeout(r,150));const PIX=[10,27,45,75,100];const ph={};for(const f of PIX){X.applyFrame(f);await W();ph[f]=await hash(c)}
 X.invalidate();const pmis=[];for(const f of [...PIX].reverse()){X.applyFrame(f);await W();if(await hash(c)!==ph[f])pmis.push(f)}
 for(const f of [45,45]){X.applyFrame(f);await W();if(await hash(c)!==ph[f])pmis.push('repeat'+f)}
 // real rAF playback: compare the pushed rig state of each displayed frame with the scrub state
 const pb=[];S.tl.loop=false;X.invalidate();S.tl.frame=0;document.getElementById('tl-play').click();const t0=performance.now();
 while(S.tl.playing&&performance.now()-t0<120000){await new Promise(r=>requestAnimationFrame(r));const f=S.tl.frame;const v=cw.eval('v');pb.push({f,dr:JSON.stringify(cw.eval('hairDrive')),m:cw.mouthPick(),l:v.EyeLOpen})}
 let pbm=0;for(const p of pb){const q=P[p.f];const qd={};const dr=q.drive||{};for(const id in dr)qd[id]={x:Math.max(-1,Math.min(1,dr[id].x*S.hair.sway)),y:Math.max(-1,Math.min(1,dr[id].y*S.hair.sway))};
   if(p.dr!==JSON.stringify(qd)||p.m!==q.m||p.l!==q.o.EyeLOpen)pbm++}
 return {frames:N+1,stateScrubChecks:order.length+N+1,stateMismatches:mism.length,mismatchFrames:mism.slice(0,10),pixelFramesChecked:PIX,pixelMismatches:pmis,
  smoothTweenShapes_0to1s:shapes,naiveTweenWouldShow:rawShapes,keyShapes:[pick(0,0),pick(1,1)],maxHairSwayX:maxSway,framesBothLidsShut:shutFrames,reversalBlinkRequests:S.eyeBake&&S.eyeBake.req,
  gazeX:{f15:P[15].o.EyeBallX,f25:P[25].o.EyeBallX,f45:P[45].o.EyeBallX},playbackFramesShown:pb.length,playbackLastFrame:pb.length?pb[pb.length-1].f:null,playbackStateMismatches:pbm}},HASH);
console.log('det done');
// screenshot: clear the timeline, pose by hand through the poser's own setters
await pg.evaluate(async()=>{const X=SVPoser,S=X.state;S.tl.keys=[];document.getElementById('tl-clear').click();document.getElementById('reset').click();
 const o={ShoulderL:-1,ShoulderR:1,ElbowL:-0.6,ElbowR:0.6,HeadTilt:0.6,EyeBallX:0.6,MouthOpen:1,MouthForm:1,HandRIndex:1,HandRMiddle:1,HandRRing:1,HandRPinky:1,HandRThumb:1,HandLSpread:1,HipL:-0.3,HipR:0.3};
 for(const k in o)X.setV(k,o[k]);X.afterEdit();X.commit();await new Promise(r=>setTimeout(r,1500))});
await sleep(1000);await pg.screenshot({path:OUT+'/shot.png'});
res.undoWorks=await pg.evaluate(async()=>{SVPoser.undo();await new Promise(r=>setTimeout(r,300));const a=SVPoser.state.vals.ShoulderL;SVPoser.redo();return {afterUndo:a,afterRedo:SVPoser.state.vals.ShoulderL}});
// back to rest, clear timeline, then compare to index.html default
await pg.evaluate(async()=>{const S=SVPoser.state;S.tl.keys=[];document.getElementById('tl-clear').click();document.getElementById('reset').click();await new Promise(r=>setTimeout(r,800))});
res.poserRestAfterTimeline=await pg.evaluate(async H=>{const hash=eval(H);const cw=document.getElementById('rig').contentWindow;return hash(cw.document.getElementById('c'))},HASH);
await pg.close();
const p2=await b.newPage();await p2.setViewport({width:1600,height:1000});p2.on('pageerror',e=>errs.push('index pageerror: '+e.message));
await p2.goto(BASE+'index.html',{waitUntil:'domcontentloaded',timeout:120000});await p2.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:900000,polling:1000});await sleep(2500);
res.indexDefault=await p2.evaluate(async H=>{const hash=eval(H);return {hash:await hash(document.getElementById('c')),auto:document.getElementById('auto').checked}},HASH);
res.restIdentical=res.indexDefault.hash===res.poserRest.hash&&res.indexDefault.hash===res.poserRestAfterTimeline;
res.errors=errs;console.log(JSON.stringify(res,null,1));fs.writeFileSync(OUT+'/verify.json',JSON.stringify(res,null,1));await b.close()})().catch(e=>{console.error(e);process.exit(1)});
