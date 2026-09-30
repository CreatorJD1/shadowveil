# builds the v1.8 working copy from the backed-up live rig; every replacement must match exactly once
import sys
src,dst=sys.argv[1],sys.argv[2]
s=open(src).read()
def R(old,new,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'patch anchor found {n}x (want {count}): {old[:90]!r}')
    s=s.replace(old,new)
# ---- title / version
R('<title>Shadowveil rig preview (contract v1.6.1)</title>','<title>Shadowveil rig preview (contract v1.8)</title>')
R('<b>Shadowveil rig preview</b> (contract v1.6.1)<br>','<b>Shadowveil rig preview</b> (contract v1.8)<br>')
# ---- UI: auto style, hair preset, foot plant, mouth crossfade
R('<label><span>Auto (blink, gaze, talk, sway, idle)</span><input type="checkbox" id="auto"></label>',
 '<label><span>Auto (blink, gaze, sway, idle)</span><input type="checkbox" id="auto"></label>\n'
 '<label><span>Auto style (v1.8)</span><select id="autostyle"><option value="idle">idle (rest mouth + soft smile, gaze drift)</option><option value="talk">talk (phrases, glances)</option></select></label>\n'
 '<label><span>Foot plant (v1.8)</span><select id="footplant"><option value="xy">on: foot line + planted foot x</option><option value="y">on: foot line only</option><option value="off">off</option></select></label>\n'
 '<label><span>Hair spring (v1.8)</span><select id="hairpreset"><option value="default">default 1.1 Hz / ζ 0.3</option><option value="A">A 4.0 Hz / ζ 0.8</option><option value="B">B 2.0 Hz / ζ 0.6</option></select></label>\n'
 '<label><span>Mouth switch (v1.8)</span><select id="mouthfade"><option value="35">35 ms crossfade</option><option value="0">hard cut</option></select></label>')
# ---- params RootX / RootY (px), own UI group
R("P.WristL=[-1,1,0];P.WristR=[-1,1,0]; // v1.4: hand rotation about the forearm wristPivot",
  "P.WristL=[-1,1,0];P.WristR=[-1,1,0]; // v1.4: hand rotation about the forearm wristPivot\n"
  "P.RootX=[-40,40,0];P.RootY=[-40,40,0]; // v1.8: root (pelvis) translation in px, whole px on screen; 0 at rest")
R("groups['Body joints']=BODY_PARAMS;","groups['Body joints']=BODY_PARAMS;groups['Root (v1.8, px)']=['RootX','RootY'];")
# ---- root translation helper (after the T() helper)
R("const I=[1,0,0,1,0,0];const T=(dx,dy)=>[1,0,0,1,dx,dy];",
  "const I=[1,0,0,1,0,0];const T=(dx,dy)=>[1,0,0,1,dx,dy];\n"
  "// v1.8 root: translate every body bone/part (and so hands, face and hair) by whole px RootX/RootY; never at rest\n"
  "function rootApply(BM,rest){if(rest)return BM;const dx=Math.round(clamp(v.RootX||0,-40,40)),dy=Math.round(clamp(v.RootY||0,-40,40));if(!dx&&!dy)return BM;const RT=T(dx,dy);for(const k in BM)BM[k]=mul(RT,BM[k]);return BM}")
# rotAt: no near-zero snap; exact identity only for an exactly zero angle
R("function rotAt(px,py,deg){if(!(Math.abs(deg)>=0.01))return I;",
  "/* v1.8: only an exactly zero angle is identity (no 0.01 deg snap) */function rotAt(px,py,deg){if(!(Math.abs(deg)>0))return I;")
