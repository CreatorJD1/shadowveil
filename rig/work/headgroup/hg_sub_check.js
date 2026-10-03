// head-group mouth sub-offsets: rest 0 px with handoff+sub applied; posed: sub moves only mouth px; w=0 == reset
const pp=require('/workspace/jt/node_modules/puppeteer-core');const PORT=process.env.PORT||8795;
(async()=>{const b=await pp.launch({executablePath:'/usr/bin/google-chrome',headless:'new',protocolTimeout:1800000,args:['--no-sandbox','--disable-dev-shm-usage']});const out={};
for(const v of ['apose','tpose','left','right','back']){const p=await b.newPage();const errs=[];p.on('pageerror',e=>errs.push(e.message));
 await p.goto(`http://127.0.0.1:${PORT}/rig/index.html?view=${v}&quality=linear&headgroup=1`,{waitUntil:'domcontentloaded',timeout:300000});
 await p.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:300000});await new Promise(r=>setTimeout(r,1500));
 out[v]=await p.evaluate(async vw=>{document.getElementById('auto').checked=false;pauseManual();for(const k in P)set(k,P[k][2]);
  const B=document.createElement('canvas');B.width=W;B.height=H;const gb=B.getContext('2d');gb.drawImage(R.im.base,0,0);const bd=gb.getImageData(0,0,W,H).data;
  const grab=rest=>{const c=document.createElement('canvas');c.width=W;c.height=H;const g=c.getContext('2d');g.__S=1;render(g,rest);return g.getImageData(0,0,W,H).data};
  const diff=(a,c)=>{let n=0,x0=1e9,y0=1e9,x1=-1,y1=-1;for(let i=0;i<a.length;i+=4){if(a[i+3]===0&&c[i+3]===0)continue;if(a[i]!==c[i]||a[i+1]!==c[i+1]||a[i+2]!==c[i+2]||a[i+3]!==c[i+3]){n++;const q=i/4,x=q%W,y=(q-x)/W;x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y)}}return{n,bbox:n?[x0,y0,x1,y1]:null}};
  RigHeadGroup.reset();const P0=grab(false);const h=await RigHeadGroup.applyHandoff(vw);const g1=RigHeadGroup.get();
  const rest=diff(grab(true),bd).n; document.getElementById('rest').click();draw();const st=document.getElementById('status').textContent.split('\n')[0];
  const A=grab(false);const sub=JSON.parse(JSON.stringify(g1.sub||{}));RigHeadGroup.set({sub:{}});const A0=grab(false);RigHeadGroup.set({sub});
  const subDiff=diff(A,A0);const mb=R.mouth&&R.mouth.partsBBox?R.mouth.partsBBox:null;
  // mouth-only: expected union of mouth bbox under group offset +- sub, padded 3
  await RigHeadGroup.easeTo(0,200);const E=grab(false);const wEnd=RigHeadGroup.get().w;const easeVsNone=diff(E,P0).n;RigHeadGroup.reset();
  return{handoff:h,sub,rest_px_with_handoff_and_sub:rest,rigRestCheck:st,sub_changed_px:subDiff.n,sub_changed_bbox:subDiff.bbox,mouth_anchor:R.mouth?R.mouth.anchor:null,w_after_ease:wEnd,eased_to0_vs_no_headgroup_px:easeVsNone}},v);
 out[v].errs=errs;await p.close()}
console.log(JSON.stringify(out,null,1));await b.close()})().catch(e=>{console.error(e);process.exit(1)});
