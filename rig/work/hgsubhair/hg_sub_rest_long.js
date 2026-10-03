const pp=require('/workspace/jt/node_modules/puppeteer-core');const PORT=process.env.PORT||8795;
(async()=>{const b=await pp.launch({executablePath:'/usr/bin/google-chrome',headless:'new',protocolTimeout:1800000,args:['--no-sandbox','--disable-dev-shm-usage']});const out={};
for(const v of ['apose','tpose','left','right','back']){const p=await b.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));
 await p.goto(`http://127.0.0.1:${PORT}/rig/index.html?view=${v}&quality=linear&headgroup=1`,{waitUntil:'domcontentloaded',timeout:900000});
 await p.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:900000});await new Promise(r=>setTimeout(r,1500));
 out[v]=await p.evaluate(async vw=>{pauseManual();for(const k in P)set(k,P[k][2]);
  const B=document.createElement('canvas');B.width=W;B.height=H;const gb=B.getContext('2d');gb.drawImage(R.im.base,0,0);const bd=gb.getImageData(0,0,W,H).data;
  const grab=rest=>{const c=document.createElement('canvas');c.width=W;c.height=H;const g=c.getContext('2d');g.__S=1;render(g,rest);return g.getImageData(0,0,W,H).data};
  const n=(a,c)=>{let k=0;for(let i=0;i<a.length;i+=4){if(a[i+3]===0&&c[i+3]===0)continue;if(a[i]!==c[i]||a[i+1]!==c[i+1]||a[i+2]!==c[i+2]||a[i+3]!==c[i+3])k++}return k};
  RigHeadGroup.reset();document.getElementById('rest').click();draw();const chk=(document.getElementById('status').textContent.match(/(PASS|FAIL)[^\n]*/)||[''])[0];
  const restNoHandoff=n(grab(true),bd);
  // sub alone (group offset 0): rest must stay exact
  await RigHeadGroup.applyHandoff(vw);const sub=JSON.parse(JSON.stringify(RigHeadGroup.get().sub||{}));RigHeadGroup.set({dx:0,dy:0,rot:0,scale:1});
  const restSubOnly=n(grab(true),bd);const posedSubOnly=n(grab(false),(RigHeadGroup.set({sub:{}}),grab(false)));RigHeadGroup.reset();
  return{rigRestCheck:chk,rest_px_headgroup_no_handoff:restNoHandoff,sub,rest_px_with_sub_only:restSubOnly,posed_px_changed_by_sub:posedSubOnly}},v);
 out[v].errs=errs;await p.close()}
console.log(JSON.stringify(out));await b.close()})().catch(e=>{console.error(e);process.exit(1)});