# drawM: pixel-exact only for rest or exact identity; posed axis-aligned transforms with fractional offsets are smoothed
R("const isAxis=M=>Math.abs(M[1])<1e-9&&Math.abs(M[2])<1e-9&&Math.abs(M[0]-1)<1e-9&&Math.abs(M[3]-1)<1e-9;",
  "const isAxis=M=>Math.abs(M[1])<1e-9&&Math.abs(M[2])<1e-9&&Math.abs(M[0]-1)<1e-9&&Math.abs(M[3]-1)<1e-9;\n"
  "// v1.8: POSED is set by render(); in posed frames an axis-aligned transform is drawn pixel-exact only when its offset is already whole px\n"
  "let POSED=false;const isWhole=M=>M[4]===Math.round(M[4])&&M[5]===Math.round(M[5]);")
R("if(isAxis(M)){g.setTransform(S,0,0,S,S*Math.round(M[4]),S*Math.round(M[5]));g.imageSmoothingEnabled=false}",
  "if(isAxis(M)&&(!POSED||isWhole(M))){g.setTransform(S,0,0,S,S*Math.round(M[4]),S*Math.round(M[5]));g.imageSmoothingEnabled=false}")
# render: set POSED, apply root to cut chain and skin chain
R("function render(g,rest){const im=R.im,Z=R.z;","function render(g,rest){POSED=!rest;const im=R.im,Z=R.z;")
R("if(R.body){const bps=R.body.parts;BM=chain(bps,rest?()=>0:bodyAngle,null,p=>p.parent!==undefined?p.parent:BODY_PARENT_OF[p.id]);",
  "if(R.body){const bps=R.body.parts;BM=rootApply(chain(bps,rest?()=>0:bodyAngle,null,p=>p.parent!==undefined?p.parent:BODY_PARENT_OF[p.id]),rest);")
R("const Sk=R.skin;BM=chain(Sk.bones,rest?()=>0:bodyAngle,null,p=>p.parent);",
  "const Sk=R.skin;BM=rootApply(chain(Sk.bones,rest?()=>0:bodyAngle,null,p=>p.parent),rest);")
# headPose for hair includes the root
R("const bps=R.body.parts;const BM=chain(bps,bodyAngle,null,p=>p.parent!==undefined?p.parent:BODY_PARENT_OF[p.id]);const hp=",
  "const bps=R.body.parts;const BM=rootApply(chain(bps,bodyAngle,null,p=>p.parent!==undefined?p.parent:BODY_PARENT_OF[p.id]),false);const hp=")
# body UI: root sliders enabled whenever a body rig is active
R("setBodyUI(!!(r.body||r.skin),drv);","setBodyUI(!!(r.body||r.skin),drv);groupBox['Root (v1.8, px)'].style.display=(r.body||r.skin)?'':'none';r.feet=footSetup(r);r.eyeW=eyeWidth(r);")
R("setBodyUI(false);","setBodyUI(false);groupBox['Root (v1.8, px)'].style.display='none';")
# ---- mouth: hold 120 ms, crossfade 35 ms or hard cut, talk excludes EE/EE_half/smile
R("function mouthPick(){const S=R.mouthShapes;",
  "// v1.8 talk driver: while auto talk is running, EE, EE_half and smile are not picked\n"
  "const TALK_EXCLUDE=new Set(['EE','EE_half','smile']);let mouthTalk=false;\n"
  "function mouthPick(){const S0=R.mouthShapes;const S=mouthTalk&&S0?S0.filter(s=>!TALK_EXCLUDE.has(s.name)):S0;")
R("const MOUTH_HOLD_MS=70,MOUTH_FADE_MS=60;let holdLog=null;",
  "const MOUTH_HOLD_MS=120,MOUTH_HOLD_TARGET_MS=125;let MOUTH_FADE_MS=35;let holdLog=null; // v1.8: min hold 120 ms (target 125), crossfade 35 ms or 0 = hard cut")
R("const pending=mouthUpdate(now);const st=mouthState;const a=Math.min(1,(now-st.t0)/MOUTH_FADE_MS);",
  "const pending=mouthUpdate(now);const st=mouthState;const a=MOUTH_FADE_MS>0?Math.min(1,(now-st.t0)/MOUTH_FADE_MS):1;")
