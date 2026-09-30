# v1.9 wrist + twist patch: WristRot (existing WristL/R, stress-unclamped), WristTwist (authored hand-angle switching),
# forearm->hand blend band (leak fix), twist axes for every joint (width scale + sub-part offset in the skin mesh), hair preset A default.
import sys
src,dst=sys.argv[1],sys.argv[2]
s=open(src).read()
def rep(a,b,cnt=1):
    global s
    n=s.count(a)
    assert n==cnt,(n,a[:80])
    s=s.replace(a,b)
# ---- params
rep("P.WristL=[-1,1,0];P.WristR=[-1,1,0]; // v1.4: hand rotation about the forearm wristPivot",
"P.WristL=[-1,1,0];P.WristR=[-1,1,0]; // v1.4: hand rotation about the forearm wristPivot\n"
"P.WristTwistL=[-1,1,0];P.WristTwistR=[-1,1,0]; // v1.9 palm turn: +-1 = +-180 deg pronation(+)/supination(-); switches between authored hand angles\n"
"const TWIST_J={Shoulder:{bone:'upperArm',deg:60,asp:0.9,prof:'bump'},Elbow:{bone:'forearm',deg:80,asp:0.85,prof:'ramp'},Hip:{bone:'thigh',deg:40,asp:0.9,prof:'bump'},Knee:{bone:'shin',deg:15,asp:0.9,prof:'bump'},Ankle:{bone:'foot',deg:20,asp:0.9,prof:'bump'}};\n"
"const TWIST_NECK={deg:60,asp:0.9,r:40};const TWIST_OFF=0.08,TWIST_OFF_MAX=3;\n"
"const TWIST_PARAMS=[];for(const j in TWIST_J)for(const sd of['L','R']){P['Twist'+j+sd]=[-1,1,0];TWIST_PARAMS.push('Twist'+j+sd)}P.TwistNeck=[-1,1,0];TWIST_PARAMS.push('TwistNeck');\n"
"const WRIST_BAND=[-16,4],WRIST_BLEND=14,WT_SQUASH=0.15,WT_XF=0.1,WT_FOLLOW=0.5,WT_FULL=180;")
rep("groups['Body joints']=BODY_PARAMS;","groups['Body joints']=BODY_PARAMS;groups['Twist (v1.9)']=TWIST_PARAMS;")
rep(".map(f=>'Hand'+h+f).concat(['Wrist'+h]);",".map(f=>'Hand'+h+f).concat(['Wrist'+h,'WristTwist'+h]);")
# ---- hair preset A default
rep('<option value="default">default 1.1 Hz / ζ 0.3</option><option value="A">A 4.0 Hz / ζ 0.8</option>','<option value="A" selected>A 4.0 Hz / ζ 0.8 (default)</option><option value="default">old default 1.1 Hz / ζ 0.3</option>')
rep("let HAIR_PRESET='default';","let HAIR_PRESET='A';")
rep("const HP=HAIR_PRESETS[HAIR_PRESET]||HAIR_PRESETS.default;","const HP=HAIR_PRESETS[HAIR_PRESET]||HAIR_PRESETS.A;")
# ---- palmExt: stress unclamps; add hand root with twist squash
rep("const mx=+(p.maxWristDeg??(R.hands&&R.hands.wristMaxDeg)??25);const x=clamp(v[k],-1,1);",
    "const mx=+(p.maxWristDeg??(R.hands&&R.hands.wristMaxDeg)??25);const x=STRESS?(+v[k]||0):clamp(v[k],-1,1);")
