# v1.8 part 3 (applied to the output of patch_v18b.py): one resampling path for posed frames, mouth crossfade fix + tie rule,
# blink timing, and the procedural "Life" layer for the idle style
import sys
src,dst=sys.argv[1],sys.argv[2]
s=open(src).read()
def R(old,new,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'patch anchor found {n}x (want {count}): {old[:90]!r}')
    s=s.replace(old,new)
# ---- (1) flicker: posed frames always take the same path (2x supersampled, linear), no 0-angle / axis-aligned special case
R("let QUAL='linear';","let QUAL='ss2'; // v1.8: posed frames default to 2x supersampled so every angle (incl. exactly 0) goes through one resampling path")
R('<option value="linear">linear</option><option value="ss2">2x supersampled</option>','<option value="linear">linear</option><option value="ss2" selected>2x supersampled</option>')
R(" if(isAxis(M)&&(!POSED||isWhole(M))){"," if(isAxis(M)&&!POSED){")
R("meshDraw(Sk,grs,(pose.ident||QUAL==='nearest')?'nearest':'linear',g.__S||1)","meshDraw(Sk,grs,(pose.rest||QUAL==='nearest')?'nearest':'linear',g.__S||1)")
R("meshDraw(U,[{start:0,count:U.nt}],(poseIdent(pose)||QUAL==='nearest')?'nearest':'linear',g.__S||1)","meshDraw(U,[{start:0,count:U.nt}],(pose.rest||QUAL==='nearest')?'nearest':'linear',g.__S||1)")
# ---- (2) mouth crossfade: incoming already >0 on the switch frame; outgoing fades out over the last half (no opaque underlay)
R("const a=MOUTH_FADE_MS>0?Math.min(1,(now-st.t0)/MOUTH_FADE_MS):1;",
  "const el=now-st.t0,FD=MOUTH_FADE_MS;const a=FD>0?clamp((el+FD/4)/FD,0,1):1;const aOut=FD>0?(el<FD/2?1:clamp(1-(el-FD/2)/(FD/2),0,1)):0;const inFade=FD>0&&el<FD&&!!st.prev;")
R("const fading=a<1&&st.prev;if(fading)add(zm(st.cur),STEP.mouth,g=>drawM(g,need('mouth:'+st.prev,im['mouth:'+st.prev]),headM),",
  "const fading=inFade;if(fading&&aOut>0)add(zm(st.cur),STEP.mouth,g=>drawM(g,need('mouth:'+st.prev,im['mouth:'+st.prev]),headM,aOut),")
R("info:'opacity 1.00 (underneath)'","info:'opacity '+f1(aOut)+' (underneath, fades over the last half)'")
R("if((a<1&&st.prev)||pending){","if(inFade||pending){")
# tie rule: an exact tie between rest and another shape resolves to the other (target) shape; at the rest point rest has distance 0 and wins
R("s.name==='rest'?0:1","s.name==='rest'?1:0")
# ---- (3) blinks: 42 ms snap shut, 165 ms hold, 125 ms ease-in reopen (reads shut, open<0.5, for ~250 ms; total ~330 ms); >=2.5 s apart incl. turn blinks
R("const BLINK={close:0.042,hold:0.165,open:0.125,min:2.5,max:5.0,turnGap:1.5};","const BLINK={close:0.042,hold:0.165,open:0.125,min:2.5,max:5.0,turnGap:2.5};")
R("else if(u<C+Hd+O)open=ease.outC((u-C-Hd)/O)","else if(u<C+Hd+O)open=ease.inQ((u-C-Hd)/O)")
# ---- (4) Life UI + URL
R('<label><span>Auto style (v1.8)</span>',
  '<label><span>Life (v1.8, idle)</span><input type="range" id="life" min="0" max="1" step="0.05" value="1"></label>\n<label><span>Auto style (v1.8)</span>')