# ---- auto mode (v1.8)
old_anim_start="function makeAnim(seed){const r=rng(seed);return{r,t:0,"
R(old_anim_start,"function makeAnim(seed){const r=rng(seed);return{r,t:0,lastBlinkEnd:-10,turn:{dir:0,ext:0,prevLean:null},")
# blink: 42 / 165 / 125 ms, every 2.5-5 s, no doubles, plus a blink when a head turn reverses
R("""function stepBlink(A){const b=A.blink,t=A.t;const C=0.075,Hd=0.035,O=0.17;
 if(b.t0<0&&t>=b.next){b.t0=t}
 let open=1;if(b.t0>=0){const u=t-b.t0;if(u<C)open=1-ease.inQ(u/C);else if(u<C+Hd)open=0;else if(u<C+Hd+O)open=ease.outC((u-C-Hd)/O);else{b.t0=-1;if(!b.dbl&&A.r()<0.18){b.dbl=true;b.next=t+0.09+A.r()*0.08}else{b.dbl=false;b.next=t+2+A.r()*4}}}
 set('EyeLOpen',open);set('EyeROpen',open)}""",
"""// v1.8 (Base Eyes): ~330 ms blink = snap shut 42 ms, hold 165 ms, reopen 125 ms; every 2.5-5 s at random; both eyes; plus one when a head turn reverses
const BLINK={close:0.042,hold:0.165,open:0.125,min:2.5,max:5.0,turnGap:1.5};
function stepBlink(A){const b=A.blink,t=A.t;const C=BLINK.close,Hd=BLINK.hold,O=BLINK.open;
 if(b.t0<0&&(t>=b.next||(b.turnReq&&t-A.lastBlinkEnd>=BLINK.turnGap))){b.t0=t;b.turnReq=false}
 let open=1;if(b.t0>=0){const u=t-b.t0;if(u<C)open=1-u/C;else if(u<C+Hd)open=0;else if(u<C+Hd+O)open=ease.outC((u-C-Hd)/O);else{b.t0=-1;A.lastBlinkEnd=t;b.next=t+BLINK.min+A.r()*(BLINK.max-BLINK.min)}}
 b.turnReq=false;set('EyeLOpen',open);set('EyeROpen',open)}
// v1.8 idle gaze: slow drift of ~0.1 eye width that follows the head sway and leads it by ~3 frames (0.1 s); no big glances
function stepGazeIdle(A){const t=A.t;const lead=0.1;const L=R.eyes&&R.eyes.irisLimitsPx;if(!L){set('EyeBallX',0);set('EyeBallY',0);return}
 const dir=Math.sign(headDirX())||1;const s=clamp(leanAt(A,t+lead)/IDLE.leanAmp,-1,1)*0.8+0.2*Math.sin(2*Math.PI*t/9.3+1.1);const px=dir*s*0.1*(R.eyeW||20);
 const x=px>=0?(L.dxAtXplus1>0?px/L.dxAtXplus1:0):(L.dxAtXminus1<0?px/(-L.dxAtXminus1):0);set('EyeBallX',clamp(x,-1,1));set('EyeBallY',0)}
// head turn reversal -> request a blink
function watchTurn(A){const lv=v.BodyLean;const T0=A.turn;if(T0.prevLean!=null){const d=lv-T0.prevLean;const s=Math.sign(d);if(s&&s!==T0.dir){if(T0.dir&&Math.abs(lv-T0.ext)>=0.05)A.blink.turnReq=true;T0.dir=s;T0.ext=lv}}T0.prevLean=lv}
// v1.8 idle mouth: rest, with Base Mouth's soft smile (MouthForm keys 2.5-4.9 s) once per 8 s loop
const IDLE_SMILE=[[0,0],[2.5,0],[2.55,0.0741],[2.6,0.2593],[2.65,0.5],[2.7,0.7407],[2.75,0.9259],[2.8,1],[4.6,1],[4.65,0.9259],[4.7,0.7407],[4.75,0.5],[4.8,0.2593],[4.85,0.0741],[4.9,0],[8,0]];
function keyLerp(ks,t){if(t<=ks[0][0])return ks[0][1];for(let i=1;i<ks.length;i++)if(t<=ks[i][0]){const[a,x]=ks[i-1],[b,y]=ks[i];return b>a?x+(y-x)*(t-a)/(b-a):y}return ks[ks.length-1][1]}
function stepMouthIdle(A){const u=((A.t%8)+8)%8;set('MouthOpen',0);set('MouthForm',clamp(keyLerp(IDLE_SMILE,u),-1,1))}""")
# body idle: readable but safe amplitudes
R("""function stepBody(A){const b=A.body,t=A.t,r=A.r;const breath=Math.sin(2*Math.PI*t/4.6);
 if(t>=b.next){b.w0=b.w;let w;do{w=[-1,0,1][Math.floor(r()*3)]}while(w===b.w1);b.w1=w;b.t0=t;b.next=t+7+r()*7}
 b.w=b.w0+(b.w1-b.w0)*ease.smooth(clamp((t-b.t0)/1.6,0,1));
 set('BodyLean',clamp(0.025*breath-0.02*b.w,-1,1));set('ShoulderL',0.012*breath);set('ShoulderR',-0.012*breath);
 set('HipL',0.03*b.w);set('HipR',0.03*b.w);set('KneeL',-0.03*b.w);set('KneeR',-0.03*b.w);set('AnkleL',0);set('AnkleR',0);set('ToeL',0.05*Math.max(0,b.w));set('ToeR',0.05*Math.max(0,-b.w));set('ElbowL',0.01*breath);set('ElbowR',-0.01*breath)}""",
"""// v1.8 idle body (rig units: limbs x25 deg, lean x8 deg): breathing lean +-1.76 deg, arm drift ~2.5 deg, hip drift/weight shift ~2.5 deg; root via foot plant
const IDLE={leanAmp:0.22,leanShift:0.06,armDrift:0.07,armBreath:0.03,elbow:0.06,hip:0.1,hipDrift:0.02};
function leanAt(A,t){const b=A.body;const w=b.w0+(b.w1-b.w0)*ease.smooth(clamp((t-b.t0)/1.6,0,1));return IDLE.leanAmp*Math.sin(2*Math.PI*t/4.6)-IDLE.leanShift*w}
function stepBody(A){const b=A.body,t=A.t,r=A.r;const breath=Math.sin(2*Math.PI*t/4.6);
 if(t>=b.next){b.w0=b.w;let w;do{w=[-1,0,1][Math.floor(r()*3)]}while(w===b.w1);b.w1=w;b.t0=t;b.next=t+7+r()*7}
 b.w=b.w0+(b.w1-b.w0)*ease.smooth(clamp((t-b.t0)/1.6,0,1));const J=IDLE;
 const dL=Math.sin(2*Math.PI*t/7.1+0.3),dR=Math.sin(2*Math.PI*t/6.4+1.9),dH=Math.sin(2*Math.PI*t/9.7+0.7);
 const lag=t-0.35,dLl=Math.sin(2*Math.PI*lag/7.1+0.3),dRl=Math.sin(2*Math.PI*lag/6.4+1.9);
 set('BodyLean',clamp(leanAt(A,t),-1,1));set('ShoulderL',J.armBreath*breath+J.armDrift*dL);set('ShoulderR',-J.armBreath*breath-J.armDrift*dR);
 set('ElbowL',J.elbow*dLl);set('ElbowR',-J.elbow*dRl);
 const h=J.hip*b.w+J.hipDrift*dH;set('HipL',h);set('HipR',h);set('KneeL',-h);set('KneeR',-h);set('AnkleL',0);set('AnkleR',0);set('ToeL',0.05*Math.max(0,b.w));set('ToeR',0.05*Math.max(0,-b.w))}
// direction the head moves on screen for BodyLean +1 (+1 = viewer's right)
function headDirX(){const bs=R.skin?R.skin.bones:(R.body?R.body.parts:[]);const tb=bs.find(p=>bodyParamOf(p)==='BodyLean');if(!tb)return 1;const s0=v.BodyLean;v.BodyLean=1;const a=bodyAngle(tb);v.BodyLean=s0;return Math.sign(a)||1}""")
# hair presets + per-tip clamp after chaining
R("""// damped springs, hierarchical: one phase per strand chain (root); each child follows its parent's drive with extra lag
function stepHair(A,dt){""",
"""// v1.8 hair spring presets (default unchanged until the user picks): f Hz, zeta, child low-pass s, gravity
const HAIR_PRESETS={default:{rf:1.1,rz:0.3,cf:1.0,cz:0.3,lp:0.09,g:0.8},A:{rf:4.0,rz:0.8,cf:4.0,cz:0.8,lp:0.03,g:0.4},B:{rf:2.0,rz:0.6,cf:2.0,cz:0.6,lp:0.05,g:0.8}};
let HAIR_PRESET='default';let hairClampLog=null;
// damped springs, hierarchical: one phase per strand chain (root); each child follows its parent's drive with extra lag
function stepHair(A,dt){const hpE=document.getElementById('hairpreset');HAIR_PRESET=hpE?hpE.value:HAIR_PRESET;const HP=HAIR_PRESETS[HAIR_PRESET]||HAIR_PRESETS.default;const byH={};for(const q of (R.hair||[]))byH[q.id]=q;const chainDeg={};""")
R("tx=clamp(-hp.a/6,-1,1)*0.8+0.16*Math.sin(2*Math.PI*0.23*t+ph)+0.07*Math.sin(2*Math.PI*0.61*t+1.7*ph);ty=0.12*Math.sin(2*Math.PI*0.31*t+ph);f=1.1;z=0.3;",
  "tx=clamp(-hp.a/6,-1,1)*HP.g+0.16*Math.sin(2*Math.PI*0.23*t+ph)+0.07*Math.sin(2*Math.PI*0.61*t+1.7*ph);ty=0.12*Math.sin(2*Math.PI*0.31*t+ph);f=HP.rf;z=HP.rz;")