rep("// posed frames may be rendered at 2x and downsampled",
r"""// v1.9 wrist twist: authored hand angles (native + donor views of the same hand, never mirrored), aligned at the wrist pivot
// by the forearm axis (rotation only, authored size), crossfaded around each midpoint with <=15% width squash toward it.
const WT_DONORS={apose:{L:[['left',90],['back',180]],R:[['right',90],['back',180]]},tpose:{L:[['apose',-90],['back',90]],R:[['apose',-90],['back',90]]},
 left:{L:[['apose',-90],['back',90]]},right:{R:[['apose',-90],['back',90]]},back:{L:[['left',-90],['apose',-180]],R:[['right',-90],['apose',-180]]}};
function faAxis(bj,H){const bs=bj&&(bj.bones||partsOf(bj));if(!bs)return null;const f=bs.find(b=>(b.name||b.id)==='forearm_'+H);if(!f)return null;const wp=pt(f.wristPivot);const pv=f.pivot||[f.pivotX,f.pivotY];if(!wp||!pv)return null;return{wp,a:Math.atan2(wp[1]-pv[1],wp[0]-pv[0])}}
async function loadHandAngles(r,vw,hands){const out={};const D=WT_DONORS[vw]||{};const bT=r.skin?{bones:r.skin.bones.map(b=>({name:b.id,pivot:[b.pivotX,b.pivotY],wristPivot:b.wristPivot}))}:(r.body?{parts:r.body.parts}:null);
 for(const H of['L','R']){const palm=hands&&hands.parts.find(p=>p.id===H+'_palm'&&p.file&&!p.hidden);if(!palm)continue;const tA=faAxis(bT,H);if(!tA)continue;const E=[{deg:0,native:true,src:vw}];
  for(const [dv,deg] of (D[H]||[])){const b='../views/'+dv+'/';const hj=await json(b+'hands/rig.json');const bj=await json(b+'body/skin.json')||await json(b+'body/rig.json');const ps=partsOf(hj);if(!ps)continue;
   const dp=ps.find(p=>p.id===H+'_palm'&&p.file&&!p.hidden);const dA=faAxis(bj,H);if(!dp||!dA)continue;const parts=[];
   for(const p of byLayer(ps.filter(p=>p.file&&!p.hidden&&p.id.startsWith(H+'_')))){const i=await img(b+'hands/'+p.file);if(i)parts.push({id:p.id,im:trim(i)})}
   let mask=null;if(dv==='left'||dv==='right'){const mi=await img('twist_masks/'+dv+'_'+H+'.png');if(mi)mask=trim(mi)}
   const th=tA.a-dA.a;const A=mul(T(tA.wp[0],tA.wp[1]),mul([Math.cos(th),Math.sin(th),-Math.sin(th),Math.cos(th),0,0],T(-dA.wp[0],-dA.wp[1])));
   E.push({deg,src:dv,parts,mask,A,rotDeg:+(th*180/Math.PI).toFixed(1)})}
  E.sort((a,b)=>a.deg-b.deg);out[H]={E,axis:tA.a,wp:tA.wp,min:E[0].deg,max:E[E.length-1].deg}}return out}
// which authored angles show for WristTwist<H>: [{e,alpha,squash}], native always underneath (alpha 1), donors on top
function twistState(H,rest){const S=R&&R.handAngles&&R.handAngles[H];if(rest||!S)return null;const x=clamp(+v['WristTwist'+H]||0,-1,1);if(!x)return null;
 const want=x*WT_FULL,tau=clamp(want,S.min,S.max);const E=S.E;let i=0;while(i<E.length-2&&tau>E[i+1].deg)i++;const a=E[i],b=E[Math.min(i+1,E.length-1)];
 const f=b.deg>a.deg?clamp((tau-a.deg)/(b.deg-a.deg),0,1):0;const sq=u=>1-WT_SQUASH*Math.min(1,u/0.5);let L;
 if(f<=0.5-WT_XF)L=[{e:a,alpha:1,s:sq(f)}];else if(f>=0.5+WT_XF)L=[{e:b,alpha:1,s:sq(1-f)}];else{const t=(f-(0.5-WT_XF))/(2*WT_XF);L=a.native?[{e:a,alpha:1,s:sq(f)},{e:b,alpha:t,s:sq(1-f)}]:b.native?[{e:b,alpha:1,s:sq(1-f)},{e:a,alpha:1-t,s:sq(f)}]:[{e:a,alpha:1,s:sq(f)},{e:b,alpha:t,s:sq(1-f)}]}
 return{L,tau,want,clamped:Math.abs(tau-want)>1e-6,S}}
// width squash about the hand axis through the wrist pivot (perpendicular scale s)
function squashM(S,s){if(!S||s===1)return I;const c=Math.cos(S.axis),n=Math.sin(S.axis);const Rm=[c,n,-n,c,0,0],Ri=[c,-n,n,c,0,0];return mul(T(S.wp[0],S.wp[1]),mul(Rm,mul([1,0,0,s,0,0],mul(Ri,T(-S.wp[0],-S.wp[1])))))}
function twistDegOf(H){const S=twistState(H,false);return S?S.tau:0}
// posed frames may be rendered at 2x and downsampled""")
# ---- skin setup hooks: wrist band + twist fields
rep("r.neck=neckSetup(r);r.feet=footSetup(r);","r.neck=neckSetup(r);r.wrist=wristSetup(r);r.twist=twistSetup(r);r.handAngles=await loadHandAngles(r,view,hands);r.feet=footSetup(r);")
rep("function rootApply(BM,rest){",
r"""// v1.9 wrist band (leak fix): renderer-side weights. Forearm-dominant verts from WRIST_BAND[0] to [1] px along the forearm axis
// past the wristPivot blend (smoothstep) to a virtual bone __hand_<H> that follows the palm root, so the flat stub under the palm
// turns with the hand and the visible wrist bends smoothly. skin.json is untouched; at rest __hand = forearm = identity.
function wristSetup(r){const Sk=r.skin;if(!Sk)return null;const out={};
 for(const H of['L','R']){const fi=Sk.bones.findIndex(b=>b.id==='forearm_'+H);if(fi<0)continue;const fb=Sk.bones[fi];const wp=pt(fb.wristPivot);if(!wp)continue;
  const L=Math.hypot(wp[0]-fb.pivotX,wp[1]-fb.pivotY)||1;const ax=(wp[0]-fb.pivotX)/L,ay=(wp[1]-fb.pivotY)/L;
  let hm=null;if(r.hands){const c=document.createElement('canvas');c.width=W;c.height=fb?Math.round(Sk.img.naturalHeight||Sk.img.height):0;const q=guard(c.getContext('2d'));let any=false;for(const p of r.hands.parts)if(p.file&&!p.hidden&&p.id[0]===H){const im=r.im['hands:'+p.id];if(im&&!im.empty){q.drawImage(im,im.ox||0,im.oy||0);any=true}}
   if(any){const dd=q.getImageData(0,0,c.width,c.height).data;hm=new Uint8Array(c.width*c.height);for(let k=0;k<hm.length;k++)hm[k]=dd[k*4+3]>0?1:0}}
  const hi=Sk.bones.length;Sk.bones.push({id:'__hand_'+H,parent:'forearm_'+H,pivotX:wp[0],pivotY:wp[1],param:null,virtual:true});
  const gate=M=>{let n=0;for(let i=0;i<M.nv;i++){let k0=-1,wf=0;for(let k=0;k<4;k++)if(M.wb[i*4+k]===fi&&M.ww[i*4+k]>wf){wf=M.ww[i*4+k];k0=k}if(k0<0)continue;
   const x=M.V[2*i],y=M.V[2*i+1];const d=(x-wp[0])*ax+(y-wp[1])*ay;if(d<=-48)continue;let sw=d>=WRIST_BAND[1]?1:0;
   if(sw<1&&hm){const xi=Math.round(x),yi=Math.round(y);if(hm[yi*W+xi])sw=1;else{let md=1e9;for(let b=-WRIST_BLEND;b<=WRIST_BLEND;b++)for(let a=-WRIST_BLEND;a<=WRIST_BLEND;a++){const X=xi+a,Y=yi+b;if(X<0||Y<0||X>=W||Y>=hm.length/W)continue;if(hm[Y*W+X]){const e=a*a+b*b;if(e<md)md=e}}
    md=Math.sqrt(md);if(md<WRIST_BLEND){const u=1-md/WRIST_BLEND;sw=Math.max(sw,u*u*(3-2*u))}}}
   if(!hm&&d>WRIST_BAND[0]){const u=clamp((d-WRIST_BAND[0])/(WRIST_BAND[1]-WRIST_BAND[0]),0,1);sw=Math.max(sw,u*u*(3-2*u))}if(sw<=0)continue;
   let kf=-1;for(let k=0;k<4;k++)if(!M.ww[i*4+k]&&k!==k0){kf=k;break}if(kf<0){let mn=9;for(let k=0;k<4;k++)if(k!==k0&&M.ww[i*4+k]<mn){mn=M.ww[i*4+k];kf=k}M.ww[i*4+k0]+=M.ww[i*4+kf]}
   const wt=M.ww[i*4+k0];M.ww[i*4+k0]=Math.fround(wt*(1-sw));M.wb[i*4+kf]=hi;M.ww[i*4+kf]=Math.fround(wt*sw);n++}return n};
  const n=gate(Sk);let nu=0;const U=Sk.underlay;if(U&&U.wb&&U.wb!==Sk.wb&&U.V)nu=gate(U);out[H]={bone:'__hand_'+H,wp,axis:[ax,ay],verts:n,underlayVerts:nu,band:hm?'palm mask + '+WRIST_BLEND+' px blend':WRIST_BAND}}return out}
// v1.9 twist axes: every limb bone gets Twist<Joint><S> (and TwistNeck): the bone's cross-section width scales by
// sqrt(cos^2 + asp^2 sin^2) of the twist angle and shifts sideways (sub-part offset <= 3 px) in the rest mesh before skinning,
// weighted along the bone (bump = 0 at both joints, ramp = 0 at the elbow to 1 at the wrist), so the skin follows and seams stay put.
function twistSetup(r){const Sk=r.skin;if(!Sk)return null;const E=[];const byId={};Sk.bones.forEach((b,i)=>byId[b.id]=i);
 const dom=(M,i)=>{let b=-1,w=-1;for(let k=0;k<4;k++)if(M.ww[i*4+k]>w){w=M.ww[i*4+k];b=M.wb[i*4+k]}return b};
 for(const j in TWIST_J)for(const sd of['L','R']){const id=TWIST_J[j].bone+'_'+sd;const bi=byId[id];if(bi==null)continue;const b=Sk.bones[bi];let d=pt(b.wristPivot);
  if(!d){const ch=Sk.bones.find(c=>c.parent===id&&!c.virtual&&Math.hypot(c.pivotX-b.pivotX,c.pivotY-b.pivotY)>20);if(ch)d=[ch.pivotX,ch.pivotY]}
  if(!d){let far=0;for(let i=0;i<Sk.nv;i++)if(dom(Sk,i)===bi){const e=Math.hypot(Sk.V[2*i]-b.pivotX,Sk.V[2*i+1]-b.pivotY);if(e>far){far=e;d=[Sk.V[2*i],Sk.V[2*i+1]]}}}
  if(!d)continue;const L=Math.hypot(d[0]-b.pivotX,d[1]-b.pivotY)||1;const ax=(d[0]-b.pivotX)/L,ay=(d[1]-b.pivotY)/L;const e={param:'Twist'+j+sd,j,sd,bi,a:[b.pivotX,b.pivotY],ax,ay,nx:-ay,ny:ax,L,deg:TWIST_J[j].deg,asp:TWIST_J[j].asp,prof:TWIST_J[j].prof};
  const ns=[];for(let i=0;i<Sk.nv;i++)if(dom(Sk,i)===bi){const u=((Sk.V[2*i]-e.a[0])*ax+(Sk.V[2*i+1]-e.a[1])*ay)/L;if(u>0.2&&u<0.8)ns.push((Sk.V[2*i]-e.a[0])*e.nx+(Sk.V[2*i+1]-e.a[1])*e.ny)}
  if(ns.length<4)continue;ns.sort((a,b)=>a-b);e.c0=ns[ns.length>>1];e.hw=(ns[Math.floor(ns.length*0.95)]-ns[Math.floor(ns.length*0.05)])/2;E.push(e)}
 const N=r.neck;if(N&&Sk.bones[byId[Sk.headBone]])E.push({param:'TwistNeck',j:'Neck',neck:true,a:[N.x,N.y],ax:0,ay:-1,nx:1,ny:0,deg:TWIST_NECK.deg,asp:TWIST_NECK.asp,c0:0,hw:TWIST_NECK.r*0.6,bi:byId[Sk.headBone],ti:byId[Sk.bones[byId[Sk.headBone]].parent]});
 const field=M=>{const tw=new Int16Array(M.nv).fill(-1),tn=new Float32Array(M.nv),tw8=new Float32Array(M.nv);
  for(let i=0;i<M.nv;i++){const b=dom(M,i),x=M.V[2*i],y=M.V[2*i+1];for(let q=0;q<E.length;q++){const e=E[q];let w=0;
    if(e.neck){if(b!==e.bi&&b!==e.ti)continue;const dd=Math.hypot(x-e.a[0],y-e.a[1]);if(dd>=TWIST_NECK.r)continue;const u=1-dd/TWIST_NECK.r;w=u*u*(3-2*u)}
    else{if(b!==e.bi)continue;const u=((x-e.a[0])*e.ax+(y-e.a[1])*e.ay)/e.L;w=e.prof==='ramp'?(u<=0?0:u>=1?1:u*u*(3-2*u)):(u<=0||u>=1?0:Math.sin(Math.PI*u))}
    if(w>0){tw[i]=q;tw8[i]=w;tn[i]=(x-e.a[0])*e.nx+(y-e.a[1])*e.ny-e.c0;break}}}
  return{tw,tn,tw8}};
 Sk.twf=field(Sk);if(Sk.underlay&&Sk.underlay.V&&Sk.underlay.ok!==false)Sk.underlay.twf=field(Sk.underlay);
 return{entries:E.map(e=>({param:e.param,deg:e.deg,asp:e.asp,prof:e.prof,halfWidthPx:+e.hw.toFixed(1),offMaxPx:+Math.min(TWIST_OFF_MAX,TWIST_OFF*e.hw).toFixed(2)})),E}}
// per-render twist amounts: {q: [s, off]} (null at rest or when all twist is 0)
let TWS=null;
function twistAmounts(rest){const TW=R&&R.twist;if(rest||!TW)return null;const o={};let any=false;
 TW.E.forEach((e,q)=>{let deg=clamp(+v[e.param]||0,-1,1)*e.deg;if(e.j==='Elbow')deg=clamp(deg+WT_FOLLOW*twistDegOf(e.sd),-e.deg,e.deg);if(!deg)return;const th=deg*Math.PI/180;
  o[q]=[Math.sqrt(Math.cos(th)**2+(e.asp*Math.sin(th))**2),Math.min(TWIST_OFF_MAX,TWIST_OFF*e.hw)*Math.sin(th),deg];any=true});return any?o:null}
function rootApply(BM,rest){""")
# meshDeform: twist pre-deform of the rest position
rep("function meshDeform(Mh,BM,bones){const n=Mh.nv,V=Mh.V,D=Mh.def,wb=Mh.wb,ww=Mh.ww;const Ms=bones.map(b=>BM[b.id]||I);\n for(let i=0;i<n;i++){const x=V[2*i],y=V[2*i+1];",
    "function meshDeform(Mh,BM,bones){const n=Mh.nv,V=Mh.V,D=Mh.def,wb=Mh.wb,ww=Mh.ww;const Ms=bones.map(b=>BM[b.id]||I);const TF=TWS&&Mh.twf,TE=TF&&R.twist.E;\n for(let i=0;i<n;i++){let x=V[2*i],y=V[2*i+1];if(TF){const q=TF.tw[i];if(q>=0&&TWS[q]){const e=TE[q],w=TF.tw8[i],sh=w*(TF.tn[i]*(TWS[q][0]-1)+TWS[q][1]);x+=sh*e.nx;y+=sh*e.ny}}")
