const launch=(()=>{const {chromium}=require('/usr/local/lib/pnpm/5/.pnpm/playwright-core@1.59.1/node_modules/playwright-core');return()=>chromium.launch({executablePath:'/usr/bin/google-chrome',args:['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']})})();
const URL='http://127.0.0.1:8765/app/driver/simple.html';
(async()=>{const b=await launch();const p=await b.newPage({viewport:{width:1500,height:1000}});
const errs=[],warns=[];p.on('console',m=>{if(m.type()==='error')errs.push(m.text());if(m.type()==='warning')warns.push(m.text())});p.on('pageerror',e=>errs.push('PAGEERR '+e.message));p.on('response',r=>{if(r.status()>=400)errs.push('HTTP '+r.status()+' '+r.url())});
const res={pass:[],fail:[]};const ok=(n,c,d='')=>(c?res.pass:res.fail).push(n+(d?' ['+d+']':''));
const ready=async(loads)=>{await p.waitForFunction(n=>window.SVSimple&&SVSimple.ready&&SVSimple.loads>=n,loads,{timeout:300000})};
const vals=()=>p.evaluate(()=>({...SVSimple.cw.eval('v')}));
const atRest=()=>p.evaluate(()=>{const P=SVSimple.cw.eval('P'),v=SVSimple.cw.eval('v');return Object.keys(P).filter(k=>v[k]!==P[k][2])});
const reset=async()=>{await p.click('#reset');await p.waitForTimeout(150);return atRest()};
await p.goto(URL);await ready(1);await p.waitForTimeout(800);
const frHash=()=>p.evaluate(()=>{const cw=SVSimple.cw;cw.draw();const FR=cw.eval('FR');const a=FR.getContext('2d').getImageData(0,0,FR.width,FR.height).data;let h=0;for(let i=0;i<a.length;i++)h=(h*31+a[i])|0;return h});
const FR0=await frHash();
ok('loads at exact rest',(await atRest()).length===0,(await atRest()).join(','));
const rigPanelHidden=await p.evaluate(()=>getComputedStyle(SVSimple.cw.document.getElementById('ui')).display==='none'&&getComputedStyle(SVSimple.cw.document.getElementById('layers')).display==='none');
ok('rig own panels hidden inside the stage',rigPanelHidden);
ok('hair preset A by default',await p.evaluate(()=>SVSimple.cw.document.getElementById('hairpreset').value==='A'));
// ranges
const ranges=await p.evaluate(()=>SVSimple.controls.filter(c=>c.kind==='range').map(c=>({id:c.id,keys:c.keys,min:+c.el.min,max:+c.el.max,dis:c.el.disabled})));
const perCtl=[];
for(const r of ranges){
  if(r.id==='sway')continue;               // tested with physics below
  if(r.dis){ok('range '+r.id+' enabled',false,'disabled at apose');continue}
  const before=await vals();
  const target=await p.evaluate(({id})=>{const c=SVSimple.controls.find(c=>c.id===id);const cur=+c.el.value,mn=+c.el.min,mx=+c.el.max;const t=cur<(mn+mx)/2?mx:mn;c.el.value=t;c.el.dispatchEvent(new Event('input',{bubbles:true}));return t},r);
  await p.waitForTimeout(60);const after=await vals();
  const moved=r.keys.filter(k=>Math.abs(after[k]-before[k])>1e-9);
  perCtl.push(`${r.id} -> ${target}: ${moved.map(k=>k+' '+before[k].toFixed(2)+'→'+after[k].toFixed(2)).join(', ')}`);
  ok('range '+r.id+' moves '+r.keys.join('/'),moved.length>0,moved.join(','));
  const left=await reset();ok('reset after '+r.id,left.length===0,left.join(','));
}
// gaze pad
{const bb=await p.locator('#gaze').boundingBox();await p.mouse.move(bb.x+bb.width*0.9,bb.y+bb.height*0.15);await p.mouse.down();await p.mouse.move(bb.x+bb.width*0.95,bb.y+bb.height*0.1);await p.mouse.up();
 const v=await vals();ok('gaze pad moves EyeBallX/Y',v.EyeBallX>0.5&&v.EyeBallY<-0.5,`X ${v.EyeBallX.toFixed(2)} Y ${v.EyeBallY.toFixed(2)}`);perCtl.push(`gaze -> EyeBallX ${v.EyeBallX.toFixed(2)}, EyeBallY ${v.EyeBallY.toFixed(2)}`);
 await p.dblclick('#gaze');const v2=await vals();ok('gaze dblclick centres',v2.EyeBallX===0&&v2.EyeBallY===0);ok('reset after gaze',(await reset()).length===0)}
// expressions
for(const [n,o,f,shape] of [['Smile',0,1,'mouth_smile'],['Anger',0.25,-1,'mouth_anger'],['Neutral',0,0,'mouth_rest']]){await p.click(`[data-expr=${n}]`);await p.waitForTimeout(400);
 const v=await vals();const cur=await p.evaluate(()=>SVSimple.cw.eval('mouthState.cur'));ok(`expression ${n} sets MouthOpen/Form (${o},${f})`,v.MouthOpen===o&&v.MouthForm===f,`${v.MouthOpen},${v.MouthForm} shape ${cur}`);perCtl.push(`expr ${n} -> MouthOpen ${v.MouthOpen}, MouthForm ${v.MouthForm}, shape ${cur}`)}
ok('reset after expressions',(await reset()).length===0);
// hand pose
for(const n of ['Fist','Point','Peace','Open']){await p.selectOption('[data-ctl=handpose]',n);await p.waitForTimeout(80);const v=await vals();const s=['Thumb','Index','Middle','Ring','Pinky'].map(f=>v['HandL'+f]+'/'+v['HandR'+f]).join(' ');perCtl.push(`handpose ${n} -> ${s}`);
 const exp={Fist:[1,1,1,1,1],Point:[1,0,1,1,1],Peace:[1,0,0,1,1],Open:[0,0,0,0,0]}[n];ok('hand pose '+n,['Thumb','Index','Middle','Ring','Pinky'].every((f,i)=>v['HandL'+f]===exp[i]&&v['HandR'+f]===exp[i]))}
ok('reset after hand pose',(await reset()).length===0);
// auto-blink
await p.check('[data-ctl=autoblink]');let minL=1;for(let i=0;i<70;i++){await p.waitForTimeout(100);const v=await vals();minL=Math.min(minL,v.EyeLOpen,v.EyeROpen)}
ok('auto-blink closes lids',minL<0.2,'min open '+minL.toFixed(2));perCtl.push('autoblink -> min EyeL/ROpen over 7 s '+minL.toFixed(2));await p.uncheck('[data-ctl=autoblink]');
// auto-talk
await p.check('[data-ctl=autotalk]');let maxO=0;const shapes=new Set();for(let i=0;i<40;i++){await p.waitForTimeout(100);const v=await vals();maxO=Math.max(maxO,v.MouthOpen);shapes.add(await p.evaluate(()=>SVSimple.cw.eval('mouthState.cur')))}
ok('auto-talk opens mouth',maxO>0.2,'max MouthOpen '+maxO.toFixed(2));ok('auto-talk never picks EE/smile/anger',![...shapes].some(s=>/EE|smile|anger/.test(s)),[...shapes].join(','));perCtl.push('autotalk -> max MouthOpen '+maxO.toFixed(2)+', shapes '+[...shapes].join(','));
await p.uncheck('[data-ctl=autotalk]');await p.waitForTimeout(100);{const v=await vals();ok('auto-talk off restores mouth',v.MouthOpen===0&&v.MouthForm===0)}
// physics + sway amount
await p.check('[data-ctl=physics]');await p.waitForTimeout(1500);
const drive=()=>p.evaluate(()=>{const d=SVSimple.cw.eval('hairDrive');if(!d)return null;return Object.values(d).reduce((a,q)=>a+Math.abs(q.x)+Math.abs(q.y),0)});
const d1=await drive();ok('physics on: strands driven',d1!=null&&d1>0,'sum|drive| '+(d1||0).toFixed(3));
await p.evaluate(()=>{const c=SVSimple.controls.find(c=>c.id==='sway');c.el.value=0;c.el.dispatchEvent(new Event('input',{bubbles:true}))});await p.waitForTimeout(300);
const d0=await drive();ok('sway amount 0 zeroes all strands',d0===0,'sum '+d0);
await p.evaluate(()=>{const c=SVSimple.controls.find(c=>c.id==='sway');c.el.value=1.5;c.el.dispatchEvent(new Event('input',{bubbles:true}))});await p.waitForTimeout(300);
const d15=await drive();ok('sway amount 1.5 scales strands up',d15>d1*0.9,'sum '+(d15||0).toFixed(3));perCtl.push(`physics+sway -> sum|hairDrive| at 1.0: ${d1?.toFixed(3)}, 0: ${d0}, 1.5: ${d15?.toFixed(3)}`);
await p.selectOption('[data-ctl=preset]','B');ok('spring preset B reaches rig',await p.evaluate(()=>SVSimple.cw.document.getElementById('hairpreset').value==='B'));
await p.selectOption('[data-ctl=preset]','A');
await p.uncheck('[data-ctl=physics]');await p.waitForTimeout(200);ok('physics off clears drive',(await drive())===null);
// missing params
const miss=await p.evaluate(()=>[...document.querySelectorAll('[data-missing]')].map(e=>e.dataset.ctl+':'+e.disabled));ok('no-param controls disabled',miss.every(s=>s.endsWith(':true')),miss.join(' '));
// full pose then Reset -> exact rest incl. pixels
for(const id of ['p:BodyLean','weight','p:ShoulderL','curlR','p:HeadTilt','p:RootX','p:NeckTwist']) await p.evaluate(id=>{const c=SVSimple.controls.find(c=>c.id===id);c.el.value=c.el.max*0.6;c.el.dispatchEvent(new Event('input',{bubbles:true}))},id);
await p.check('[data-ctl=physics]');await p.check('[data-ctl=autoblink]');await p.check('[data-ctl=autotalk]');await p.waitForTimeout(800);
ok('posed before reset',(await atRest()).length>5);
const left=await reset();await p.waitForTimeout(500);ok('Reset to rest: every param at rest (with physics/blink/talk on)',left.length===0&&(await atRest()).length===0,left.join(','));
const FR1=await frHash();ok('on-screen frame after Reset == frame of a fresh rest load',FR1===FR0,FR0+' vs '+FR1);
await p.evaluate(()=>SVSimple.cw.document.getElementById('check').click());await p.waitForTimeout(3000);const rc=await p.evaluate(()=>SVSimple.cw.document.getElementById('status').textContent.split('\n')[0]);ok('rig Rest check',/^PASS/.test(rc),rc);
await p.screenshot({path:'/workspace/shadowveil/app/driver/simple.png'});
// view dial carries manual pose
await p.evaluate(()=>{const c=SVSimple.controls.find(c=>c.id==='p:BodyLean');c.el.value=0.5;c.el.dispatchEvent(new Event('input',{bubbles:true}))});
await p.click('text[data-view=tpose]');await ready(2);await p.waitForTimeout(500);
{const s=await p.evaluate(()=>({src:SVSimple.cw.location.search,lean:SVSimple.cw.eval('v.BodyLean'),viewSel:SVSimple.cw.document.getElementById('view').value}));ok('view dial -> tpose (pose carried)',s.viewSel==='tpose'&&s.lean===0.5,JSON.stringify(s))}
ok('reset at tpose',(await reset()).length===0);
// motion
await p.selectOption('#motion','jump');await ready(3);await p.waitForTimeout(2500);await p.click('#replay');await p.waitForTimeout(300);
{const st=await p.evaluate(()=>({clip:SVSimple.cw.SVClip.state,auto:SVSimple.cw.document.getElementById('auto').checked,src:SVSimple.cw.location.search}));const a=await vals();await p.waitForTimeout(250);const b2=await vals();const mv=Object.keys(a).filter(k=>a[k]!==b2[k]);
 ok('motion jump plays live clip',st.clip.ready&&mv.length>0,JSON.stringify(st)+' moving '+mv.length);perCtl.push('motion jump -> '+mv.length+' params moving, '+st.src)}
await p.selectOption('#motion','idle');await ready(4);await p.waitForTimeout(2500);
{const a=await vals();await p.waitForTimeout(500);const b2=await vals();const mv=Object.keys(a).filter(k=>a[k]!==b2[k]);ok('motion idle plays',mv.length>0,mv.length+' moving');perCtl.push('motion idle -> '+mv.length+' params moving')}
await p.click('#reset');await ready(5);await p.waitForTimeout(500);ok('Reset from motion -> manual + rest',(await atRest()).length===0&&await p.evaluate(()=>!SVSimple.state.motion&&!SVSimple.cw.location.search.includes('clip')));
// counts
const counts=await p.evaluate(()=>({all:document.querySelectorAll('aside input,aside select,aside button,#gaze,#dial text').length,missing:document.querySelectorAll('[data-missing]').length,adv:document.querySelectorAll('#sec-adv input').length}));
console.log(JSON.stringify(res,null,1));console.log('per-control:\n'+perCtl.join('\n'));console.log('counts',JSON.stringify(counts));console.log('console errors',JSON.stringify(errs));console.log('warnings',JSON.stringify(warns.slice(0,10)));
await b.close()})().catch(e=>{console.error('FATAL',e);process.exit(1)});