R("const k=clamp(dt/0.09,0,1);","const k=clamp(dt/HP.lp,0,1);")
R("tx=s.lx*0.9+0.04*Math.sin(2*Math.PI*0.4*t+ph+d);ty=s.ly*0.8;f=1.0;z=0.3}",
  "tx=s.lx*0.9+0.04*Math.sin(2*Math.PI*0.4*t+ph+d);ty=s.ly*0.8;f=HP.cf;z=HP.cz}")
R("  s.x=clamp(s.x,-1,1);s.y=clamp(s.y,-1,1);out[p.id]={x:s.x,y:s.y}}",
"""  s.x=clamp(s.x,-1,1);s.y=clamp(s.y,-1,1);
  // v1.8: a chained segment's total angle (ancestors + own) never exceeds its own limit swayWeight*maxSwayDeg
  const wd=(p.swayWeight||0)*(p.maxSwayDeg||0);let anc=0;{let q=p.parent&&byH[p.parent];let n=0;while(q&&n++<20){anc+=chainDeg[q.id]||0;q=q.parent&&byH[q.parent]}}
  if(inf.parent&&wd){const lim=Math.abs(wd);const tot=anc+wd*s.x;const tc=clamp(tot,-lim,lim);if(tc!==tot){s.x=clamp((tc-anc)/wd,-1,1);s.vx=0;if(hairClampLog)hairClampLog.push(p.id)}}
  chainDeg[p.id]=wd*s.x;out[p.id]={x:s.x,y:s.y}}""")