# render: twist amounts, __hand bones, hand root with squash, donor drawing
rep("function render(g,rest){POSED=!rest;","function render(g,rest){POSED=!rest;TWS=twistAmounts(rest);const TWH={L:twistState('L',rest),R:twistState('R',rest)};")
rep("const Sk=R.skin;BM=headApply(rootApply(chain(Sk.bones,rest?()=>0:bodyAngle,null,p=>p.parent),rest),rest,Sk.headBone);",
    "const Sk=R.skin;BM=headApply(rootApply(chain(Sk.bones,rest?()=>0:bodyAngle,null,p=>p.parent),rest),rest,Sk.headBone);if(R.wrist&&R.hands)for(const H in R.wrist){const pm=R.hands.parts.find(p=>p.id===H+'_palm'&&p.file);if(pm)BM['__hand_'+H]=handRoot(pm,BM,rest,TWH)}")
rep("if(R.hands){const M=handChain(R.hands.parts,rest?()=>0:handAngle(R.hands),p=>palmExt(p,BM,rest),rest);\n  for(const p of R.hands.parts)if(p.file){",
    "if(R.hands){const M=handChain(R.hands.parts,rest?()=>0:handAngle(R.hands),p=>handRoot(p,BM,rest,TWH),rest);\n  for(const H of['L','R']){const st=TWH[H];if(!st)continue;const pm=R.hands.parts.find(p=>p.id===H+'_palm'&&p.file);if(!pm)continue;const root0=palmExt(pm,BM,rest);\n   for(const it of st.L){if(it.e.native)continue;const Mr=mul(root0,squashM(st.S,it.s));const e=it.e,al=it.alpha;add(R.z['hands:'+pm.id],STEP.hands,g=>drawDonor(g,e,Mr,al),{id:'hands:'+H+':twist:'+e.src,gid:'hands:'+H,glabel:(H==='L'?'left':'right')+' hand ('+H+')',sys:'hands',label:'authored angle '+e.src+' ('+e.deg+'°)',info:'WristTwist '+st.tau.toFixed(0)+'° · alpha '+al.toFixed(2)+' · squash '+it.s.toFixed(2)+(st.clamped?' · CLAMPED (no art past '+st.S.min+'..'+st.S.max+'°)':'')})}}\n  for(const p of R.hands.parts)if(p.file){if(TWH[p.id[0]]&&!TWH[p.id[0]].L.some(q=>q.e.native))continue;")
