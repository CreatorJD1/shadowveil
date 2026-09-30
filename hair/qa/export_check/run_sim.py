import json,math,sys
sys.path.insert(0,'/workspace/shadowveil/hair/qa/export_check')
from sim import *
PRE,TAIL=4.0,5.0; dt=1/60
MODES=['ref','rig8','rig12']
res=[];worst={}
for v in VIEWS:
    V=load_view(v); parts={p['id']:p for p in V['hair'] if V['info'][p['id']]['sway']}
    for c in CLIPS:
        dur,fps,frames=clip_frames(c); loops=1 if dur>1 else 3
        for mode in MODES:
            def drive(t,act=True):
                u=t-PRE
                J=sample(frames,fps,dur,u) if (act and 0<=u<dur*loops) else dict(torso=0,hinge=0,neck=0,head=0)
                return head_pose(V,J,mode)
            T=PRE+dur*loops+TAIL
            for sn,S in SETTINGS.items():
                rec=simulate(V,S,drive,T); base=simulate(V,S,lambda t:drive(t,False),T)
                hpk=max(abs(r[1][0]) for r in rec)
                row=dict(view=v,clip=c,mode=mode,setting=sn,headPeakDeg=round(hpk,2),parts={})
                end=PRE+dur*loops
                for pid,p in parts.items():
                    w=p.get('swayWeight') or 0; mx=p.get('maxSwayDeg') or 0; eff=w*mx
                    par=V['info'][pid]['parent']
                    pk=(0,None);over=[];dpk=(0,0);chain=(0,None)
                    for (t,hp,o),(tb,hb,ob) in zip(rec,base):
                        x,raw=o[pid][0],o[pid][1]; a=eff*x; u=t-PRE
                        fr=(int(math.floor(u*fps))%len(frames), int(u//dur)) if 0<=u<dur*loops else ('rest', round(u-dur*loops,2) if u>=0 else 'pre')
                        if t<PRE-1e-9: continue
                        if abs(a)>abs(pk[0]): pk=(a,fr,round(t,3))
                        if abs(raw)>1: over.append((fr,round(eff*(abs(raw)-1),2),round(t,3)))
                        dl=x-ob[pid][0]
                        if t<end and abs(dl)>abs(dpk[0]): dpk=(dl,t)
                        if par:
                            ca=a+ (parts[par].get('swayWeight') or 0)*(parts[par].get('maxSwayDeg') or 0)*o[par][0]
                            if abs(ca)>abs(chain[0]): chain=(ca,fr,round(t,3))
                    # rebound + settle after clip end
                    post=[(t,o[pid][0]-ob[pid][0]) for (t,hp,o),(tb,hb,ob) in zip(rec,base) if t>=end]
                    reb=max([-d*math.copysign(1,dpk[0]) for t,d in post]+[0]) if dpk[0] else 0
                    settle=0.0
                    for t,d in post:
                        if abs(d)>=0.05: settle=t-end
                    settle=None if (post and abs(post[-1][1])>=0.05) else round(settle,2)
                    ovr=None
                    if hpk>=6: ovr=round(100*(abs(dpk[0])-S['g'])/S['g'],1)
                    row['parts'][pid]=dict(w=w,maxSwayDeg=mx,limEff=round(eff,2),peakDeg=round(pk[0],2),peakAt=pk[1],peakT=pk[2],
                        overMaxSway=round(abs(pk[0])-mx,2) if abs(pk[0])>mx else 0,
                        satFrames=sorted({str(f[0]) for f in over}), satMaxOverDeg=max([f[1] for f in over]+[0]),
                        chainPeakDeg=round(chain[0],2) if par else None, chainAt=chain[1] if par else None,
                        chainOverTipMax=round(abs(chain[0])-mx,2) if par and abs(chain[0])>mx else 0,
                        headDrivenPeak=round(dpk[0],3), overshootPct=ovr, reboundNorm=round(reb,3), settleS=settle)
                    key=(v,sn,mode)
                    if abs(pk[0])/max(eff,1e-9)>worst.get(key,(0,))[0]:
                        worst[key]=(abs(pk[0])/max(eff,1e-9),c,pk[2])
                res.append(row)
        print(v,c,flush=True)
json.dump(res,open(OUT+'/sim_results.json','w'),indent=0)
json.dump({'|'.join(k):v for k,v in worst.items()},open(OUT+'/worst.json','w'),indent=1)