# animStep: style, turn watch, foot plant
R("function animStep(A,dt,o){A.t+=dt;if(o.face){stepBlink(A);stepGaze(A);if(R.mouth)stepTalk(A,dt)}if(o.body&&R.body)stepBody(A);if(o.hair&&R.hair)stepHair(A,dt)}",
"""function autoStyle(){const e=document.getElementById('autostyle');return e?e.value:'idle'}
function animStep(A,dt,o){A.t+=dt;const talk=autoStyle()==='talk';
 if(o.body&&R.body){stepBody(A);if(!o.rootKeyed)footPlantApply()}
 watchTurn(A);
 if(o.face){mouthTalk=talk&&!!R.mouth;stepBlink(A);if(talk)stepGaze(A);else stepGazeIdle(A);if(R.mouth){if(talk)stepTalk(A,dt);else stepMouthIdle(A)}}
 if(o.hair&&R.hair)stepHair(A,dt)}
// ---- v1.8 foot plant: when RootX/RootY are not keyed, offset the root so the lower foot stays on the rest foot line
// (mode 'xy' also keeps the planted foot's x at its rest x; the planted foot is blended smoothly by height so nothing pops)
function footSetup(r){const out={L:null,R:null,line:null};const Sk=r.skin;
 const pick=s=>['foot_'+s,'toes_'+s];
 if(Sk){const bi=Object.fromEntries(Sk.bones.map((b,i)=>[b.id,i]));let line=-1e9;
  for(const s of['L','R']){const ids=new Set(pick(s).map(id=>bi[id]).filter(x=>x!=null));if(!ids.size)continue;let ymax=-1e9;const cand=[];
   for(let i=0;i<Sk.nv;i++){let best=-1,bw=-1;for(let k=0;k<4;k++){const w=Sk.ww[i*4+k];if(w>bw){bw=w;best=Sk.wb[i*4+k]}}if(ids.has(best)){cand.push(i);if(Sk.V[2*i+1]>ymax)ymax=Sk.V[2*i+1]}}
   const sole=cand.filter(i=>Sk.V[2*i+1]>=ymax-30);if(!sole.length)continue;line=Math.max(line,ymax);
   out[s]={pts:sole.map(i=>({x:Sk.V[2*i],y:Sk.V[2*i+1],w:[0,1,2,3].map(k=>[Sk.wb[i*4+k],Sk.ww[i*4+k]]).filter(q=>q[1]>0)})),restX:sole.reduce((a,i)=>a+Sk.V[2*i],0)/sole.length}}
  out.line=line>-1e9?line:null;out.bones=Sk.bones;return out}
 if(r.body){let line=-1e9;for(const s of['L','R']){const pts=[];for(const id of pick(s)){const im=r.im['body:'+id];if(!im||im.empty)continue;const y=im.oy+im.height-1;for(let k=0;k<=8;k++)pts.push({x:im.ox+k*(im.width-1)/8,y,part:id});line=Math.max(line,y)}if(pts.length)out[s]={pts,restX:pts.reduce((a,p)=>a+p.x,0)/pts.length}}out.line=line>-1e9?line:null;return out}
 return out}
function footPlantMode(){const e=document.getElementById('footplant');return e?e.value:'xy'}
function footPlantApply(){const F=R&&R.feet;const mode=footPlantMode();if(!F||F.line==null||mode==='off'||!(F.L||F.R)){return null}
 const bones=R.skin?R.skin.bones:R.body.parts;const BM=chain(bones,bodyAngle,null,R.skin?(p=>p.parent):(p=>p.parent!==undefined?p.parent:BODY_PARENT_OF[p.id]));const Ms=R.skin?R.skin.bones.map(b=>BM[b.id]||I):null;
 const foot=s=>{const f=F[s];if(!f)return null;let ymax=-1e9,sx=0;for(const p of f.pts){let x=0,y=0;if(Ms){for(const[b,w]of p.w){const M=Ms[b];x+=w*(M[0]*p.x+M[2]*p.y+M[4]);y+=w*(M[1]*p.x+M[3]*p.y+M[5])}}else{const M=BM[p.part]||I;x=M[0]*p.x+M[2]*p.y+M[4];y=M[1]*p.x+M[3]*p.y+M[5]}if(y>ymax)ymax=y;sx+=x}return{y:ymax,dx:sx/f.pts.length-f.restX}};
 const a=foot('L'),b=foot('R');const ys=[a,b].filter(Boolean);const low=Math.max(...ys.map(q=>q.y));const ry=clamp(F.line-low,-40,40);let rx=0;
 if(mode==='xy'){if(a&&b){const wa=1/(1+Math.exp(-(a.y-b.y)/2));rx=-(wa*a.dx+(1-wa)*b.dx)}else rx=-(a||b).dx;rx=clamp(rx,-40,40)}
 set('RootX',rx);set('RootY',ry);return{rx,ry,lowFoot:a&&b?(a.y>=b.y?'L':'R'):(a?'L':'R')}}
function eyeWidth(r){if(!r.eyes)return 0;const ms=r.eyes.measurements||{};const ws=[];for(const E of r.eyes.eyes){const o=ms[E]&&ms[E].opening_bbox;if(Array.isArray(o)&&o.length===4)ws.push(o[2]-o[0]+1);else{const im=r.im['eyes:'+E+'_white'];if(im&&!im.empty)ws.push(im.width)}}return ws.length?ws.reduce((a,b)=>a+b,0)/ws.length:0}""")
# loop: talk flag off when auto is off
R("if(!on||!R||mqRunning){if(anim&&!mqRunning){anim=null;hairDrive=null;draw()}lastTs=ts;return}",
  "if(!on||!R||mqRunning){if(!mqRunning)mouthTalk=false;if(anim&&!mqRunning){anim=null;hairDrive=null;draw()}lastTs=ts;return}")
