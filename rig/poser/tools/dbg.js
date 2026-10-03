const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');
(async()=>{const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new',protocolTimeout:900000});
const pg=await b.newPage();await pg.setViewport({width:1600,height:1000});
await pg.goto('http://127.0.0.1:8797/rig/poser.html',{waitUntil:'domcontentloaded'});await pg.waitForFunction('window.SVPoser&&SVPoser.ready',{timeout:900000,polling:1000});
const r=await pg.evaluate(()=>{const X=SVPoser,S=X.state;const d={};for(const k in S.P)d[k]=S.P[k][2];const K=(t,o,mouth='step')=>({t,ease:'inout',mouth,values:{...d,...o}});
 S.tl.keys=[K(0,{}),K(1,{NeckTwist:1,BodyLean:1,HeadTilt:1,MouthOpen:1,MouthForm:1},'smooth'),K(2,{NeckTwist:-1})];X.invalidate();
 const p=X.poseAt(0.9);X.applyFrame(27);const cw=document.getElementById('rig').contentWindow;const v=cw.eval('v');
 return {p:{n:p.NeckTwist,l:p.BodyLean,mo:p.MouthOpen},vals:{n:S.vals.NeckTwist,mo:S.vals.MouthOpen},v:{n:v.NeckTwist,l:v.BodyLean,mo:v.MouthOpen,t:v.HeadTilt},en:cw.eval('inputs.NeckTwist.disabled+","+inputs.BodyLean.disabled'),pick:cw.mouthPick()}});
console.log(JSON.stringify(r));await b.close()})();
