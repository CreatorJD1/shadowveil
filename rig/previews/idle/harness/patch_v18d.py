# v1.8 part 4: Life uses Body's idle_arm_sway as its base; gaze sized to the 1-3 px iris limits; render-only stress bypass
import sys
src,dst=sys.argv[1],sys.argv[2]
s=open(src).read()
def R(old,new,count=1):
    global s
    n=s.count(old)
    if n!=count: raise SystemExit(f'patch anchor found {n}x (want {count}): {old[:90]!r}')
    s=s.replace(old,new)
# stress bypass: off by default; only stressEnable(clip) with clip.stressTest===true turns it on (render-only; rest and the guard are unaffected)
R("function bodyAngle(p){const k=bodyParamOf(p);if(!k||!(k in v))return 0;const x=clamp(v[k],-1,1);",
  "// v1.8 stress: render-only clamp bypass for Body's stressTest clips (wanted angles beyond +-1, root beyond +-40 px); default off\n"
  "let STRESS=false;function stressEnable(clip){STRESS=!!(clip&&clip.stressTest===true);return STRESS}const rootLim=()=>STRESS?400:40;\n"
  "function bodyAngle(p){const k=bodyParamOf(p);if(!k||!(k in v))return 0;const x=STRESS?(+v[k]||0):clamp(v[k],-1,1);")
R("const dx=Math.round(clamp(v.RootX||0,-40,40)),dy=Math.round(clamp(v.RootY||0,-40,40));","const dx=Math.round(clamp(v.RootX||0,-rootLim(),rootLim())),dy=Math.round(clamp(v.RootY||0,-rootLim(),rootLim()));")
# Life base: Body's idle_arm_sway (8 s loop), scaled by Life; our procedural layers go on top
R("function lifeAmt(){",
  "let LIFE_BASE=null;fetch('../body_tools/idle/idle_clips.json').then(r=>r.json()).then(j=>{LIFE_BASE=(j.clips&&j.clips.idle_arm_sway)||null}).catch(()=>{LIFE_BASE=null});\n"
  "function lifeBase(t){const c=LIFE_BASE;const o={};if(!c)return o;const vw=document.getElementById('view').value;const ks=Object.assign({},c.keys||{},(c.viewKeys||{})[vw]||{});const d=c.duration||8;const u=c.loop?((t%d)+d)%d:t;\n"
  " for(const k of [...BODY_PARAMS,'WristL','WristR'])if(ks[k]&&ks[k].length)o[k]=keyLerp(ks[k],u);return o}\n"
  "function lifeAmt(){")
R("shBreath:0.04,shDrift:0.07,elDrift:0.08,wrDrift:0.1,","shBreath:0.04,shDrift:0.05,elDrift:0.03,wrDrift:0.08,")
R("LIFE={breathT:4.0,wMin:6,wMax:10,hip:0.055,","LIFE={breathT:4.0,wMin:6,wMax:10,hip:0.08,")
R("sacEvery:[0.8,2.0],sacPx:0.06,gazeLead:0.1,","sacEvery:[0.8,2.0],sacPx:0.03,gazeDrift:0.04,gazeLead:0.1,")
R("const px=L*(dir*ahead*0.1*ew+sc.x*ew)","const px=L*(dir*ahead*LIFE.gazeDrift*ew+sc.x*ew)")
R(" const br=Math.sin(2*Math.PI*t/LIFE.breathT),inh=(br+1)/2,w=lifeW(Lf);",
  " const br=Math.sin(2*Math.PI*t/LIFE.breathT),inh=(br+1)/2,w=lifeW(Lf);const B=lifeBase(t);const bv=k=>L*(B[k]||0);")
R("const leanT=L*(-LIFE.lean*w*(f?0.5:1)+LIFE.leanBreath*br);","const leanT=L*(-LIFE.lean*w*(f?0.5:1)+LIFE.leanBreath*br)+bv('BodyLean');")
R("  const sh=clamp(spr(sp('sh'+sd),shT,dt,LIFE.spF,LIFE.spZ),-1,1);","  const sh=clamp(spr(sp('sh'+sd),shT+bv('Shoulder'+sd),dt,LIFE.spF,LIFE.spZ),-1,1);")
R("*(f?pm:out(sd));\n  const faW=","*(f?pm:out(sd))+bv('Elbow'+sd);\n  const faW=")
R("set('Elbow'+sd,clamp(lifePar(S,'Elbow'+sd,faW-Uw),-0.35,0.35));","set('Elbow'+sd,clamp(lifePar(S,'Elbow'+sd,faW-Uw),-1,1));")
R("const hW=spr(sp('hand'+sd),faNow+LIFE.wristDeg*wrB,dt,LIFE.spF,LIFE.spZ);set('Wrist'+sd,clamp((hW-faNow)/LIFE.wristDeg,-0.35,0.35));",
  "const hW=spr(sp('hand'+sd),faNow+LIFE.wristDeg*(wrB+bv('Wrist'+sd)),dt,LIFE.spF,LIFE.spZ);set('Wrist'+sd,clamp((hW-faNow)/LIFE.wristDeg,-0.6,0.6));")
open(dst,'w').write(s);print('ok',len(s))
