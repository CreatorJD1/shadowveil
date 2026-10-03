// ?armsub=1 smoke: page errors, rest check, and at each handoff view: posed px changed by the sub, palm pivot vs forearm wristPivot (posed)
const puppeteer=require('/workspace/jt/node_modules/puppeteer-core');
(async()=>{const PORT=process.env.PORT||8794;const b=await puppeteer.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--disable-dev-shm-usage'],headless:'new',protocolTimeout:1800000});const out={};
for(const v of (process.argv[2]||'apose,tpose,left,right,back').split(',')){const pg=await b.newPage();const errs=[];pg.on('pageerror',e=>errs.push(String(e)));
 await pg.goto(`http://127.0.0.1:${PORT}/rig/index.html?view=${v}&armsub=1&quality=linear`,{waitUntil:'domcontentloaded',timeout:1500000});
 await pg.waitForFunction('typeof R!=="undefined"&&R&&!R.loading',{timeout:1500000});await new Promise(r=>setTimeout(r,1500));
 out[v]=await pg.evaluate(async(v)=>{document.getElementById('auto').checked=false;document.getElementById('rest').click();await new Promise(r=>setTimeout(r,300));
  const cmp=(A,B)=>{let n=0;for(let i=0;i<A.length;i+=4){if(A[i]!==B[i]||A[i+1]!==B[i+1]||A[i+2]!==B[i+2]||A[i+3]!==B[i+3])n++}return n};
  const bc=document.createElement('canvas');bc.width=W;bc.height=H;const gb=bc.getContext('2d');gb.drawImage(R.im.base,0,0);const Bs=gb.getImageData(0,0,W,H).data;
  const h=await RigArmSub.applyHandoff(v);const restPx=cmp(restPixels(),Bs);
  // posed frame with all params 0 (POSED=true via draw), sub on vs off
  draw();const on=FR.getContext('2d').getImageData(0,0,W,H).data.slice();const keep=RigArmSub.get().sub;RigArmSub.set({sub:{}});draw();const off=FR.getContext('2d').getImageData(0,0,W,H).data.slice();RigArmSub.set({sub:keep,w:1});draw();
  const sk=R.skin;const res={handoff:h,restPixels_vs_base:restPx,posed_px_changed_by_sub:cmp(on,off),palm:{}};
  if(sk&&typeof BM!=='undefined'){for(const s of ['L','R']){const fb=sk.bones.find(q=>q.id==='forearm_'+s);if(!fb||!fb.wristPivot)continue;const M=BM['forearm_'+s];const wp=[fb.wristPivot.x,fb.wristPivot.y];const tw=[M[0]*wp[0]+M[2]*wp[1]+M[4],M[1]*wp[0]+M[3]*wp[1]+M[5]];
    const hp=R.hands&&R.hands.parts.find(q=>q.id===s+'_palm');res.palm[s]={wrist_posed:tw.map(x=>+x.toFixed(2)),forearm_rot_deg:+(Math.atan2(M[1],M[0])*180/Math.PI).toFixed(2),palm_pivot_rest_dist:hp&&hp.pivotX!=null?+Math.hypot(hp.pivotX-wp[0],hp.pivotY-wp[1]).toFixed(2):null}}}
  RigArmSub.easeTo(0,0);await new Promise(r=>setTimeout(r,50));draw();res.after_ease0_px_vs_off=cmp(FR.getContext('2d').getImageData(0,0,W,H).data,off);
  document.getElementById('check').click();res.restCheck=document.getElementById('status').textContent.split('\n')[0];return res},v);
 out[v].errors=errs;await pg.close()}
console.log(JSON.stringify(out,null,1));await b.close()})().catch(e=>{console.error(e);process.exit(1)});