rep("// v1.4 wrist: palm root = forearm world transform",
r"""// v1.9 hand root: palmExt x twist width squash of the native art (when the native angle is showing)
function handRoot(p,BM,rest,TWH){const r0=palmExt(p,BM,rest);const st=TWH&&TWH[p.id[0]];if(!st)return r0;const nat=st.L.find(q=>q.e.native);const it=nat||st.L[st.L.length-1];return mul(r0,squashM(st.S,it.s))}
// donor hand angle (profile donors are clipped by rig/twist_masks/<view>_<H>.png, which removes the thigh-skin rim cut outside her outline): its parts (f0, donor layer order) into one offscreen group, drawn with one alpha (no see-through between its parts)
let DONORC=null;function drawDonor(g,e,Mr,al){const S=g.__S||1;const cw=g.canvas.width,ch=g.canvas.height;if(!DONORC)DONORC=document.createElement('canvas');if(DONORC.width!==cw||DONORC.height!==ch){DONORC.width=cw;DONORC.height=ch}
 const q=guard(DONORC.getContext('2d'));q.setTransform(1,0,0,1,0,0);q.globalAlpha=1;q.globalCompositeOperation='source-over';q.clearRect(0,0,cw,ch);q.__S=S;const M=mul(Mr,e.A);const d0=DIM;DIM=1;try{for(const p of e.parts)drawM(q,p.im,M);if(e.mask){q.globalCompositeOperation='destination-in';drawM(q,e.mask,M);q.globalCompositeOperation='source-over'}}finally{DIM=d0}
 g.save();g.setTransform(1,0,0,1,0,0);g.globalAlpha=al*DIM;g.imageSmoothingEnabled=false;g.drawImage(DONORC,0,0);g.restore()}
// v1.4 wrist: palm root = forearm world transform""")
open(dst,'w').write(s)
print('ok',len(s))
# ---- v1.9 manual rotation control (queued item): arrows + dial between authored views, never mirrored
s=open(dst).read()
a='<option>back</option></select>\n'
assert s.count(a)==1
s=s.replace(a,'<option>back</option></select>\n<span title="v1.9 rotation: steps between the authored views (front 0°, left 90°, back 180°, right 270°); never mirrors"><button id="rotL">◀</button><input id="rotdial" type="range" min="0" max="359" step="1" value="0" style="width:90px;vertical-align:middle"><button id="rotR">▶</button> <span id="rotlbl"></span></span>\n')
b="const qv=new URLSearchParams(location.search).get('view');if(qv)document.getElementById('view').value=qv;load();"
assert s.count(b)==1
s=s.replace(b,r"""// v1.9 manual rotation: arrows/dial snap to the nearest AUTHORED view by camera yaw (front = apose or tpose, whichever was last shown); no mirroring
const ROT_VIEWS=[['front',0],['left',90],['back',180],['right',270]];let ROT_FRONT='apose';
function rotYaw(vw){return vw==='left'?90:vw==='back'?180:vw==='right'?270:0}
function rotSync(){const vw=document.getElementById('view').value;if(vw==='apose'||vw==='tpose')ROT_FRONT=vw;const y=rotYaw(vw);document.getElementById('rotdial').value=y;document.getElementById('rotlbl').textContent=y+'° '+vw}
function rotTo(yaw){yaw=((yaw%360)+360)%360;let best=ROT_VIEWS[0],bd=1e9;for(const r of ROT_VIEWS){const d=Math.min(Math.abs(yaw-r[1]),360-Math.abs(yaw-r[1]));if(d<bd){bd=d;best=r}}const vw=best[0]==='front'?ROT_FRONT:best[0];const e=document.getElementById('view');if(e.value!==vw){e.value=vw;e.onchange()}rotSync()}
document.getElementById('rotL').onclick=()=>rotTo(rotYaw(document.getElementById('view').value)-90);document.getElementById('rotR').onclick=()=>rotTo(rotYaw(document.getElementById('view').value)+90);
document.getElementById('rotdial').onchange=e=>rotTo(+e.target.value);document.getElementById('view').addEventListener('change',rotSync);
"""+b+"rotSync();")
s=s.replace('<b>Shadowveil rig preview</b> (contract v1.8)','<b>Shadowveil rig preview</b> (contract v1.9)')
open(dst,'w').write(s);print('rot ok')
# ---- v1.9 split finger curl (queued item): Hand<H>Claw bends the middle and tip joints (segments 2, 3) by claw x their maxCurlDeg on top of
# the finger curl, base joint unchanged. Only where segment 2/3 frames carry art (in-plane curl, i.e. tpose); in views whose curled shape lives
# in segment 1's frame (apose/left/right/back frames v3: segment 2/3 f1/f2 are empty) the claw is clamped to 0 and reported (Hands gap).
s=open(dst).read()
a="P.WristTwistL=[-1,1,0];P.WristTwistR=[-1,1,0];"
assert s.count(a)==1
s=s.replace(a,a+"P.HandLClaw=[0,1,0];P.HandRClaw=[0,1,0];")
a=".map(f=>'Hand'+h+f).concat(['Wrist'+h,'WristTwist'+h]);"
assert s.count(a)==1
s=s.replace(a,".map(f=>'Hand'+h+f).concat(['Hand'+h+'Claw','Wrist'+h,'WristTwist'+h]);")
a="function handAngle(j){const sp=j.spread||{};return p=>{const m=p.id.match(/^([LR])_(Thumb|Index|Middle|Ring|Pinky)(\\d)$/);if(!m)return 0;const[_,h,f,n]=m;let a=(v['Hand'+h+f]||0)*(p.maxCurlDeg||0);"
assert s.count(a)==1,'handAngle'
s=s.replace(a,a+"if((n==='2'||n==='3')&&f!=='Thumb'&&R.claw&&R.claw[h])a+=clamp(+v['Hand'+h+'Claw']||0,0,1)*(p.maxCurlDeg||0);")
a="r.handAngles=await loadHandAngles(r,view,hands);"
assert s.count(a)==1
s=s.replace(a,a+"r.claw={};for(const h of['L','R']){const segs=hands?hands.parts.filter(p=>new RegExp('^'+h+'_(Index|Middle|Ring|Pinky)[23]$').test(p.id)&&p.file&&!p.hidden):[];r.claw[h]=segs.length>0&&segs.every(p=>{const fr=r.frames[p.id];return fr&&fr.length>1&&fr.slice(1).every(f=>!trim(f.img).empty)})}")
open(dst,'w').write(s);print('claw ok')
