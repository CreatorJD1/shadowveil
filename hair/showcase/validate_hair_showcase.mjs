// Validates hair_showcase.json against the renderer's own param table (evaluated from rig/index.html, not copied)
// and the key parse/interp logic of rig/previews/idle/harness/render_idle.mjs (__keyAt). Read-only outside this folder.
import fs from 'node:fs';
const ROOT='/workspace/shadowveil';const html=fs.readFileSync(ROOT+'/rig/index.html','utf8');
const grab=re=>{const m=html.match(re);if(!m)throw new Error('not found in index.html: '+re);return m[0]};
const src=[grab(/const P=\{[^\n]*?\};/),grab(/for\(const h of\['L','R'\]\)\{for\(const f of[^\n]*/),grab(/const BODY_PARAMS=\[[^\]]*\];/),grab(/for\(const k of BODY_PARAMS\)P\[k\]=\[-1,1,0\];/),grab(/P\.WristL=\[-1,1,0\];P\.WristR=\[-1,1,0\];/)].join('\n');
const P=new Function(src+';return P')();
const J=JSON.parse(fs.readFileSync(process.argv[2]||ROOT+'/hair/showcase/hair_showcase.json','utf8'));
let bad=[];const res={};
for(const [name,c] of Object.entries(J.clips)){
 for(const f of['fps','duration','loop','interp','keys'])if(!(f in c))bad.push(name+': missing '+f);
 const views=['apose','tpose','left','right','back'];
 for(const view of views){const K=Object.assign({},c.keys,(c.viewKeys||{})[view]||{});
  const unknown=Object.keys(K).filter(k=>!(k in P));if(unknown.length)bad.push(view+': unknown params '+unknown);
  for(const [k,ks] of Object.entries(K)){if(!(k in P))continue;const [lo,hi,def]=P[k];
   for(let i=0;i<ks.length;i++){const [t,v]=ks[i];if(!(Number.isFinite(t)&&Number.isFinite(v)))bad.push(k+' non-finite key '+i);if(v<lo||v>hi)bad.push(k+' out of range '+v+' at '+t);if(i&&t<ks[i-1][0])bad.push(k+' keys not sorted at '+t);if(t<0||t>c.duration+1e-9)bad.push(k+' key outside [0,duration] '+t)}}
  const keyAt=t=>{const o={};for(const k in K){if(!(k in P))continue;const ks=K[k];let tt=t;if(c.loop)tt=((t%c.duration)+c.duration)%c.duration;
    if(tt<=ks[0][0]){o[k]=ks[0][1];continue}if(tt>=ks[ks.length-1][0]){o[k]=ks[ks.length-1][1];continue}
    let i=1;while(ks[i][0]<tt)i++;const [t0,v0]=ks[i-1],[t1,v1]=ks[i];o[k]=t1>t0?v0+(v1-v0)*(tt-t0)/(t1-t0):v1}return o};
  const N=Math.round(c.duration*c.fps);const first=keyAt(0),last=keyAt(N/c.fps);
  const notRest=(o,tag)=>{for(const k in o)if(o[k]!==P[k][2])bad.push(view+' '+tag+' frame not at rest: '+k+'='+o[k])};notRest(first,'first');if(c.endsAtRest===false)res[name+'_lastFrame_'+view]=last.BodyLean;else notRest(last,'last');
  if(view==='apose'){const peak={},samples=[];for(let f=0;f<=N;f++){const o=keyAt(f/c.fps);for(const k in o)peak[k]=Math.max(peak[k]||0,Math.abs(o[k]))}
   for(const t of[0,0.5,1.0,1.8,2.2,2.6,3.4,3.9,4.9,4.95,5.0,5.05,6.55,6.6,6.7,8.2])samples.push([t,+keyAt(t).BodyLean.toFixed(4)]);
   res[name]={frames:N+1,duration:c.duration,fps:c.fps,loop:c.loop,params:Object.keys(K).length,nonzeroPeaks:Object.fromEntries(Object.entries(peak).filter(([k,v])=>v>0)),limits:Object.fromEntries(Object.keys(K).map(k=>[k,P[k]])).BodyLean,BodyLean:samples}}}}
// body rigs: BodyLean must drive a delivered torso in every view; report its degree limit
for(const view of['apose','tpose','left','right','back']){const r=JSON.parse(fs.readFileSync(`${ROOT}/views/${view}/body/rig.json`,'utf8'));const t=r.parts.find(p=>p.id==='torso');const hd=r.parts.find(p=>p.id==='head');
 if(!t||!(r.paramMap||{}).BodyLean==='torso')bad.push(view+': no torso/BodyLean');res['torsoDeg_'+view]=t.maxRotDeg;res['headDriven_'+view]=hd?(hd.param??null):'no head part'}
console.log(JSON.stringify(res,null,1));console.log(bad.length?'FAIL\n'+bad.join('\n'):'PASS: parses, all params exist in rig/index.html P, all keys within range, first frame exact rest in all 5 views; last frame exact rest unless the clip sets endsAtRest:false (reported as <clip>_lastFrame_<view>)');process.exit(bad.length?1:0)