R("QUAL=document.getElementById('quality').value}",
  "QUAL=document.getElementById('quality').value;const lq=q.get('life');if(lq!=null&&isFinite(+lq))document.getElementById('life').value=clamp(+lq,0,1)}")
LIFE_JS=r"""
// ---- v1.8 Life: layered procedural secondary motion for the idle style (amount 0..1: UI 'Life', URL life=; never at rest)
// breathing 4 s, weight shift 6-10 s (hips + foot plant -> pelvis sway, torso counter-tilt, profile knee give), overlapping
// follow-through (torso -> head via HeadTilt/HeadNod, upper arm -> forearm -> hand as damped followers), finger drift,
// micro-saccades leading the head, occasional smile / M press. Rig units: limbs x25 deg, lean x8 deg, tilt x8 deg, nod x6 deg / 4 px.
const LIFE={breathT:4.0,wMin:6,wMax:10,hip:0.055,lean:0.2,leanBreath:0.04,headDrift:2.0,headKeep:0.45,nodBreath:0.3,nodBreathProf:0.1,
 shBreath:0.04,shDrift:0.07,elDrift:0.08,wrDrift:0.1,fLo:0.05,fHi:0.15,fCapTpose:0.12,give:0.04,spF:2.2,spZ:0.55,leanF:1.6,leanZ:0.6,wristDeg:25,
 sacEvery:[0.8,2.0],sacPx:0.06,gazeLead:0.1,mouthEvery:[6,12]};
function lifeAmt(){const e=document.getElementById('life');return e?clamp(+e.value,0,1):1}
function spr(s,x,dt,f,z){if(s.y==null){s.y=x;s.v=0}const K=(2*Math.PI*f)**2,D=2*z*2*Math.PI*f;const n=Math.max(1,Math.ceil(dt/(1/240))),h=dt/n;for(let i=0;i<n;i++){s.v+=(K*(x-s.y)-D*s.v)*h;s.y+=s.v*h}return s.y}
function lifeSlopes(){const bs=R.skin?R.skin.bones:(R.body?R.body.parts:[]);const o={};for(const k of BODY_PARAMS){const b=bs.find(p=>bodyParamOf(p)===k);if(!b){o[k]=[0,0];continue}const s0=v[k];v[k]=1;const a1=bodyAngle(b);v[k]=-1;const am=bodyAngle(b);v[k]=s0;o[k]=[a1,am]}return o}
const lifeDeg=(S,k,x)=>x>=0?x*S[k][0]:-x*S[k][1];
const lifePar=(S,k,d)=>{const[a1,am]=S[k];if(a1&&d/a1>=0)return d/a1;if(am)return -d/am;return 0};
function lifeW(Lf,dtAhead){return Math.sin(2*Math.PI*(Lf.ph+(dtAhead||0)/Lf.P))}
function lifeInit(A){return A.life||(A.life={ph:A.r(),P:LIFE.wMin+A.r()*(LIFE.wMax-LIFE.wMin),S:lifeSlopes(),sp:{},mouth:{next:2.5+A.r()*3,t0:-1,kind:null,dur:0},sac:{next:0.4+A.r(),x:0,y:0},log:{}})}
function stepLife(A,dt){const L=lifeAmt(),t=A.t,Lf=lifeInit(A),S=Lf.S,sp=k=>Lf.sp[k]||(Lf.sp[k]={});const f=headFacing();const view=document.getElementById('view').value;
 Lf.ph+=dt/Lf.P;if(Lf.ph>=1){Lf.ph-=1;Lf.P=LIFE.wMin+A.r()*(LIFE.wMax-LIFE.wMin)}
 const br=Math.sin(2*Math.PI*t/LIFE.breathT),inh=(br+1)/2,w=lifeW(Lf);
 const out=sd=>(sd==='L'?-1:1)*(view==='back'?-1:1);const pm=view==='right'?-1:1;
 // weight shift (legs; foot plant then moves the root so the planted feet stay put)
 const h=L*LIFE.hip*w;const leg={};
 for(const sd of['L','R']){if(f){const g=L*LIFE.give*Math.max(0,sd==='L'?w:-w);const hip=h+g/2,knee=-Math.max(0,h)-g,ank=-(hip+knee);leg[sd]=[hip*pm,knee*pm,ank*pm]} // canonical: hip +flex, knee <=0 (flexion only), foot kept flat
  else leg[sd]=[h,-h,0]} // front/back: thighs sway together, shins stay vertical (feet flat)
 for(const sd of['L','R']){set('Hip'+sd,leg[sd][0]);set('Knee'+sd,leg[sd][1]);set('Ankle'+sd,leg[sd][2]);set('Toe'+sd,0)}
 // torso: counter-tilt against the sway + breath, as a damped follower (settles after the hips)
 const leanT=L*(-LIFE.lean*w*(f?0.5:1)+LIFE.leanBreath*br);const lean=clamp(spr(sp('lean'),leanT,dt,LIFE.leanF,LIFE.leanZ),-1,1);set('BodyLean',lean);
 const torsoDeg=lifeDeg(S,'BodyLean',lean);
 // head: stabilises (keeps ~45% of the torso angle) + its own slow drift, followed with lag/overshoot; lag = the head param
 const hdT=torsoDeg*LIFE.headKeep+L*LIFE.headDrift*(f?0.6:1)*Math.sin(2*Math.PI*t/5.7+0.9);const hd=spr(sp('head'),hdT,dt,LIFE.spF,LIFE.spZ);const lag=hd-torsoDeg;
 if(f){set('HeadTilt',0);set('HeadNod',clamp(lag/(HEAD_NOD_DEG*f)-L*LIFE.nodBreathProf*br,-1,1))}
 else{set('HeadTilt',clamp(lag/HEAD_TILT_DEG,-1,1));set('HeadNod',clamp(-L*LIFE.nodBreath*inh,-1,1))}
 // arms: shoulder (breath lift + drift) -> forearm -> hand, each a damped follower of its parent's world angle
 const ph={L:0.3,R:1.9};
 for(const sd of['L','R']){
  const shT=f?L*LIFE.shDrift*Math.sin(2*Math.PI*t/7.1+ph[sd])*pm:out(sd)*L*(LIFE.shBreath*inh+LIFE.shDrift*Math.sin(2*Math.PI*t/7.1+ph[sd]));
  const sh=clamp(spr(sp('sh'+sd),shT,dt,LIFE.spF,LIFE.spZ),-1,1);set('Shoulder'+sd,sh);
  const Uw=torsoDeg+lifeDeg(S,'Shoulder'+sd,sh);
  const elB=L*LIFE.elDrift*Math.sin(2*Math.PI*(t-0.3)/6.3+ph[sd]+0.8)*(f?pm:out(sd));
  const faW=spr(sp('fa'+sd),Uw+lifeDeg(S,'Elbow'+sd,elB),dt,LIFE.spF,LIFE.spZ);set('Elbow'+sd,clamp(lifePar(S,'Elbow'+sd,faW-Uw),-0.35,0.35));
  if(R.hands){const faNow=Uw+lifeDeg(S,'Elbow'+sd,v['Elbow'+sd]);const wrB=L*LIFE.wrDrift*Math.sin(2*Math.PI*(t-0.45)/5.1+ph[sd]+1.7);
   const hW=spr(sp('hand'+sd),faNow+LIFE.wristDeg*wrB,dt,LIFE.spF,LIFE.spZ);set('Wrist'+sd,clamp((hW-faNow)/LIFE.wristDeg,-0.35,0.35));
   const cap=view==='tpose'?LIFE.fCapTpose:LIFE.fHi;['Thumb','Index','Middle','Ring','Pinky'].forEach((n,i)=>{const c=LIFE.fLo+(LIFE.fHi-LIFE.fLo)*(0.5+0.5*Math.sin(2*Math.PI*t/5.3+i*1.1+(sd==='R'?2.1:0)));set('Hand'+sd+n,L>0?clamp(c*L,0,cap):0)})}}
 Lf.log={br,w,h,lean,lag,P:Lf.P}}
// eyes: slow drift that leads the head sway by ~3 frames + micro-saccades (whole-px iris jumps) every 0.8-2 s
function stepGazeLife(A){const L=lifeAmt(),t=A.t,Lf=lifeInit(A);const Lm=R.eyes&&R.eyes.irisLimitsPx;if(!Lm){set('EyeBallX',0);set('EyeBallY',0);return}
 const sc=Lf.sac;if(t>=sc.next){sc.x=(A.r()*2-1)*LIFE.sacPx;sc.y=(A.r()*2-1)*LIFE.sacPx*0.5;sc.next=t+LIFE.sacEvery[0]+A.r()*(LIFE.sacEvery[1]-LIFE.sacEvery[0])}
 const dir=Math.sign(headDirX())||1;const ahead=-lifeW(Lf,LIFE.gazeLead)*(headFacing()?0.5:1);const ew=R.eyeW||20;
 const px=L*(dir*ahead*0.1*ew+sc.x*ew),py=L*sc.y*ew;const nx=px>=0?(Lm.dxAtXplus1>0?px/Lm.dxAtXplus1:0):(Lm.dxAtXminus1<0?px/(-Lm.dxAtXminus1):0);
 const ny=py>=0?(Lm.dyAtYplus1>0?py/Lm.dyAtYplus1:0):(Lm.dyAtYminus1<0?py/(-Lm.dyAtYminus1):0);set('EyeBallX',clamp(nx,-1,1));set('EyeBallY',clamp(ny,-1,1))}
// mouth: rest, with an occasional soft smile (1.6-2.6 s) or a short M press (0.5-0.9 s), 6-12 s apart; one switch in, one out
function stepMouthLife(A){const L=lifeAmt(),t=A.t,Lf=lifeInit(A),m=Lf.mouth;set('MouthOpen',0);
 if(L<=0){set('MouthForm',0);return}
 if(m.t0<0&&t>=m.next){m.t0=t;m.kind=A.r()<0.65?'smile':'M';m.dur=m.kind==='smile'?1.6+A.r():0.5+A.r()*0.4}
 let e=0;if(m.t0>=0){const u=t-m.t0,rp=0.12;e=u<rp?ease.smooth(u/rp):u<m.dur-rp?1:u<m.dur?ease.smooth((m.dur-u)/rp):0;if(u>=m.dur){m.t0=-1;m.next=t+LIFE.mouthEvery[0]+A.r()*(LIFE.mouthEvery[1]-LIFE.mouthEvery[0])}}
 const Ms=(R.mouthShapes||[]).find(q=>q.name==='M');const tg=m.kind==='M'&&Ms?{o:Ms.open,f:Ms.form}:{o:0,f:1};
 set('MouthOpen',clamp(e*tg.o,0,1));set('MouthForm',clamp(e*tg.f,-1,1))}
function autoStyle(){"""
R("function autoStyle(){",LIFE_JS)
R("""function animStep(A,dt,o){A.t+=dt;const talk=autoStyle()==='talk';
 if(o.body&&R.body){stepBody(A);if(!o.rootKeyed)footPlantApply()}""",
"""function animStep(A,dt,o){A.t+=dt;const talk=autoStyle()==='talk';
 if(o.body&&R.body){if(talk)stepBody(A);else stepLife(A,dt);if(!o.rootKeyed)footPlantApply()}""")
R("if(talk)stepGaze(A);else stepGazeIdle(A);if(R.mouth){if(talk)stepTalk(A,dt);else stepMouthIdle(A)}",
  "if(talk)stepGaze(A);else if(o.body)stepGazeLife(A);else stepGazeIdle(A);if(R.mouth){if(talk)stepTalk(A,dt);else if(o.body)stepMouthLife(A);else stepMouthIdle(A)}")
open(dst,'w').write(s);print('ok',len(s))
