// apose skin-mesh check of hair attachment + hair_back peeking under body joints (real renderer, headless Chrome)
import { spawn } from 'node:child_process'; import fs from 'node:fs';
const port=9339, prof='/tmp/cdp-skinhair-prof';
const ch=spawn('google-chrome',['--headless=new','--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader',`--remote-debugging-port=${port}`,`--user-data-dir=${prof}`,'--window-size=1400,1000','about:blank'],{stdio:'ignore'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));let ws,id=0;const pend={};const logs=[];
async function connect(){for(let i=0;i<60;i++){try{const l=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();const pg=l.find(x=>x.type==='page');if(pg)return pg.webSocketDebuggerUrl}catch(e){}await sleep(200)}throw new Error('no chrome')}
function send(method,params={}){return new Promise(r=>{const i=++id;pend[i]=r;ws.send(JSON.stringify({id:i,method,params}))})}
async function ev(expr){const r=await send('Runtime.evaluate',{expression:expr,awaitPromise:true,returnByValue:true});if(r.result?.exceptionDetails)return {err:r.result.exceptionDetails.exception?.description||r.result.exceptionDetails.text};return r.result?.result?.value}
const VIEW=process.env.VIEW||'apose';const NECK={apose:363,tpose:355,back:349,left:397,right:395}[VIEW];const HB={apose:[530,20,290,350],tpose:[530,20,300,340],left:[540,20,305,310],right:[515,20,315,310],back:[545,20,275,325]}[VIEW];const out={view:VIEW,neckY:NECK};
try{ws=new WebSocket(await connect());await new Promise(r=>ws.onopen=r);
 ws.onmessage=m=>{const d=JSON.parse(m.data);if(d.id&&pend[d.id]){pend[d.id](d);delete pend[d.id]}
  if(d.method==='Runtime.consoleAPICalled'&&['error','warning'].includes(d.params.type))logs.push(d.params.type+': '+d.params.args.map(a=>a.value??a.description).join(' '));
  if(d.method==='Runtime.exceptionThrown')logs.push('EXC: '+(d.params.exceptionDetails.exception?.description||d.params.exceptionDetails.text))};
 await send('Runtime.enable');await send('Page.enable');
 await send('Page.navigate',{url:'http://127.0.0.1:8765/rig/index.html?view='+VIEW});
 for(let i=0;i<120;i++){await sleep(500);if(await ev("typeof R!=='undefined'&&!!R&&!!R.im")===true)break}
 await sleep(1000);
 out.load=await ev(`({skin:!!R.skin,useSkin:useSkin(),skinSrc:R.skin&&R.skin.src,headBone:R.skin&&R.skin.headBone,status:document.getElementById('status').textContent,warn:R.warn,hairParts:(R.hair||[]).map(p=>p.id),hairLoaded:(R.hair||[]).filter(p=>p.file).map(p=>[p.id,!!R.im['hair:'+p.id]&&!R.im['hair:'+p.id].empty])})`);
 await ev("document.getElementById('check').click()");await sleep(1500);
 out.restCheck=await ev("document.getElementById('status').textContent.split('\\n')[0]");
 out.result=await ev(`(()=>{const cv=document.createElement('canvas');cv.width=W;cv.height=H;const g=guard(cv.getContext('2d'));g.__S=1;
  const all=()=>g.getImageData(0,0,W,H).data;
  const reset=()=>{for(const k in P)v[k]=P[k][2];hairDrive=null};
  const hairKeys=Object.keys(R.im).filter(k=>k.startsWith('hair:'));const saved={};for(const k of hairKeys)saved[k]=R.im[k];
  const EMPTY={empty:true};
  const rend=(rest,drop)=>{for(const k of hairKeys)R.im[k]=drop&&drop(k)?EMPTY:saved[k];renderIssues=new Set();render(g,rest);const d=all();for(const k of hairKeys)R.im[k]=saved[k];return {d,issues:[...renderIssues]}};
  const diffMask=(a,b)=>{const m=new Uint8Array(W*H);for(let i=0,j=0;i<a.length;i+=4,j++){if(Math.abs(a[i]-b[i])+Math.abs(a[i+1]-b[i+1])+Math.abs(a[i+2]-b[i+2])+Math.abs(a[i+3]-b[i+3])>8)m[j]=1}return m};
  const headMof=()=>{const BM=chain(R.skin.bones,bodyAngle,null,p=>p.parent);return BM[R.skin.headBone]||I};
  reset();const F0=rend(true).d,N0=rend(true,k=>k==='hair:hair_back').d;const V0=diffMask(F0,N0);
  const H0=diffMask(F0,rend(true,k=>true).d);
  const inv=M=>{const det=M[0]*M[3]-M[1]*M[2];return[M[3]/det,-M[1]/det,-M[2]/det,M[0]/det,(M[2]*M[5]-M[3]*M[4])/det,(M[1]*M[4]-M[0]*M[5])/det]};
  // dilate rest mask by 2 px after mapping
  const mapped=(mask,M)=>{const Mi=inv(M);const o=new Uint8Array(W*H);for(let y=0;y<H;y++)for(let x=0;x<W;x++){const X=x+.5,Y=y+.5;const sx=Mi[0]*X+Mi[2]*Y+Mi[4],sy=Mi[1]*X+Mi[3]*Y+Mi[5];
     let hit=0;for(let dy=-2;dy<=2&&!hit;dy++)for(let dx=-2;dx<=2&&!hit;dx++){const xi=Math.floor(sx)+dx,yi=Math.floor(sy)+dy;if(xi>=0&&yi>=0&&xi<W&&yi<H&&mask[yi*W+xi])hit=1}o[y*W+x]=hit}return o};
  const poses=[];const J=['ShoulderL','ShoulderR','ElbowL','ElbowR','HipL','HipR','KneeL','KneeR','AnkleL','AnkleR','ToeL','ToeR','WristL','WristR','BodyLean'];
  for(const k of J)for(const s of [-1,1])poses.push({[k]:s});
  for(const a of [-1,1])for(const b of [-1,1])for(const c of [-1,1])poses.push({BodyLean:a,ShoulderL:b,ShoulderR:c,ElbowL:b,ElbowR:c});
  for(const a of [-1,1])for(const hx of [-1,1])for(const hy of [-1,1])poses.push({BodyLean:a,ShoulderL:a,ShoulderR:-a,HairSwayX:hx,HairSwayY:hy});
  const res=[];let restIdentity=null;
  for(const p of poses){reset();Object.assign(v,p);const M=headMof();
    const F=rend(false),N=rend(false,k=>k==='hair:hair_back'),NA=rend(false,k=>true);
    const V=diffMask(F.d,N.d);const Hm=diffMask(F.d,NA.d);
    const Vr=mapped(V0,M);
    const Mi=inv(M);const neckList=[];let peek=0,peekNeck=0,bb=[1e9,1e9,-1,-1];for(let j=0;j<V.length;j++)if(V[j]&&!Vr[j]){peek++;const x=j%W,y=(j/W)|0;const sy=Mi[1]*(x+.5)+Mi[3]*(y+.5)+Mi[5];if(sy>=${NECK}){peekNeck++;if(neckList.length<40)neckList.push([x,y,F.d[j*4],F.d[j*4+1],F.d[j*4+2],F.d[j*4+3]])}bb=[Math.min(bb[0],x),Math.min(bb[1],y),Math.max(bb[2],x),Math.max(bb[3],y)]}
    // attachment: hair mask should equal the rest hair mask carried by the head matrix (only for poses without hair sway)
    let att=null;if(!('HairSwayX' in p)){const Hr=mapped(H0,M);const Hr0=H0;let miss=0,n=0;for(let j=0;j<Hm.length;j++){if(Hm[j]){n++;if(!Hr[j])miss++}}att={hairPx:n,outsideRestHairMappedByHead2px:miss}}
    // alpha holes in final composite vs rest silhouette inside the head/neck box
    res.push({pose:p,headAngleDeg:+(Math.atan2(M[1],M[0])*180/Math.PI).toFixed(3),headT:[+M[4].toFixed(2),+M[5].toFixed(2)],hairBackVisiblePx:V.reduce((a,b)=>a+b,0),hairBackPeekPx:peek,peekBelowNeckBoundary:peekNeck,neckPeekPx:neckList,peekBBox:peek?bb:null,attach:att,issues:F.issues})}
  reset();render(g,true);
  return {restHairBackVisiblePx:V0.reduce((a,b)=>a+b,0),restHairPx:H0.reduce((a,b)=>a+b,0),poses:res}})()`);
 // pixel compare: head region at BodyLean=+1 vs rest rendered then carried by headM (checks offset)
 out.offset=await ev(`(()=>{const cv=document.createElement('canvas');cv.width=W;cv.height=H;const g=guard(cv.getContext('2d'));g.__S=1;
  for(const k in P)v[k]=P[k][2];render(g,true);const rest=document.createElement('canvas');rest.width=W;rest.height=H;rest.getContext('2d').drawImage(cv,0,0);
  const r=[];for(const s of [-1,1]){v.BodyLean=s;const BM=chain(R.skin.bones,bodyAngle,null,p=>p.parent);const M=BM[R.skin.headBone];render(g,false);const A=g.getImageData(${HB[0]},${HB[1]},${HB[2]},${HB[3]}).data;
   const c2=document.createElement('canvas');c2.width=W;c2.height=H;const q=c2.getContext('2d');q.imageSmoothingEnabled=true;q.imageSmoothingQuality='high';q.setTransform(M[0],M[1],M[2],M[3],M[4],M[5]);q.drawImage(rest,0,0);const B=q.getImageData(${HB[0]},${HB[1]},${HB[2]},${HB[3]}).data;
   let best=null;for(let oy=-2;oy<=2;oy++)for(let ox=-2;ox<=2;ox++){let s2=0,n=0;for(let y=3;y<${HB[3]-3};y++)for(let x=3;x<${HB[2]-3};x++){const i=(y*${HB[2]}+x)*4,j=((y+oy)*${HB[2]}+x+ox)*4;if(A[i+3]<250||B[j+3]<250)continue;s2+=Math.abs(A[i]-B[j])+Math.abs(A[i+1]-B[j+1])+Math.abs(A[i+2]-B[j+2]);n++}const e=s2/n/3;if(!best||e<best.err)best={ox,oy,err:+e.toFixed(3)}}
   r.push({BodyLean:s,headAngleDeg:+(Math.atan2(M[1],M[0])*180/Math.PI).toFixed(3),bestShift:best})}
  for(const k in P)v[k]=P[k][2];return r})()`);
 const shot=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync('/workspace/shadowveil/hair/qa/cdp/skin_'+VIEW+'.png',Buffer.from(shot.result.data,'base64'));
 out.consoleErrors=[...logs];
}catch(e){out.error=String(e)}
finally{fs.writeFileSync(process.env.OUT||'/tmp/skin_hair.json',JSON.stringify(out,null,1));ch.kill('SIGKILL');process.exit(0)}