# rest button resets root too (P loop already covers RootX/RootY) and talk flag
R("document.getElementById('rest').onclick=()=>{for(const k in P)set(k,P[k][2]);hairDrive=null;draw()};",
  "document.getElementById('rest').onclick=()=>{for(const k in P)set(k,P[k][2]);hairDrive=null;mouthTalk=false;draw()};\n"
  "// v1.8 settings: UI selects + URL (?auto=talk|idle, ?footplant=xy|y|off, ?hair=default|A|B, ?mouthfade=35|0)\n"
  "{const q=new URLSearchParams(location.search);for(const[k,id]of[['auto','autostyle'],['footplant','footplant'],['hair','hairpreset'],['mouthfade','mouthfade'],['quality','quality']]){const x=q.get(k);const e=document.getElementById(id);if(x!=null&&[...e.options].some(o=>o.value===x))e.value=x}\n"
  " const mf=document.getElementById('mouthfade');MOUTH_FADE_MS=+mf.value;mf.onchange=()=>{MOUTH_FADE_MS=+mf.value};QUAL=document.getElementById('quality').value}")
# motion test: the flicker threshold follows the new hold
R("(minHold<MOUTH_HOLD_MS-0.5?' (FLICKER)':'')","(minHold<MOUTH_HOLD_MS-0.5?' (FLICKER)':'')")
# motion test resets talk flag in finally
R("finally{simNow=null;holdLog=null;hairDrive=null;for(const k in P)set(k,saved[k]);mouthState=savedMouth;mqRunning=false;draw()}",
  "finally{simNow=null;holdLog=null;hairDrive=null;mouthTalk=false;for(const k in P)set(k,saved[k]);mouthState=savedMouth;mqRunning=false;draw()}")
open(dst,'w').write(s);print('ok',len(s))
